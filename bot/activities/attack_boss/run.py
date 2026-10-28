"""
run.py — Activity "Attack Boss": nhận boss từ một nguồn (sources.py), lọc theo tab, đi tới toạ độ và đánh.

Chạy MỘT MÌNH (activities.EXCLUSIVE_ACTIVITIES): worker gọi thẳng `run(bot, settings)`, hàm này tự lặp tới khi Stop. Việc duy nhất
chen vào là Crazy Eggs (ô chọn giờ ở tab Attack Boss): tới giờ thì đập trứng, rồi quay lại đánh boss.
"""
import math
from datetime import datetime

import cv2
import numpy as np

from ...common import arc_sweep, boss_scan, delay
from ...ocr import read_camera, world_mask
from ...ocr.find_bosses import find_bosses, glow_points, glow_regions, read_popup
from ..event_center.crazy_eggs import constants as eggs
from ..event_center.crazy_eggs.run import _run_crazy_eggs
from ..find_boss.constants import TO_WORLD_TAP, TO_WORLD_TRIES, TO_WORLD_WAIT
from ..join_monster_war import boss_names
from ..join_monster_war.boss_memory import JOINED, BossMemory
from ..join_monster_war.constants import (GENERAL_SEARCH, MARCH, NOT_ENOUGH_STAMINA, PRESET_ACTIVE_WAIT, PRESET_COUNT, PRESET_DX,
                                          PRESET_LOCKED, PRESET_LOCKED_THRESHOLD, PRESET_X0, PRESET_Y, REGIONS)
from ..join_monster_war.run import _Boss, _preset_active, _troops
from .constants import (NAME_GAP, NAME_MAX_H, NAME_MIN_H, NAME_MIN_W, NAME_TAP_ABOVE, AGE_LIMIT_MIN, ATTACK_FROM_WAR, ISCOUT_DONE_MINUTES, ATTACK_MENU_POLL, ATTACK_MENU_WAIT, BOSS_NEAR, BOSS_POLL, BOSS_WAIT, DROP, EGGS_KEY, FULL, FULL_RETRY_WAIT, FULL_TRIES, IDLE_WAIT, RETAP_AFTER, RETAP_MOVE, RING_MAX_DIST, LOW_ODDS, LOW_ODDS_CANCEL, LOW_ODDS_THRESHOLD, MAIN_GENERAL_REGION, MARCH_BUTTON,
                        MARCH_OPEN_WAIT, MARCH_SPEED_KEY, MARCH_THRESHOLD, MARCH_WAIT, MARCHED, NO_LANES_WAIT, ON_SPOT_KM, POLL, POPUP_WAIT,
                        RALLY_BUTTONS, RALLY_MINUTES, RALLY_TITLE, RALLY_WAIT, RETRY, RETURN_SPEED_KEY, SOURCE_ALLIANCE,
                        SOURCE_API, SOURCE_DEFAULT, SOURCE_KEY, SOURCE_PLAYER, TROOP_TRIES, TYPE_ATTACK, TYPE_DEFAULT, TYPE_KEY, TYPE_WAR,
                        VIKING_LABEL)
from . import lanes, speedup, viking
from .goto import goto_coords
from .sources import BossOffer, make_source
from .world import ensure_world


def run(bot, settings: dict):
    """`bot` là BotContext của thiết bị; `settings` là cấu hình của tab "Attack Boss". Không return (tới khi Stop)."""
    if getattr(bot, "attack_memory", None) is None:
        minutes = ISCOUT_DONE_MINUTES if settings.get(SOURCE_KEY) == SOURCE_API else AGE_LIMIT_MIN       # IsCout: boss đã đánh chỉ nhớ tối đa 10 phút
        bot.attack_memory = BossMemory(ttl=minutes * 60)      # sống cùng BotContext: qua các lần Start trong một phiên giả lập
    source = make_source(settings)
    getattr(source, "prepare", lambda _bot: None)(bot)      # IsCout: kiểm tra trình duyệt iScout trước mọi bước khác (Eggs, Viking, ra bản đồ...)
    hours = eggs_hours(settings)
    nearest_first = settings.get(SOURCE_KEY, SOURCE_DEFAULT) == SOURCE_ALLIANCE
    pending: dict[tuple[int, int], BossOffer] = {}    # boss đã nhận mà chưa đánh xong: toạ độ -> boss
    while True:
        if eggs_due(bot, hours):
            _run_crazy_eggs(bot, {"General": {eggs.INTERVAL_KEY: hours}})
            continue
        if viking.summon_due(bot, settings, bot.screenshot()):    # Viking tự gọi (luồng riêng, viking.py): gọi, nhờ giúp, tấn công luôn
            viking.run(bot, settings, lambda b: attack(b, settings, BossOffer(ident=0), own=VIKING_LABEL))
            continue
        if not ensure_world(bot):       # nhận và đánh boss đều cần ở bản đồ thế giới (Crazy Eggs vừa đưa game sang màn khác)
            bot.log("Attack Boss: không ra được bản đồ thế giới, thử lại sau")
            delay(bot, IDLE_WAIT)
            continue
        troops = len(_troops(settings.get("troop")))
        if getattr(source, "needs_home", False):      # IsCout: xếp boss theo khoảng cách tới thành
            home_coords(bot)
        for offer in source.poll(bot):              # nhận boss mới (Alliance: đọc chat; Whisper: tìm tin chưa cắt ảnh)
            if offer.uid is not None:       # IsCout: boss đã nhận dời chỗ thì bỏ toạ độ cũ, dùng toạ độ mới
                for stale in [at for at, old in pending.items() if old.uid == offer.uid and at != offer.coords]:
                    del pending[stale]
            if bot.attack_memory.status(offer.coords) is None:
                pending.setdefault(offer.coords, offer)
        if not pending:
            delay(bot, IDLE_WAIT)
            continue
        offers = list(pending.values())
        if nearest_first:
            offers = order_by_distance(offers, home_coords(bot))
        retry = False
        for offer in offers:
            if not wanted(settings, offer):
                bot.log(f"Attack Boss: bỏ qua {offer}")
                del pending[offer.coords]
                continue
            # Đánh luôn, không chờ đường: hết đường thì _war / _march tự bấm lại 5 phút / March cho tới khi vào được màn March.
            result = attack(bot, settings, offer, getattr(source, "goto", None), latest=getattr(source, "latest", None))
            if result == FULL:        # thấy "không đủ đội quân": có dùng tăng tốc thì tăng tốc ngay rồi đánh lại boss này luôn; (không dùng thì đã bấm lại hết số lần)
                pending[offer.coords] = offer
                speed_up_if_full(bot, settings, troops, force=True)
                break
            if result == RETRY:       # chưa đánh được (không có đội có tướng, hết thể lực...): giữ lại, vòng sau thử lại, KHÔNG bỏ qua
                pending[offer.coords] = offer
                retry = True
            else:
                del pending[offer.coords]
                getattr(source, "finished", lambda _offer: None)(offer)
                if result == MARCHED:
                    bot.attack_memory.mark(offer.coords, JOINED)
                    speed_up_if_full(bot, settings, troops)      # đánh xong mà số đường đã đủ tối đa thì tăng tốc, xong đánh boss mới luôn
            if eggs_due(bot, hours):
                break    # tới giờ đập trứng: các boss còn lại làm sau
        if retry:
            delay(bot, IDLE_WAIT)


def speed_up_if_full(bot, settings: dict, troops: int, force: bool = False) -> None:
    """Có chọn tăng tốc và số đường đã dùng đủ tối đa (lanes.lanes_full) thì tăng tốc mọi đội đang hành quân rồi mọi đội đang trở về (Rallying không xử lý). Chờ 1 giây trước
    cho dòng hành quân vừa gửi hiện ra ở bảng. `force`: game vừa báo "không đủ đội quân" nên tăng tốc luôn, không cần đọc số đường."""
    if not speedup.enabled(settings):
        return
    bot.sleep(1)
    if force or lanes.lanes_full(bot, troops):
        speedup.speed_up_all(bot, speedup.MARCHING, settings.get(MARCH_SPEED_KEY))
        speedup.speed_up_all(bot, speedup.RETURNING, settings.get(RETURN_SPEED_KEY))


def order_by_distance(offers: list[BossOffer], home: tuple[int, int] | None) -> list[BossOffer]:
    """Boss gần thành của mình nhất đánh trước, rồi tới boss xa dần. Chưa biết toạ độ thành (home None) thì giữ nguyên thứ tự."""
    if home is None:
        return list(offers)
    return sorted(offers, key=lambda offer: math.dist(offer.coords, home))


def home_coords(bot) -> tuple[int, int] | None:
    """Toạ độ thành của mình: ra bản đồ thế giới, bấm nút về thành rồi đọc toạ độ camera. Nhớ trên `bot` (thành không đổi chỗ), lần sau không
    phải ra bản đồ nữa. None nếu không ra được bản đồ / không đọc được toạ độ (lần sau thử lại)."""
    if getattr(bot, "attack_home", None) is not None:
        return bot.attack_home
    if not ensure_world(bot):
        return None
    if not arc_sweep.go_home(bot):      # camera đã ở thành thì nút về thành không hiện: đọc toạ độ camera luôn
        bot.log("Attack Boss: không thấy nút về thành, coi như camera đang ở thành")
    home = arc_sweep.valid_camera(read_camera(bot.screenshot()))
    if home is None:
        bot.log("Attack Boss: không đọc được toạ độ thành của mình")
        return None
    bot.attack_home = home
    bot.log(f"Attack Boss: thành của mình ở {home}")
    return home


def eggs_hours(settings: dict) -> int:
    """Số giờ giữa hai lần đập trứng (thiếu key / sai kiểu -> 0 = không làm)."""
    try:
        return max(0, int(settings.get(EGGS_KEY, 0)))
    except (TypeError, ValueError):
        return 0


def eggs_due(bot, hours: int) -> bool:
    """Tới giờ đập trứng chưa: đã bật, hôm nay chưa vỡ đủ 4 quả, và đã qua `hours` giờ kể từ lần thử trước (chưa thử lần nào = tới giờ)."""
    if hours <= 0 or bot.is_daily_done(eggs.DONE_KEY):
        return False
    try:
        since = (datetime.now() - datetime.fromisoformat(bot.done_at(eggs.TRIED_KEY))).total_seconds() / 3600
    except (TypeError, ValueError):
        return True
    return since >= hours


def wanted(settings: dict, offer: BossOffer) -> bool:
    """Có đánh boss này không (boss được gửi: Viking cũng đi theo luồng chung). Whisper: không chọn boss, được gửi boss nào đánh boss đó. Nguồn khác: theo
    boss / cấp đã tích (như Join Monster War). IsCout: bộ lọc do người dùng đặt trên trang iScout nên đánh hết boss trên bảng. Viking TỰ GỌI là việc riêng (summon_due)."""
    if settings.get(SOURCE_KEY) in (SOURCE_PLAYER, SOURCE_API):
        return True
    boss, _ = boss_names.parse(offer.name)
    return boss_names.wanted(boss_names.selection(settings), boss, offer.level)


def attack_type(settings: dict) -> str:
    """Đánh một mình (TYPE_ATTACK) hay lập Alliance War (TYPE_WAR). Boss gửi qua tin nhắn người chơi thì có thể không có Alliance War
    nên luôn đánh một mình; giá trị lạ -> mặc định."""
    if settings.get(SOURCE_KEY) == SOURCE_PLAYER:
        return TYPE_ATTACK
    kind = settings.get(TYPE_KEY, TYPE_DEFAULT)
    return kind if kind in (TYPE_ATTACK, TYPE_WAR) else TYPE_DEFAULT


def attack(bot, settings: dict, offer: BossOffer, go=None, own=None, latest=None) -> str:
    """Tới boss, chờ boss hiện ra, bấm giữa màn hình mở menu -> Attack -> cửa sổ thông tin boss -> Attack / Alliance War (theo
    attack_type) -> màn March: chọn đội rồi March. Trả:
    - MARCHED: đã hành quân;
    - DROP: boss không còn đó (đã chết), không thuộc loại được tích, hoặc game báo tỷ lệ thắng cực thấp (đã Cancel): bỏ hẳn;
    - FULL: game báo hết đường hành quân ("You cannot send more troops."): giữ boss lại, `run` chuyển sang tăng tốc rồi chờ có đường trống;
    - RETRY: chưa đánh được (không đội nào có tướng, hết thể lực, màn không mở...): giữ boss lại đánh sau, KHÔNG bỏ qua.
    Mọi nhánh thất bại đều về bản đồ sạch.

    Tới boss: `go(bot, offer)` (nguồn Whisper: mở Whisper, tìm tin của boss bằng ảnh cắt rồi bấm thẳng vào toạ độ trong tin, nhanh hơn nhập toạ độ) nếu
    nguồn có và làm được; không thì nhập toạ độ ở bản đồ thế giới (goto_coords). Camera đã đứng đúng chỗ thì khỏi di chuyển. Boss luôn nằm giữa màn hình.

    `own`: vị trí nhãn của boss Viking TỰ GỌI (đang ở giữa màn hình): bấm vào đó thay cho giữa màn hình, không tìm boss, không lọc theo ô đã tích, và luôn đánh
    bằng Alliance War vì cửa sổ boss tự gọi chỉ có nút Alliance War.

    `latest(bot, offer)` (IsCout): toạ độ mới nhất của boss theo id ngay trước khi tới; None = boss đã chết, bỏ luôn không đi tới.

    Nguồn IsCout (boss thật có thể lệch khỏi toạ độ): sau khi tới toạ độ, bấm vào vòng boss gần giữa màn hình nhất (không cần đúng giữa); không thấy vòng
    boss nào, hoặc bấm vào mà không ra Attack, thì DROP (tính là đã đánh). Từ cửa sổ thông tin trở đi giống mọi nguồn khác."""
    iscout = settings.get(SOURCE_KEY) == SOURCE_API
    tap_at = boss_scan.CAMERA_PX
    if own is None and latest is not None:       # IsCout: lấy toạ độ mới nhất của boss này ngay trước khi tới (boss lang thang đã rời toạ độ lúc nhận)
        current = latest(bot, offer)
        if current is None:
            bot.log(f"Attack Boss: boss {offer.uid} không còn trên iScout (đã chết), bỏ")
            return DROP
        offer = current
    if own is None:
        if go is not None and go(bot, offer):
            pass
        elif offer.x is None:        # Whisper không đọc toạ độ: tin đã trôi khỏi màn hình / ảnh cắt đã bị thay, không còn cách tới
            bot.log(f"Attack Boss: không tìm lại được tin của boss {offer.ident} trong Whisper, bỏ")
            boss_scan.ensure_map(bot)
            return DROP
        elif not (ensure_world(bot) and _on_spot(bot, offer)) and not goto_coords(bot, offer.x, offer.y):
            bot.log(f"Attack Boss: không nhập được toạ độ {offer.coords}, giữ lại")
            boss_scan.ensure_map(bot)
            return RETRY
        tap_at = _wait_boss(bot, nearest=iscout)
        if tap_at is None:
            bot.log(f"Attack Boss: không thấy boss ở giữa màn hình ({offer}), boss đã chết hoặc đã đi, bỏ")
            boss_scan.ensure_map(bot)
            return DROP
    opened = _tap_attack(bot, own or tap_at) if iscout else boss_scan.tap_menu_item(bot, own or tap_at, boss_scan.ATTACK_ICON)
    if not opened:
        return DROP if iscout else RETRY       # IsCout: bấm vào boss mà không ra Attack = coi như đã đánh
    screen, war = _wait_popup(bot)
    if war is None:
        bot.log(f"Attack Boss: không thấy cửa sổ thông tin boss ({offer}), thử lại sau")
        boss_scan.ensure_map(bot)
        return RETRY
    info = read_popup(screen)       # tên / cấp thật của boss trong cửa sổ; không đọc được thì tin vào tin nhắn
    if own is None and info and not wanted(settings, BossOffer(offer.x, offer.y, info["name"], info["level"])):
        bot.log(f"Attack Boss: boss {info['name']} cấp {info['level']} không được tích, bỏ")
        boss_scan.ensure_map(bot)
        return DROP
    if own is not None or attack_type(settings) == TYPE_WAR:
        marched = _war(bot, settings, war)
        if lanes.consume_full(bot):
            return FULL
        if _consume_low_odds(bot):
            return DROP
        return MARCHED if marched else RETRY
    bot.tap(war[0] + ATTACK_FROM_WAR[0], war[1] + ATTACK_FROM_WAR[1])
    marched = _march(bot, settings, MAIN_GENERAL_REGION)
    if lanes.consume_full(bot):
        return FULL
    if _consume_low_odds(bot):
        return DROP
    return MARCHED if marched else RETRY


def _consume_low_odds(bot) -> bool:
    """`_march` vừa gặp hộp "tỷ lệ thắng cực thấp" (đã Cancel): True một lần, rồi xoá cờ."""
    flagged = getattr(bot, "attack_low_odds", False)
    bot.attack_low_odds = False
    return flagged


def _war(bot, settings: dict, war: tuple[int, int]) -> bool:
    """Bấm nút Alliance War, chọn thời gian chờ rally (RALLY_MINUTES) ở hộp "Alliance War Rally!", rồi màn March của rally: chọn đội có tướng và March.
    Hết đường (game báo "You cannot send more troops." mà hộp vẫn mở): cứ bấm lại thời gian rally (cách FULL_RETRY_WAIT giây, tối đa FULL_TRIES lần) cho tới khi vào được màn March."""
    keep = not speedup.enabled(settings)           # thấy "không đủ đội quân": không dùng tăng tốc thì bấm tiếp; có dùng thì bỏ ra (FULL) để tăng tốc
    bot.tap(*war, delay=0)
    for _ in range(round(RALLY_WAIT / POLL)):
        bot.sleep(POLL)
        if bot.find(RALLY_TITLE, threshold=0.9) is None:
            continue
        for attempt in range(FULL_TRIES if keep else 1):
            if attempt and bot.find(RALLY_TITLE, threshold=0.9) is None:     # hộp đã đóng: không bấm mò lên bản đồ
                break
            bot.tap(*RALLY_BUTTONS[RALLY_MINUTES], delay=0)
            state = _march_or_full(bot)
            if state == MARCH_OPEN:
                return _march(bot, settings, REGIONS[GENERAL_SEARCH])
            if state == FULL:
                lanes.learn(bot)
                if keep:
                    bot.log("Attack Boss: hết đường, bấm lại thời gian rally")
                    bot.sleep(FULL_RETRY_WAIT)
                    continue
            break
        boss_scan.ensure_map(bot)
        return False
    bot.log("Attack Boss: không thấy hộp chọn thời gian rally")
    boss_scan.ensure_map(bot)
    return False


MARCH_OPEN = "march"


def _march_or_full(bot) -> str:
    """Sau khi chọn thời gian rally: chờ tới NO_LANES_WAIT giây thấy thông báo hết đường (FULL) hoặc màn March (MARCH_OPEN; hết giờ mà chưa thấy gì cũng coi như màn March đang mở)."""
    for _ in range(round(NO_LANES_WAIT / POLL)):
        bot.sleep(POLL)
        screen = bot.screenshot()
        if lanes.no_lanes(bot, screen):
            return FULL
        if bot.find(MARCH_BUTTON, screen=screen, region=REGIONS[MARCH], threshold=MARCH_THRESHOLD) is not None:
            break
    return MARCH_OPEN


def _on_spot(bot, offer: BossOffer) -> bool:
    """Camera đang đứng trên toạ độ của boss (lệch không quá ON_SPOT_KM mỗi trục)."""
    camera = arc_sweep.valid_camera(read_camera(bot.screenshot()))
    return camera is not None and abs(camera[0] - offer.x) <= ON_SPOT_KM and abs(camera[1] - offer.y) <= ON_SPOT_KM


def _name_point(screen):
    """IsCout: chọn MỘT vùng cam (vòng sáng) gần giữa màn hình nhất (điểm vòng sáng cách tâm không quá RING_MAX_DIST px, xa hơn là boss khác), rồi chỉ trong vùng đó tìm
    dòng tên boss (chữ be kem, nối huy hiệu cấp và các từ của tên bằng NAME_GAP; không cần đọc ra tên); nhiều dòng thì lấy dòng gần vòng sáng nhất. Điểm bấm = (giữa dòng tên
    theo x, mép trên dòng tên - NAME_TAP_ABOVE), tức cao hơn tên một chút. None nếu không có vùng cam gần tâm hoặc không thấy dòng tên."""
    masked = world_mask.mask_ui(screen)
    points = [point for point in glow_points(screen, masked) if math.dist(point, boss_scan.CAMERA_PX) <= RING_MAX_DIST]
    if not points:
        return None
    glow = min(points, key=lambda point: math.dist(point, boss_scan.CAMERA_PX))      # vòng sáng gần tâm nhất
    region = next((box for box in glow_regions(screen, masked) if box[0] <= glow[0] <= box[2] and box[1] <= glow[1] <= box[3]), None)
    if region is None:
        return None
    x1, y1, x2, y2 = region
    area = masked[y1:y2, x1:x2].astype(np.int16)
    text = (((area[..., 2] > 185) & (area[..., 1] > 150) & (area[..., 2] - area[..., 0] > 20)) * 255).astype(np.uint8)
    merged = cv2.dilate(text, cv2.getStructuringElement(cv2.MORPH_RECT, (NAME_GAP, 1)))
    count, _, stats, _ = cv2.connectedComponentsWithStats(merged, 8)
    names = [(int(x1 + x + w // 2), int(y1 + y)) for x, y, w, h, _ in stats[1:count] if w >= NAME_MIN_W and NAME_MIN_H <= h <= NAME_MAX_H]
    if not names:
        return None
    x, top = min(names, key=lambda name: math.dist(name, glow))
    return x, top - NAME_TAP_ABOVE


def _wait_boss(bot, nearest: bool = False):
    """Chờ tới BOSS_WAIT giây cho boss hiện ra (bản đồ vừa nhảy tới, boss tải chậm hơn nền đất). Tìm mỗi BOSS_POLL (1) giây. Trả vị trí để bấm vào boss, None nếu không thấy.
    Mặc định boss phải nằm trong BOSS_NEAR quanh giữa màn hình và bấm giữa màn hình. `nearest` (IsCout: boss thật có thể lệch khỏi toạ độ nhận được):
    lấy vùng cam (vòng sáng) gần giữa màn hình nhất trong RING_MAX_DIST px, tìm dòng tên boss trong vùng đó và bấm cao hơn tên một chút (`_name_point`). Không thấy tên trong vùng cam thì coi như
    boss đã đánh: hết BOSS_WAIT giây trả None (attack trả DROP)."""
    for _ in range(round(BOSS_WAIT / BOSS_POLL)):
        bot.sleep(BOSS_POLL)
        screen = bot.screenshot()
        if nearest:
            point = _name_point(screen)
            if point is not None:
                return point
            continue
        found = find_bosses(screen)
        if not found:
            continue
        best = min(found, key=lambda boss: math.dist(boss["pos"], boss_scan.CAMERA_PX))
        if math.dist(best["pos"], boss_scan.CAMERA_PX) <= BOSS_NEAR:
            return boss_scan.CAMERA_PX
    return None


def _tap_attack(bot, pos: tuple[int, int], relocate=None) -> bool:
    """IsCout: bấm vào boss rồi tìm nút Attack của menu nhanh mỗi ATTACK_MENU_POLL (1) giây, tối đa ATTACK_MENU_WAIT (8) giây; thấy thì bấm. False nếu
    không thấy (về bản đồ sạch): boss tính là đã đánh. Boss có thể đang di chuyển (Bayard, Kamaitachi): có `relocate(screen)` thì sau RETAP_AFTER lần chưa
    thấy menu, tìm lại vòng màu và bấm vào chỗ mới nếu nó cách chỗ đã bấm hơn RETAP_MOVE px (cùng chỗ thì chỉ chờ tiếp, menu có thể hiện chậm do lag).
    Không dùng boss_scan.tap_menu_item (dùng chung, nhịp 0,3 giây / 5 giây) để không đổi các hoạt động khác."""
    bot.tap(*pos, delay=0)
    tapped, waited = pos, 0
    for _ in range(round(ATTACK_MENU_WAIT / ATTACK_MENU_POLL)):
        bot.sleep(ATTACK_MENU_POLL)
        screen = bot.screenshot()
        found = boss_scan.find_menu_item(bot, screen, boss_scan.ATTACK_ICON)
        if found is not None:
            bot.tap(*found, delay=0)
            return True
        waited += 1
        if relocate is not None and waited >= RETAP_AFTER:
            moved = relocate(screen)
            if moved is not None and math.dist(moved, tapped) > RETAP_MOVE:
                bot.log(f"Attack Boss: boss dời chỗ, bấm lại {moved}")
                bot.tap(*moved, delay=0)
                tapped, waited = moved, 0
    bot.log(f"Attack Boss: không thấy nút Attack sau khi bấm {pos}")
    boss_scan.ensure_map(bot)
    return False


def _wait_popup(bot):
    """Chờ cửa sổ thông tin boss (thấy nút Alliance War): trả (ảnh, vị trí nút) hoặc (ảnh cuối, None)."""
    screen = None
    for _ in range(round(POPUP_WAIT / POLL)):
        bot.sleep(POLL)
        screen = bot.screenshot()
        war = bot.find(boss_scan.POPUP_ICON, threshold=boss_scan.MENU_THRESHOLD, screen=screen)
        if war is not None:
            return screen, war
    return screen, None


def _pick_troop(bot, helper, screen, region) -> int | None:
    """Chọn đội (preset 1-8) CHỈ trong các đội đã tích (từ đội nhỏ nhất, bỏ đội bị khoá), không đụng tới đội khác; xoay vòng qua các đội đã tích tối đa TROOP_TRIES (10) lần thử;
    đội đạt = ô preset sáng lên và ô Main General có tướng (thấy kính lúp). Trả số đội, None nếu không đội đã tích nào có tướng. Bố cục màn March của Attack khác rally: ô tướng chính nằm cao hơn."""
    locked = len(bot.find_all(PRESET_LOCKED, threshold=PRESET_LOCKED_THRESHOLD, screen=screen, region=REGIONS[PRESET_LOCKED]))
    unlocked = range(1, PRESET_COUNT - locked + 1)
    chosen = [t for t in helper.troops if t in unlocked]
    candidates = chosen          # chỉ các đội người dùng đã tích
    for attempt in range(TROOP_TRIES if candidates else 0):      # xoay vòng qua các đội, tối đa TROOP_TRIES lần thử
        troop = candidates[attempt % len(candidates)]
        bot.tap_percent(PRESET_X0 + (troop - 1) * PRESET_DX, PRESET_Y)
        _, active = helper._poll_screen(f"attack_activate_troop_{troop}", lambda image: _preset_active(image, troop),
                                        timeout=PRESET_ACTIVE_WAIT, interval=1)
        if not active:
            bot.log(f"Attack Boss: bấm đội {troop} mà ô không sáng, thử lại")
            continue
        _, general = helper._poll_screen(f"attack_troop_{troop}_general", lambda image: bot.find(GENERAL_SEARCH, screen=image, region=region))
        if general is not None:
            bot.log(f"Attack Boss: chọn đội {troop}")
            return troop
        bot.log(f"Attack Boss: đội {troop} không có tướng")
    return None


def _march(bot, settings: dict, region) -> bool:
    """Màn March: BẮT BUỘC chọn được đội quân có tướng chính (đội không có tướng thì thử đội khác; tích Select General thì chọn tướng cho đội;
    vẫn không có thì Back, không hành quân). Tướng phụ không bắt buộc (không chọn). Xong bấm March; thành công khi về bản đồ sạch."""
    if getattr(bot, "boss_memory", None) is None:
        bot.boss_memory = BossMemory()     # _Boss cần, Attack Boss không dùng
    helper = _Boss(bot, settings)      # dùng lại phần chọn đội / tướng của Join Monster War
    screen = None
    for _ in range(round(MARCH_OPEN_WAIT / POLL)):      # màn March mở mất ~2-3 giây sau khi bấm Attack
        bot.sleep(POLL)
        screen = bot.screenshot()
        if bot.find(MARCH_BUTTON, screen=screen, region=REGIONS[MARCH], threshold=MARCH_THRESHOLD) is not None:
            break
    else:
        bot.log("Attack Boss: không thấy màn March sau khi bấm đánh")
        boss_scan.ensure_map(bot)
        return False
    if _pick_troop(bot, helper, screen, region) is None:
        bot.record("Attack Boss: không có đội quân nào có tướng, không hành quân")
        bot.back()
        return False
    pos = bot.find(MARCH_BUTTON, region=REGIONS[MARCH], threshold=MARCH_THRESHOLD)
    if pos is None:
        bot.back()
        return False
    keep = not speedup.enabled(settings)           # thấy "không đủ đội quân": không dùng tăng tốc thì bấm lại March; có dùng thì bỏ ra (FULL) để tăng tốc
    for _ in range(FULL_TRIES if keep else 1):
        bot.tap(*pos)
        full = False
        for _ in range(round(MARCH_WAIT / POLL)):
            bot.sleep(POLL)
            shot = bot.screenshot()
            if lanes.no_lanes(bot, shot):          # hết đường: học số đường tối đa
                lanes.learn(bot)
                full = True
                break
            odds = bot.find(LOW_ODDS, screen=shot, threshold=LOW_ODDS_THRESHOLD)
            if odds is not None:                   # "tỷ lệ thắng cực thấp, vẫn gửi quân?": không gửi, bấm Cancel; boss này tính là đã đánh (attack trả DROP)
                bot.record("Attack Boss: tỷ lệ thắng cực thấp, không gửi quân, tính là đã đánh")
                bot.tap(odds[0] + LOW_ODDS_CANCEL[0], odds[1] + LOW_ODDS_CANCEL[1])
                bot.attack_low_odds = True
                boss_scan.ensure_map(bot)
                return False
            if bot.find(NOT_ENOUGH_STAMINA, screen=shot) is not None:
                # TODO: dùng vật phẩm thể lực (helper._use_stamina gắn với vòng lặp Join Boss), tạm bỏ qua boss này.
                bot.record("Attack Boss: hết thể lực, chưa xử lý")
                boss_scan.ensure_map(bot)
                return False
            if boss_scan.on_map(bot, shot):
                return True
        if not full or bot.find(MARCH_BUTTON, region=REGIONS[MARCH], threshold=MARCH_THRESHOLD) is None:
            break                                  # không phải hết đường, hoặc màn March đã đóng: không bấm mò
        bot.log("Attack Boss: hết đường, bấm lại March")
        bot.sleep(FULL_RETRY_WAIT)
    boss_scan.ensure_map(bot)
    return False
