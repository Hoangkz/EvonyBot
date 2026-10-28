"""
goto.py — đưa camera tới toạ độ (X, Y) trên bản đồ thế giới bằng hộp "Search" (bấm vào dòng toạ độ X:… Y:… ở đáy màn hình): nhập X, nhập Y,
bấm Go. Xong thì boss ở toạ độ đó nằm giữa màn hình. Kiểm lại bằng toạ độ camera đọc ở thanh X:Y.
"""
from ...common import arc_sweep
from ...ocr import read_camera
from ..event.kings_path.heal.constants import INPUT_OK
from .constants import (COORD_BAR, GO_BUTTON, GO_THRESHOLD, GOTO_TRIES, GOTO_WAIT, INPUT_DELETES, INPUT_SETTLE, SEARCH_OPEN_WAIT,
                        SEARCH_TITLE, SEARCH_X, SEARCH_Y)


def goto_coords(bot, x: int, y: int) -> bool:
    """Camera tới (x, y); True khi toạ độ camera đọc lại khớp, hoặc không đọc được (bộ đọc thanh X:Y đôi khi trả None, VD "0572 0112"; chỉ thử lại
    khi đọc được mà sai). Thử tối đa GOTO_TRIES lần."""
    for _ in range(GOTO_TRIES):
        if _search(bot, x, y):
            camera = arc_sweep.valid_camera(read_camera(bot.screenshot()))
            if camera is None or camera == (x, y):
                return True
            bot.log(f"Attack Boss: nhập toạ độ {(x, y)} mà camera ở {camera}")
    return False


def _search(bot, x: int, y: int) -> bool:
    if not _open_search(bot):
        return False
    for field, value in ((SEARCH_X, x), (SEARCH_Y, y)):
        if not _type(bot, field, value):
            bot.back()
            return False
    go = bot.find(GO_BUTTON, threshold=GO_THRESHOLD)
    if go is None:
        bot.back()
        return False
    bot.tap(*go)
    bot.sleep(GOTO_WAIT)        # camera chạy tới toạ độ mới
    return True


def _open_search(bot) -> bool:
    """Bấm dòng toạ độ ở đáy màn hình, chờ hộp Search (thấy tiêu đề)."""
    bot.tap(*COORD_BAR, delay=0)
    for _ in range(round(SEARCH_OPEN_WAIT / 0.5)):
        bot.sleep(0.5)
        if bot.find(SEARCH_TITLE, threshold=GO_THRESHOLD) is not None:
            return True
    return False


def _type(bot, field: tuple[int, int], value: int) -> bool:
    """Bấm ô `field` -> thanh nhập ở đáy màn (nút OK); xoá số cũ, gõ `value` (một lệnh adb: thanh nhập tự đóng sau ~10 giây), bấm OK."""
    bot.tap(*field, delay=0)
    for _ in range(round(SEARCH_OPEN_WAIT / 0.5)):
        bot.sleep(0.5)
        if bot.find(INPUT_OK) is not None:
            break
    else:
        return False
    keys = " ".join(["KEYCODE_DEL"] * INPUT_DELETES)
    bot.shell(f"input keyevent KEYCODE_MOVE_END; input keyevent {keys}; input text {value}")
    bot.sleep(INPUT_SETTLE)
    ok = bot.find(INPUT_OK)
    if ok is None:
        return False
    bot.tap(*ok)
    bot.sleep(0.5)
    return True
