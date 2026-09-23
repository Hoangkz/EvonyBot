"""
images_in.py — every .png in an Images/ folder.
"""
from ..context import TEMPLATE_DIR


def images_in(folder: str) -> list[str]:
    """Every .png in Images/<folder>, sorted, as paths relative to Images/."""
    return [f"{folder}/{p.name}" for p in sorted((TEMPLATE_DIR / folder).glob("*.png"))]
