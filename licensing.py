"""
licensing.py — activation code (license) client.

The app asks the license server (Next.js + Postgres) to activate a code for this machine. The server
answers with a signed payload; the app keeps it in %LOCALAPPDATA%\\EvonyBot\\license.json and checks the
signature (Ed25519, public key below) so the file cannot be edited or copied to another machine.

Server contract (JSON over HTTPS), both endpoints take {"code", "hwid", "app_version"}:
    POST {API_URL}/activate   first activation (binds this hwid to the code)
    POST {API_URL}/verify     refresh: is the code still valid for this hwid; also carries
                              "running_devices": [serial, ...] (emulators with a bot running) and "peak_devices": int (most
                              bots running at once since the last report); the server
                              answers {"ok": false, "error": "device_limit"} when there are more than max_devices
  ok     -> {"ok": true,  "payload": "<JSON text>", "signature": "<base64 Ed25519 over payload bytes>"}
            payload JSON = {"code", "hwid", "issued_at", "expires_at", "max_devices"}  (ISO 8601 UTC; expires_at null = no expiry;
                                     max_devices = số giả lập chạy cùng lúc, thiếu/null = không giới hạn)
  failed -> {"ok": false, "error": "<invalid_code|revoked|expired|customer_limit|...>"}
"""
import base64
import hashlib
import json
import os
import platform
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

from cryptography.exceptions import InvalidSignature
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# installer/config_key.py is git-ignored: from source it is found through the installer folder; in the built app
# installer/build.ps1 compiles it into the app, where the plain import finds it.
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "installer"))
try:
    from config_key import CONFIG_KEY_B64
except ImportError:
    CONFIG_KEY_B64 = ""

from database import DATA_DIR
from updater import _SSL
from version import __version__

API_URL = "https://evony-bot-admin-self.vercel.app/api/license"
ADMIN_CONTACT = ""   # added to the license notices as "Contact: ...", e.g. "Zalo 09xx xxx xxx - email@example.com"
# Ed25519 public key (raw 32 bytes, base64) matching the server's private signing key.
PUBLIC_KEY_B64 = "NFk+b9b9URDa8hLorZRGCZljj08Yw406on/3fWJR0Ns="
OFFLINE_GRACE = timedelta(hours=72)           # how long a signed answer stays usable without reaching the server
LICENSE_PATH = DATA_DIR / "license.json"
# The gist holds one encrypted line (installer/license_config.py encrypt <address>): the license server's address. Changing the
# server only needs a gist edit. Answers stay Ed25519-signed, so a wrong server cannot forge a license.
CONFIG_URL = "https://gist.githubusercontent.com/evony428/847a42a99d48dfcd6d0e78f8c7b58f95/raw"
CONFIG_AAD = b"evonybot-license-server"
API_PATH = "/api/license"
_LOCAL_HOSTS = ("localhost", "127.0.0.1")

_ERRORS = {
    "invalid_code": "Activation code is not valid.",
    "invalid_info": "Please enter a valid email, full name and phone number.",
    "revoked": "Your account has been locked. Please contact the admin to unlock it.",
    "expired": "Your account has expired. Please contact the admin to renew it.",
    "device_limit": "More emulators are running than your license allows. Please contact the admin.",
    "customer_limit": "This activation code has reached its maximum number of users. Please contact the admin.",
}


class LicenseError(Exception):
    """The server refused the code (or the local license is unusable); message is shown to the user."""


class OfflineError(Exception):
    """The server could not be reached; the local license may still be inside its grace period."""


def hwid() -> str:
    """Stable id of this machine: SHA-256 of the Windows MachineGuid."""
    guid = ""
    if sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography",
                                0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
                guid = winreg.QueryValueEx(key, "MachineGuid")[0]
        except OSError:
            pass
    if not guid:
        guid = f"{os.environ.get('COMPUTERNAME', '')}-{os.environ.get('PROCESSOR_IDENTIFIER', '')}"
    return hashlib.sha256(guid.encode()).hexdigest()


def device_name() -> str:
    """Readable name of this machine for the admin panel, e.g. "DESKTOP-ABC (Windows 11)"."""
    return f"{platform.node()} (Windows {platform.release()})" if sys.platform == "win32" else platform.node()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_time(text: str) -> datetime:
    when = datetime.fromisoformat(text.replace("Z", "+00:00"))
    return when if when.tzinfo else when.replace(tzinfo=timezone.utc)


def _signature_ok(payload: str, signature: str) -> bool:
    try:
        key = Ed25519PublicKey.from_public_bytes(base64.b64decode(PUBLIC_KEY_B64))
        key.verify(base64.b64decode(signature), payload.encode())
        return True
    except (InvalidSignature, ValueError):   # bad signature / malformed key or base64
        return False


def decrypt_server(token: str) -> str | None:
    """Token (base64url of nonce(12) + AES-256-GCM ciphertext) -> the address inside, or None when it cannot be read."""
    try:
        token = token.strip()
        raw = base64.urlsafe_b64decode(token + "=" * (-len(token) % 4))
        return AESGCM(base64.b64decode(CONFIG_KEY_B64)).decrypt(raw[:12], raw[12:], CONFIG_AAD).decode()
    except (InvalidTag, ValueError):   # wrong key / corrupt token / missing key
        return None


def parse_server(address: str) -> str | None:
    """Decrypted address -> license API base URL, or None when unusable. A bare domain / host:port gets https:// (http://
    only for localhost, for development) and API_PATH; http:// is refused for any other host (customer data goes there)."""
    line = address.strip()
    if not line or " " in line:
        return None
    if "://" not in line:
        line = ("http://" if line.split(":")[0].split("/")[0] in _LOCAL_HOSTS else "https://") + line
    parts = urllib.parse.urlsplit(line)
    if not parts.hostname or parts.scheme not in ("http", "https"):
        return None
    if parts.scheme == "http" and parts.hostname not in _LOCAL_HOSTS:
        return None
    return f"{parts.scheme}://{parts.netloc}{parts.path.rstrip('/') or API_PATH}"


_api_url_cache: str | None = None


def api_url() -> str:
    """License API base URL: the address decrypted from the gist's token, read fresh each time the app starts (kept in
    memory for the run); if the gist cannot be read or decrypted, the built-in API_URL."""
    global _api_url_cache
    if _api_url_cache:
        return _api_url_cache
    url = None
    if CONFIG_KEY_B64:
        try:
            req = urllib.request.Request(CONFIG_URL, headers={"User-Agent": "EvonyBot"})
            with urllib.request.urlopen(req, timeout=5, context=_SSL) as resp:
                text = resp.read(4096).decode("utf-8", "replace")
            token = next((ln.strip() for ln in text.splitlines() if ln.strip()), "")
            url = parse_server(decrypt_server(token) or "")
        except (urllib.error.URLError, OSError, ValueError):
            pass
    _api_url_cache = url or API_URL
    return _api_url_cache


def _call(endpoint: str, code: str, customer: dict | None = None, running: list[str] | None = None,
          peak: int | None = None) -> dict:
    """POST to the server; returns the stored form {"code", "payload", "signature"} of a valid answer.
    `customer` (email, full_name, phone, address) is sent on activation only; `running` (serials of the
    emulators with a bot running) and `peak` (most bots running at once since the last report) on verify only."""
    body = json.dumps({"code": code, "hwid": hwid(), "app_version": __version__,
                       "device_name": device_name(), **(customer or {}),
                       **({"running_devices": running} if running is not None else {}),
                       **({"peak_devices": peak} if peak is not None else {})}).encode()
    req = urllib.request.Request(f"{api_url()}/{endpoint}", data=body, method="POST", headers={
        "Content-Type": "application/json", "User-Agent": "EvonyBot"})
    try:
        with urllib.request.urlopen(req, timeout=15, context=_SSL) as resp:
            answer = json.load(resp)
    except urllib.error.HTTPError as e:
        try:
            answer = json.load(e)   # the server sends its refusals as 4xx with the JSON body
        except Exception:
            raise OfflineError(f"Server error {e.code}") from e
    except (urllib.error.URLError, OSError, ValueError) as e:
        raise OfflineError(str(e)) from e
    if not answer.get("ok"):
        error = answer.get("error", "")
        raise LicenseError(_ERRORS.get(error, f"Activation refused ({error or 'unknown error'}). Please contact the admin."))
    payload, signature = answer.get("payload", ""), answer.get("signature", "")
    if not _signature_ok(payload, signature):
        raise LicenseError("Invalid answer from the license server. Please contact the admin.")
    return {"code": code, "payload": payload, "signature": signature}


def _save(license_: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    license_["last_run"] = _now().isoformat()
    LICENSE_PATH.write_text(json.dumps(license_), encoding="utf-8")


def _load() -> dict | None:
    try:
        return json.loads(LICENSE_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def stored_code() -> str:
    return (_load() or {}).get("code", "")


def check_local() -> str | None:
    """None when the stored license is valid right now (signed, this machine, not expired, inside the offline
    grace period, clock not rolled back); otherwise the reason."""
    license_ = _load()
    if not license_:
        return "No activation code."
    payload = license_.get("payload", "")
    if not _signature_ok(payload, license_.get("signature", "")):
        return "License file is invalid. Please contact the admin."
    try:
        data = json.loads(payload)
        issued = _parse_time(data["issued_at"])
        expires = _parse_time(data["expires_at"]) if data.get("expires_at") else None
        last_run = _parse_time(license_["last_run"])
    except (KeyError, ValueError):
        return "License file is invalid. Please contact the admin."
    now = _now()
    if data.get("hwid") != hwid():
        return "This license belongs to another machine. Please contact the admin."
    if expires and now >= expires:
        return _ERRORS["expired"]
    if now < last_run - timedelta(minutes=5):
        return "The system clock was set back. Set the correct time and reopen the app."
    if now - issued > OFFLINE_GRACE:
        return "Could not reach the license server for too long. Connect to the internet and reopen the app."
    _save(license_)   # refresh last_run
    return None


def max_devices() -> int | None:
    """Số giả lập được chạy cùng lúc theo giấy phép (payload "max_devices"); None = không giới hạn
    (payload hợp lệ nhưng không có trường này). Không có giấy phép, chữ ký sai hoặc payload hỏng -> 0
    (không cho chạy giả lập nào)."""
    license_ = _load()
    if not license_ or not _signature_ok(license_.get("payload", ""), license_.get("signature", "")):
        return 0
    try:
        value = json.loads(license_["payload"]).get("max_devices")
        if value is None:
            return None
        return int(value) if int(value) > 0 else None
    except (KeyError, ValueError, TypeError, AttributeError):
        return 0


def activate(code: str, customer: dict):
    """Activate `code` on this machine for `customer` {"email", "full_name", "phone", "address"}.
    Raises LicenseError (refused) or OfflineError (no server)."""
    _save(_call("activate", code.strip(), customer))


def verify(running: list[str] | None = None, peak: int | None = None) -> str | None:
    """Refresh the stored license from the server. Returns None when valid.
    Raises LicenseError when the server no longer accepts it (the stored license file is kept as it is) or
    OfflineError when the server cannot be reached (the caller decides with check_local())."""
    code = stored_code()
    if not code:
        raise LicenseError("No activation code.")
    _save(_call("verify", code, running=running, peak=peak))
    return None
