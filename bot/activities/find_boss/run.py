"""
run.py — "Find Boss" activity: về chỗ camera ở thành, quét quạt (góc, bán kính ở tab) bằng boss_scan.scan_bosses — kéo bản đồ (arc_sweep),
nhận boss (find_bosses), chia sẻ boss đang tích vào liên minh (nếu tích "Share") — xong thì về toạ độ của mình (arc_sweep) và quét tiếp khi còn rảnh. Xem FLOW.md.
"""
from ...common import delay, go_home
from ...ocr.find_bosses import set_selection
from ..result import save_errors
from .constants import (BOSSES_KEY, END_DEFAULT, EXCLUDED_BOSSES, END_KEY, KEY, RADIUS_DEFAULT, RADIUS_KEY, SHARE_DEFAULT, SHARE_KEY, START_DEFAULT,
                        START_KEY, TO_WORLD_TAP, TO_WORLD_TRIES, TO_WORLD_WAIT)


HOME_ICON = "CityMap/worldHome.png"   # = arc_sweep.HOME_ICON (nút về thành ở bản đồ thế giới); không import arc_sweep ở đây: bot.activities được nạp trước bot.city nên sẽ vòng tròn


def ensure_map(bot) -> bool:
    from ...common.boss_scan import ensure_map as real
    return real(bot)


def scan_bosses(bot, *args, **kwargs):
    from ...common.boss_scan import scan_bosses as real
    return real(bot, *args, **kwargs)


def _selected(settings: dict) -> list[dict]:
    """Boss được tích (không có Viking)."""
    return [boss for boss in settings.get(BOSSES_KEY, []) if boss.get("name") not in EXCLUDED_BOSSES]


def to_world(bot) -> bool:
    """Đưa game ra bản đồ thế giới (thấy nút về thành worldHome). Đang ở thành thì bấm nút góc dưới phải; lỗi màn lạ thì go_home. False nếu không ra được."""
    for _ in range(TO_WORLD_TRIES):
        screen = bot.screenshot()
        if bot.find(HOME_ICON, threshold=0.8, screen=screen) is not None:
            return True
        bot.tap_percent(*TO_WORLD_TAP, delay=TO_WORLD_WAIT)
        if bot.find(HOME_ICON, threshold=0.8) is None:
            go_home(bot, bot.screenshot())      # không ra được thế giới: có thể đang ở màn lạ
            delay(bot, 2)
    return bot.find(HOME_ICON, threshold=0.8) is not None


@save_errors(KEY)   # lỗi thì lưu `find_boss_error` vào DB
def run(bot, settings: dict):
    """`bot` is the device's BotContext; `settings` is the "Find Boss" tab's config. Một lần chạy = một vòng quét."""
    start = float(settings.get(START_KEY, START_DEFAULT))
    end = float(settings.get(END_KEY, END_DEFAULT))
    radius = float(settings.get(RADIUS_KEY, RADIUS_DEFAULT))
    share = bool(settings.get(SHARE_KEY, SHARE_DEFAULT))
    selected = _selected(settings)
    if not selected:
        bot.log("Find Boss: chưa tích boss nào, bỏ qua")
        return
    set_selection(selected)              # chỉ boss được tích tính là "active" cho nhận diện / chia sẻ (theo luồng của máy này)
    bot.log(f"Find Boss: quét {start:g}° -> {end:g}°, bán kính {radius:g} km{', chia sẻ liên minh' if share else ''}")
    if not to_world(bot) or not ensure_map(bot):
        bot.log("Find Boss: không ra được bản đồ thế giới, lượt sau thử lại")
        return
    watch = getattr(bot, "swipe_watch", None)
    if watch is not None:
        watch(bot)                       # ghi số boss ban đầu (như scan_city): boss mới tới trong lúc quét làm số này tăng
    bot.swipe_recover = lambda b: ensure_map(b) and to_world(b) and ensure_map(b)   # sau Join Boss giữa chừng: Back (chỉ khi có popup) về bản đồ thế giới, không bấm về thành
    try:
        found = scan_bosses(bot, start, end, radius, share=share)
    finally:
        bot.swipe_recover = None
    shared = sum(1 for boss in found if boss.get("shared") == "shared")
    bot.record(f"Find Boss: thấy {len(found)} boss (chia sẻ {shared})")
    for boss in found:
        bot.log(f"Find Boss: {boss['name'] or '?'} cấp {boss['level']} ở {boss['x']}:{boss['y']}")
    # arc_sweep đã bấm nút về toạ độ của mình khi quét xong; ở lại bản đồ thế giới để vòng sau quét tiếp ngay (nhiệm vụ khác tự về thành: go_home / to_city).


# Dòng cho bot/worker/priority.py: chỉ cần tích ít nhất một boss. Mỗi lần chạy là MỘT vòng quét (arc_sweep xong thì bấm nút về thành / toạ độ của mình);
# worker chạy nhiệm vụ idle_only liên tục khi rảnh nên quét xong là quét tiếp, và mỗi vòng worker xét lại xem có nhiệm vụ khác tới lượt chưa.
JOB = {"run": run, "enabled": lambda settings: bool(_selected(settings))}
