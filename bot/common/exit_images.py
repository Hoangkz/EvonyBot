"""
exit_images.py — Images/exit.
"""
from .images_in import images_in


def exit_images() -> list[str]:
    """Images/exit — popups closed with the BACK key."""
    return images_in("exit")
