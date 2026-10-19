"""
templates.py — where template images live and the default match score.
"""
from pathlib import Path

import cv2
import numpy as np

from .image_store import open_pack

_ROOT = Path(__file__).resolve().parent.parent.parent
_PACK = _ROOT / "images.dat"

# Template images, referenced relative to this folder, e.g. "Science/donate.png". The installed build
# has no Images/ folder, only images.dat (see image_store.py); from source it is the real folder.
TEMPLATE_DIR = open_pack(_PACK) if _PACK.is_file() else _ROOT / "Images"
DEFAULT_THRESHOLD = 0.9


def read_image(path, flags=cv2.IMREAD_COLOR):
    """Decode the image at `path` (a real Path or one under TEMPLATE_DIR); None if missing/unreadable."""
    try:
        data = path.read_bytes()
    except OSError:
        return None
    return cv2.imdecode(np.frombuffer(data, np.uint8), flags)
