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
   vương miện (không xét màu chấm), không thì Refresh tiếp -> kiểm tra tên tướng (OCR, so với tướng đã tích ở UI), rồi kéo ảnh tướng sang trái / phải tới
   các tướng tím / vàng khác kiểm tra tên (_handle_generals); cần mua thì mua rồi kéo tiếp, xong Refresh tiếp; mua đủ BUY_LIMIT (3) tướng thì dừng: có trong danh sách cần mua -> luồng mua (CHƯA làm, chỉ ghi log); không -> Refresh tiếp. Cũng dừng khi
   rời màn Recruit General, mất nút Refresh hoặc đủ REFRESH_MAX lần.
Trả True khi tới màn Recruit General và hai ô đúng trạng thái, False khi không tới được / không đổi được ô.
"""
import itertools
import os
import re
import time
from pathlib import Path

import cv2
import numpy as np

from ...context.templates import TEMPLATE_DIR
from ...city.city_map import BUILDING_THRESHOLD, centre, city_screen, find_keep, goto, locate, scan_city, swipe
from ..daily_activities.constants import MAIN_MORE
from ..event.city_building import TAVERN
from ...ocr import read_general_name
from ...ocr.read_general_name import similarity
from .constants import (
    BOX_CHECKED,
    CANCEL,
    CANCEL_WAIT,
    CONFIRM,
    CONFIRM_WAIT,
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
    GENERALS_FULL,
    GOLD_MAX_USES,
    GOLD_LIST_MIN_DIFF,
    HOW_TO_GET_TITLE,
    HOW_TO_GET_WAIT,
    LIST_USE,
    LIST_USE_REGION,
    LIST_USE_THRESHOLD,
    OPEN_GOLD_KEY,
    MAX_TAPS,
    POPUP_MAX,
    GOLD_STEP_DELAY,
    POPUP_MINIMUM,
    POPUP_OPEN_WAIT,
    POPUP_USE,
    POPUP_WAIT,
    USE_LOAD_WAIT,
    BUY_COUNT_KEY,
    BUY_LIMIT,
    BUY_RECRUIT,
    BUY_TOKEN,
    DETAIL_BUY_TOKEN,
    DETAIL_RECRUIT,
    DETAIL_THRESHOLD,
    DETAIL_BACK_WAIT,
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
    GENERALS_KEY,
    HISTORIC_BOX,
    LIST_RELOAD_WAIT,
    LIST_WAIT,
    HISTORIC_REGION,
    HOME_BACKS,
    MENU_RECRUIT,
    MENU_TRIES,
    MENU_WAIT,
    NAME,
    NAME_MATCH,
    NAME_STRIP,
    REFRESH,
    REFRESH_KEY,
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
        bot.back(delay=1)  # delay cố định, không cần sửa
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
        bot.tap_percent(*centre, delay=0)  # delay cố định, không cần sửa
        for _ in range(BOX_WAIT):
            bot.sleep(1)  # delay cố định, không cần sửa
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


def _limit(value, default: int) -> int | None:
    """Số lần tối đa từ setting của tab: số nguyên dương; "ALL" = không giới hạn (None); thiếu / không hợp lệ (settings cũ) = `default`."""
    if value == "ALL":
        return None
    return value if isinstance(value, int) and not isinstance(value, bool) and value > 0 else default


def _refresh(bot, settings: dict) -> bool:
    """Bấm Refresh liên tục, mỗi lần chờ REFRESH_WAIT giây. Hiện popup tướng xịn thì bấm Cancel, kiểm tra / mua tướng (`_handle_generals`) rồi Refresh tiếp. Cũng dừng khi không còn ở màn Recruit General, không thấy nút Refresh, hoặc đủ số lần Refresh của tab (setting `refresh_count`, ALL = không giới hạn; mặc định REFRESH_MAX). Dừng khi mua đủ `buy_count` tướng (ALL = không giới hạn; mặc định BUY_LIMIT). True (đã bấm ít nhất một lần hoặc dừng vì màn đổi)."""
    bought = 0   # số tướng đã mua trong lượt chạy này
    refresh_limit, buy_limit = _limit(settings.get(REFRESH_KEY), REFRESH_MAX), _limit(settings.get(BUY_COUNT_KEY), BUY_LIMIT)
    for count in (itertools.count() if refresh_limit is None else range(refresh_limit)):
        screen = bot.screenshot()
        if bot.find(HIGH_QUALITY_POPUP, screen=screen, threshold=THRESHOLD) is not None:   # xét trước: tiêu đề / Refresh vẫn khớp dưới popup
            cancel = bot.find(CANCEL, screen=screen, threshold=THRESHOLD)
            if cancel is not None:
                bot.tap(*cancel, delay=CANCEL_WAIT)  # delay cố định, không cần sửa
            bot.record(f"{NAME}: high quality General after {count} refresh(es), cancelled")
            try:
                bought_now = _handle_generals(bot, settings)
            except NotEnoughGold as error:
                bot.record(f"{NAME}: not enough gold to recruit {error}, stop")
                return False
            except GeneralsFull:
                return False   # đã ghi log ở `_how_to_get_shown`
            if bought_now:
                bought += bought_now
                bot.record(f"{NAME}: bought {bought}/{buy_limit or 'ALL'} General(s) so far")
                if buy_limit is not None and bought >= buy_limit:
                    bot.record(f"{NAME}: bought {bought} General(s), stop")
                    return True
                if not _set_warnings(bot):   # mua xong game có thể bỏ tích hai ô: tích lại Historic
                    return False
            if not _refresh_confirm(bot):   # đã kiểm tra hết tướng xịn: Refresh tiếp, popup hiện lại thì bấm Confirm
                return False
            continue
        if bot.find(TITLE, screen=screen, threshold=THRESHOLD) is None:
            bot.record(f"{NAME}: left the Recruit General screen after {count} refresh(es), stop")
            return True
        button = bot.find(REFRESH, screen=screen, threshold=THRESHOLD)
        if button is None:
            bot.record(f"{NAME}: Refresh button not found after {count} refresh(es), stop")
            return False
        # Thực hiện bấm Refresh cho đến khi ra tướng lịch sử (popup high quality General -> Cancel, dừng ở trên).
        bot.tap(*button, delay=REFRESH_WAIT)  # delay cố định, không cần sửa
    bot.record(f"{NAME}: {refresh_limit} refreshes done")
    return True


def _refresh_confirm(bot) -> bool:
    """Các tướng xịn đã kiểm tra xong (không mua / đã mua): bấm Refresh, popup "high quality General" hiện lại thì bấm Confirm (chờ tối đa
    CONFIRM_WAIT giây, 1 giây / lần). False nếu không thấy nút Refresh."""
    button = bot.find(REFRESH, threshold=THRESHOLD)
    if button is None:
        bot.record(f"{NAME}: Refresh button not found to refresh after checking the Generals, stop")
        return False
    bot.tap(*button, delay=1)  # delay cố định, không cần sửa
    for _ in range(CONFIRM_WAIT):
        screen = bot.screenshot()
        if bot.find(HIGH_QUALITY_POPUP, screen=screen, threshold=THRESHOLD) is not None:
            confirm = bot.find(CONFIRM, screen=screen, threshold=THRESHOLD)
            if confirm is not None:
                bot.tap(*confirm, delay=REFRESH_WAIT)  # delay cố định, không cần sửa
                bot.log(f"{NAME}: Generals checked, Confirm the refresh")
                return True
        bot.sleep(1)  # delay cố định, không cần sửa
    return True   # không có popup (VD refresh miễn phí): đã refresh


LOGS_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "EvonyBot" / "logs" / "generals"
_logged: set = set()    # tên OCR đã lưu trong phiên này


def _log_unknown(text: str | None, strip) -> None:
    """Tên OCR có "?" (glyph chưa có mẫu): lưu dải tên (đúng ảnh cho `python -m bot.ocr.add_sample GeneralName`) vào logs/generals/<tên OCR>.png
    ("?" đổi thành "x" trong tên file; cùng tên đọc lại thì ghi đè) và ghi logs/generals/unknown.logs. Mỗi tên chỉ lưu một lần mỗi lần chạy."""
    if not text or "?" not in text or text in _logged:
        return
    _logged.add(text)
    image = re.sub(r'[\\/:*"<>|\s]+', "_", text.replace("?", "x")) + ".png"
    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(LOGS_DIR / image), strip)
        with open(LOGS_DIR / "unknown.logs", "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} name={text!r} image={image}\n")
    except OSError:
        pass


def _wanted_general(bot, wanted: list) -> str | None:
    """Tên tướng đang hiện nếu nằm trong danh sách tướng đã tích ở UI (`wanted` = settings["generals"]), không thì None. Đọc tên bằng OCR
    (read_general_name) rồi lấy tướng giống nhất, từ NAME_MATCH (50%) trở lên là khớp: chữ OCR chỉ cần nằm trong tên (một phần tên là đủ, VD "?athanael" khớp "Nathanael Greene"), chỉ xét chữ cái, bỏ phần trong ngoặc của tên."""
    strip = bot.crop(bot.screenshot(), *NAME_STRIP)
    text = read_general_name(strip)
    _log_unknown(text, strip)
    score, name = max(((similarity(text, general), general) for general in wanted), default=(0.0, None))
    bot.log(f"{NAME}: General name read {text!r}, best match {name!r} {score:.0%}")
    if name is not None and score >= NAME_MATCH:
        return name
    bot.log(f"{NAME}: General not in the wanted list, keep refreshing")
    return None


class GeneralsFull(Exception):
    """Đã đủ số tướng tối đa (popup "You can only have up to N Generals..." + nút Confirm giữa màn): dừng activity (`_refresh` bắt, trả False)."""


class NotEnoughGold(Exception):
    """Không đủ vàng mua tướng (Open Gold tắt, hoặc đã mở hết rương vẫn thiếu): dừng activity (`_refresh` bắt, trả False)."""


def _buy(bot, name: str, buy_with: str = BUY_RECRUIT, open_gold: bool = False) -> bool:
    """Mua tướng `name` đang hiện: bấm vào ảnh tướng -> chờ màn chi tiết (1 giây / lần tối đa DETAIL_WAIT giây, mất nút Refresh = đã ra) -> bấm nút mua: màn chỉ có MỘT nút (Recruit General ở
    giữa) thì bấm thẳng nút đó; có hai nút thì bấm theo setting `buy_with` (Recruit General / Buy General Token). Bấm nút xong chờ về màn danh sách tướng (`_wait_list`, tối đa LIST_WAIT giây, quá hạn thì Back). Popup / màn kết quả giữa chừng CHƯA có ảnh. True nếu đã bấm nút."""
    bot.record(f"{NAME}: wanted General {name} is in the Tavern, open its detail")
    bot.tap_percent(*GENERAL_ART)
    for _ in range(DETAIL_WAIT):   # chờ 1 giây rồi xét; mất nút Refresh của Tavern = đã ra màn chi tiết, còn thì chờ thêm 1 giây
        bot.sleep(1)  # delay cố định, không cần sửa
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
    if _how_to_get_shown(bot):   # thiếu vàng: game mở màn "How to get" thay vì mua
        if not open_gold:
            bot.record(f"{NAME}: not enough gold for {name} and Open Gold is off, back to the General list and stop")
            bot.back(delay=1)    # How to get -> màn chi tiết; delay cố định, không cần sửa
            bot.back(delay=1)    # màn chi tiết -> màn danh sách; delay cố định, không cần sửa
            _wait_list(bot)
            raise NotEnoughGold(name)
        bot.record(f"{NAME}: not enough gold for {name}, open all the gold items")
        _open_all_gold(bot)
        bot.back()                             # hết rương Use: How to get -> màn chi tiết
        template = DETAIL_RECRUIT if label == BUY_RECRUIT else DETAIL_BUY_TOKEN
        if bot.wait_for(template, timeout=DETAIL_BACK_WAIT, threshold=DETAIL_THRESHOLD, interval=1) is None:
            bot.record(f"{NAME}: General detail screen not shown after {DETAIL_BACK_WAIT}s after opening gold, stop")
            return False
        bot.tap(*button, delay=GOLD_STEP_DELAY)   # bấm lại nút mua với số vàng mới; delay cố định, không cần sửa
        bot.record(f"{NAME}: tapped {label} for {name} again after opening gold")
        if _how_to_get_shown(bot):
            bot.record(f"{NAME}: still not enough gold for {name}, back to the General list and stop")
            bot.back(delay=1)  # delay cố định, không cần sửa
            bot.back(delay=1)  # delay cố định, không cần sửa
            _wait_list(bot)
            raise NotEnoughGold(name)
    _wait_list(bot)
    return True


def _how_to_get_shown(bot) -> bool:
    """Sau khi bấm nút mua: wait_for màn "How to get" (thiếu vàng), 1 giây / lần tối đa HOW_TO_GET_WAIT giây, True khi thấy; thấy nút Refresh của
    Tavern (đã mua xong, về danh sách) thì dừng chờ, False; thấy popup hết chỗ tướng (GENERALS_FULL) thì raise GeneralsFull."""
    for _ in range(HOW_TO_GET_WAIT):
        if bot.wait_for(HOW_TO_GET_TITLE, timeout=1, threshold=THRESHOLD, interval=1) is not None:
            return True
        if bot.find(GENERALS_FULL, threshold=THRESHOLD) is not None:   # popup hết chỗ tướng (nút Confirm giữa màn): không bấm Confirm, dừng
            bot.record(f"{NAME}: the General limit is reached (popup with the Confirm button), stop")
            raise GeneralsFull()
        if bot.find(REFRESH, threshold=THRESHOLD) is not None:
            return False
    return False


def _open_all_gold(bot) -> int:
    """Màn "How to get": bấm "Use" của từng rương vàng từ trên xuống, mỗi rương hiện popup số lượng: thanh trượt đã ở mức tối đa thì nút trái là "Minimum"
    (bấm Use luôn); là "Max" (chưa ở tối đa) thì bấm Max trước rồi bấm Use. Không thấy nút Use nào trên màn = hết vàng, dừng
    (người gọi Back về màn mua). Chỉ có một rương thì Use dùng luôn, không popup (danh sách đổi = đã dùng); bấm Use mà màn không đổi thì bỏ qua. Tối đa GOLD_MAX_USES lần. Trả số rương đã dùng."""
    used, tried = 0, []
    while used < GOLD_MAX_USES:
        screen = bot.screenshot()
        buttons = sorted(bot.find_all(LIST_USE, screen=screen, threshold=LIST_USE_THRESHOLD, region=LIST_USE_REGION), key=lambda p: p[1])
        button = next((b for b in buttons if all(abs(b[1] - y) > 8 for y in tried)), None)
        if button is None:      # không còn nút Use nào trên màn: hết vàng (rương còn lại là nút kim cương)
            break
        tried.append(button[1])
        bot.tap(*button, delay=GOLD_STEP_DELAY)  # delay cố định, không cần sửa
        if _use_in_popup(bot):                      # nhiều hơn một: popup số lượng, bấm Use xong về danh sách
            used += 1
            tried = []
        elif _list_changed(bot, screen):            # chỉ có một: không popup, dùng luôn, danh sách đổi
            bot.log(f"{NAME}: used one gold item without a quantity popup")
            used += 1
            tried = []
        else:
            bot.log(f"{NAME}: nothing happened after the Use button, skip it")
    bot.record(f"{NAME}: opened {used} gold item(s)")
    return used


def _use_in_popup(bot) -> bool:
    """Popup số lượng của rương: chờ tối đa POPUP_WAIT giây; bấm Max (tìm ảnh nút) nếu chưa ở tối đa, bấm Use, chờ popup đóng. True nếu đã bấm Use."""
    for _ in range(POPUP_OPEN_WAIT):
        screen = bot.screenshot()
        if bot.find(POPUP_USE, screen=screen, threshold=THRESHOLD) is not None:
            break
        bot.sleep(GOLD_STEP_DELAY)  # delay cố định, không cần sửa
    else:
        return False
    for _ in range(MAX_TAPS):   # nút trái chỉ ghi "Max" hoặc "Minimum": "Max" = chưa ở tối đa, bấm xong đổi thành "Minimum" (thanh trượt ở tối đa)
        maximum = bot.find(POPUP_MAX, threshold=THRESHOLD)
        if maximum is None:
            break
        bot.tap(*maximum, delay=GOLD_STEP_DELAY)  # delay cố định, không cần sửa
    if bot.find(POPUP_MINIMUM, threshold=THRESHOLD) is None:
        bot.log(f"{NAME}: popup left button is not Minimum after Max, press Use anyway")
    use = bot.find(POPUP_USE, threshold=THRESHOLD)
    if use is None:
        return False
    bot.tap(*use, delay=USE_LOAD_WAIT)   # giữa màn hiện vòng tròn xoay (đang tải): chờ xong rồi mới xét; delay cố định, không cần sửa
    for _ in range(POPUP_WAIT):   # chờ popup đóng
        if bot.find(POPUP_USE, threshold=THRESHOLD) is None:
            return True
        bot.sleep(GOLD_STEP_DELAY)  # delay cố định, không cần sửa
    bot.back(delay=GOLD_STEP_DELAY)   # popup còn nguyên (VD hiện thêm popup kết quả): đóng; delay cố định, không cần sửa
    return True


def _list_changed(bot, before) -> bool:
    """Danh sách rương khác ảnh `before` (chụp trước khi bấm Use): chỉ có một rương thì Use dùng luôn, không popup, danh sách đổi."""
    bot.sleep(USE_LOAD_WAIT)   # vòng tròn xoay giữa màn (đang tải) xong rồi mới so ảnh; delay cố định, không cần sửa
    return _screen_diff(before, bot.screenshot()) > GOLD_LIST_MIN_DIFF


def _screen_diff(before, after) -> float:
    """Độ khác nhau trung bình (0..255) của hai ảnh màn hình, bỏ thanh tiêu đề và đáy."""
    y0, y1 = int(before.shape[0] * 0.15), int(before.shape[0] * 0.95)
    return float(np.abs(before[y0:y1].astype(np.int16) - after[y0:y1].astype(np.int16)).mean())


def _wait_list(bot) -> bool:
    """Sau khi bấm nút mua: chờ 1 giây, thấy nút Refresh của Tavern = đã về màn danh sách tướng; chưa thì chờ thêm 1 giây / lần tới
    tối đa LIST_WAIT giây; vẫn chưa về thì bấm Back. Về được (tự về hoặc sau Back) thì chờ thêm LIST_RELOAD_WAIT giây rồi mới làm tiếp.
    True nếu tự về."""
    back = False
    for _ in range(LIST_WAIT):
        bot.sleep(1)  # delay cố định, không cần sửa
        if bot.find(REFRESH, screen=bot.screenshot(), threshold=THRESHOLD) is not None:
            back = True
            break
    if not back:
        bot.record(f"{NAME}: not back at the General list after {LIST_WAIT}s, Back")
        bot.back(delay=1)  # delay cố định, không cần sửa
    bot.sleep(LIST_RELOAD_WAIT)   # chờ 2s để đợi game load lại dữ liệu; delay cố định, không cần sửa
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
    cần mua thì mua (`_buy`, xong game về màn danh sách, chữ "Recruited"), rồi kéo tiếp sang tướng kế. Trả số tướng đã mua; raise NotEnoughGold khi thiếu vàng (dừng activity)."""
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
        name = _wanted_general(bot, list(settings.get(GENERALS_KEY) or []))
        if name is not None and _buy(bot, name, settings.get(BUY_KEY) or BUY_RECRUIT, bool(settings.get(OPEN_GOLD_KEY))):
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
        bot.sleep(1)  # delay cố định, không cần sửa
        return True
    for _ in range(SWIPE_CHANGE_WAIT):
        bot.sleep(1)  # delay cố định, không cần sửa
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
        bot.sleep(1)  # delay cố định, không cần sửa
    bot.log(f"{NAME}: emblem not shown next to the General name")
    return False
