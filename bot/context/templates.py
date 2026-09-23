"""
templates.py — where template images live and the default match score.
"""
from pathlib import Path

# Template images, referenced relative to this folder, e.g. "Science/donate.png".
TEMPLATE_DIR = Path(__file__).resolve().parent.parent.parent / "Images"
DEFAULT_THRESHOLD = 0.9
