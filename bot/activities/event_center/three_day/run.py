"""
run.py — event 3 ngày trong Event Center (VD "Precious Vegetation"); xem FLOW.md.

Flow: màn chính -> Event Center -> tab Limited -> cuộn tìm icon event (mọi ảnh trong Icons/) -> màn
event (tab nhiệm vụ đang chọn, tab Redeem):
1. Mỗi nhiệm vụ bật (Alliance, Heal; ô chọn ở group "3-Day Event" tab Event): cuộn tìm dòng của
   mốc đã chọn (VD "Donate to the Alliance 60"), thấy nút Claim ở dòng nào thì bấm (không dùng
   Claim All), bấm Go của dòng -> như King's Path: donate ở Alliance Science / heal ở Bệnh viện
   (after_go dùng lại của kings_path), AGAIN thì đi lại từ màn chính.
2. Xong nhiệm vụ: nhận mọi nút Claim trên cả danh sách, sang tab Redeem, đổi quà theo thứ tự ưu
   tiên của người dùng (settings three_day_redeem.order): mỗi quà đổi tới khi nút xám; nút xám ở quà
   ưu tiên thì DỪNG hẳn (để dành vé cho quà đó).
   Đổi quà: nhớ vị trí hàng của từng quà, cuộn thẳng tới đó (không cuộn về đầu mỗi quà).
3. Mọi thứ xong -> lưu daily_done DONE_KEY (đã xong ngày hôm nay): các lần gọi sau trong ngày return
   ngay, không vào game. Không thấy tab / icon event (hết event) cũng lưu DONE_KEY.
"""
from types import SimpleNamespace

import numpy as np

from ....ocr import read_progress
from ....context.templates import TEMPLATE_DIR
from ...event.common import mark_target_reached
from ...event.constants import CONGRATULATIONS, GO_BUTTON, GO_REGION
from ...event.kings_path.donate.run import _donate as donate_after_go
from ...event.kings_path.heal.run import _heal as heal_after_go
from ...event.kings_path.path_task import AGAIN
from ..common import HANDLED, ICON_NOT_FOUND, TAB_NOT_FOUND, run_task
from ..constants import LIMITED
from . import constants as c

NAME = "3-Day Event"
# (key, tên log, hàm làm sau Go)
TASKS = [
    (c.ALLIANCE_KEY, "Alliance", donate_after_go),
    (c.HEAL_KEY, "Heal", heal_after_go),
]


def run(bot, settings: dict):
    """`settings` là cấu hình tab Event: {key: {...}}."""
    if not any(key.startswith(c.GROUP_KEY) for key in settings):
        bot.log(f"{NAME}: no 3-day event settings, skip")   # cấu hình tab Event thiếu group này (VD test)
        return
    if not _active(settings):
        bot.log(f"{NAME}: group not active, skip")
        return
    if bot.is_daily_done(c.DONE_KEY):
        bot.log(f"{NAME}: done today, skip")
        return
    if not c.icons():
        bot.log(f"{NAME}: no event icon image in {c.ICONS_DIR}, skip")
        return
    # Nhiệm vụ coi là xong TRONG LƯỢT này (ctx["finished"]) chỉ khi quét danh sách thấy một trong 3 trường hợp (xem
    # _check_task); dấu "đã xong" (daily_done) do donate / heal tự lưu không dùng để bỏ qua việc kiểm tra.
    ctx = {"finished": set(), "go_tries": {}}
    misses = rounds = 0   # misses: số lần liên tiếp quét mà không kết luận được nhiệm vụ nào
    while rounds < c.MAX_ROUNDS:
        rounds += 1
        pending = _pending(bot, settings, ctx["finished"])
        if not pending:
            break
        bot.check()
        bot.record(f"{NAME}: tìm Go của {', '.join(f'{name} ({target})' for _, name, _, target in pending)}")
        before = set(ctx["finished"])
        result = _run_tasks(bot, pending, ctx)
        if result in (TAB_NOT_FOUND, ICON_NOT_FOUND):
            _missing(bot)
            return
        for key, name, _, _ in pending:
            if key in ctx["finished"] and key not in before:
                bot.record(f"{NAME}: xong {name}")
                bot.yield_to_boss()
        if result == c.NOT_FOUND or (result == c.STOP and ctx["finished"] == before):
            misses += 1
            if misses >= c.TASK_SEARCH_TRIES:
                left = [t for t in pending if t[0] not in ctx["finished"]]
                names = ", ".join(name for _, name, _, _ in left)
                bot.record(f"{NAME}: lỗi: không tìm thấy nhiệm vụ {names} sau {misses} lần, đánh dấu xong hôm nay")
                for key, *_ in left:
                    bot.mark_daily_done(key)
                    ctx["finished"].add(key)
                break
            bot.record(f"{NAME}: không kết luận được nhiệm vụ nào ({misses}/{c.TASK_SEARCH_TRIES}), Back rồi làm lại")
            bot.back(delay=1.5)
            continue
        misses = 0
    bot.check()
    if _claim_and_redeem(bot, _order(settings)) in (TAB_NOT_FOUND, ICON_NOT_FOUND):
        _missing(bot)
        return
    bot.record(f"{NAME}: xong hôm nay")
    bot.mark_daily_done(c.DONE_KEY)


def _pending(bot, settings: dict, finished: set) -> list:
    """Nhiệm vụ bật mà chưa xong TRONG LƯỢT này: [(key, tên, after_go, mốc)]. Không xét daily_done."""
    pending = []
    for key, name, after_go in TASKS:
        target = _target(settings.get(key))
        if target is None or key in finished:
            continue
        if target not in c.TIERS[key]:
            bot.record(f"{NAME}: {name} target {target} has no row image, skipped")
            continue
        pending.append((key, name, after_go, target))
    return pending


def _missing(bot):
    bot.record(f"{NAME}: event not found in Event Center, mark done today")
    bot.mark_daily_done(c.DONE_KEY)


def _active(settings: dict) -> bool:
    group = settings.get(f"{c.GROUP_KEY}_active")
    return True if group is None else bool(group.get("enabled") if isinstance(group, dict) else group)


def _target(task) -> int | None:
    """Mốc đã chọn ở ô chọn; 0 / thiếu = không làm."""
    try:
        value = int((task or {}).get("value") or 0)
    except (TypeError, ValueError):
        return None
    return value or None


def _order(settings: dict) -> list[str]:
    """Thứ tự quà ưu tiên: settings, quà chưa có trong settings xếp sau; không có -> theo tên ảnh."""
    saved = (settings.get(c.REDEEM_KEY) or {}).get("order") or []
    every = sorted(p.stem for p in (TEMPLATE_DIR / c.REWARD_DIR).glob("*.png"))
    return [*[i for i in saved if i in every], *[i for i in every if i not in saved]]


# ---- Màn event ----------------------------------------------------------------------------
def _event_targets():
    return [(c.REDEEM_TAB, c.ON_EVENT), (c.REDEEM_TAB_ON, c.ON_EVENT)]


def _event_regions():
    return {c.REDEEM_TAB: c.TABS_REGION, c.REDEEM_TAB_ON: c.TABS_REGION}


def _event_thresholds():
    return {c.REDEEM_TAB: c.TAB_THRESHOLD, c.REDEEM_TAB_ON: c.TAB_THRESHOLD}


def _on_event(bot, screen) -> bool:
    return any(bot.find(tab, threshold=c.TAB_THRESHOLD, screen=screen, region=c.TABS_REGION) is not None
               for tab in (c.REDEEM_TAB, c.REDEEM_TAB_ON))


def _redeem_selected(bot, screen) -> bool:
    x, y, w, h = c.REDEEM_TAB_COLOR_BOX
    area = bot.crop(screen, x, y, w, h)
    return area.size > 0 and float(area[:, :, 2].mean()) >= c.TAB_ON_RED


def _same(a, b) -> bool:
    return a.shape == b.shape and float(np.abs(a.astype(np.int16) - b.astype(np.int16)).mean()) < c.SAME_DIFF


def _scroll(bot, swipe=c.SWIPE) -> bool:
    """Cuộn danh sách một lần. False nếu màn không đổi (hết danh sách)."""
    before = bot.screenshot()
    bot.swipe_percent(*swipe, duration=c.SWIPE_DURATION, delay=c.SWIPE_WAIT)
    return not _same(before, bot.screenshot())


def _wait_settled(bot):
    """Sau Go game chuyển cảnh (camera lướt tới công trình): chờ màn hình đứng yên (2 ảnh liên tiếp
    cách SETTLE_INTERVAL giây gần như giống nhau), tối đa SETTLE_MAX giây, rồi mới để after_go bấm —
    bấm khi camera còn lướt thì trượt công trình (máy thật: bệnh viện)."""
    previous = bot.screenshot()
    for _ in range(c.SETTLE_MAX):
        bot.sleep(c.SETTLE_INTERVAL)
        current = bot.screenshot()
        if _same(previous, current):
            return
        previous = current
    bot.log(f"{NAME}: screen still moving after {c.SETTLE_MAX} checks")


def _close_popup(bot, screen) -> bool:
    """Băng Congratulations hoặc popup che màn event -> Back. True nếu đã Back."""
    if bot.find(CONGRATULATIONS, screen=screen) is not None or not _on_event(bot, screen):
        bot.back(delay=1.5)
        return True
    return False


_last_claim: list = []   # [vị trí Claim vừa bấm, số lần bấm liên tiếp ở đó]


def _claim_visible(bot, screen) -> bool:
    """Bấm nút Claim trên cùng đang thấy (từng dòng). True nếu đã bấm."""
    claims = sorted(_claim_buttons(bot, screen), key=lambda p: p[1])
    if not claims:
        _last_claim.clear()
        return False
    # Nút Claim bấm hoài vẫn còn ở cùng chỗ (máy thật: 36 lần liền ở (326, 553)): bỏ qua, cuộn tiếp.
    if _last_claim and abs(_last_claim[0][0] - claims[0][0]) <= 3 and abs(_last_claim[0][1] - claims[0][1]) <= 3:
        _last_claim[1] += 1
        if _last_claim[1] >= c.CLAIM_SAME_MAX:
            bot.record(f"{NAME}: claim at {claims[0]} still there after {_last_claim[1]} taps, skip")
            return False
    else:
        _last_claim[:] = [claims[0], 1]
    bot.log(f"{NAME}: claim at {claims[0]}")
    bot.tap(*claims[0], delay=c.CLAIM_WAIT)
    _close_popup(bot, bot.screenshot())
    return True


# ---- 1. Nhiệm vụ --------------------------------------------------------------------------
def _run_tasks(bot, pending, ctx):
    def handle(action, pos, screen):
        if action != c.ON_EVENT:
            return None
        return _scan_tasks(bot, pending, ctx)

    return run_task(bot, NAME, LIMITED, c.icons(), handle, targets=_event_targets(),
                    regions=_event_regions(), thresholds=_event_thresholds(),
                    icon_threshold=c.ICON_THRESHOLD)


_ROW_DONE, _RESCAN, _SEEN = "row_done", "rescan", "seen"   # kết quả _check_task (None: nhiệm vụ không có trên màn)
_CLAIM, _GO, _CLAIMED = "claim", "go", "claimed"            # trạng thái nút của một dòng nhiệm vụ


def _scan_tasks(bot, pending, ctx):
    """Tab nhiệm vụ (vừa vào là đã ở đầu danh sách, không cuộn lên): cuộn xuống, tìm dòng của các nhiệm vụ
    `pending` (Alliance / Heal), thấy cái nào xử lý cái đó rồi cuộn tiếp tìm cái còn lại. KHÔNG dựa vào dấu "đã
    xong" tự lưu để bỏ qua (donate xong là tự đánh dấu, nhưng vào danh sách vẫn kiểm cả 2): chỉ coi nhiệm vụ xong
    (ctx["finished"]) khi thấy một trong 3 trường hợp (xem _check_task). Sau khi bấm Go trả HANDLED (quét lại từ
    đầu). Không thấy nhiệm vụ nào -> NOT_FOUND (run() Back rồi thử lại); STOP = quét xong."""
    left = [t for t in pending if t[0] not in ctx["finished"]]
    found = set()
    claimed_scrolls = 0   # số màn đã cuộn qua kể từ khi thấy Claimed
    at_top = True         # chưa cuộn lần nào: dòng có Claim chỉ nổi lên đầu danh sách lúc vừa vào
    for _ in range(c.MAX_ITERATIONS):
        screen = bot.screenshot()
        if not _on_event(bot, screen):
            return HANDLED
        if _redeem_selected(bot, screen):
            bot.tap(*c.TASK_TAB_TAP, delay=2)
            continue
        rescan = False
        for task in list(left):
            result = _check_task(bot, screen, task, ctx)
            if result is None:
                continue
            found.add(task[0])
            if result == _RESCAN:
                rescan = True
                break
            if result == _ROW_DONE:
                ctx["finished"].add(task[0])
                left.remove(task)
                continue
            if result == _SEEN:
                continue
            return result
        if rescan:
            continue
        if not left:
            return c.STOP
        if at_top and _claim_visible(bot, screen):
            continue
        if _claimed_visible(bot, screen) and all(t[0] in found for t in left):
            # Dòng đã nhận nằm cuối danh sách theo thứ tự ban đầu (Donate rồi tới Heal...). Thấy Claimed chỉ cho thôi
            # cuộn khi đã thấy dòng của MỌI nhiệm vụ còn lại (dòng Claimed của nhiệm vụ đã xong không tính: Heal còn
            # nằm sau dòng Donate đã nhận); chưa thì cuộn tiếp tới cuối danh sách thật. Cuộn thêm tối đa
            # CLAIMED_EXTRA_SCROLLS màn để thấy hết dòng đã nhận của các nhiệm vụ đó.
            claimed_scrolls += 1
            if claimed_scrolls > c.CLAIMED_EXTRA_SCROLLS:
                bot.log(f"{NAME}: Claimed seen, end of list")
                break
        at_top = False
        if not _scroll(bot, c.SWIPE_FINE if found else c.SWIPE):
            break
    if not found:
        return c.NOT_FOUND
    bot.record(f"{NAME}: task row not concluded: {', '.join(name for _, name, _, _ in left)}")
    return c.STOP


def _claimed_visible(bot, screen) -> bool:
    """Nút xám "Claimed" (tâm x CLAIM_X) đang thấy: dòng đã nhận nằm cuối danh sách."""
    return any(abs(p[0] - c.CLAIM_X) <= c.CLAIM_X_TOL
               for p in bot.find_all(c.CLAIMED, threshold=c.CLAIMED_THRESHOLD, screen=screen,
                                     region=c.CLAIM_REGION))


def _row_status(bot, screen, title):
    """(trạng thái, vị trí nút) của dòng có chữ `title`: Claim (xanh) / Go / Claimed (xám); None nếu chưa thấy
    nút nào (dòng nằm sát mép màn)."""
    claim = _row_button(bot, screen, title, c.CLAIM, c.CLAIM_THRESHOLD, c.CLAIM_REGION, x=c.CLAIM_X)
    if claim is not None:
        return _CLAIM, claim
    go = _row_button(bot, screen, title, GO_BUTTON, 0.85, GO_REGION)
    if go is not None:
        return _GO, go
    claimed = _row_button(bot, screen, title, c.CLAIMED, c.CLAIMED_THRESHOLD, c.CLAIM_REGION, x=c.CLAIM_X)
    if claimed is not None:
        return _CLAIMED, claimed
    return None, None


def _three_claimed(rows) -> bool:
    """`rows` = [(chữ, trạng thái)] trên xuống dưới: có 3 dòng liên tiếp (cách nhau ROW_PITCH_TASK) cùng Claimed."""
    for i in range(len(rows) - 2):
        a, b, c3 = rows[i:i + 3]
        if (a[1] == b[1] == c3[1] == _CLAIMED
                and abs(b[0][1] - a[0][1] - c.ROW_PITCH_TASK) <= c.ROW_TOLERANCE
                and abs(c3[0][1] - b[0][1] - c.ROW_PITCH_TASK) <= c.ROW_TOLERANCE):
            return True
    return False


def _check_task(bot, screen, task, ctx):
    """Dòng của nhiệm vụ `task` trên `screen`; None nếu không thấy chữ. Gặp Claim: bấm nhận (_RESCAN). Còn lại
    xong (_ROW_DONE) chỉ trong 3 trường hợp:
    1. Có nút Go và số đã làm (OCR lại) >= mục tiêu (yêu cầu bé hơn hoặc bằng đã làm);
    2. Thấy đủ 3 dòng liên tiếp đều Claimed;
    3. Thấy đủ 3 dòng đều Claim — bấm nhận từng dòng, sau khi nhận chúng thành Claimed (trường hợp 2).
    Có Go mà chưa đủ mục tiêu: bấm Go, làm after_go (donate / heal), trả HANDLED để quét lại từ đầu và OCR
    lại; bấm quá GO_TRIES lần mà vẫn chưa đủ (hết lính bị thương, hết kim cương...) -> ghi nhận không đạt, xong hôm
    nay. Chưa kết luận được (OCR lỗi, dòng sát mép) -> _SEEN: cuộn tiếp."""
    key, name, after_go, target = task
    titles = _titles(bot, screen, key)
    if not titles:
        return None
    rows = [(title, *_row_status(bot, screen, title)) for title in titles]
    for title, status, pos in rows:
        if status == _CLAIM:
            bot.log(f"{NAME}: {name} row has Claim, claim")
            bot.tap(*pos, delay=c.CLAIM_WAIT)
            _close_popup(bot, bot.screenshot())
            return _RESCAN
    for title, status, pos in rows:
        if status != _GO:
            continue
        done = _progress(bot, screen, pos)
        bot.log(f"{NAME}: {name} done {done}, target {target}")
        if done is None:
            bot.record(f"{NAME}: {name} cannot read progress, skip this screen")
            return _SEEN
        if done >= target:
            bot.record(f"{NAME}: {name} target reached ({done} >= {target}), done")
            mark_target_reached(bot, key)
            return _ROW_DONE
        tries = ctx["go_tries"][key] = ctx["go_tries"].get(key, 0) + 1
        if tries > c.GO_TRIES:
            bot.record(f"{NAME}: {name} cannot reach {target} after {c.GO_TRIES} tries, mark done today")
            bot.mark_daily_done(key)
            return _ROW_DONE
        bot.tap(*pos, delay=c.GO_WAIT)
        _wait_settled(bot)
        after_go(bot, SimpleNamespace(key=key, name=name), done, target)
        return HANDLED
    if _three_claimed([(title, status) for title, status, _ in rows]):
        bot.record(f"{NAME}: {name} 3 rows all Claimed, done")
        mark_target_reached(bot, key)
        return _ROW_DONE
    return _SEEN


def _titles(bot, screen, key) -> list:
    """Mọi chữ chung của nhiệm vụ `key` đang thấy (tâm, trên -> dưới, gộp khớp trùng)."""
    hits = sorted((pos for image in c.row_texts(key)
                   for pos in bot.find_all(image, threshold=c.ROW_TEXT_THRESHOLD, screen=screen,
                                           region=c.ROWS_REGION)), key=lambda p: p[1])
    out = []
    for pos in hits:
        if not out or abs(pos[1] - out[-1][1]) > c.ROW_TOLERANCE:
            out.append(pos)
    return out


def _claim_buttons(bot, screen) -> list:
    """Nút Claim xanh (tâm x CLAIM_X): ảnh "Claim" cũng khớp phần đầu của nút xám "Claimed" nhưng
    tâm lệch về trái (~x 326) -> loại theo x."""
    return [p for p in bot.find_all(c.CLAIM, threshold=c.CLAIM_THRESHOLD, screen=screen, region=c.CLAIM_REGION)
            if abs(p[0] - c.CLAIM_X) <= c.CLAIM_X_TOL]


def _row_button(bot, screen, title, template, threshold, region, x=None):
    """Nút `template` (Go / Claim) nằm cùng dòng với tiêu đề `title`, hoặc None. `x`: chỉ nhận nút có
    tâm x gần giá trị này."""
    for button in sorted(bot.find_all(template, threshold=threshold, screen=screen, region=region),
                         key=lambda p: p[1]):
        if x is not None and abs(button[0] - x) > c.CLAIM_X_TOL:
            continue
        if abs(button[1] - (title[1] + c.ROW_GO_DY)) <= c.ROW_GO_TOLERANCE:
            return button
    return None


def _progress(bot, screen, go) -> int | None:
    dx, dy, w, h = c.PROGRESS_FROM_GO
    return read_progress(bot.crop(screen, go[0] + dx, go[1] + dy, w, h))


# ---- 2. Nhận quà + đổi quà ----------------------------------------------------------------
def _claim_and_redeem(bot, order):
    """Cả 2 nhiệm vụ đã xong (quà đã nhận ngay lúc quét nhiệm vụ): sang tab Redeem và đổi quà luôn, không cuộn
    lại danh sách nhiệm vụ để kiểm tra."""
    def handle(action, pos, screen):
        if action != c.ON_EVENT:
            return None
        if not _redeem_selected(bot, screen):
            bot.tap(*c.REDEEM_TAB_TAP, delay=2)
            return HANDLED
        _redeem(bot, order)
        return c.STOP

    return run_task(bot, NAME, LIMITED, c.icons(), handle, targets=_event_targets(),
                    regions=_event_regions(), thresholds=_event_thresholds(),
                    icon_threshold=c.ICON_THRESHOLD)


_GREY, _REDEEMED = "grey", "redeemed"   # kết quả _redeem_item (không thấy quà: None)


def _redeem(bot, order):
    """Đổi lần lượt theo `order`. Vừa sang tab Redeem chưa biết đang đứng ở đâu (game giữ vị trí cuộn cũ): tìm
    ảnh quà theo thứ tự ưu tiên tới hết danh sách quà, thấy ảnh nào thì biết đang ở hàng nào (_measure). Sau đó
    mỗi quà cuộn THẲNG tới hàng của nó (hàng nhớ trong event.json, lên hoặc xuống tuỳ vị trí đang đứng) rồi
    đổi hết; nút xám (hết vé hoặc hết lượt) thì bỏ qua sang quà kế; GREY_STOP quà xám liên tiếp thì dừng."""
    rows = c.reward_rows()
    order = [i for i in order if i in rows]
    # state: offset = px đã cuộn xuống từ đầu danh sách (None = chưa biết); factor = px danh sách thực trôi /
    # px vuốt (quán tính làm danh sách trôi hơn quãng vuốt; tự hiệu chỉnh sau mỗi lần vuốt).
    state = {"offset": None, "factor": c.DRAG_FACTOR, "order": order, "rows": rows}
    state["offset"] = _locate(bot, state)
    bot.log(f"{NAME}: redeem list offset {state['offset']}")
    grey = 0   # số quà xám liên tiếp
    for item in order:
        result = _redeem_item(bot, item, rows[item], state)
        grey = grey + 1 if result == _GREY else 0
        if grey >= c.GREY_STOP:
            bot.record(f"{NAME}: {grey} greyed items in a row, stop redeem")
            break
    bot.record(f"{NAME}: redeem pass finished")


def _locate(bot, state: dict):
    """Vị trí cuộn hiện tại: đo (_measure) trên màn vừa chụp; không thấy icon nào (màn còn đang chuyển sang tab
    Redeem, animation, popup) thì chờ rồi đo lại tối đa LOCATE_TRIES lần, KHÔNG tự giả định đang ở đầu danh sách."""
    for attempt in range(c.LOCATE_TRIES):
        offset = _measure(bot, bot.screenshot(), state)
        if offset is not None:
            return offset
        if attempt < c.LOCATE_TRIES - 1:
            bot.log(f"{NAME}: no reward icon on screen yet, wait and measure again ({attempt + 1}/{c.LOCATE_TRIES})")
            bot.sleep(c.LOCATE_WAIT)
    return None


def _measure(bot, screen, state: dict):
    """Vị trí cuộn hiện tại (px từ đầu danh sách) theo icon quà đầu tiên thấy, tìm theo thứ tự ưu tiên rồi tới
    hết các quà còn lại; None nếu không thấy icon nào."""
    rows = state["rows"]
    for item in [*state["order"], *[i for i in rows if i not in state["order"]]]:
        pos = bot.find(f"{c.REWARD_DIR}/{item}.png", threshold=c.REWARD_THRESHOLD, screen=screen,
                       region=c.REWARD_REGION)
        if pos is not None:
            return _row_y(rows[item], 0) - pos[1]
    return None


def _drag(bot, delta: float):
    """Vuốt danh sách sao cho ngón tay đi `delta` px (dương = cuộn xuống, âm = lên), chia nhiều lần nếu dài."""
    while abs(delta) > c.DRAG_MIN:
        step = min(abs(delta), c.DRAG_MAX)
        sign = 1 if delta > 0 else -1
        y1 = c.DRAG_MID + sign * step / 2 / c.SCREEN_H * 100
        y2 = c.DRAG_MID - sign * step / 2 / c.SCREEN_H * 100
        bot.swipe_percent(50, y1, 50, y2, duration=c.DRAG_DURATION, delay=c.SWIPE_WAIT)
        delta -= sign * step


def _row_y(index: int, offset: float) -> float:
    return c.ROW_FIRST_Y + c.ROW_PITCH * index - offset


def _find_row(bot, icon: str, index: int, state: dict, tries: int = c.GOTO_TRIES):
    """Cuộn tới hàng `index` rồi trả toạ độ icon (None nếu không tới được sau GOTO_TRIES lần). Mỗi vòng: thấy
    icon (trong vùng bấm được) thì xong; không thì đo vị trí thật (_measure), vuốt phần còn lại chia cho hệ số
    trôi, rồi đo lại để hiệu chỉnh hệ số. Gần đích mà chưa thấy icon thì xê dịch lên / xuống."""
    target = max(0.0, _row_y(index, 0) - c.ROW_TARGET_Y)
    for attempt in range(tries):
        screen = bot.screenshot()
        pos = bot.find(icon, threshold=c.REWARD_THRESHOLD, screen=screen, region=c.REWARD_REGION)
        if pos is not None and c.ROW_VISIBLE[0] <= pos[1] <= c.ROW_VISIBLE[1]:
            state["offset"] = _row_y(index, 0) - pos[1]
            return pos
        offset = _measure(bot, screen, state)
        if offset is None:
            offset = state["offset"] if state["offset"] is not None else _locate(bot, state)
        if offset is None:
            bot.log(f"{NAME}: row {index}: list position unknown, assume top")
            offset = 0.0
        delta = target - offset
        if abs(delta) < c.GOTO_TOL:
            delta = c.NUDGE * (1 if attempt % 2 == 0 else -1)
        commanded = delta / state["factor"]
        bot.log(f"{NAME}: row {index}: at {offset:.0f}, target {target:.0f}, drag {commanded:.0f} (x{state['factor']:.2f})")
        _drag(bot, commanded)
        after = _measure(bot, bot.screenshot(), state)
        if after is not None and abs(commanded) > c.FACTOR_MIN_DRAG:
            ratio = (after - offset) / commanded
            if 0.5 <= ratio <= 3.5:
                state["factor"] = 0.5 * state["factor"] + 0.5 * ratio
        state["offset"] = after if after is not None else offset + commanded * state["factor"]
    return None


def _redeem_item(bot, item, index: int, state: dict):
    """Quà `item` (hàng `index`): tìm icon (cuộn tới hàng nếu chưa thấy), nút Redeem cùng dòng xanh thì bấm
    -> popup số lượng: bấm cạnh "+" (chọn tất cả) -> nút xanh -> xong, loại quà khỏi danh sách đổi (_REDEEMED);
    nút xám thì loại luôn (_GREY); không tìm thấy icon -> None. Không kiểm lại dòng sau khi đổi. Danh sách
    đổi chỉ giữ trong lượt chạy này (không lưu DB)."""
    icon = f"{c.REWARD_DIR}/{item}.png"
    pos = _find_row(bot, icon, index, state)
    if pos is None:
        bot.log(f"{NAME}: redeem {item} not found near row {index}")
        return None
    button = (c.REDEEM_BUTTON_X, pos[1] + c.REDEEM_BUTTON_DY)
    if not _button_green(bot, bot.screenshot(), button):
        bot.record(f"{NAME}: redeem {item} greyed, skip")
        return _GREY
    bot.log(f"{NAME}: redeem {item} at {button}")
    bot.tap(*button, delay=c.REDEEM_WAIT)
    if bot.wait_for(c.QTY_PLUS, timeout=c.QTY_WAIT, threshold=0.9) is not None:
        bot.tap(*c.QTY_MAX_TAP, delay=1)
        bot.tap(*c.QTY_CONFIRM_TAP, delay=c.REDEEM_WAIT)
    for _ in range(c.POPUP_BACKS):
        if not _close_popup(bot, bot.screenshot()):
            break
    bot.record(f"{NAME}: redeemed {item}")
    return _REDEEMED


def _button_green(bot, screen, center) -> bool:
    dx, dy, w, h = c.REDEEM_COLOR_BOX
    area = bot.crop(screen, center[0] + dx, center[1] + dy, w, h).reshape(-1, 3).mean(axis=0)
    return float(area[1] - area[2]) >= c.REDEEM_GREEN_DIFF   # BGR: G - R
