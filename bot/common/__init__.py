"""
common — helpers shared by several activities (ports of the C# `Utils`
class and the image folders every activity scans). One function per module:

- images_in:     every .png in an Images/ folder
- exit_images:   Images/exit — popups closed with BACK
- find_first:    the first known image on a screenshot
- click_images:  Images/click — buttons tapped when seen
- delay:         Utils.delay
- current_focus: the focused Android window
- go_home:       Utils.Home — recover when nothing known is on screen
- get_server:    read the account's server number
- wait_gone:     wait until a recognised screen goes away
- wait_until:    wait until the screen passes a check
"""
from .click_images import click_images
from .current_focus import current_focus
from .delay import delay
from .exit_images import exit_images
from .find_first import find_first
from .get_server import get_server
from .go_home import GAME_PACKAGE, go_home
from .images_in import images_in
from .wait_gone import wait_gone
from .wait_until import wait_until

__all__ = ["GAME_PACKAGE", "click_images", "current_focus", "delay", "exit_images",
           "find_first", "get_server", "go_home", "images_in", "wait_gone",
           "wait_until"]
