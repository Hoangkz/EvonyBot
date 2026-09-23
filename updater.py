"""
updater.py — self-update from GitHub Releases.

A release is published with tag "vX.Y.Z" (or "X.Y.Z") and the installer
built by installer/build.ps1 (EvonyBot-Setup-X.Y.Z.exe) attached as an
asset. The updater compares the tag with version.__version__, downloads
the .exe and runs it silently; the installer relaunches the app when it
gets /RELAUNCH (see installer/EvonyBot.iss).
"""
import json
import os
import re
import subprocess
import tempfile
import urllib.request
from pathlib import Path
from typing import Callable

from version import __version__

GITHUB_REPO = "Hoangkz/EvonyBot"   # owner/repo that hosts the releases (must be public)
_API_LATEST = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
_HEADERS = {"User-Agent": "EvonyBot-Updater", "Accept": "application/vnd.github+json"}


def _parse_version(text: str) -> tuple[int, ...]:
    return tuple(int(n) for n in re.findall(r"\d+", text))


def check_latest() -> dict | None:
    """Latest release as {"version", "url", "name"} if it is newer than this
    app and has an .exe asset, else None."""
    req = urllib.request.Request(_API_LATEST, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        release = json.load(resp)
    latest = release.get("tag_name", "").lstrip("vV")
    if _parse_version(latest) <= _parse_version(__version__):
        return None
    for asset in release.get("assets", []):
        if asset["name"].lower().endswith(".exe"):
            return {"version": latest, "url": asset["browser_download_url"], "name": asset["name"]}
    raise RuntimeError(f"Release {latest} has no .exe installer attached")


def download(url: str, name: str, on_progress: Callable[[int], None] | None = None) -> Path:
    """Download the installer into %TEMP%; on_progress gets 0-100."""
    dest = Path(tempfile.gettempdir()) / name
    req = urllib.request.Request(url, headers={"User-Agent": _HEADERS["User-Agent"]})
    with urllib.request.urlopen(req, timeout=30) as resp, open(dest, "wb") as f:
        total = int(resp.headers.get("Content-Length") or 0)
        done = 0
        while chunk := resp.read(256 * 1024):
            f.write(chunk)
            done += len(chunk)
            if on_progress and total:
                on_progress(done * 100 // total)
    return dest


def run_installer(path: Path):
    """Start the installer detached so it outlives this process, which must
    exit right after so its files can be replaced."""
    flags = 0
    if os.name == "nt":
        flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    subprocess.Popen(
        [str(path), "/SILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/RELAUNCH"],
        creationflags=flags,
        close_fds=True,
    )
