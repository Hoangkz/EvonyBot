"""Hoạt động Super Value Return (file riêng, độc lập với Valuable Event; cùng cách đi hàng tab).

Một LƯỢT TÌM (tối đa PASSES lượt mỗi ngày, số lượt đã xong lưu DB key ``gift_super_value_return_pass_1..3``):

1. Từ màn thành bấm vào Super Value Return (open_super_value_return; chọn một lối vào thay thế trong launcher.py).
2. Làm các event cần làm đang thấy ở hàng tab: bấm giữa ô tab, chờ sang trang, bấm chỗ tiêu đề rồi chạy flow riêng (do_visible).
3. Kéo dài về giới hạn bên trái (swipe_to_left_edge), một lần mỗi lượt; làm tiếp các event cần làm vừa hiện ra.
4. Kéo ngắn từ phải sang trái từng cú, mỗi chỗ làm các event cần làm đang thấy; icon ngoài cùng bên trái đứng nguyên chỗ 2 cú
   liên tiếp = đã chạm bên phải (scan_to_right_edge).
5. Chạm bên phải: lưu DB đã xong lượt tìm N hôm nay, bấm Back, làm lại từ bước 1.

Lượt thấy event mới thì đếm lại từ lượt 1. Đủ PASSES lượt (hoặc mọi event đã xong): đánh dấu mọi event và key tổng là xong hôm nay.
"""
import cv2

from ....common import to_city
from ....daily_reset import last_reset
from ..common import (REFERENCE_WIDTH, back_if_close_x, find, mark_task_done, on_main, return_home,
                      skip_for_run)
from ..screens import GiftScreen, identify
from ..valuable_event.named_flow import (SLOW_SWIPE_DURATION, STEP_DELAY, TASK_TAB_THRESHOLD, TOP_CAROUSEL,
                                         process_exact)
from . import (city_growth_plan, empire_depot, login_gifts, lucky_raffle,
                refining_weekly_card)
from ..valuable_event import hall_of_historic_generals, soul_of_spiritual_beast
from .launcher import find_super_value_return
from .run import SPECS, run_opened

KEY = "gift_super_value_return"
NAME = "Super Value Return"
PASSES = 3              # số lượt tìm mỗi ngày; đủ thì mọi event của hoạt động coi là xong hôm nay
SEEN_ATTR = "_super_value_return_seen"   # thuộc tính trên context: (mốc reset, event đã thấy) — xem seen_today
OPEN_TAPS = 2           # bấm nút vào; vẫn ở màn thành thì bấm lại, tổng tối đa chừng này lần
OPEN_WAITS = 8          # sau mỗi lần bấm: cứ 1s chụp kiểm tra tiêu đề Super Value Return, tối đa chừng này lần
# Hàng tab cùng kiểu với Valuable Event (đo trên màn 396x704):
TAB_TAP_Y = 13                   # % màn: bấm vào chính giữa ô tab (ô cao y 62-122), x theo tab tìm được
AFTER_TAB_TAP = (50, 5)          # % màn (chỗ tiêu đề): đã sang trang event thì bấm chỗ này, nghỉ 1s, rồi mới chạy flow
PAGE_PROBE = (2, 20, 30, 30)     # % màn: ô cắt trước khi bấm tab (dưới hàng tab, góc trái) để biết đã sang event chưa
PAGE_SAME = 0.9                  # ô đó còn khớp từ mức này = chưa sang trang event mới
TAB_WAITS = 5                    # sau mỗi lần bấm tab: kiểm tra tối đa chừng này lần, mỗi lần chờ 1s
TAB_TAPS = 2                     # số lần bấm tab (bấm lại 1 lần); vẫn chưa sang thì bỏ qua event trong lượt này
SELECTED_BAND_Y = (16.4, 17.1)   # % màn: dải ngay dưới chữ tên tab; tab đang chọn sáng hơn
SELECTED_HALF_W = 35             # px (màn rộng 396): lấy dải này trong khoảng tâm tab +- chừng này
SELECTED_V = 60                  # độ sáng trung bình từ mức này = tab đang chọn
FIRST_SWIPE = (5, 12, 500, 12)   # % màn: cú kéo dài đầu tiên về bên trái (điểm cuối ra ngoài mép phải)
EDGE_BACK_SWIPE = (5, 12, 95, 12)   # % màn: swipe_to_left_edge từ cú thứ 2 kéo ngắn trái sang phải
EDGE_SWIPES = 8                  # swipe_to_left_edge: tối đa chừng này cú kéo
EDGE_ICON = (36, 7.5, 52, 13.5)  # % màn: ô cắt một icon ở hàng tab sau mỗi cú kéo
EDGE_SEARCH = (0, 5, 100, 17)    # % màn: vùng tìm lại icon đã cắt (cả hàng tab)
EDGE_SAME = 0.8                  # icon vẫn thấy (khớp từ mức này) ...
EDGE_SETTLE = 1.0                # giây nghỉ sau mỗi cú kéo, rồi mới chụp
SHORT_SWIPE = (60, 12, 5, 12)    # % màn: kéo ngắn từ phải sang trái tìm tiếp
SHORT_SWIPES = 30                # scan_to_right_edge: tối đa chừng này cú kéo ngắn
LEFT_ICON = (8, 7.5, 26, 13.5)   # % màn: ô cắt icon ngoài cùng bên trái trước mỗi cú kéo ngắn
LEFT_SAME_PX = 20                # ... VÀ lệch không quá chừng này px mới là giới hạn trái
SHORT_SAME_PX = 2                # scan_to_right_edge: icon phải đứng nguyên chỗ
EDGE_CONFIRM = 2                 # số cú kéo ngắn liên tiếp không dịch mới là chạm bên phải
TITLE_REGION = (0, 0, 100, 6)    # % màn: thanh tiêu đề; trước mỗi cú kéo phải khớp ảnh cắt lúc vừa vào màn (popup che thì không)
TITLE_SAME = 0.99
TITLE_WAITS = 5                  # không khớp: chờ 1s, tối đa chừng này lần; vẫn không khớp thì Back
NOTICE_BAND = (13.0, 16.7)       # % màn: dải thông báo chạy chữ có dấu X đỏ để tắt
NOTICE_X_PX = (9, 22)            # px (màn rộng 396): cạnh cụm đỏ
NOTICE_X_FILL = (0.15, 0.5)
NOTICE_X_DIAG = 0.5
DEPOT_POPUP_CLOSE = "SuperValueReturn/button_close_popup"   # popup Depot Rewards Boost
DEPOT_POPUP_REGION = (80, 5, 100, 20)

TASKS = (
    login_gifts.TASK,
    empire_depot.TASK,
    hall_of_historic_generals.TASK,
    soul_of_spiritual_beast.TASK,
    lucky_raffle.TASK,
    city_growth_plan.TASK,
    refining_weekly_card.TASK,
)


def _box(screen, region):
    height, width = screen.shape[:2]
    x0, y0, x1, y1 = region
    return int(width * x0 / 100), int(height * y0 / 100), int(width * x1 / 100), int(height * y1 / 100)


def _cut(screen, region):
    left, top, right, bottom = _box(screen, region)
    return screen[top:bottom, left:right].copy()


def _find_icon(screen, icon) -> tuple[float, int]:
    """(độ khớp, x) chỗ giống icon đã cắt nhất trong hàng tab."""
    left, top, right, bottom = _box(screen, EDGE_SEARCH)
    _, score, _, (x, _) = cv2.minMaxLoc(cv2.matchTemplate(screen[top:bottom, left:right], icon, cv2.TM_CCOEFF_NORMED))
    return score, left + x


def _at_edge(screen, icon, cut_x: int, same_px: float) -> bool:
    """Icon đã cắt ở `cut_x` vẫn thấy (>= EDGE_SAME) và lệch không quá `same_px` = hàng tab không dịch nữa (đã chạm biên)."""
    score, x = _find_icon(screen, icon)
    return score >= EDGE_SAME and abs(x - cut_x) <= same_px * screen.shape[1] / REFERENCE_WIDTH


def find_notice_x(screen) -> "tuple[int, int] | None":
    """Tâm dấu X đỏ của dải thông báo chạy chữ, hoặc None. Chỉ xét hình dấu X, không đọc chữ thông báo."""
    height, width = screen.shape[:2]
    scale = width / REFERENCE_WIDTH
    top, bottom = int(height * NOTICE_BAND[0] / 100), int(height * NOTICE_BAND[1] / 100)
    hsv = cv2.cvtColor(screen[top:bottom], cv2.COLOR_BGR2HSV)
    red = (((hsv[..., 0] <= 10) | (hsv[..., 0] >= 170)) & (hsv[..., 1] > 140) & (hsv[..., 2] > 140)).astype("uint8")
    count, labels, stats, _ = cv2.connectedComponentsWithStats(red, 8)
    low, high = NOTICE_X_PX[0] * scale, NOTICE_X_PX[1] * scale
    for i in range(1, count):
        x, y, w, h, area = (int(v) for v in stats[i])
        if not (low <= w <= high and low <= h <= high and 0.7 <= w / h <= 1.4):
            continue
        if not NOTICE_X_FILL[0] <= area / (w * h) <= NOTICE_X_FILL[1]:
            continue
        ys, xs = (labels[y:y + h, x:x + w] == i).nonzero()
        u, v = xs / w, ys / h
        if (abs(u - v) < 0.25).mean() >= NOTICE_X_DIAG and (abs(u + v - 1) < 0.25).mean() >= NOTICE_X_DIAG:
            return x + w // 2, top + y + h // 2
    return None


def _settled_screenshot(bot):
    """Sau một cú kéo: nghỉ 1s rồi chụp; thấy dấu X của dải thông báo thì bấm tắt, nghỉ 1s, chụp lại."""
    bot.sleep(EDGE_SETTLE)
    screen = bot.screenshot()
    notice = find_notice_x(screen)
    if notice is None:
        return screen
    bot.record(f"Gift Claims: thấy dấu X của thông báo tại {notice}; bấm tắt")
    bot.tap(*notice)
    bot.sleep(EDGE_SETTLE)
    return bot.screenshot()


def capture_title(bot, screen=None):
    """Cắt thanh tiêu đề (TITLE_REGION) trên màn Super Value Return vừa vào, làm mốc so trước mỗi cú kéo (biến của lượt tìm)."""
    screen = bot.screenshot() if screen is None else screen
    return _cut(screen, TITLE_REGION)


def title_matches(screen, title) -> bool:
    """Thanh tiêu đề hiện tại khớp ảnh mốc `title` (1 - chênh lệch điểm ảnh TB / 255 >= TITLE_SAME)."""
    current = _cut(screen, TITLE_REGION)
    if current.shape != title.shape:
        return False
    return 1 - float(cv2.absdiff(current, title).mean()) / 255 >= TITLE_SAME


def wait_title_clear(bot, title) -> bool:
    """Trước một cú kéo: thanh tiêu đề phải khớp ảnh mốc `title`. Không khớp thì chờ 1s, tối đa TITLE_WAITS lần; vẫn không khớp thì
    Back (đóng popup đang phủ) rồi kiểm tra lại. True khi đã khớp."""
    for _ in range(TITLE_WAITS):
        if title_matches(bot.screenshot(), title):
            return True
        bot.sleep(STEP_DELAY)
    bot.record(f"Gift Claims: thanh tiêu đề {NAME} chưa khớp sau {TITLE_WAITS} lần chờ; bấm Back")
    bot.back(delay=STEP_DELAY)
    return title_matches(bot.screenshot(), title)


def swipe_to_left_edge(bot, title) -> bool:
    """Kéo hàng tab về giới hạn bên trái, tối đa EDGE_SWIPES cú: cú đầu kéo dài FIRST_SWIPE (5% -> 500%), từ cú thứ 2 kéo ngắn
    EDGE_BACK_SWIPE (5% -> 95%). Sau mỗi cú nghỉ 1s, cắt một icon (EDGE_ICON); sau cú kế tiếp icon đó vẫn thấy, lệch không quá
    LEFT_SAME_PX = đã tới giới hạn, dừng. True khi thấy đã tới giới hạn."""
    icon = None
    cut_x = 0
    for swipe in range(1, EDGE_SWIPES + 1):
        if not wait_title_clear(bot, title):
            bot.record(f"Gift Claims: tiêu đề {NAME} vẫn bị che; dừng kéo về trái")
            return False
        bot.swipe_percent(*(FIRST_SWIPE if swipe == 1 else EDGE_BACK_SWIPE), duration=SLOW_SWIPE_DURATION)
        screen = _settled_screenshot(bot)
        if icon is not None and _at_edge(screen, icon, cut_x, LEFT_SAME_PX):
            bot.record(f"Gift Claims: hàng tab {NAME} đã tới giới hạn bên trái sau {swipe} cú kéo")
            return True
        icon = _cut(screen, EDGE_ICON)
        cut_x = _box(screen, EDGE_ICON)[0]
    bot.record(f"Gift Claims: kéo hàng tab {NAME} {EDGE_SWIPES} cú vẫn chưa thấy giới hạn bên trái")
    return False


def _page_changed(screen, probe, box) -> bool:
    """Ô PAGE_PROBE đã khác ảnh cắt trước khi bấm (so đúng chỗ đó) = đã sang trang event khác."""
    left, top, right, bottom = box
    return float(cv2.matchTemplate(screen[top:bottom, left:right], probe, cv2.TM_CCOEFF_NORMED).max()) < PAGE_SAME


def tab_selected(screen, pos) -> bool:
    """Tab có tâm `pos` đang được chọn (nền sáng hơn): dải SELECTED_BAND_Y dưới chữ tên tab, trong khoảng tâm +- SELECTED_HALF_W."""
    height, width = screen.shape[:2]
    half = SELECTED_HALF_W * width / REFERENCE_WIDTH
    top, bottom = int(height * SELECTED_BAND_Y[0] / 100), int(height * SELECTED_BAND_Y[1] / 100) + 1
    left, right = max(0, int(pos[0] - half)), min(width, int(pos[0] + half))
    band = cv2.cvtColor(screen[top:bottom, left:right], cv2.COLOR_BGR2HSV)[..., 2]
    return band.size > 0 and float(band.mean()) >= SELECTED_V


def tap_title(bot) -> None:
    """Đã ở trang event: bấm AFTER_TAB_TAP (chỗ tiêu đề) rồi nghỉ 1s, xong mới chạy flow của event."""
    bot.record("Gift Claims: bấm chỗ tiêu đề trước khi làm event")
    bot.tap_percent(*AFTER_TAB_TAP)
    bot.sleep(STEP_DELAY)


def open_tab(bot, pos) -> bool:
    """Mở trang event của tab tại `pos`, rồi bấm chỗ tiêu đề (tap_title). Tab đã được chọn sẵn thì không bấm tab. Còn lại: cắt ô
    PAGE_PROBE, bấm giữa ô tab (x của `pos`, y TAB_TAP_Y), cứ 1s xem ô đó đổi chưa, tối đa TAB_WAITS lần; chưa đổi thì bấm lại
    (TAB_TAPS lần bấm). True khi đã sang trang event."""
    before = bot.screenshot()
    if tab_selected(before, pos):
        bot.record("Gift Claims: tab event đang được chọn sẵn; không bấm tab")
        tap_title(bot)
        return True
    box = _box(before, PAGE_PROBE)
    probe = before[box[1]:box[3], box[0]:box[2]].copy()
    target = (pos[0], round(before.shape[0] * TAB_TAP_Y / 100))
    for attempt in range(1, TAB_TAPS + 1):
        bot.record(f"Gift Claims: bấm tab event tại {target} (lần {attempt}/{TAB_TAPS})")
        bot.tap(*target)
        for _ in range(TAB_WAITS):
            bot.sleep(STEP_DELAY)
            if _page_changed(bot.screenshot(), probe, box):
                tap_title(bot)
                return True
    return False


def close_popup(bot, screen) -> bool:
    """Đóng popup đang che hàng tab: Depot Rewards Boost (nút đóng góc trên phải) hoặc panel có nút X (Back). True khi đã đóng."""
    close = find(bot, DEPOT_POPUP_CLOSE, screen, threshold=0.78, region=DEPOT_POPUP_REGION)
    if close is not None:
        bot.record("Gift Claims: đóng Depot Rewards Boost trước khi tìm tab")
        bot.tap(*close)
        bot.sleep(STEP_DELAY)
        return True
    return back_if_close_x(bot, screen)


def find_tab(bot, spec, screen):
    """Tâm ảnh tab của event `spec` trên hàng tab, hoặc None."""
    return find(bot, spec.tab, screen, threshold=TASK_TAB_THRESHOLD, region=TOP_CAROUSEL)


def run_event(bot, spec) -> bool:
    """Đã ở trang event: chạy flow riêng; True = DONE. Login Gifts và Refining Weekly Card có hàm nhận riêng."""
    if spec.task.key == login_gifts.KEY:
        return bool(login_gifts.claim_opened(bot))
    if spec.task.key == refining_weekly_card.KEY:
        outcome = refining_weekly_card.claim_opened(bot)
        return outcome is True or outcome == refining_weekly_card.DONE
    if spec.task.key == hall_of_historic_generals.KEY:
        outcome = hall_of_historic_generals.claim_opened(bot)
        return outcome is True or outcome == hall_of_historic_generals.DONE
    if spec.task.key == soul_of_spiritual_beast.KEY:
        outcome = soul_of_spiritual_beast.claim_opened(bot)
        return outcome is True or outcome == soul_of_spiritual_beast.DONE
    return process_exact(bot, spec.flow)


def do_visible(bot, pending: set[str], attempted: set[str]) -> None:
    """Làm các event cần làm (`pending`, chưa thử trong lượt này) đang thấy ở hàng tab: mỗi lần chụp lại, bấm tab bên trái nhất
    (open_tab; không sang trang thì bỏ qua event trong lượt này) rồi chạy flow riêng; xong thì đánh dấu DONE và bỏ khỏi `pending`,
    chưa xong thì giữ PENDING (không thử lại trong lượt)."""
    while True:
        bot.check()
        screen = bot.screenshot()
        if close_popup(bot, screen):
            screen = bot.screenshot()
        visible = [(spec, pos) for spec in SPECS
                   if spec.task.key in pending and spec.task.key not in attempted
                   and (pos := find_tab(bot, spec, screen)) is not None]
        if not visible:
            return
        spec, pos = min(visible, key=lambda item: item[1][0])
        key = spec.task.key
        bot.record(f"Gift Claims: {NAME} mở {spec.task.label}")
        attempted.add(key)
        if not open_tab(bot, pos):
            bot.record(f"Gift Claims: bấm {spec.task.label} 2 lần vẫn chưa sang trang event; bỏ qua, lượt sau làm tiếp")
            continue
        if run_event(bot, spec):
            mark_task_done(bot, key)
            pending.discard(key)
        else:
            bot.record(f"Gift Claims: {spec.task.label} chưa đạt điều kiện DONE; giữ PENDING")
        bot.sleep(STEP_DELAY)


def scan_to_right_edge(bot, pending: set[str], attempted: set[str], title) -> bool:
    """Kéo ngắn SHORT_SWIPE (phải sang trái) tối đa SHORT_SWIPES cú, mỗi chỗ làm các event cần làm đang thấy. Trước mỗi cú cắt
    icon ngoài cùng bên trái (LEFT_ICON); kéo xong icon đó đứng nguyên chỗ EDGE_CONFIRM cú liên tiếp = chạm bên phải. Trước mỗi cú
    chờ tiêu đề rõ (wait_title_clear); không rõ thì dừng, lượt không được tính. True khi chạm bên phải."""
    still = 0
    for _ in range(SHORT_SWIPES):
        do_visible(bot, pending, attempted)
        if not wait_title_clear(bot, title):
            bot.record(f"Gift Claims: tiêu đề {NAME} vẫn bị che; dừng lượt này (không tính lượt)")
            return False
        before = bot.screenshot()
        icon = _cut(before, LEFT_ICON)
        cut_x = _box(before, LEFT_ICON)[0]
        bot.swipe_percent(*SHORT_SWIPE, duration=SLOW_SWIPE_DURATION)
        after = _settled_screenshot(bot)
        if not _at_edge(after, icon, cut_x, SHORT_SAME_PX):
            still = 0
            continue
        still += 1
        if still < EDGE_CONFIRM:
            bot.record(f"Gift Claims: hàng tab {NAME} không dịch; kéo thêm một cú để kiểm tra")
            continue
        bot.record(f"Gift Claims: hàng tab {NAME} đã chạm bên phải ({EDGE_CONFIRM} cú liên tiếp không dịch)")
        do_visible(bot, pending, attempted)
        return True
    bot.record(f"Gift Claims: kéo ngắn {SHORT_SWIPES} cú vẫn chưa chạm bên phải hàng tab {NAME}")
    return False


def open_super_value_return(bot) -> bool:
    """Từ màn thành chính (có nút •••; đang ở bản đồ thế giới thì to_city vào thành trước) tìm nút vào bằng
    find_super_value_return (các lối vào thay thế trong launcher.py) rồi bấm; cứ 1s xem có tiêu đề Super Value Return chưa, tối đa OPEN_WAITS lần.
    - Vào được: True.
    - Vẫn ở màn thành: bấm lại đúng nút đã chọn (tổng OPEN_TAPS lần), không thử các lối vào khác; vẫn không vào thì bỏ hoạt động tới khi Start lại (skip_for_run).
    - Sang màn khác: về thành, bỏ hoạt động tới khi Start lại.
    Không ở màn thành / không thấy nút: False (worker thử lại lần sau)."""
    bot.check()
    if not on_main(bot, bot.screenshot()):
        return_home(bot)
    if to_city(bot):
        bot.record("Gift Claims: đang ở bản đồ thế giới; đã chuyển vào thành")
    if not on_main(bot, bot.screenshot()):
        bot.record("Gift Claims: chưa ở màn thành chính; chưa mở được Super Value Return")
        return False
    pos = find_super_value_return(bot)
    if pos is None:
        return False
    for attempt in range(1, OPEN_TAPS + 1):
        bot.record(f"Gift Claims: bấm nút vào Super Value Return tại {pos} (lần {attempt}/{OPEN_TAPS})")
        bot.tap(*pos)
        for _ in range(OPEN_WAITS):
            bot.sleep(1)
            screen = bot.screenshot()
            if identify(bot, screen) == GiftScreen.SUPER_VALUE_RETURN:
                bot.record("Gift Claims: đã vào Super Value Return")
                return True
        if not on_main(bot, screen):
            bot.record("Gift Claims: bấm nút vào Super Value Return mà sang màn khác; bỏ qua tới khi Start lại")
            return_home(bot)
            skip_for_run(bot, KEY)
            return False
        bot.record(f"Gift Claims: sau {OPEN_WAITS}s vẫn ở màn thành (lần {attempt}/{OPEN_TAPS})")
    bot.record(f"Gift Claims: bấm {OPEN_TAPS} lần vẫn không vào Super Value Return; bỏ qua tới khi Start lại")
    skip_for_run(bot, KEY)
    return False


def search_pass(bot, pending: set[str], attempted: set[str]) -> bool:
    """Một lượt tìm (bước 1-4 ở đầu file); `attempted` (rỗng khi gọi) nhận các event đã thấy và bấm vào trong lượt. True khi đã đi
    hết hàng tab (chạm bên phải) hoặc mọi event cần làm đã xong."""
    if not open_super_value_return(bot):
        return False
    title = capture_title(bot)
    do_visible(bot, pending, attempted)
    if not pending:
        return True
    bot.record(f"Gift Claims: kéo dài hàng tab {NAME} về giới hạn bên trái")
    swipe_to_left_edge(bot, title)
    do_visible(bot, pending, attempted)
    if not pending:
        return True
    return scan_to_right_edge(bot, pending, attempted, title)


def _pass_key(number: int) -> str:
    return f"{KEY}_pass_{number}"


def passes_done(bot) -> int:
    """Số lượt tìm đã xong hôm nay (key DB tự hết hạn theo mốc reset server)."""
    return sum(1 for number in range(1, PASSES + 1) if bot.is_daily_done(_pass_key(number)))


def _reset_passes(bot) -> None:
    for number in range(1, PASSES + 1):
        if bot.done_at(_pass_key(number)) is not None:
            bot.forget_daily(_pass_key(number))


def seen_today(bot) -> set[str]:
    """Event đã thấy ở các lượt trước hôm nay. Để trên context, không ghi DB: còn qua các lần bị ngắt trong lần Start này; Start
    lại hoặc qua mốc reset server thì làm lại từ rỗng."""
    server_time = getattr(bot, "server_time", None)
    value = server_time() if callable(server_time) else ""
    day = last_reset(value if isinstance(value, str) else "")
    stored = getattr(bot, SEEN_ATTR, None)
    if not (isinstance(stored, tuple) and stored[0] == day):
        stored = (day, set())
        setattr(bot, SEEN_ATTR, stored)
    return stored[1]


def run(bot) -> bool:
    """Xong event nào lưu DB event đó; đủ lượt thì lưu key tổng KEY. Worker (``gift_claims.job``) chỉ đọc KEY trong DB (hoặc
    skip_for_run). Lượt nào thấy event MỚI (chưa thấy ở các lượt trước hôm nay) thì đếm lại từ lượt 1."""
    if bot.is_daily_done(KEY):
        return True
    seen = seen_today(bot)
    while passes_done(bot) < PASSES:
        pending = {task.key for task in TASKS if not bot.is_daily_done(task.key)}
        if not pending:
            break
        attempted: set[str] = set()
        if not search_pass(bot, pending, attempted):
            return_home(bot)
            return False      # không mở được / chưa đi hết hàng tab: lần chạy sau làm tiếp lượt này
        if attempted - seen:
            bot.record("Gift Claims: lượt này thấy event mới; đếm lại lượt tìm từ 1")
            _reset_passes(bot)
        seen |= attempted
        number = passes_done(bot) + 1
        bot.mark_daily_done(_pass_key(number))
        bot.record(f"Gift Claims: {NAME} xong lượt tìm {number}/{PASSES} hôm nay")
        bot.back(delay=STEP_DELAY)
    for task in TASKS:
        mark_task_done(bot, task.key)
    bot.mark_daily_done(KEY)
    bot.record(f"Gift Claims: {NAME} đủ {PASSES} lượt tìm; mọi event của hoạt động xong hôm nay")
    return_home(bot)
    return True


def _sweep(bot, pending: list[str], deferred: set[str] | None = None) -> set[str]:
    todo = [task for task in TASKS if task.key in pending and (deferred is None or task.key not in deferred)]
    if not todo:
        return set()
    if identify(bot, bot.screenshot()) != GiftScreen.SUPER_VALUE_RETURN:
        if not open_super_value_return(bot):
            bot.record("Gift Claims: không mở được Super Value Return; "
                       "chưa tính là không thấy")
            return set()
    results, scanned_all = run_opened(bot, {task.key for task in todo})
    if not scanned_all:
        return set()
    if deferred is not None:
        for k, v in results.items():
            if v == "done_1":
                deferred.add(k)
    return {key for key, state in results.items() if state == "not_present"}
