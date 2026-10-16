"""
run.py — activity "Recruit General": `run(bot, settings)` (chưa có cấu hình riêng).

1. Về màn thành sạch (nút "•••").
2. Máy chưa có route công trình trong DB (bot.city_map) -> đi tìm đầy đủ 13 ô công trình (city_map.scan_city) và lưu vào DB.
3. Tavern đang trên màn thì kéo vào giữa; không thì đi theo route trong DB (goto); không được thì đường đã đo sẵn (find_keep rồi
   ROUTES[("keep", "tavern")]).
4. Bấm Tavern -> menu tròn -> icon "Recruit" -> màn Recruit General.
5. Đã mở ít hơn MIN_GENERALS (5) tướng (3/6, 4/6): level Tavern quá thấp để roll tướng xịn -> ghi log rồi dừng.
   Ô cảnh báo: "Historic General" chưa tích thì tích; "Epic (Orange) General" đang tích thì bỏ tích.
6. Bấm Refresh liên tục (mỗi lần chờ 0,3 giây). Hiện popup "Your Tavern has a high quality General..." -> bấm Cancel -> tướng đang hiện phải có
   vương miện (không xét màu chấm), không thì Refresh tiếp -> kiểm tra tên tướng (GENERALS_DIR), rồi kéo ảnh tướng sang trái / phải tới
   các tướng tím / vàng khác kiểm tra tên (_handle_generals); cần mua thì mua rồi kéo tiếp, xong Refresh tiếp; mua đủ BUY_LIMIT (3) tướng thì dừng: có trong danh sách cần mua -> luồng mua (CHƯA làm, chỉ ghi log); không -> Refresh tiếp. Cũng dừng khi
   rời màn Recruit General, mất nút Refresh hoặc đủ REFRESH_MAX lần.
Trả True khi tới màn Recruit General và hai ô đúng trạng thái, False khi không tới được / không đổi được ô.
"""
import cv2
import numpy as np

from ...context.templates import TEMPLATE_DIR
from ...city.city_map import BUILDING_THRESHOLD, centre, city_screen, find_keep, goto, locate, scan_city, swipe
from ..daily_activities.constants import MAIN_MORE
from ..event.city_building import TAVERN
from .constants import (
    BOX_CHECKED,
    CANCEL,
    CANCEL_WAIT,
    CROWNS,
    CROWN_COLOR_DX,
    CROWN_COLOR_Y,
    CROWN_HUE,
    CROWN_MIN_SATURATION,
    CROWN_MIN_VALUE,
    CROWN_MIN_PIXELS,
    CROWN_REGION_DX,
    CROWN_THRESHOLD,
    CROWN_Y,
    BUY_KEY,
    BUY_LIMIT,
    BUY_RECRUIT,
    BUY_TOKEN,
    DETAIL_BUY_TOKEN,
    DETAIL_RECRUIT,
    DETAIL_THRESHOLD,
    DETAIL_WAIT,
    DOT_HUES,
    EMBLEM,
    EMBLEM_REGION,
    EMBLEM_THRESHOLD,
    EMBLEM_WAIT,
    DOT_MIN_SATURATION,
    DOT_MIN_VALUE,
    DOT_CENTER_X_PCT,
    DOT_EDGE_DIFF,
    DOT_EDGE_PX,
    DOT_MAX,
    DOT_WHITE_MAX_SATURATION,
    DOT_MIN,
    DOT_SPACING_PCT,
    DOT_Y_PCT,
    BOX_TAPS,
    BOX_WAIT,
    EPIC_BOX,
    EPIC_REGION,
    HIGH_QUALITY_POPUP,
    MIN_GENERALS,
    GENERAL_ART,
    GENERALS_DIR,
    HISTORIC_BOX,
    LIST_RELOAD_WAIT,
    LIST_WAIT,
    HISTORIC_REGION,
    HOME_BACKS,
    MENU_RECRUIT,
    MENU_TRIES,
    MENU_WAIT,
    NAME,
    NAME_REGION,
    NAME_THRESHOLD,
    REFRESH,
    REFRESH_MAX,
    REFRESH_WAIT,
    SCREEN_WAIT,
    SHOWN_MIN_POINTS,
    SHOWN_RING,
    SWIPE_CHANGE_WAIT,
    SWIPE_LEFT,
    SWIPE_RIGHT,
    SWITCH_MAX,
    THRESHOLD,
    TITLE,
)


def run(bot, settings: dict) -> bool:
    if bot.find(TITLE, threshold=THRESHOLD) is not None:   # đã ở màn Recruit General: chỉ chỉnh hai ô
        return _enough_generals(bot) and _set_warnings(bot) and _refresh(bot, settings)
    if not _to_city(bot):
        bot.record(f"{NAME}: not at the city screen")
        return False
    if not getattr(bot, "city_map", None):   # chưa có route trong DB: đi tìm đầy đủ 13 ô công trình rồi lưu (bot.set_city_map)
        bot.record(f"{NAME}: no city route in DB, scanning all the buildings")
        if not scan_city(bot, NAME):
            bot.record(f"{NAME}: route scan failed")
            return False
    tavern = _tavern(bot)
    if tavern is None:
        return False
    return _open_recruit(bot, tavern) and _enough_generals(bot) and _set_warnings(bot) and _refresh(bot, settings)


def _enough_generals(bot) -> bool:
    """Số tướng đã mở (số chấm, 3..6) phải >= MIN_GENERALS. Ít hơn (3/6, 4/6): level Tavern quá thấp, không thể roll ra tướng xịn
    -> ghi log rồi trả False (dừng activity, bot dừng). Không đọc được chấm nào thì cứ đi tiếp."""
    count = len(dot_xs(bot.screenshot()))
    if 0 < count < MIN_GENERALS:
        bot.record(f"{NAME}: only {count}/6 Generals unlocked, Tavern level too low to roll a high quality General, stop")
        return False
    return True


def _to_city(bot) -> bool:
    """Back tới khi thấy màn thành sạch (nút "•••")."""
    for _ in range(HOME_BACKS):
        if bot.find(MAIN_MORE) is not None:
            return True
        bot.back(delay=1)
    return bot.find(MAIN_MORE) is not None


def _tavern(bot):
    """Đưa Tavern vào giữa màn, trả vị trí (None + ghi log nếu không được):
    1. Tavern đang trên màn -> kéo vào giữa.
    2. Route trong DB (bot.city_map, city_map.goto): đi từ công trình đã biết đang thấy trên màn tới Tavern.
    3. Không được thì đi theo các đường ĐÃ ĐO sẵn của civ (city_tour.py ROUTES): `find_keep` về Thành chính rồi
       ROUTES[("keep", "tavern")] và kéo Tavern vào giữa."""
    score, pos = locate(bot, city_screen(bot), TAVERN)
    if pos is not None and score >= BUILDING_THRESHOLD:
        return centre(bot, TAVERN, pos)[0]
    city_map = dict(getattr(bot, "city_map", None) or {})
    if TAVERN in city_map:
        pos = goto(bot, NAME, TAVERN, city_map)
        if pos is not None:
            return pos
        bot.log(f"{NAME}: cannot reach the Tavern with the city route, use the fixed routes")
    tour = find_keep(bot, NAME)
    if tour is None:
        bot.record(f"{NAME}: cannot find the Keep (or this civilization has no measured route data)")
        return None
    route = tour.ROUTES.get(("keep", "tavern"))
    if route is None:
        bot.record(f"{NAME}: no measured route from the Keep to the Tavern for this civilization")
        return None
    bot.log(f"{NAME}: Keep -> Tavern by the fixed route: {len(route)} swipe(s)")
    for finger in route:
        swipe(bot, finger)
    score, pos = locate(bot, city_screen(bot), TAVERN)
    if pos is None or score < BUILDING_THRESHOLD:
        bot.record(f"{NAME}: Tavern not seen after the fixed route")
        return None
    return centre(bot, TAVERN, pos)[0]


def _open_recruit(bot, tavern) -> bool:
    """Bấm Tavern -> chờ menu tròn -> bấm icon Recruit -> chờ màn Recruit General."""
    for _ in range(MENU_TRIES):
        bot.tap(*tavern)
        icon = bot.wait_for(MENU_RECRUIT, timeout=MENU_WAIT, threshold=THRESHOLD, interval=1)
        if icon is not None:
            break
    else:
        bot.record(f"{NAME}: Recruit icon not shown after tapping the Tavern")
        return False
    bot.tap(*icon)
    if bot.wait_for(TITLE, timeout=SCREEN_WAIT, threshold=THRESHOLD, interval=1) is None:
        bot.record(f"{NAME}: Recruit General screen not shown")
        return False
    bot.record(f"{NAME}: Recruit General screen opened")
    return True


def _is_checked(bot, region) -> bool:
    """Ô đã tích: thấy dấu tích xanh trong vùng của ô."""
    return bot.find(BOX_CHECKED, threshold=THRESHOLD, region=region) is not None


def _set_box(bot, label: str, region, centre, want: bool) -> bool:
    """Đưa ô về trạng thái `want` (True = tích): đã đúng thì không bấm; không thì bấm rồi chờ đổi, tối đa BOX_TAPS lần."""
    for _ in range(BOX_TAPS):
        if _is_checked(bot, region) == want:
            bot.log(f"{NAME}: {label} is {'checked' if want else 'unchecked'}")
            return True
        bot.tap_percent(*centre, delay=0)
        for _ in range(BOX_WAIT):
            bot.sleep(1)
            if _is_checked(bot, region) == want:
                break
    ok = _is_checked(bot, region) == want
    if ok:
        bot.record(f"{NAME}: {label} {'checked' if want else 'unchecked'}")
    else:
        bot.record(f"{NAME}: cannot set {label}")
    return ok


def _set_warnings(bot) -> bool:
    """Historic General phải tích, Epic (Orange) General phải bỏ tích."""
    historic = _set_box(bot, "Historic General", HISTORIC_REGION, HISTORIC_BOX, True)
    epic = _set_box(bot, "Epic General", EPIC_REGION, EPIC_BOX, False)
    return historic and epic


def _refresh(bot, settings: dict) -> bool:
    """Bấm Refresh liên tục, mỗi lần chờ REFRESH_WAIT giây. Hiện popup tướng xịn thì bấm Cancel, kiểm tra / mua tướng (`_handle_generals`) rồi Refresh tiếp. Cũng dừng khi không còn ở màn Recruit General, không thấy nút Refresh, hoặc đủ REFRESH_MAX lần. True (đã bấm ít nhất một lần hoặc dừng vì màn đổi)."""
    bought = 0   # số tướng đã mua trong lượt chạy này
    for count in range(REFRESH_MAX):
        screen = bot.screenshot()
        if bot.find(HIGH_QUALITY_POPUP, screen=screen, threshold=THRESHOLD) is not None:   # xét trước: tiêu đề / Refresh vẫn khớp dưới popup
            cancel = bot.find(CANCEL, screen=screen, threshold=THRESHOLD)
            if cancel is not None:
                bot.tap(*cancel, delay=CANCEL_WAIT)
            bot.record(f"{NAME}: high quality General after {count} refresh(es), cancelled")
            bought_now = _handle_generals(bot, settings)
            if bought_now:
                bought += bought_now
                bot.record(f"{NAME}: bought {bought}/{BUY_LIMIT} General(s) so far")
                if bought >= BUY_LIMIT:
                    bot.record(f"{NAME}: bought {bought} General(s), stop")
                    return True
                if not _set_warnings(bot):   # mua xong game có thể bỏ tích hai ô: tích lại Historic
                    return False
            continue   # xong lượt kiểm tra: Refresh tiếp
        if bot.find(TITLE, screen=screen, threshold=THRESHOLD) is None:
            bot.record(f"{NAME}: left the Recruit General screen after {count} refresh(es), stop")
            return True
        button = bot.find(REFRESH, screen=screen, threshold=THRESHOLD)
        if button is None:
            bot.record(f"{NAME}: Refresh button not found after {count} refresh(es), stop")
            return False
        # Thực hiện bấm Refresh cho đến khi ra tướng lịch sử (popup high quality General -> Cancel, dừng ở trên).
        bot.tap(*button, delay=REFRESH_WAIT)
    bot.record(f"{NAME}: {REFRESH_MAX} refreshes done")
    return True


def _wanted_general(bot) -> str | None:
    """Tên tướng đang hiện nếu nằm trong danh sách cần mua (ảnh tên trong GENERALS_DIR, tên file = tên tướng), không thì None."""
    screen = bot.screenshot()
    for path in sorted((TEMPLATE_DIR / GENERALS_DIR).glob("*.png")):
        if bot.find(f"{GENERALS_DIR}/{path.name}", screen=screen, threshold=NAME_THRESHOLD, region=NAME_REGION) is not None:
            return path.stem
    bot.log(f"{NAME}: General not in the wanted list, keep refreshing")
    return None


def _buy(bot, name: str, buy_with: str = BUY_RECRUIT) -> bool:
    """Mua tướng `name` đang hiện: bấm vào ảnh tướng -> chờ màn chi tiết (1 giây / lần tối đa DETAIL_WAIT giây, mất nút Refresh = đã ra) -> bấm nút mua: màn chỉ có MỘT nút (Recruit General ở
    giữa) thì bấm thẳng nút đó; có hai nút thì bấm theo setting `buy_with` (Recruit General / Buy General Token). Bấm nút xong chờ về màn danh sách tướng (`_wait_list`, tối đa LIST_WAIT giây, quá hạn thì Back). Popup / màn kết quả giữa chừng CHƯA có ảnh. True nếu đã bấm nút."""
    bot.record(f"{NAME}: wanted General {name} is in the Tavern, open its detail")
    bot.tap_percent(*GENERAL_ART)
    for _ in range(DETAIL_WAIT):   # chờ 1 giây rồi xét; mất nút Refresh của Tavern = đã ra màn chi tiết, còn thì chờ thêm 1 giây
        bot.sleep(1)
        screen = bot.screenshot()
        if bot.find(REFRESH, screen=screen, threshold=THRESHOLD) is None:
            break
    else:
        bot.record(f"{NAME}: General detail screen not shown after {DETAIL_WAIT}s (Refresh button still there)")
        return False
    recruit = bot.find(DETAIL_RECRUIT, screen=screen, threshold=DETAIL_THRESHOLD)
    token = bot.find(DETAIL_BUY_TOKEN, screen=screen, threshold=DETAIL_THRESHOLD)
    if token is None:   # chỉ một nút: bấm thẳng
        button, label = recruit, BUY_RECRUIT
        bot.log(f"{NAME}: only the Recruit General button on this General")
    elif buy_with == BUY_TOKEN:
        button, label = token, BUY_TOKEN
    else:
        button, label = recruit, BUY_RECRUIT
    if button is None:
        bot.record(f"{NAME}: {label} button not found on the detail screen")
        return False
    bot.tap(*button)
    bot.record(f"{NAME}: tapped {label} for {name}")
    _wait_list(bot)
    return True


def _wait_list(bot) -> bool:
    """Sau khi bấm nút mua: chờ 1 giây, thấy nút Refresh của Tavern = đã về màn danh sách tướng; chưa thì chờ thêm 1 giây / lần tới
    tối đa LIST_WAIT giây; vẫn chưa về thì bấm Back. Về được (tự về hoặc sau Back) thì chờ thêm LIST_RELOAD_WAIT giây rồi mới làm tiếp.
    True nếu tự về."""
    back = False
    for _ in range(LIST_WAIT):
        bot.sleep(1)
        if bot.find(REFRESH, screen=bot.screenshot(), threshold=THRESHOLD) is not None:
            back = True
            break
    if not back:
        bot.record(f"{NAME}: not back at the General list after {LIST_WAIT}s, Back")
        bot.back(delay=1)
    bot.sleep(LIST_RELOAD_WAIT)   # chờ 2s để đợi game load lại dữ liệu
    return back


def _dot_color(hsv, x: int, y: int) -> str:
    """Màu chấm tại (x, y): "white" / "green" / "blue" / "purple" / "gold", hoặc "?" nếu không rõ (trung vị HSV 3x3 px)."""
    hue, saturation, value = (int(v) for v in np.median(hsv[y - 1:y + 2, x - 1:x + 2].reshape(-1, 3), axis=0))
    if value < DOT_MIN_VALUE:
        return "?"
    if saturation < DOT_WHITE_MAX_SATURATION:
        return "white"
    if saturation < DOT_MIN_SATURATION:   # bão hoà lưng chừng: nền (gỗ, bóng giày), không phải chấm
        return "?"
    return next((name for name, (low, high) in DOT_HUES.items() if low <= hue <= high), "?")


def dot_xs(screen) -> list[int]:
    """Toạ độ x (px) các chấm tướng, từ trái sang phải. Số chấm (DOT_MIN..DOT_MAX) = n lớn nhất mà mọi vị trí của bố cục n chấm căn giữa
    đều là chấm (xem constants: màu ở tâm đọc được và hai bên khác màu tâm). [] nếu không thấy chấm nào."""
    height, width = screen.shape[:2]
    y = round(height * DOT_Y_PCT / 100)
    hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
    for n in range(DOT_MAX, DOT_MIN - 1, -1):
        xs = [round(width * (DOT_CENTER_X_PCT + (i - (n - 1) / 2) * DOT_SPACING_PCT) / 100) for i in range(n)]
        if all(_is_dot(screen, hsv, x, y) for x in xs):
            return xs
    return []


def _is_dot(screen, hsv, x: int, y: int) -> bool:
    """Vị trí (x, y) là một chấm: màu tâm đọc được và một trong hai điểm cách DOT_EDGE_PX hai bên khác màu tâm (nền đồng màu như giày đen thì không)."""
    if _dot_color(hsv, x, y) == "?":
        return False
    center = screen[y - 1:y + 2, x - 1:x + 2].reshape(-1, 3).mean(axis=0)
    diffs = [float(np.abs(center - screen[y - 1:y + 2, side - 1:side + 2].reshape(-1, 3).mean(axis=0)).sum())
             for side in (x - DOT_EDGE_PX, x + DOT_EDGE_PX)]
    return max(diffs) >= DOT_EDGE_DIFF   # một bên khác rõ là đủ (bên kia có thể là chấm bên cạnh, hay viền vàng)


def dot_colors(screen) -> list[str]:
    """Màu các chấm tướng (3..6 chấm), từ trái sang phải: "white" / "green" / "blue" / "purple" / "gold" (hoặc "?" nếu không rõ)."""
    height = screen.shape[0]
    y = round(height * DOT_Y_PCT / 100)
    hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
    return [_dot_color(hsv, x, y) for x in dot_xs(screen)]


def crowned_slots(bot, screen) -> list[int]:
    """Số thứ tự (0..) các chấm có vương miện (tướng xịn, có thể 2 tướng cùng lúc), không xét màu chấm. Vương miện: đếm điểm cam vàng đậm phía trên chấm (CROWN_MIN_PIXELS) HOẶC tìm ảnh CROWNS
    trong vùng quanh từng chấm (3..6 chấm)."""
    height, width = screen.shape[:2]
    hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
    slots = []
    for slot, x in enumerate(dot_xs(screen)):
        strip = hsv[CROWN_COLOR_Y[0]:CROWN_COLOR_Y[1], x - CROWN_COLOR_DX:x + CROWN_COLOR_DX + 1]
        yellow = int(((strip[..., 0] >= CROWN_HUE[0]) & (strip[..., 0] <= CROWN_HUE[1])
                      & (strip[..., 1] > CROWN_MIN_SATURATION) & (strip[..., 2] > CROWN_MIN_VALUE)).sum())
        region = (max(0, (x - CROWN_REGION_DX) / width * 100), CROWN_Y[0] / height * 100,
                  min(100, (x + CROWN_REGION_DX) / width * 100), CROWN_Y[1] / height * 100)
        if yellow >= CROWN_MIN_PIXELS or any(
                bot.find(path, screen=screen, threshold=CROWN_THRESHOLD, region=region) is not None for path in CROWNS):
            slots.append(slot)
    return slots


def shown_slot(screen) -> int | None:
    """Số thứ tự (0..) chấm của tướng ĐANG HIỆN: chấm có viền vàng sáng quanh (nhiều điểm vàng nhất trên nửa dưới vòng SHOWN_RING,
    tối thiểu SHOWN_MIN_POINTS). None nếu không thấy."""
    height = screen.shape[0]
    y = round(height * DOT_Y_PCT / 100)
    hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
    counts = []
    for x in dot_xs(screen):
        count = 0
        for dx, dy in SHOWN_RING:
            hue, saturation, value = (int(v) for v in hsv[y + dy, x + dx])
            if 15 <= hue <= 35 and saturation > 150 and value > 40:
                count += 1
        counts.append(count)
    if not counts:
        return None
    best = max(counts)
    return counts.index(best) if best >= SHOWN_MIN_POINTS else None


def _handle_generals(bot, settings: dict) -> int:
    """Sau Cancel: các tướng xịn = chấm có vương miện (có thể 2 tướng, hiếm). Không có tướng nào có vương miện thì thôi (0). Kiểm tra
    tên tướng đang hiện (nếu có vương miện) rồi kéo sang từng tướng có vương miện còn lại (gần trước); tướng nào tên nằm trong danh sách
    cần mua thì mua (`_buy`, xong game về màn danh sách, chữ "Recruited"), rồi kéo tiếp sang tướng kế. Trả số tướng đã mua."""
    screen = bot.screenshot()
    crowned = crowned_slots(bot, screen)
    if not crowned:
        bot.log(f"{NAME}: no crown on any General, keep refreshing")
        return 0
    colors = dot_colors(screen)
    current = shown_slot(screen)
    bot.record(f"{NAME}: crowned General slot(s) (1 = leftmost): {[f'{i + 1} {colors[i]}' for i in crowned]}, shown: "
               f"{current + 1 if current is not None else '?'}")
    here = current if current is not None else crowned[0]
    order = sorted(crowned, key=lambda i: (i != here, abs(i - here)))   # tướng đang hiện trước (nếu có vương miện), rồi gần trước
    bought = 0
    for slot in order:
        if slot != shown_slot(bot.screenshot()) and not _goto_slot(bot, slot):
            bot.log(f"{NAME}: cannot reach General slot {slot + 1}")
            continue
        name = _wanted_general(bot)
        if name is not None and _buy(bot, name, settings.get(BUY_KEY) or BUY_RECRUIT):
            bought += 1   # mua xong: tướng vẫn đang hiện (chữ "Recruited"), kéo tiếp sang tướng kế
    return bought


def _goto_slot(bot, target: int) -> bool:
    """Kéo ảnh tướng sang trái / phải tới khi tướng ĐANG HIỆN (viền vàng) là chấm `target`. Hướng đầu: đích bên phải thì kéo sang trái
    (tướng bên phải), bên trái thì kéo sang phải; sau một lần kéo mà tướng đang hiện xa chấm đích hơn thì đổi hướng. Mỗi lần kéo xong
    chờ chấm đang hiện đổi (`_swipe_until_changed`), hết giờ thì lần lặp sau kéo lại. Tối đa SWITCH_MAX lần kéo."""
    swipe, previous = None, None
    for _ in range(SWITCH_MAX):
        current = shown_slot(bot.screenshot())
        if current == target:
            _wait_emblem(bot)
            return True
        if current is not None:
            distance = abs(current - target)
            if swipe is None:
                swipe = SWIPE_LEFT if target > current else SWIPE_RIGHT
            elif previous is not None and distance > previous:
                swipe = SWIPE_RIGHT if swipe == SWIPE_LEFT else SWIPE_LEFT
            previous = distance
        _swipe_until_changed(bot, swipe or SWIPE_LEFT)
    return shown_slot(bot.screenshot()) == target


def _swipe_until_changed(bot, swipe) -> bool:
    """Kéo rồi chờ tướng đang hiện (viền vàng quanh chấm, `shown_slot`) sang chấm khác: kiểm tra 1 giây / lần tối đa SWIPE_CHANGE_WAIT giây.
    Chỉ cần chấm đang hiện đổi vị trí là đủ, không kiểm tra ảnh tướng (hai tướng giống nhau thì ảnh không đổi). Không đọc được chấm đang hiện
    trước khi kéo thì chờ 1 giây rồi coi là xong (người gọi đọc lại). True nếu đã đổi; False nếu hết giờ (người gọi đọc lại và kéo lại)."""
    before = shown_slot(bot.screenshot())
    bot.swipe_percent(*swipe)
    if before is None:
        bot.sleep(1)
        return True
    for _ in range(SWIPE_CHANGE_WAIT):
        bot.sleep(1)
        after = shown_slot(bot.screenshot())
        if after is not None and after != before:
            return True
    bot.log(f"{NAME}: shown General dot unchanged {SWIPE_CHANGE_WAIT}s after the swipe")
    return False


def _wait_emblem(bot) -> bool:
    """Tới tướng đích: chờ huy hiệu của tướng xịn hiện bên trái tên (tối đa EMBLEM_WAIT giây, 1 giây / lần). Không thấy thì ghi log và
    vẫn đi tiếp (kiểm tra tên)."""
    for _ in range(EMBLEM_WAIT):
        if bot.find(EMBLEM, threshold=EMBLEM_THRESHOLD, region=EMBLEM_REGION) is not None:
            return True
        bot.sleep(1)
    bot.log(f"{NAME}: emblem not shown next to the General name")
    return False
