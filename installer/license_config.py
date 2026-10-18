"""
license_config.py — encrypt / decrypt the license server address that the app reads from the gist.

    python installer/license_config.py encrypt https://my-app.vercel.app/   -> token to paste into the gist
    python installer/license_config.py decrypt <token>                     -> the address inside a token

The key lives in config_key.py (git-ignored, created on first use and shipped by installer/build.ps1).
Token = base64url(nonce(12) + AES-256-GCM(address)); see licensing.decrypt_server.
"""
import base64
import importlib
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
KEY_FILE = Path(__file__).resolve().parent / "config_key.py"

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

import licensing


def load_key() -> bytes:
    if not KEY_FILE.exists():
        key = base64.b64encode(AESGCM.generate_key(bit_length=256)).decode()
        KEY_FILE.write_text(f'# Git-ignored. Key that decrypts the license server address (installer/license_config.py).\n'
                            f'CONFIG_KEY_B64 = "{key}"\n', encoding="utf-8")
        print(f"Created {KEY_FILE.name} with a new key (keep it; changing it invalidates old tokens).", file=sys.stderr)
    namespace: dict = {}
    exec(KEY_FILE.read_text(encoding="utf-8"), namespace)
    return base64.b64decode(namespace["CONFIG_KEY_B64"])


def encrypt(address: str) -> str:
    nonce = os.urandom(12)
    data = AESGCM(load_key()).encrypt(nonce, address.strip().encode(), licensing.CONFIG_AAD)
    return base64.urlsafe_b64encode(nonce + data).decode().rstrip("=")


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("encrypt", "decrypt"):
        sys.exit(__doc__)
    if sys.argv[1] == "encrypt":
        print(encrypt(sys.argv[2]))
    else:
        load_key()
        importlib.invalidate_caches()
        importlib.reload(licensing)   # pick up config_key.py if load_key() just created it
        print(licensing.decrypt_server(sys.argv[2]) or "Cannot decrypt (wrong key or corrupt token).")
