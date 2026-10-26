"""Hoạt động Valuable Event độc lập (không gồm Super Value Return).

Một LƯỢT TÌM (tối đa PASSES lượt mỗi ngày, số lượt đã xong lưu DB key ``gift_valuable_event_pass_1..3``):

1. Từ màn chính bấm vào Valuable Event (open_valuable_event).
2. Làm các event cần làm đang thấy ở hàng tab: bấm icon tab rồi chạy flow riêng của event đó (do_visible).
3. Kéo dài về giới hạn bên trái (swipe_to_left_edge), một lần mỗi lượt; làm tiếp các event cần làm vừa hiện ra.
4. Kéo ngắn từ phải sang trái từng cú, mỗi chỗ làm các event cần làm đang thấy; trước mỗi cú cắt icon ngoài cùng bên trái, kéo
   xong vẫn thấy icon đó = đã chạm bên phải (scan_to_right_edge).
5. Chạm bên phải: lưu DB đã xong lượt tìm N hôm nay, bấm Back, làm lại từ bước 1.

Lượt thấy event mới thì đếm lại từ lượt 1. Đủ PASSES lượt (hoặc mọi event đã xong): đánh dấu mọi event của hoạt động và key tổng là xong hôm nay.
"""
import cv2

from ....common import to_city
from ....daily_reset import last_reset
from ....ocr.find_valuable_event import find_valuable_event
from ..common import REFERENCE_WIDTH, back_if_close_x, mark_task_done, on_main, return_home
from ..screens import GiftScreen, identify
from . import (
    active_monthly_card, ancient_dynasty_treasury, general_vault, golden_tree_rewards, limited_offer,
    optional_package, refining_stone_sprint, resource_consumption_sprint,
    runestone_consumption_sprint,
    speedup_sprint, strategic_stockpile,
    successive_purchase_benefits, super_blazon_sale,
    super_value_weekly_card, tomb_expedition, wheel_of_dragon_war,
)
from .named_flow import SLOW_SWIPE_DURATION, STEP_DELAY, process_exact
from .run import SPECS, _tab

KEY = "gift_valuable_event"
PASSES = 3              # số lượt tìm mỗi ngày; đủ thì mọi event của hoạt động coi là xong hôm nay
SEEN_ATTR = "_valuable_event_seen"   # thuộc tính trên context: (mốc reset, event đã thấy) — xem seen_today
OPEN_ATTEMPTS = 3       # số lần về màn chính tìm nút + bấm; hết mà chưa vào thì bỏ hoạt động trong lần chạy này
OPEN_WAITS = 8          # sau khi bấm: chụp kiểm tra màn Valuable Event tối đa chừng này lần, mỗi lần chờ 1s
ICON_ABOVE = 30         # px (màn rộng 396): find_valuable_event trả về tâm chữ "Event", bấm lên icon phía trên
# % màn: tìm thấy tab thì bấm vào chính giữa ô tab. Ô tab cao y 62-122 trên màn 704 -> giữa y 92 (13%); icon nằm giữa ô theo
# chiều ngang nên x lấy theo tab tìm được. Tâm icon (y ~75) chỉ là nửa trên ô: Optional Package bấm ở đó game không nhận.
TAB_TAP_Y = 13
AFTER_TAB_TAP = (50, 5)  # % màn (chỗ tiêu đề): đã sang trang event thì bấm chỗ này, nghỉ 1s, rồi mới chạy flow của event
PAGE_PROBE = (2, 20, 30, 30)   # % màn: ô cắt trước khi bấm tab (dưới hàng tab, góc trái: banner trang event) để biết đã sang event chưa
PAGE_SAME = 0.9                # ô đó còn khớp từ mức này = chưa sang trang event mới
TAB_WAITS = 5                  # sau mỗi lần bấm tab: kiểm tra tối đa chừng này lần, mỗi lần chờ 1s
TAB_TAPS = 2                   # số lần bấm tab (bấm lại 1 lần); vẫn chưa sang thì bỏ qua event trong lượt này
# Tab đang chọn có nền xanh sáng hơn: dải ngay dưới chữ tên tab (y 116-120 trên màn 704) sáng ~89-90 (V của HSV), tab thường ~33.
SELECTED_BAND_Y = (16.4, 17.1)   # % màn
SELECTED_HALF_W = 35             # px (màn rộng 396): lấy dải này trong khoảng tâm tab +- chừng này
SELECTED_V = 60                  # độ sáng trung bình từ mức này = tab đang chọn
# % màn: kéo dài hàng tab từ trái sang phải, x 5% -> 1000% (điểm cuối ra ngoài mép phải): đưa hàng tab về đầu
# (500% chưa đủ khi màn mở ở tab cuối).
FIRST_SWIPE = (5, 12, 1000, 12)
EDGE_BACK_SWIPE = (5, 12, 95, 12)   # % màn: swipe_to_left_edge từ cú thứ 2 kéo ngắn trái sang phải
EDGE_SWIPES = 8                  # swipe_to_left_edge: tối đa chừng này cú kéo (cú đầu dài, các cú sau ngắn)
EDGE_ICON = (36, 7.5, 52, 13.5)  # % màn: ô cắt một icon ở hàng tab (icon tab thứ hai) sau mỗi cú kéo
EDGE_SEARCH = (0, 5, 100, 17)    # % màn: vùng tìm lại icon đã cắt sau cú kéo kế tiếp (cả hàng tab)
EDGE_SAME = 0.8                  # icon vẫn thấy (khớp từ mức này) ...
EDGE_SETTLE = 1.0                # giây nghỉ sau mỗi cú kéo, rồi mới chụp để cắt / kiểm tra icon
SHORT_SWIPE = (60, 12, 5, 12)    # % màn: kéo ngắn từ phải sang trái tìm tiếp, xong nghỉ 1s (95 -> 5 dịch ~4 tab một cú: sót tab)
SHORT_SWIPES = 30                # scan_to_right_edge: tối đa chừng này cú kéo ngắn
LEFT_ICON = (8, 7.5, 26, 13.5)   # % màn: ô cắt icon ngoài cùng bên trái trước mỗi cú kéo ngắn (kéo ngắn đẩy nó ra khỏi màn)
# ... VÀ lệch không quá chừng này px (màn rộng 396) mới là chạm biên. Icon tab đều có khung cánh vàng giống nhau nên icon cắt ra hay
# khớp nhầm sang tab bên cạnh (0.6-0.8+); ở biên thật hàng tab đứng yên.
LEFT_SAME_PX = 20                # swipe_to_left_edge: VD x 10 -> 20 vẫn là giới hạn trái
SHORT_SAME_PX = 2                # scan_to_right_edge (kéo ngắn): icon đổi chỗ thì KHÔNG phải giới hạn, phải đứng nguyên chỗ
EDGE_CONFIRM = 2                 # scan_to_right_edge: số cú kéo ngắn liên tiếp không dịch mới là chạm bên phải (cú đầu có thể bị popup chặn)
# Trước mỗi cú kéo: thanh tiêu đề phải khớp gần như tuyệt đối với ảnh cắt lúc vừa vào màn Valuable Event (popup sau khi nhận quà
# phủ lên thì cú kéo không làm hàng tab dịch). So bằng chênh lệch điểm ảnh (1 - chênh lệch TB / 255) để nhạy cả lớp phủ tối:
# dải y 0-6% chụp lúc khác nhau giống 1.0; phủ tối 10% -> 0.978, 30% -> 0.937.
TITLE_REGION = (0, 0, 100, 6)    # % màn: thanh tiêu đề
TITLE_SAME = 0.99
TITLE_WAITS = 5                  # không khớp: chờ 1s, tối đa chừng này lần; vẫn không khớp thì Back
# Dải thông báo chạy chữ đè lên dòng tên tab (y 92-116 trên màn 704) có dấu X đỏ để tắt: sau mỗi cú kéo (dài / ngắn) thấy thì bấm.
# Chỉ nhận dấu X (chữ thông báo mỗi lần mỗi khác): cụm đỏ cỡ NOTICE_X_PX, nét mảnh (tỉ lệ điểm đỏ NOTICE_X_FILL, chấm đỏ thông
# báo thì tròn đặc), điểm đỏ nằm dọc cả hai đường chéo (>= NOTICE_X_DIAG; dấu X thật 0.54 / 0.60, chỗ đỏ khác <= 0.48).
NOTICE_BAND = (13.0, 16.7)       # % màn: dải thông báo
NOTICE_X_PX = (9, 22)            # px (màn rộng 396): cạnh cụm đỏ
NOTICE_X_FILL = (0.15, 0.5)
NOTICE_X_DIAG = 0.5

TASKS = (
    resource_consumption_sprint.TASK, runestone_consumption_sprint.TASK,
    ancient_dynasty_treasury.TASK,
    general_vault.TASK, refining_stone_sprint.TASK, strategic_stockpile.TASK,
    limited_offer.TASK, speedup_sprint.TASK, super_blazon_sale.TASK,
    super_value_weekly_card.TASK,
    successive_purchase_benefits.TASK, optional_package.TASK,
    active_monthly_card.TASK, tomb_expedition.TASK,
    wheel_of_dragon_war.TASK, golden_tree_rewards.TASK,
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
    """Cắt thanh tiêu đề (TITLE_REGION) trên màn Valuable Event vừa vào, làm mốc so trước mỗi cú kéo. Chỉ là biến của lượt tìm
    (search_pass truyền xuống các hàm kéo), không gắn lên bot: hết lượt / sang nhiệm vụ khác là không còn."""
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
    bot.record(f"Gift Claims: thanh tiêu đề Valuable Event chưa khớp sau {TITLE_WAITS} lần chờ; bấm Back")
    bot.back(delay=STEP_DELAY)
    return title_matches(bot.screenshot(), title)


def swipe_to_left_edge(bot, title) -> bool:
    """Kéo hàng tab về giới hạn bên trái, tối đa EDGE_SWIPES cú: cú đầu kéo dài FIRST_SWIPE (5% -> 1000%), từ cú thứ 2 kéo ngắn
    EDGE_BACK_SWIPE (5% -> 95%). Sau mỗi cú nghỉ 1s, cắt một icon (EDGE_ICON); sau cú kế tiếp icon đó vẫn thấy, lệch không quá
    LEFT_SAME_PX = đã tới giới hạn, dừng. Icon mất thì kéo tiếp. True khi thấy đã tới giới hạn."""
    icon = None
    cut_x = 0
    for swipe in range(1, EDGE_SWIPES + 1):
        if not wait_title_clear(bot, title):
            bot.record("Gift Claims: tiêu đề Valuable Event vẫn bị che; dừng kéo về trái")
            return False
        bot.swipe_percent(*(FIRST_SWIPE if swipe == 1 else EDGE_BACK_SWIPE), duration=SLOW_SWIPE_DURATION)
        screen = _settled_screenshot(bot)
        if icon is not None and _at_edge(screen, icon, cut_x, LEFT_SAME_PX):
            bot.record(f"Gift Claims: hàng tab Valuable Event đã tới giới hạn bên trái sau {swipe} cú kéo")
            return True
        icon = _cut(screen, EDGE_ICON)
        cut_x = _box(screen, EDGE_ICON)[0]
    bot.record(f"Gift Claims: kéo hàng tab Valuable Event {EDGE_SWIPES} cú vẫn chưa thấy giới hạn bên trái")
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
    """Mở trang event của tab tại `pos`, rồi bấm chỗ tiêu đề (tap_title). Tab đã được chọn sẵn (tab_selected) thì đang ở đúng
    trang: không bấm tab. Còn lại: trước khi bấm cắt ô PAGE_PROBE (dưới hàng tab, góc trái); bấm tab (x của `pos`, y TAB_TAP_Y),
    sau mỗi 1s kiểm tra ô đó đã
    đổi chưa, tối đa TAB_WAITS lần; chưa đổi thì bấm lại tab một lần và chờ tiếp như vậy (TAB_TAPS lần bấm). True khi đã sang trang
    event (đã bấm chỗ tiêu đề)."""
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


def do_visible(bot, pending: set[str], attempted: set[str]) -> None:
    """Làm các event cần làm (`pending`, chưa thử trong lượt này) đang thấy ở hàng tab: mỗi lần chụp lại, bấm tab bên trái nhất
    (open_tab: chờ sang trang event, không sang thì bỏ qua event trong lượt này) rồi chạy flow riêng của nó; xong thì đánh dấu
    DONE và bỏ khỏi `pending`, chưa xong thì giữ PENDING (không thử lại trong lượt)."""
    while True:
        bot.check()
        screen = bot.screenshot()
        if back_if_close_x(bot, screen):
            screen = bot.screenshot()
        visible = [(spec, pos) for spec in SPECS
                   if spec.task.key in pending and spec.task.key not in attempted
                   and (pos := _tab(bot, spec, screen)) is not None]
        if not visible:
            return
        spec, pos = min(visible, key=lambda item: item[1][0])
        key = spec.task.key
        bot.record(f"Gift Claims: Valuable Event mở {spec.task.label}")
        attempted.add(key)
        if not open_tab(bot, pos):
            bot.record(f"Gift Claims: bấm {spec.task.label} 2 lần vẫn chưa sang trang event; bỏ qua, lượt sau làm tiếp")
            continue
        if process_exact(bot, spec.flow):
            mark_task_done(bot, key)
            pending.discard(key)
        else:
            bot.record(f"Gift Claims: {spec.task.label} chưa đạt điều kiện DONE; giữ PENDING")
        bot.sleep(STEP_DELAY)


def scan_to_right_edge(bot, pending: set[str], attempted: set[str], title) -> bool:
    """Kéo ngắn SHORT_SWIPE (phải sang trái) tối đa SHORT_SWIPES cú, mỗi chỗ làm các event cần làm đang thấy. Trước mỗi cú cắt
    icon ngoài cùng bên trái (LEFT_ICON); kéo xong (nghỉ 1s) icon đó vẫn đứng nguyên chỗ (lệch <= SHORT_SAME_PX; đổi chỗ thì chưa phải)
    = hàng tab không dịch. Phải EDGE_CONFIRM cú liên tiếp không dịch mới là chạm bên phải (cú đầu không dịch có thể do popup sau khi
    nhận quà phủ lên). Trước mỗi cú chờ tiêu đề rõ (wait_title_clear); không rõ thì dừng, lượt không được tính. True khi chạm bên phải."""
    still = 0
    for _ in range(SHORT_SWIPES):
        do_visible(bot, pending, attempted)
        if not wait_title_clear(bot, title):
            bot.record("Gift Claims: tiêu đề Valuable Event vẫn bị che; dừng lượt này (không tính lượt)")
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
        score, x = _find_icon(after, icon)
        if still < EDGE_CONFIRM:
            bot.record(f"Gift Claims: hàng tab Valuable Event không dịch (icon khớp {score:.2f}, lệch {x - cut_x} px); "
                       "kéo thêm một cú để kiểm tra")
            continue
        bot.record(f"Gift Claims: hàng tab Valuable Event đã chạm bên phải ({EDGE_CONFIRM} cú liên tiếp không dịch)")
        do_visible(bot, pending, attempted)
        return True
    bot.record(f"Gift Claims: kéo ngắn {SHORT_SWIPES} cú vẫn chưa chạm bên phải hàng tab Valuable Event")
    return False


def open_valuable_event(bot) -> bool:
    """Từ màn chính (có nút •••; đang ở bản đồ thế giới thì to_city vào thành trước) tìm nút Valuable Event bằng find_valuable_event (mẫu chữ "Event" rồi OCR), bấm, chờ màn
    Valuable Event (tiêu đề ValuableEvent/title) tối đa OPEN_WAITS lần x 1s. Chưa vào thì về màn chính làm lại, tối đa
    OPEN_ATTEMPTS lần; vẫn không vào thì trả False (DB chưa xong: worker gọi lại lần sau)."""
    for attempt in range(1, OPEN_ATTEMPTS + 1):
        bot.check()
        screen = bot.screenshot()
        if not on_main(bot, screen):
            return_home(bot)
        if to_city(bot):      # hoạt động này phải làm trong thành: đang ở bản đồ thế giới thì bấm nút toà thành
            bot.record("Gift Claims: đang ở bản đồ thế giới; đã chuyển vào thành")
        screen = bot.screenshot()
        pos = find_valuable_event(screen) if on_main(bot, screen) else None
        if pos is None:
            bot.record(f"Gift Claims: không thấy nút Valuable Event ở màn chính (lần {attempt}/{OPEN_ATTEMPTS})")
            continue
        above = round(ICON_ABOVE * screen.shape[1] / REFERENCE_WIDTH)
        bot.record(f"Gift Claims: bấm nút Valuable Event tại {pos} (lần {attempt}/{OPEN_ATTEMPTS})")
        bot.tap(pos[0], max(0, pos[1] - above))
        for _ in range(OPEN_WAITS):
            bot.sleep(1)
            if identify(bot, bot.screenshot()) == GiftScreen.VALUABLE_EVENT:
                bot.record("Gift Claims: đã vào Valuable Event")
                return True
        bot.record(f"Gift Claims: bấm rồi mà chưa vào màn Valuable Event sau {OPEN_WAITS}s "
                   f"(lần {attempt}/{OPEN_ATTEMPTS})")
    bot.record(f"Gift Claims: {OPEN_ATTEMPTS} lần không vào được Valuable Event; lần sau làm tiếp")
    return False


def search_pass(bot, pending: set[str], attempted: set[str]) -> bool:
    """Một lượt tìm (bước 1-4 ở đầu file); `attempted` (rỗng khi gọi) nhận các event đã thấy và bấm vào trong lượt. True khi đã đi
    hết hàng tab (chạm bên phải) hoặc mọi event cần làm đã xong."""
    if not open_valuable_event(bot):
        return False
    title = capture_title(bot)
    do_visible(bot, pending, attempted)
    if not pending:
        return True
    bot.record("Gift Claims: kéo dài hàng tab Valuable Event về giới hạn bên trái")
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
    """Event đã thấy ở các lượt trước hôm nay. Để trên context của bot, không ghi DB: còn qua các lần bị ngắt (Join Boss, hết 120s...)
    trong lần Start này; Start lại hoặc qua mốc reset server thì làm lại từ rỗng."""
    server_time = getattr(bot, "server_time", None)
    value = server_time() if callable(server_time) else ""
    day = last_reset(value if isinstance(value, str) else "")
    stored = getattr(bot, SEEN_ATTR, None)
    if not (isinstance(stored, tuple) and stored[0] == day):
        stored = (day, set())
        setattr(bot, SEEN_ATTR, stored)
    return stored[1]


def run(bot) -> bool:
    """Xong event nào lưu DB event đó; đủ lượt thì lưu key tổng KEY. Worker (``gift_claims.job``) chỉ đọc KEY trong DB: chưa có
    thì gọi lại, bị ngắt giữa chừng (hết 120s, boss...) thì lần sau chạy lại từ đầu và bỏ qua các event đã xong.
    Chạy hoạt động Valuable Event; True khi mọi nhiệm vụ của nó đã xong hôm nay. Lượt nào thấy event MỚI (chưa thấy ở các lượt
    trước hôm nay, seen_today) thì đếm lại: lượt đó tính là lượt 1. Event lượt nào cũng thấy mà chưa DONE không reset lại nữa, để
    không lặp mãi."""
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
        bot.record(f"Gift Claims: Valuable Event xong lượt tìm {number}/{PASSES} hôm nay")
        bot.back(delay=STEP_DELAY)
    for task in TASKS:
        mark_task_done(bot, task.key)
    bot.mark_daily_done(KEY)
    bot.record(f"Gift Claims: Valuable Event đủ {PASSES} lượt tìm; mọi event của hoạt động xong hôm nay")
    return_home(bot)
    return True
