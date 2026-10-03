"""
run.py — flow nhiệm vụ Cultivate Generals (Gather Troops).

Chạy trong vòng lặp chung run_task() (xem event/common.py): ảnh ưu tiên, ảnh riêng
của nhiệm vụ, rồi common_targets(); action không phải của nhiệm vụ thì handle_common()
lo việc đi từ màn hình chính tới màn event.

Flow:
1. Màn chính -> nút dưới Event Center -> danh sách event -> icon Gather Troops.
   Đang ở sẵn màn Gather Troops thì làm luôn từ bước 2. Chưa bấm Go trong lượt này mà gặp
   danh sách Generals / màn tướng / màn Cultivate (VD lượt trước dừng ở đó) -> Back cho tới
   khi về lại Gather Troops (bắt buộc đi qua dòng Go để biết nhiệm vụ còn cần làm không).
2. Màn Gather Troops: tab "Recruit More" chưa chọn thì bấm vào.
3. Tab "Recruit More" đang chọn: đọc số đã làm ở "300 / 500" trên nút "Go" gần tab nhất
   (OCR) rồi bấm "Go" -> danh sách Generals.
   Không còn nút "Go" nào -> nhiệm vụ đã xong: đánh dấu xong (tới lần reset server).
4. Danh sách Generals: tim lọc yêu thích chưa tích thì bấm tích; rồi kéo nhanh xuống cuối
   6 lần, bấm thẻ tướng cuối (10%, 90%) và chờ màn đổi (tối đa 15 s).
5. Màn chi tiết tướng: bấm "Cultivate".
6. Màn Cultivate (mở ở tab "Cultivate Once"): bấm tab "Quick Cultivate".
7. Tab Quick Cultivate (trên cùng ảnh chụp):
   - thấy "Cancel" (kết quả lần trước) -> bấm Cancel;
   - thấy "Cultivate x100" -> bấm, số đã làm += 100 (nút đổi thành Cancel); đạt TOTAL
     thì đánh dấu xong và dừng. Không đọc được số đã làm ở bước 3 thì không bấm (tránh
     tiêu gems khi không biết lúc nào dừng).
"""
from .....common import wait_gone
from .....ocr import read_progress
from ...common import (HANDLED, STOP, EventState, is_done_today, mark_complete,
                       mark_target_reached, run_task)
from ...constants import GATHER_TROOPS_ICON, GO_BUTTON, GO_REGION, PROGRESS_FROM_GO
from .constants import (
    CANCEL,
    CULTIVATE_BUTTONS,
    CULTIVATE_X100,
    CULTIVATE_X100_TIMES,
    FAVORITE_OFF,
    FAVORITE_ON,
    GENERAL_OPEN_WAIT,
    GENERAL_PATCH,
    KEY,
    LAST_GENERAL,
    LIST_FLING,
    LIST_FLING_DURATION,
    LIST_FLING_TIMES,
    ON_GENERALS_LIST,
    ON_QUICK_CULTIVATE,
    ON_RECRUIT_MORE,
    OPEN_CULTIVATE,
    OPEN_QUICK_CULTIVATE,
    OPEN_RECRUIT_MORE,
    QUICK_CULTIVATE,
    QUICK_CULTIVATE_SELECTED,
    RECRUIT_MORE,
    RECRUIT_MORE_SELECTED,
    REGIONS,
    THRESHOLDS,
    TOTAL,
    TICK_FAVORITE,
    X100_WAIT,
)

_PATCH = "general_patch"   # action của ảnh nhỏ cắt quanh thẻ tướng (dùng cho wait_gone)
_X100 = "x100"             # action của nút Cultivate x100 (dùng cho wait_gone)


def run(bot, task: dict, state: EventState):
    """`task` là settings của nhiệm vụ: {"enabled": bool, "day": int}."""
    if is_done_today(bot, KEY):
        bot.log("Cultivate Generals: already done")
        return
    done = None   # số lần đã cultivate, đọc ở dòng có nút Go (None = chưa đọc / đọc lỗi)
    went = False   # đã bấm Go trong lượt này (bắt buộc trước các màn sau Go)

    def handle(action, pos, screen):
        nonlocal done, went
        if action in _AFTER_GO_ACTIONS and not went:
            bot.log(f"Cultivate Generals: {action} before Go, back")
            bot.back(delay=1)
            return HANDLED
        if action == ON_QUICK_CULTIVATE:
            cancel = bot.find(CANCEL, screen=screen, region=REGIONS[CANCEL])
            if cancel is not None:
                bot.tap(*cancel, delay=1)
                return HANDLED
            x100 = bot.find(CULTIVATE_X100, screen=screen, region=REGIONS[CULTIVATE_X100])
            if x100 is None:
                return HANDLED   # chưa hiện nút nào: quét lại
            if done is None:
                bot.record("Cultivate Generals: progress unknown, not using Cultivate x100")
                return STOP
            bot.tap(*x100)
            done += CULTIVATE_X100_TIMES
            bot.record(f"Cultivate Generals: Cultivate x100 -> {done}/{TOTAL}")
            if done >= TOTAL:
                mark_target_reached(bot, KEY)
                return STOP
            # Chờ nút đổi thành Cancel để không bấm (và đếm) x100 hai lần.
            wait_gone(bot, [(CULTIVATE_X100, _X100)], _X100, x100, timeout=X100_WAIT)
        elif action in (OPEN_QUICK_CULTIVATE, OPEN_CULTIVATE, OPEN_RECRUIT_MORE):
            bot.tap(*pos, delay=2)
        elif action == TICK_FAVORITE:
            bot.tap(*pos, delay=1)
        elif action == ON_GENERALS_LIST:
            _open_last_general(bot)
        elif action == ON_RECRUIT_MORE:
            go = _nearest_go(bot, screen, pos)
            if go is None:
                bot.log("Cultivate Generals: no Go left, done")
                mark_complete(bot, KEY)
                return STOP
            done = _read_done(bot, screen, go)
            bot.tap(*go, delay=3)
            went = True
        else:
            return None   # EVENT_OPENED hoặc action dùng chung: run_task lo
        return HANDLED

    run_task(bot, state, "Cultivate Generals", GATHER_TROOPS_ICON, handle,
             targets=_TARGETS, regions=REGIONS, thresholds=THRESHOLDS)


# Ảnh riêng của nhiệm vụ (màn sau trước, màn trước sau). Tab "đang chọn" xét trước tab
# "chưa chọn" (hai ảnh khớp chéo, xem constants).
_TARGETS = [
    (QUICK_CULTIVATE_SELECTED, ON_QUICK_CULTIVATE),
    (QUICK_CULTIVATE, OPEN_QUICK_CULTIVATE),
    *[(path, OPEN_CULTIVATE) for path in CULTIVATE_BUTTONS],
    (FAVORITE_OFF, TICK_FAVORITE),
    (FAVORITE_ON, ON_GENERALS_LIST),
    (RECRUIT_MORE_SELECTED, ON_RECRUIT_MORE),
    (RECRUIT_MORE, OPEN_RECRUIT_MORE),
]


# Màn sau khi bấm Go: cần bấm Go trong lượt này trước, xem `went` trong run().
_AFTER_GO_ACTIONS = (ON_QUICK_CULTIVATE, OPEN_QUICK_CULTIVATE, OPEN_CULTIVATE, TICK_FAVORITE,
                     ON_GENERALS_LIST)


def _nearest_go(bot, screen, tab):
    """Nút "Go" gần tab Recruit More nhất (tức dòng chưa xong trên cùng), hoặc None."""
    gos = bot.find_all(GO_BUTTON, screen=screen, region=GO_REGION)
    if not gos:
        return None
    return min(gos, key=lambda p: (p[0] - tab[0]) ** 2 + (p[1] - tab[1]) ** 2)


def _read_done(bot, screen, go) -> int | None:
    """Số lần đã cultivate đọc ở "300 / 500" ngay trên nút `go`, hoặc None."""
    dx, dy, w, h = PROGRESS_FROM_GO
    done = read_progress(bot.crop(screen, go[0] + dx, go[1] + dy, w, h))
    if done is None:
        bot.record("Cultivate Generals: cannot read progress")
    else:
        bot.log(f"Cultivate Generals: done {done}, remaining {max(0, TOTAL - done)}")
    return done


def _open_last_general(bot):
    """Kéo nhanh danh sách Generals xuống cuối, bấm thẻ tướng cuối rồi chờ màn đổi:
    cắt một ảnh nhỏ quanh điểm bấm (chỉ giữ trong RAM) và wait_gone tới khi nó biến mất."""
    for _ in range(LIST_FLING_TIMES):
        bot.swipe_percent(*LIST_FLING, duration=LIST_FLING_DURATION, delay=1)
    w, h = bot.window_size()
    x, y = int(w * LAST_GENERAL[0] / 100), int(h * LAST_GENERAL[1] / 100)
    half = GENERAL_PATCH // 2
    patch = bot.crop(bot.screenshot(), x - half, y - half, GENERAL_PATCH, GENERAL_PATCH)
    bot.tap(x, y)
    if wait_gone(bot, [(patch, _PATCH)], _PATCH, (x, y), timeout=GENERAL_OPEN_WAIT) is None:
        bot.record("Cultivate Generals: general screen did not open")
