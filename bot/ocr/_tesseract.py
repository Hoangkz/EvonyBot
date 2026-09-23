"""
_tesseract.py — locate tesseract.exe for pytesseract. The C# app ran a
bundled data/Tesseract/main.exe; here Tesseract is called via pytesseract.

tesseract.exe is looked up in this order: the TESSERACT_CMD environment
variable, a Tesseract-OCR folder next to the app, the default install
folder, then PATH.
"""
import os
import shutil
import sys
from pathlib import Path

_APP_DIR = (Path(sys.executable).resolve().parent if getattr(sys, "frozen", False)
            else Path(__file__).resolve().parent.parent.parent)
_CANDIDATES = [
    _APP_DIR / "Tesseract-OCR" / "tesseract.exe",
    Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
    Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
]

_tesseract_cmd: str | None = None


def _find_tesseract() -> str:
    global _tesseract_cmd
    if _tesseract_cmd is None:
        env = os.environ.get("TESSERACT_CMD")
        found = next((str(p) for p in _CANDIDATES if p.exists()), None)
        _tesseract_cmd = env or found or shutil.which("tesseract")
        if not _tesseract_cmd:
            raise RuntimeError("Tesseract OCR not found (install it or set TESSERACT_CMD)")
    return _tesseract_cmd


def pytesseract():
    """The pytesseract module, pointed at tesseract.exe."""
    import pytesseract as module

    module.pytesseract.tesseract_cmd = _find_tesseract()
    return module
