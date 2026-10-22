"""
boss_scan.py — quét một hình quạt trên bản đồ thế giới tìm boss: kéo camera bằng arc_sweep, ở mỗi ô chụp màn hình, nhận boss bằng find_bosses, đổi vị trí nhãn trên màn hình ra toạ độ
X:Y và gộp các boss thấy lặp ở hai màn kề nhau.

    boss = scan_bosses(bot, 0, 90, 200)       # góc, bán kính như arc_sweep; chỉ giữ boss đang bật trong ui/tabs/boss.py
    # [{"name": "Zombie", "level": 1, "tier": None, "tag": True, "x": 633, "y": 441, "active": True, "score": 0.77}, ...]

Toạ độ là ước tính từ vị trí nhãn so với tâm màn hình (CAMERA_PX = điểm trên màn hình ứng với toạ độ camera đọc ở thanh X:Y, PX_X / PX_Y của arc_sweep), sai vài km: đủ để
tìm boss trên bản đồ, muốn chính xác thì bấm vào boss rồi đọc toạ độ trong cửa sổ thông tin.
"""
import math

import cv2
import numpy as np

from ..ocr import read_camera, world_mask
from ..ocr.find_bosses import find_bosses, read_popup
from . import no_alliance
from .arc_sweep import MIN_SWIPE, STEP, SWIPE_FULL, SWIPE_FULL_V, STEP_FRAC, _camera, _swipe, arc_sweep, px_to_world, safe_shift, valid_camera, world_to_px
from .shared_bosses import SharedBosses

MENU_TEXT = {"attack": "CityMap/menuText_attack.png", "share": "CityMap/menuText_share.png"}   # chữ vàng dưới nút của menu nhanh hiện ra khi bấm vào tên boss (menu: Attack / Add Bookmark / Share):
# nhận nút bằng chữ vàng (ảnh "độ vàng" mềm) vì biểu tượng nút trong suốt, nền bản đồ khác nhau làm ảnh biểu tượng khớp kém (đã gây lỗi "không thấy nút Attack" dù menu đang hiện)
ATTACK_ICON, SHARE_ICON = "attack", "share"
MENU_TEXT_THRESHOLD = 0.82      # menu có mặt: 0.89-1.0; không có menu: tối đa 0.6-0.7
SHARE_FROM_ATTACK = (-5, 116)   # px: tâm biểu tượng Share so với điểm bấm của Attack (đo ở 3 menu: lệch (-6..-3, +94..+106) so với tâm chữ Attack, điểm bấm Attack cao hơn tâm chữ 16 px)
MENU_ICON_ABOVE = 16            # px: bấm cao hơn tâm chữ chừng này (vào phần dưới của biểu tượng nút nằm ngay trên chữ)
SHARE_CONFIRM_ICON = "CityMap/shareConfirm.png"   # nút Confirm của hộp "Confirm to share with <liên minh>" (cạnh nút Cancel)
SHARE_WORLD_ICON = "CityMap/shareWorld.png"   # nút World Channel trong hộp "Share the Coordinates with" (nút liên minh nằm đối xứng với nó qua giữa màn hình, theo chiều ngang)
LIT_REGIONS = ((358, 22, 394, 50), (335, 575, 392, 630))   # (x1, y1, x2, y2): biểu tượng kim cương ở thanh tài nguyên và nút Mail: độ sáng xám trung bình 95-101 trên mọi địa hình, mọi popup / hộp thoại làm tối chúng (<= 46)
LIT_MIN = 75                     # độ sáng trung bình tối thiểu của MỌI vùng LIT_REGIONS để coi là bản đồ sạch
EXIT_CANCEL_ICON = "CityMap/exitCancel.png"   # nút Cancel của hộp "Are you sure you want to exit the game?" (Back trên bản đồ sạch hiện hộp này): bấm Cancel, không bấm Back
MONSTER_POPUP_ICON = "CityMap/monsterPopup.png"   # nút Go của cửa sổ thông tin quái thường (không phải boss): thấy nó thì bỏ ngay, khỏi chờ hết 5 lần
POPUP_ICON = "CityMap/bossPopup.png"      # nút Alliance War của cửa sổ thông tin boss (hiện sau khi bấm Attack): thấy nó là cửa sổ đã mở
MENU_THRESHOLD = 0.75
MENU_WAIT = 1.0              # giây: chờ nút của menu mỗi lần
MENU_TRIES = 5               # số lần chờ: hết mà không thấy nút thì bỏ qua boss này
POLL = 0.3                   # giây: chờ một thứ hiện ra (menu nhanh, cửa sổ, hộp Share / Confirm, toạ độ camera) thì kiểm tra mỗi chừng này thay vì ngủ cứng MENU_WAIT rồi mới xem (menu hiện sớm vẫn phải đợi đủ 1 giây = chậm)
POLL_TRIES = round(MENU_TRIES * MENU_WAIT / POLL)   # tổng thời gian chờ tối đa giữ nguyên (5 giây)

CAMERA_PX = (198, 352)       # điểm trên màn hình 396 x 704 ứng với toạ độ camera (giữa màn hình)
LABEL_ABOVE = 15             # px: ô đất của boss nằm cao hơn chữ nhãn chừng này (nhãn nằm dưới chân boss)
SAFE_ZONE = (190, 300, 180, 480)   # (x1, x2, y1, y2): menu nhanh luôn mọc về BÊN TRÁI nhãn boss ~70-75 px (Attack cao hơn ~70 px, Share thấp hơn ~50 px): boss ngoài khoảng này thì các mục của menu rơi
# xuống dưới các nút giao diện (Bookmarks, World Map, Quests ở x < 66; thanh trên y < 60; nút dưới y > 575) và cú bấm trúng nút giao diện thay vì Attack / Share (đã mở nhầm Bookmarks)
CENTRE_TO = (240, 330)             # đưa boss ở rìa về chỗ này trước khi bấm
SETTLE_DIFF = 2.0                  # độ lệch điểm ảnh trung bình (0-255) giữa hai ảnh cách 0.5 giây dưới mức này coi là bản đồ đã dừng (sau cú kéo bản đồ còn trượt theo quán tính vài giây)
VISIBLE = (10, 70, 386, 620)       # (x1, y1, x2, y2): vùng bản đồ nhìn được trên màn hình (không tính thanh trên / dưới): boss trượt ra ngoài vùng này sau một cú kéo là mất khỏi màn hình
MAX_REVISIT = 6                    # số vòng thêm (ngoài MAX_ACTIONS) mỗi màn dành cho việc kéo tới các boss trong danh sách chờ
MAX_REVISIT_TRIES = 3              # số lần kéo tối đa tới cùng một boss trong danh sách chờ (xa quá một cú kéo không tới thì kéo tiếp)
RESTORE_KM = 3.0                   # km: camera lệch ô dự tính hơn mức này (sau khi bấm / kéo boss) thì kéo bù về ô dự tính trước khi sang ô kế
RESTORE_TRIES = 3                  # số cú kéo bù tối đa mỗi ô (mỗi cú bị giới hạn độ dài, xa quá thì kéo nhiều cú)
MAX_ACTIONS = 10             # số boss tối đa xử lý trên một màn hình (chặn vòng lặp vô hạn khi không đọc được toạ độ camera để nhận ra boss đã xử lý)
SAME_BOSS_KM = 4.0           # km: cùng tên / tầng, cách nhau gần hơn mức này (hai màn kề nhau) là cùng một boss


def world_position(camera: tuple[int, int], pos: tuple[int, int]) -> tuple[float, float]:
    """Toạ độ (X, Y) của chỗ trên màn hình `pos` (px) khi camera đứng ở `camera` (X, Y)."""
    u, v = px_to_world(pos[0] - CAMERA_PX[0], pos[1] - LABEL_ABOVE - CAMERA_PX[1])
    return camera[0] + u, camera[1] + v


def _lit(screen) -> bool:
    gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
    return all(float(gray[y1:y2, x1:x2].mean()) >= LIT_MIN for x1, y1, x2, y2 in LIT_REGIONS)


_menu_cache: dict = {}


def _yellowness(image: np.ndarray) -> np.ndarray:
    """Độ vàng 0-1 của từng điểm (chữ vàng của menu nhanh), làm mờ nhẹ, cộng nhiễu rất nhỏ cố định để vùng phẳng không cho điểm khớp ảo."""
    b, g, r = (image[..., i].astype(np.float32) for i in range(3))
    y = cv2.GaussianBlur(np.clip((np.minimum(r, g) - b - 60) / 150, 0, 1), (3, 3), 0.8)
    return y + np.random.RandomState(0).rand(*y.shape).astype(np.float32) * 0.02


def find_menu_item(bot, screen, item: str) -> tuple[int, int] | None:
    """Vị trí để bấm nút `item` ("attack" / "share") của menu nhanh trên `screen`, hoặc None nếu menu chưa hiện."""
    if item not in _menu_cache:
        from ..context.templates import TEMPLATE_DIR, read_image
        image = read_image(TEMPLATE_DIR / MENU_TEXT[item], cv2.IMREAD_GRAYSCALE)
        _menu_cache[item] = image.astype(np.float32) / 255 + np.random.RandomState(1).rand(*image.shape).astype(np.float32) * 0.02
    template = _menu_cache[item]
    result = cv2.matchTemplate(_yellowness(screen), template, cv2.TM_CCOEFF_NORMED)
    _, best, _, at = cv2.minMaxLoc(result)
    if best >= MENU_TEXT_THRESHOLD:
        return at[0] + template.shape[1] // 2, at[1] + template.shape[0] // 2 - MENU_ICON_ABOVE
    if item == "share":                       # chữ "Share" bị nút giao diện che (boss sát mép màn hình): tìm Attack rồi suy ra, Share luôn ở ngay dưới Attack
        attack = find_menu_item(bot, screen, "attack")
        if attack is not None:
            return attack[0] + SHARE_FROM_ATTACK[0], attack[1] + SHARE_FROM_ATTACK[1]
    return None


def on_map(bot, screen=None) -> bool:
    """Đang ở màn bản đồ sạch: các biểu tượng cố định của giao diện (LIT_REGIONS) còn sáng. Popup / hộp thoại làm tối chúng, địa hình bản đồ (nước, rừng...) thì không ảnh hưởng."""
    return _lit(bot.screenshot() if screen is None else screen)


def ensure_map(bot) -> bool:
    """Đưa màn hình về bản đồ sạch: còn popup / hộp thoại (giao diện bị tối) thì bấm Back, hộp "thoát game" thì bấm Cancel; mỗi lần chờ 1 giây, tối đa MENU_TRIES lần.
    CHỈ bấm Back khi giao diện bị tối, không bao giờ trên bản đồ sạch (Back ở đó hỏi thoát game). False nếu hết lần vẫn chưa về bản đồ."""
    for _ in range(MENU_TRIES):
        screen = bot.screenshot()
        if _lit(screen):
            return True
        cancel = bot.find(EXIT_CANCEL_ICON, threshold=0.8, screen=screen)
        if cancel is not None:
            bot.tap(*cancel, delay=MENU_WAIT)
        else:
            bot.back(delay=MENU_WAIT)
    return _lit(bot.screenshot())


def tap_menu_item(bot, pos: tuple[int, int], icon: str) -> bool:
    """Bấm vào `pos` (tên boss), chờ nút `icon` của menu nhanh hiện (mỗi MENU_WAIT giây, tối đa MENU_TRIES lần) rồi bấm nó. False nếu nút không hiện (bấm trượt,
    không phải boss...): bỏ qua boss này. Bấm vào boss làm camera dời theo boss."""
    bot.tap(*pos, delay=0)
    for _ in range(POLL_TRIES):
        bot.sleep(POLL)
        found = find_menu_item(bot, bot.screenshot(), icon)
        if found is not None:
            bot.tap(*found, delay=0)
            return True
    bot.log(f"boss: không thấy nút {icon} sau khi bấm {pos}, bỏ qua")
    ensure_map(bot)
    return False


def open_boss_info(bot, boss: dict) -> bool:
    """Bấm tên boss rồi bấm Attack: mở cửa sổ thông tin boss (tên, cấp, toạ độ). False nếu Attack không hiện."""
    return tap_menu_item(bot, boss["pos"], ATTACK_ICON)


def share_to_alliance(bot) -> bool:
    """Ở hộp "Share the Coordinates with" (hai nút nằm ngang hàng: World Channel và liên minh, đổi chỗ cho nhau): chờ hộp hiện (mỗi MENU_WAIT giây, tối đa MENU_TRIES lần), tìm nút
    World Channel bằng ảnh mẫu rồi bấm nút đối xứng với nó qua giữa màn hình (x -> chiều rộng - x, cùng y) = nút liên minh; rồi chờ hộp "Confirm to share with ..." và bấm Confirm
    (sau Confirm game tự về lại bản đồ: chờ tới khi hai hộp biến mất, không cần đóng gì thêm; mọi bước chờ đều 1 giây tối đa 5 lần). False nếu hộp chọn kênh hoặc nút Confirm không hiện (hộp xác nhận còn mở thì bấm Back để huỷ)."""
    for _ in range(POLL_TRIES):
        bot.sleep(POLL)
        world = bot.find(SHARE_WORLD_ICON, threshold=MENU_THRESHOLD)
        if world is not None:
            bot.tap(world_mask.SIZE[0] - world[0], world[1], delay=0)
            break
    else:
        bot.log("boss: không thấy hộp chọn kênh Share, bỏ qua")
        ensure_map(bot)
        return False
    for _ in range(POLL_TRIES):
        bot.sleep(POLL)
        confirm = bot.find(SHARE_CONFIRM_ICON, threshold=MENU_THRESHOLD)
        if confirm is not None:
            bot.tap(*confirm, delay=0)
            for _ in range(POLL_TRIES):                              # game tự về lại bản đồ sau Confirm: chờ hộp xác nhận / hộp Share biến mất
                bot.sleep(POLL)
                screen = bot.screenshot()
                if bot.find(SHARE_CONFIRM_ICON, threshold=MENU_THRESHOLD, screen=screen) is None and bot.find(SHARE_WORLD_ICON, threshold=MENU_THRESHOLD, screen=screen) is None:
                    return True
            bot.log("boss: sau Confirm hộp Share vẫn còn, coi như đã gửi")
            return True
    bot.log("boss: không thấy nút Confirm khi share liên minh, bỏ qua")
    ensure_map(bot)
    return False


def check_boss(bot, boss: dict) -> dict | None:
    """Boss chỉ đọc được một phần (confirm): bấm tên, bấm Attack, chờ cửa sổ thông tin hiện (1 giây, tối đa MENU_TRIES lần), đọc tên boss trong đó (read_popup) rồi bấm Back đóng cửa sổ (về bản đồ).
    Trả {"name", "tier", "level", "active", ...} theo boss.py, hoặc None nếu Attack / cửa sổ không hiện hoặc tên không có trong danh mục. Bấm vào boss làm camera dời ra giữa boss, nên sau Back
    nhãn boss đã đọc được đủ trên bản đồ."""
    if not open_boss_info(bot, boss):
        return None
    for _ in range(POLL_TRIES):
        bot.sleep(POLL)
        screen = bot.screenshot()
        if bot.find(POPUP_ICON, threshold=MENU_THRESHOLD, screen=screen) is not None:
            info = read_popup(screen)
            ensure_map(bot)
            return info
        if bot.find(MONSTER_POPUP_ICON, threshold=MENU_THRESHOLD, screen=screen) is not None:
            bot.log("boss: cửa sổ của quái thường, không phải boss, bỏ qua")
            ensure_map(bot)
            return None
    bot.log("boss: không thấy cửa sổ thông tin boss sau khi bấm Attack (không phải boss?), bỏ qua")
    ensure_map(bot)                                           # có thể đã mở cửa sổ của quái thường: đóng lại
    return None


SHARED, ALREADY, FAILED = "shared", "already", "failed"      # kết quả của share_boss


def share_boss(bot, boss: dict, shared: SharedBosses) -> str:
    """Bấm tên boss; khi menu nhanh hiện (có nút Share) đọc toạ độ X:Y của boss ở thanh toạ độ (bấm vào boss làm camera dời ra đúng boss; hộp Share sau đó làm tối thanh nên phải đọc
    lúc này). Boss ở toạ độ đó đã chia sẻ trước đây (`shared`) thì dừng: ALREADY. Chưa thì bấm Share, chọn liên minh, Confirm (share_to_alliance), ghi toạ độ vào `shared`: SHARED.
    FAILED nếu Share không hiện, không đọc được toạ độ (không biết đã chia sẻ chưa nên không gửi) hoặc hộp chọn kênh / Confirm không hiện. boss thêm "x", "y" (toạ độ đọc được)."""
    if no_alliance.known(bot):
        return FAILED                                        # chưa có liên minh: không có chỗ chia sẻ
    bot.tap(*boss["pos"], delay=0)
    for _ in range(POLL_TRIES):
        bot.sleep(POLL)
        screen = bot.screenshot()
        found = find_menu_item(bot, screen, SHARE_ICON)
        if found is not None:
            break
    else:
        bot.log(f"boss: không thấy nút Share sau khi bấm {boss['pos']}, bỏ qua")
        ensure_map(bot)
        return FAILED
    coords = valid_camera(read_camera(screen))
    for _ in range(POLL_TRIES):                              # bấm vào boss làm camera chạy ra giữa boss: chờ camera dừng hẳn (hai lần đọc liên tiếp ra số và giống nhau) mới lấy toạ độ; đọc thất bại (~5% ảnh) thì thử lại
        bot.sleep(POLL)
        screen = bot.screenshot()
        again = valid_camera(read_camera(screen))
        if again is not None and again == coords:
            break
        if again is not None:
            coords = again
    if coords is None:
        bot.log("boss: không đọc được toạ độ boss, bỏ qua (không biết đã chia sẻ chưa)")
        ensure_map(bot)
        return FAILED
    boss["x"], boss["y"] = coords
    if shared.has(*coords, boss["name"], boss["tier"]):
        bot.log(f"boss: {boss['text']} ở {coords[0]}:{coords[1]} đã chia sẻ trước đó, không chia sẻ lại")
        return ALREADY
    bot.tap(*found, delay=0)
    if not share_to_alliance(bot):
        return FAILED
    shared.add(coords[0], coords[1], name=boss["name"], tier=boss["tier"], level=boss["level"])
    return SHARED


def handle_screen(bot, handled: list[dict], only_active: bool = True, shared: SharedBosses | None = None, camera_guess: tuple[float, float] | None = None) -> list[dict]:
    """Xử lý các boss thấy trên màn hình hiện tại, mỗi lần bấm xong chụp lại và tìm lại từ đầu (bấm vào boss làm camera dời theo). Thứ tự: boss đọc ĐỦ tên (không cần xác nhận)
    trước; boss đang được tích (active) thì chia sẻ vào liên minh (share_boss) nếu toạ độ của nó chưa có trong `shared` (mặc định danh sách chung của server `bot.server`: mọi bot cùng server
    dùng chung, nhớ qua các lần chạy; chưa biết server thì không chia sẻ gì).
    Hết boss đọc đủ tên thì xử lý các boss chỉ đọc được một phần: KÉO LUÔN boss ra giữa màn hình (centre_boss_pos) rồi đọc lại nhãn (nhãn không còn bị cắt); đọc ra đúng boss đang tích thì lần lặp
    sau chia sẻ luôn như boss thường. Chỉ khi kéo xong mà nhãn vẫn đọc thiếu (hoặc màn không đổi) mới kiểm tra bằng cửa sổ thông tin (check_boss: bấm tên, bấm Attack, đọc tên, Back); không đủ điều kiện thì bỏ qua. Trả về các boss còn cần xác nhận. `handled` (danh sách {name, tier, x, y}) nhớ các boss đã xử lý trong lần quét này,
    tránh bấm lại khi boss hiện ở giữa màn sau khi bấm.
    Danh sách chờ (`waiting`): mọi boss cần xử lý đã thấy ở ô này được nhớ theo toạ độ THẾ GIỚI. Mỗi lần kéo / bấm làm camera dời, hướng tới từng boss được tính lại từ toạ độ camera đọc được
    (screen_of): xử lý xong một boss, hết việc ở màn hiện tại mà danh sách chờ còn thì kéo tới boss kế (trên-trái trước) rồi tìm lại, tới khi hết danh sách."""
    # camera_guess: toạ độ camera dự tính (ô quét) khi không đọc được thanh X:Y; được cập nhật theo các cú kéo / bấm boss của chính hàm này.
    server = str(getattr(bot, "server", "") or "").strip()
    if shared is None:
        if not server:
            bot.log("boss: chưa biết server nên không chia sẻ (không biết boss đã chia sẻ chưa)")
            return [b for b in find_bosses(bot.screenshot()) if b["confirm"]]
        shared = SharedBosses.for_server(server)
    skipped: list[tuple[int, int]] = []          # vị trí đã thử mà không chia sẻ được: không thử lại ở màn này
    centred: list[tuple[int, int]] = []          # vị trí boss sát rìa đã kéo về giữa (mỗi chỗ chỉ kéo một lần)
    waiting: list[dict] = []                     # danh sách chờ: mọi boss cần xử lý đã thấy ở ô này, theo TOẠ ĐỘ THẾ GIỚI {"world": (x, y), "tries": số lần kéo tới}; hướng tới từng boss tính lại từ camera mỗi lần
    pending: list[dict] = []
    for _ in range(MAX_ACTIONS + 1 + MAX_REVISIT):
        screen = settle(bot)
        camera = _camera(bot, screen)
        if camera is not None:
            camera_guess = camera
        else:
            camera = camera_guess                          # đọc hỏng (OCR ~5% ảnh, vùng X thấp hay None): dùng toạ độ dự tính
        found = [b for b in find_bosses(screen) if b["name"] or b["confirm"]]
        if centred and not found:
            bot.log("boss: sau khi kéo về giữa không còn thấy boss nào ở màn này")
        found.sort(key=lambda b: (b["confirm"], not in_safe_zone(b["pos"]), reading_order(b["pos"])))   # đọc đủ tên trước; boss ở vùng giữa (không phải kéo, không đẩy boss khác ra ngoài) trước, rồi boss sát rìa theo thứ tự trên-trái trước
        pending = [b for b in found if b["confirm"]]
        todo = None
        if camera:                                       # ghi mọi boss cần xử lý đang thấy vào danh sách chờ (toạ độ thế giới), bỏ boss đã xử lý
            for b in found:
                if b["confirm"] or (only_active and not b["active"]) or any(abs(b["pos"][0] - x) < 12 and abs(b["pos"][1] - y) < 12 for x, y in skipped):
                    continue
                w = world_position(camera, b["pos"])
                entry = next((e for e in waiting if math.hypot(e["world"][0] - w[0], e["world"][1] - w[1]) < SAME_BOSS_KM and same_boss(e, b)), None)
                if entry is None:
                    waiting.append({"world": w, "tries": 0, "name": b["name"], "tier": b["tier"]})
                else:
                    entry["world"] = w                    # toạ độ ước tính mới nhất (camera gần boss hơn thì chính xác hơn)
                    entry["name"], entry["tier"] = b["name"] or entry["name"], b["tier"] or entry["tier"]
            waiting[:] = [e for e in waiting if not any(math.hypot(h["x"] - e["world"][0], h["y"] - e["world"][1]) < SAME_BOSS_KM and same_boss(e, h) for h in handled)]
        for boss in found:
            if boss["confirm"] or (only_active and not boss["active"]) or any(abs(boss["pos"][0] - x) < 12 and abs(boss["pos"][1] - y) < 12 for x, y in skipped):
                continue
            where = world_position(camera, boss["pos"]) if camera else None
            if where and any(h["name"] == boss["name"] and h["tier"] == boss["tier"] and math.hypot(h["x"] - where[0], h["y"] - where[1]) < SAME_BOSS_KM for h in handled):
                continue
            todo = boss
            break
        if todo is not None and not in_safe_zone(todo["pos"]) and not any(abs(todo["pos"][0] - x) < 12 and abs(todo["pos"][1] - y) < 12 for x, y in centred):
            centred.append(todo["pos"])                   # boss sát rìa: kéo về giữa rồi tìm lại, rồi mới bấm
            moved, new_pos = centre_boss_pos(bot, todo["pos"])
            if new_pos:
                centred.append(new_pos)
                camera_guess = _shift(camera_guess, todo["pos"], new_pos)
            bot.log(f"boss: kéo boss ở {todo['pos']} về giữa -> {'đã dời' if moved else 'màn không đổi'}")
            if moved:
                continue
        if todo is None:                                  # hết boss đọc đủ tên: kiểm tra các boss chỉ đọc được một phần
            todo = next((b for b in sorted(found, key=lambda b: reading_order(b["pos"])) if b.get("partial") and (not only_active or b["active"])
                         and not any(abs(b["pos"][0] - x) < 12 and abs(b["pos"][1] - y) < 12 for x, y in skipped)), None)
            if todo is None:
                if camera and waiting:                       # còn boss trong danh sách chờ mà chưa thấy: kéo tới hướng của nó (trên-trái trước) rồi tìm lại, cho tới khi hết danh sách
                    here = {id(e): screen_of(camera, e["world"]) for e in waiting}
                    waiting[:] = [e for e in waiting if not visible(here[id(e)])]     # đang trong màn hình mà không có việc: đã xử lý / bỏ qua rồi
                    if waiting:
                        target = min(waiting, key=lambda e: reading_order(here[id(e)]))
                        target["tries"] += 1
                        if target["tries"] > MAX_REVISIT_TRIES:
                            waiting.remove(target)
                            continue
                        moved, new_pos = centre_boss_pos(bot, here[id(target)])
                        if new_pos:
                            camera_guess = _shift(camera_guess, here[id(target)], new_pos)
                        bot.log(f"boss: kéo tới boss tiếp theo trong danh sách chờ (còn {len(waiting)}) -> {'đã dời' if moved else 'màn không đổi'}")
                        if not moved:
                            waiting.remove(target)
                        continue
                return pending
            if not any(abs(todo["pos"][0] - x) < 12 and abs(todo["pos"][1] - y) < 12 for x, y in centred):
                centred.append(todo["pos"])               # boss chỉ đọc được một phần (ở đâu cũng vậy): kéo luôn ra giữa (nhãn đọc đủ chữ) rồi đọc lại; đúng boss đang tích thì lần lặp sau chia sẻ luôn
                moved, new_pos = centre_boss_pos(bot, todo["pos"])
                if new_pos:
                    camera_guess = _shift(camera_guess, todo["pos"], new_pos)
                    centred.append(new_pos)               # chỗ mới đã kéo rồi: còn đọc thiếu thì mới mở cửa sổ thông tin (check_boss), không kéo lần nữa
                bot.log(f"boss: kéo boss một phần ở {todo['pos']} ({todo.get('candidates')}) về giữa -> {'đã dời' if moved else 'màn không đổi'}")
                if moved:
                    continue
            info = check_boss(bot, todo)
            bot.log(f"boss: kiểm tra '{todo['text']}' ({todo.get('candidates')}) -> {info['text'] + (' (đang tích)' if info['active'] else ' (không tích)') if info else 'không phải boss cần chia sẻ'}")
            old_pos = todo["pos"]
            skipped.append(old_pos)                       # vị trí này đã kiểm tra: không kiểm tra lại ở màn này
            if info is None or (only_active and not info["active"]):
                continue                                  # không phải boss cần chia sẻ
            pos = relocate(bot, info, old_pos)            # sau Back camera có thể đã dời ra giữa boss (nhãn đọc đủ) hoặc chưa (nhãn vẫn bị cắt ở chỗ cũ)
            if pos is None:
                bot.log(f"boss: {info['text']} đủ điều kiện nhưng không tìm lại được chỗ để bấm, bỏ qua")
                continue
            bot.log(f"boss: {info['text']} đủ điều kiện, chia sẻ")
            todo = dict(todo, name=info["name"], tier=info["tier"], level=info["level"], text=info["text"], active=True, partial=False, confirm=False, pos=pos)
        result = share_boss(bot, todo, shared)
        if result == FAILED:
            skipped.append(todo["pos"])
            continue
        handled.append({"name": todo["name"], "tier": todo["tier"], "x": todo["x"], "y": todo["y"], "result": result})
        camera_guess = (todo["x"], todo["y"])               # bấm vào boss làm camera chạy ra giữa boss
        if result == SHARED:
            bot.log(f"boss: đã chia sẻ {todo['text']} (cấp {todo['level']}) ở {todo['x']}:{todo['y']}")
    return pending


def reading_order(pos: tuple[int, int]) -> int:
    """Khoá xếp thứ tự xử lý: boss ở góc TRÊN-TRÁI trước (càng trái và càng cao càng sớm)."""
    return pos[0] + pos[1]


def visible(pos: tuple[int, int]) -> bool:
    return VISIBLE[0] <= pos[0] <= VISIBLE[2] and VISIBLE[1] <= pos[1] <= VISIBLE[3]


def screen_of(camera: tuple[int, int], world: tuple[float, float]) -> tuple[int, int]:
    """Vị trí trên màn hình (px, chỗ nhãn) của điểm toạ độ thế giới `world` khi camera đứng ở `camera`: ngược của world_position. Ngoài màn hình thì toạ độ nằm ngoài vùng
    nhìn thấy (có thể âm hoặc lớn hơn màn hình): đó chính là HƯỚNG và khoảng cách phải kéo để đưa boss vào."""
    px, py = world_to_px(world[0] - camera[0], world[1] - camera[1])
    return round(CAMERA_PX[0] + px), round(CAMERA_PX[1] + py + LABEL_ABOVE)


def restore_camera(bot, expected: tuple[float, float]) -> bool:
    """Kéo bù camera về `expected` (X, Y): sau khi bấm vào boss (camera chạy ra giữa boss) hoặc kéo boss ra giữa, camera lệch khỏi ô quét dự tính; arc_sweep kéo theo độ dời tương đối nên
    độ lệch cộng dồn qua các boss. Đọc toạ độ camera thật, lệch hơn RESTORE_KM thì kéo đúng độ lệch (mỗi cú giới hạn như cú quét, không ngắn hơn MIN_SWIPE), tối đa RESTORE_TRIES cú.
    False nếu không đọc được camera (không biết lệch bao nhiêu: để nguyên)."""
    for _ in range(RESTORE_TRIES):
        camera = _camera(bot, settle(bot))
        if camera is None:
            bot.log("boss: không đọc được toạ độ camera, không kéo bù về ô quét")
            return False
        du, dv = expected[0] - camera[0], expected[1] - camera[1]
        if math.hypot(du, dv) <= RESTORE_KM:
            return True
        px, py = world_to_px(du, dv)                      # camera cần dời bấy nhiêu px => ngón tay kéo ngược lại
        fx, fy = -px, -py
        scale = min(1.0, STEP_FRAC * SWIPE_FULL / max(abs(fx), 1e-9), STEP_FRAC * SWIPE_FULL_V / max(abs(fy), 1e-9))
        fx, fy = round(fx * scale), round(fy * scale)
        if math.hypot(fx, fy) < MIN_SWIPE:
            return True                                   # lệch quá nhỏ để kéo (ngắn hơn MIN_SWIPE game coi là bấm)
        bot.log(f"boss: camera lệch ô quét ({camera[0]}:{camera[1]} so với {expected[0]:.0f}:{expected[1]:.0f}), kéo bù")
        _swipe(bot, fx, fy, None, safe_shift(fx, fy))
    camera = _camera(bot, settle(bot))
    return camera is not None and math.hypot(expected[0] - camera[0], expected[1] - camera[1]) <= RESTORE_KM


def _shift(camera, old_pos, new_pos):
    """Camera dự tính sau khi kéo bản đồ làm vật ở `old_pos` chạy tới `new_pos` trên màn hình (camera dời ngược chiều ngón tay)."""
    if camera is None:
        return None
    du, dv = px_to_world(old_pos[0] - new_pos[0], old_pos[1] - new_pos[1])
    return camera[0] + du, camera[1] + dv


def same_boss(a: dict, b: dict) -> bool:
    """Hai bản ghi boss (`name`, `tier`) có thể là cùng một boss: tên khác nhau (cả hai đã biết) thì không; chưa biết tên (đọc một phần) thì coi là có thể."""
    return a.get("name") is None or b.get("name") is None or (a["name"] == b["name"] and a.get("tier") == b.get("tier"))


def in_safe_zone(pos: tuple[int, int]) -> bool:
    return SAFE_ZONE[0] <= pos[0] <= SAFE_ZONE[1] and SAFE_ZONE[2] <= pos[1] <= SAFE_ZONE[3]


def centre_boss(bot, pos: tuple[int, int]) -> bool:
    """centre_boss_pos(...)[0]: True nếu màn hình đã đổi."""
    return centre_boss_pos(bot, pos)[0]


def centre_boss_pos(bot, pos: tuple[int, int]) -> tuple[bool, tuple[int, int] | None]:
    """Kéo bản đồ để đưa boss đang ở `pos` về gần giữa màn hình (CENTRE_TO): nhãn không còn bị cắt ở rìa / che bởi nút giao diện nên đọc lại được đủ tên, và menu nhanh không bị nút giao diện đè. Cú kéo ít nhất MIN_SWIPE px (ngắn hơn game coi là bấm), né nút giao diện
    (safe_shift). Camera bị lệch một chút, không sao. Trả (màn hình đã đổi chưa, chỗ boss sau khi kéo (ước tính, bản đồ chạy theo ngón tay) hoặc None nếu màn không đổi)."""
    fx, fy = CENTRE_TO[0] - pos[0], CENTRE_TO[1] - pos[1]
    length = math.hypot(fx, fy) or 1.0
    scale = max(1.0, MIN_SWIPE / length)
    fx, fy = fx * scale, fy * scale
    limit = min(STEP / max(abs(fx), 1e-9), STEP_FRAC * SWIPE_FULL_V / max(abs(fy), 1e-9), 1.0)
    fx, fy = round(fx * limit), round(fy * limit)
    moved, _ = _swipe(bot, fx, fy, None, safe_shift(fx, fy))
    return moved, ((pos[0] + fx, pos[1] + fy) if moved else None)


def settle(bot):
    """Ảnh màn hình khi bản đồ đã dừng hẳn: chụp liên tiếp cách MENU_WAIT / 2 giây tới khi hai ảnh gần như giống nhau (tối đa MENU_TRIES lần), vì sau cú kéo bản đồ còn trượt theo quán tính làm nhãn
    boss ở rìa trôi đi giữa hai lần tìm."""
    last = bot.screenshot()
    for _ in range(MENU_TRIES):
        bot.sleep(MENU_WAIT / 2)
        now = bot.screenshot()
        if not (hasattr(last, "shape") and hasattr(now, "shape")):
            return now
        diff = float(cv2.absdiff(cv2.cvtColor(cv2.resize(last, None, fx=0.25, fy=0.25), cv2.COLOR_BGR2GRAY), cv2.cvtColor(cv2.resize(now, None, fx=0.25, fy=0.25), cv2.COLOR_BGR2GRAY)).mean())
        last = now
        if diff < SETTLE_DIFF:
            break
    return last


def relocate(bot, info: dict, old_pos: tuple[int, int]) -> tuple[int, int] | None:
    """Chỗ để bấm vào boss `info` (từ cửa sổ thông tin) sau khi đóng cửa sổ: chụp lại, tìm lại boss; camera đã dời ra giữa boss thì nhãn đọc đủ cùng tên / tầng ở chỗ mới, chưa dời
    thì nhãn vẫn bị cắt ở gần chỗ cũ `old_pos`. None nếu không thấy."""
    for boss in find_bosses(bot.screenshot()):
        if boss["name"] == info["name"] and boss["tier"] == info["tier"] and not boss.get("partial"):
            return boss["pos"]
    for boss in find_bosses(bot.screenshot()):
        if boss.get("partial") and abs(boss["pos"][0] - old_pos[0]) < 15 and abs(boss["pos"][1] - old_pos[1]) < 15:
            return boss["pos"]
    return None


def add_boss(found: list[dict], boss: dict, x: float, y: float) -> bool:
    """Thêm boss thấy ở (x, y) vào `found` nếu chưa có boss cùng tên / tầng gần đó (có rồi thì giữ bản có điểm đọc cao hơn). True nếu là boss mới."""
    for old in found:
        if old["name"] == boss["name"] and old["tier"] == boss["tier"] and math.hypot(old["x"] - x, old["y"] - y) < SAME_BOSS_KM:
            if boss["score"] > old["score"]:
                old.update(level=boss["level"], x=round(x), y=round(y), score=boss["score"])
            return False
    found.append({"name": boss["name"], "level": boss["level"], "tier": boss["tier"], "tag": boss["tag"], "x": round(x), "y": round(y),
                  "active": boss["active"], "score": boss["score"]})
    return True


def scan_bosses(bot, start_deg: float, end_deg: float, radius: float, only_active: bool = True, share: bool = True, **sweep) -> list[dict]:
    """Quét quạt (xem arc_sweep) và trả các boss tìm được. only_active=True: bỏ boss không bật trong ui/tabs/boss.py. share=True: ở mỗi ô của vòng quét chia sẻ vào liên minh các boss
    đang bật chưa chia sẻ (handle_screen: xử lý hết boss thấy được rồi mới kéo sang ô kế); camera bị dời do bấm vào boss thì cứ kéo tiếp theo đường đi cũ (lệch một chút, không sao).
    `sweep`: tham số thêm cho arc_sweep (resync, ...). Mỗi boss trả về: name, level, tier, tag, x, y, active, score, và khi share=True: "shared" = "shared" / "already" (toạ độ x, y đọc thật);
    boss chỉ đọc được một phần (cần bấm xem lại) có name None, "candidates" (các tên khả dĩ) và "partial" = True."""
    found: list[dict] = []
    handled: list[dict] = []                     # boss đã xử lý (chia sẻ / đã chia sẻ trước đó) trong lần quét này
    start = _camera(bot)
    if start is None:
        bot.log("boss: không đọc được toạ độ camera lúc bắt đầu, boss sẽ không có toạ độ thật")
        start = (0, 0)

    def on_step(u: float, v: float) -> bool:
        if not ensure_map(bot):
            bot.log("boss: không về được bản đồ sạch, bỏ qua ô này")
            return False
        screen = bot.screenshot()
        seen = find_bosses(screen)
        if seen:                                          # có ứng viên: chờ bản đồ dừng hẳn (quán tính sau cú kéo) rồi tìm lại cho đúng vị trí
            screen = settle(bot)
            seen = find_bosses(screen)
        base = getattr(bot, "sweep_origin", None) or start          # camera đứng ở gốc quét (arc_sweep đọc sau khi về thành)
        expected = (base[0] + u, base[1] + v)                         # camera DỰ TÍNH ở ô này
        camera = _camera(bot, screen) or expected
        for boss in seen:                 # ghi các boss thấy ở ô này (toạ độ ước tính) trước khi bấm vào boss làm camera dời
            if boss["name"] is None and not boss.get("partial"):
                continue
            x, y = world_position(camera, boss["pos"])
            if boss["name"] is None:                     # đọc được một phần: chờ bấm xem lại
                if not any(f.get("partial") and math.hypot(f["x"] - x, f["y"] - y) < SAME_BOSS_KM for f in found):
                    found.append({"name": None, "level": boss["level"], "tier": boss["tier"], "tag": boss["tag"], "x": round(x), "y": round(y), "active": boss["active"],
                                  "score": boss["score"], "partial": True, "candidates": boss.get("candidates", [])})
            elif not (only_active and not boss["active"]) and add_boss(found, boss, x, y):
                bot.log(f"boss: {boss['text']} (cấp {boss['level']}) ở khoảng {x:.0f}:{y:.0f}")
        if share:
            before = len(handled)
            handle_screen(bot, handled, only_active, camera_guess=camera)     # chia sẻ hết boss thấy được; chỉ trả về khi không còn boss nào để xử lý
            if seen:                                     # bấm / kéo boss làm camera lệch ô quét: kéo bù về ô dự tính để cả đường quét không bị xê dịch dần
                restore_camera(bot, expected)
            for done in handled[before:]:                # toạ độ thật của boss vừa xử lý thay cho toạ độ ước tính
                near = [f for f in found if f["name"] == done["name"] and f["tier"] == done["tier"] and math.hypot(f["x"] - done["x"], f["y"] - done["y"]) < 3 * SAME_BOSS_KM]
                if near:
                    best = min(near, key=lambda f: math.hypot(f["x"] - done["x"], f["y"] - done["y"]))
                    best.update(x=done["x"], y=done["y"], shared=done["result"])
        return False

    arc_sweep(bot, start_deg, end_deg, radius, on_step=on_step, **sweep)
    return found
