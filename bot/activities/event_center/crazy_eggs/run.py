"""
run.py — nhiệm vụ Event Center "Crazy Eggs" (đập trứng).

Flow: màn chính -> bấm chính nút Event Center -> tab "Activities" -> cuộn tìm icon Crazy
Eggs (event_center.common.run_task) -> đập các quả còn icon búa (nhãn "Scout Cost:") theo thứ
tự ORDER (2-3-1-4); quả đang "Waiting:" không có búa thì bỏ qua. Bấm thẳng vào icon búa tìm được;
quả của búa theo vị trí búa (cột 1: x < 50 % màn, hàng 1: y < 70 % màn). Mỗi lần đập hiện popup
"Congratulations!": BACK để đóng rồi mới đếm búa.

Hết đập thường (không còn quả nào có búa, hoặc hết búa: bấm một quả thì hiện hộp thoại "You don't
have enough Hammers" -> Cancel; hoặc bấm mà số quả có búa không giảm) thì dùng búa vàng mỗi ngày 1 lần cho quả 2 nếu quả 2 đang chờ: bấm quả 2 -> Confirm,
lưu daily_done LUCKY_KEY. Rồi kết thúc.

Đã đánh dấu xong hôm nay (DONE_KEY) thì return ngay, không vào game. Đánh dấu DONE_KEY (lưu DB)
rồi kết thúc khi không thấy tab Activities / icon Crazy Eggs sau ATTEMPTS lần thử và
AFTER_RESTART_ATTEMPTS lần thử sau khi tắt / mở lại game (run_task_with_retry).

Quả đã nhận hết vật phẩm thì vỡ: animation (cả màn tối, tiêu đề mờ -> bấm (50 %, 95 %) để bỏ
qua), rồi popup thưởng thêm "Congratulations on activating the egg!" -> BACK; nhãn thành
"Activated": không còn búa nên đập thường tự bỏ qua.
"""
from ..common import HANDLED, ICON_NOT_FOUND, TAB_NOT_FOUND, run_task_with_retry
from ..constants import ACTIVITIES
from .constants import (
    CONGRATS_POPUPS,
    DIM_MAX_TAPS,
    DONE,
    DONE_KEY,
    EGG_TAP_DELAY,
    COLUMN_SPLIT,
    HAMMER,
    HAMMER_THRESHOLD,
    ICON,
    ICON_THRESHOLD,
    LUCKY_CONFIRM,
    LUCKY_CONFIRM_REGION,
    LUCKY_HAMMER,
    LUCKY_KEY,
    LUCKY_LEFT,
    LUCKY_LEFT_REGION,
    NOT_ENOUGH_CANCEL,
    NOT_ENOUGH_CANCEL_REGION,
    NOT_ENOUGH_HAMMERS,
    ON_EGGS,
    ORDER,
    ROW_SPLIT,
    SKIP_ANIMATION_TAP,
    TITLE,
    TITLE_DIM_MEAN,
    TITLE_REGION,
    WAITING,
    WAITING_THRESHOLD,
)


def run(bot, settings: dict):
    """`bot` is the device's BotContext; `settings` chưa dùng (để thống nhất với activity)."""
    if bot.is_daily_done(DONE_KEY):
        bot.log("Crazy Eggs: done today, skip")
        return
    # before_tap: số quả có búa ngay trước lần bấm gần nhất; lucky_tapped: đã bấm quả 2 để
    # dùng búa vàng trong lượt này; no_hammers: đã gặp hộp thoại "not enough Hammers".
    state = {"before_tap": None, "lucky_tapped": False, "no_hammers": False}

    def handle(action, pos, screen):
        if action != ON_EGGS:
            return None
        return DONE if _crack(bot, state) else HANDLED

    result = run_task_with_retry(bot, "Crazy Eggs", ACTIVITIES, ICON, handle,
                                 targets=[(TITLE, ON_EGGS)], regions={TITLE: TITLE_REGION},
                                 icon_threshold=ICON_THRESHOLD)
    if result in (TAB_NOT_FOUND, ICON_NOT_FOUND):
        bot.log(f"Crazy Eggs: {result} even after restarting game, mark done today")
        bot.mark_daily_done(DONE_KEY)


def _crack(bot, state: dict) -> bool:
    """Màn Crazy Eggs: đập lần lượt quả có búa đầu tiên theo thứ tự ORDER, hết thì dùng búa
    vàng cho quả 2. True khi xong; False nếu rời màn Crazy Eggs để run_task xử lý rồi quay lại."""
    rechecked = False   # đã chờ thêm 1 nhịp trước khi kết luận hết búa
    dim_taps = 0        # số lần bấm bỏ qua animation liên tiếp
    while True:
        screen = bot.screenshot()
        title = bot.find(TITLE, screen=screen, region=TITLE_REGION)
        if title is None:
            return False
        if bot.find(LUCKY_HAMMER, screen=screen) is not None:
            _confirm_lucky(bot, screen)
            continue
        if bot.find(NOT_ENOUGH_HAMMERS, screen=screen) is not None:
            _cancel_not_enough(bot, screen)
            state["no_hammers"] = True
            continue
        if _title_dim(bot, screen, title):
            dim_taps += 1
            if dim_taps > DIM_MAX_TAPS:
                bot.log(f"Crazy Eggs: screen still dim after {DIM_MAX_TAPS} taps, back")
                bot.back(delay=1)
                dim_taps = 0
                continue
            bot.log("Crazy Eggs: egg breaking animation, tap to skip")
            bot.tap_percent(*SKIP_ANIMATION_TAP, delay=1)
            continue
        dim_taps = 0
        if any(bot.find(popup, screen=screen) is not None for popup in CONGRATS_POPUPS):
            _close_congratulations(bot)
            continue
        hammers = _ordered(bot, screen)
        out_of_hammers = state["no_hammers"] or (
            state["before_tap"] is not None and len(hammers) >= state["before_tap"])
        if hammers and out_of_hammers and not rechecked and not state["no_hammers"]:
            # Animation trứng vỡ có thể chưa xong (màn chưa đổi, popup chưa hiện): chờ rồi quét lại.
            rechecked = True
            bot.sleep(EGG_TAP_DELAY)
            continue
        rechecked = False
        if hammers and not out_of_hammers:
            egg, pos = hammers[0]
            bot.log(f"Crazy Eggs: crack egg {egg} at {pos} ({len(hammers)} ready)")
            state["before_tap"] = len(hammers)
            bot.tap(*pos, delay=EGG_TAP_DELAY)
            continue
        bot.log("Crazy Eggs: out of hammers" if hammers else "Crazy Eggs: no egg left to crack")
        if not _use_lucky(bot, screen, state):
            return True


def _use_lucky(bot, screen, state: dict) -> bool:
    """Búa vàng cho quả 2 (mỗi ngày 1 lần): quả 2 đang chờ thì bấm vào, trả True để quét lại
    (hộp thoại xác nhận). Đã dùng hôm nay (DB, hoặc số búa vàng trên màn không còn là "1") / quả 2
    không chờ -> False."""
    if bot.is_daily_done(LUCKY_KEY):
        return False
    if bot.find(LUCKY_LEFT, screen=screen, region=LUCKY_LEFT_REGION) is None:
        bot.log("Crazy Eggs: Lucky Hammer count is not 1, mark used")
        bot.mark_daily_done(LUCKY_KEY)
        return False
    if state["lucky_tapped"]:
        # Đã bấm quả 2 mà không hiện hộp thoại (VD đã dùng tay): coi như đã dùng hôm nay.
        bot.log("Crazy Eggs: no Lucky Hammer dialog, mark used")
        bot.mark_daily_done(LUCKY_KEY)
        return False
    egg_2 = _egg_2_waiting(bot, screen)
    if egg_2 is None:
        bot.log("Crazy Eggs: egg 2 not waiting, Lucky Hammer not used")
        return False
    bot.log(f"Crazy Eggs: Lucky Hammer on egg 2 at {egg_2}")
    state["lucky_tapped"] = True
    bot.tap(*egg_2, delay=2)
    return True


def _cancel_not_enough(bot, screen):
    """Hộp thoại "You don't have enough Hammers": bấm Cancel (không thấy nút thì BACK)."""
    bot.log("Crazy Eggs: not enough Hammers, cancel")
    pos = bot.find(NOT_ENOUGH_CANCEL, screen=screen, region=NOT_ENOUGH_CANCEL_REGION)
    if pos is None:
        bot.back(delay=1)
        return
    bot.tap(*pos, delay=1)


def _confirm_lucky(bot, screen):
    """Hộp thoại búa vàng: bấm Confirm, lưu daily_done LUCKY_KEY."""
    pos = bot.find(LUCKY_CONFIRM, screen=screen, region=LUCKY_CONFIRM_REGION)
    if pos is None:
        bot.log("Crazy Eggs: Lucky Hammer dialog without Confirm, back")
        bot.back(delay=1)
        return
    bot.log("Crazy Eggs: confirm Lucky Hammer")
    bot.tap(*pos, delay=EGG_TAP_DELAY)
    bot.mark_daily_done(LUCKY_KEY)


def _egg_2_waiting(bot, screen):
    """Tâm nhãn "Waiting:" của quả 2, hoặc None nếu quả 2 không chờ."""
    for pos in bot.find_all(WAITING, threshold=WAITING_THRESHOLD, screen=screen):
        if _egg_number(screen, pos) == 2:
            return pos
    return None


def _egg_number(screen, pos) -> int:
    """Quả (1..4) của búa / nhãn tại `pos`: cột 1 nếu x < COLUMN_SPLIT %, hàng 1 nếu y < ROW_SPLIT %."""
    h, w = screen.shape[:2]
    column = 1 if pos[0] < w * COLUMN_SPLIT / 100 else 2
    row = 0 if pos[1] < h * ROW_SPLIT / 100 else 2
    return row + column


def _title_dim(bot, screen, title) -> bool:
    """Tiêu đề "Crazy Eggs" tối hơn TITLE_DIM_MEAN (animation trứng vỡ làm tối cả màn)."""
    w, h = bot.template_size(TITLE)
    area = bot.crop(screen, title[0] - w // 2, title[1] - h // 2, w, h)
    return area.size > 0 and float(area.mean()) < TITLE_DIM_MEAN


def _close_congratulations(bot):
    """Popup "Congratulations!" sau khi đập (hoặc "Congratulations on activating the egg!" khi
    trứng vỡ): không tự mất, đóng bằng BACK."""
    bot.log("Crazy Eggs: close Congratulations")
    bot.back(delay=1)


def _ordered(bot, screen) -> list[tuple[int, tuple[int, int]]]:
    """[(quả, tâm búa)] của các icon búa, theo thứ tự đập ORDER."""
    hits = bot.find_all(HAMMER, threshold=HAMMER_THRESHOLD, screen=screen)
    pairs = [(_egg_number(screen, pos), pos) for pos in hits]
    return sorted(pairs, key=lambda pair: ORDER.index(pair[0]))
