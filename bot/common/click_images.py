"""
click_images.py — Images/click.
"""
from .images_in import images_in


def click_images() -> list[str]:
    """Images/click — buttons that are simply tapped when seen."""
    return images_in("click")
