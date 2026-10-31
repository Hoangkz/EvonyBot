"""
world.py — đưa game ra bản đồ thế giới sạch (dùng chung run.py và sources.py).
"""
from ...common import arc_sweep, boss_scan
from ..find_boss.constants import TO_WORLD_TAP
from ..event_center.viking_summon.constants import DEFEATED_TEXT
from .constants import DEFEATED_ATTR, BACK_ARROW, BACK_ARROW_THRESHOLD, TO_CITY, WORLD_POLL, WORLD_TRIES, WORLD_WAIT


def on_world(bot, screen) -> bool:
    """Đang ở bản đồ thế giới: thấy nút về thành (chỉ hiện khi camera xa thành) hoặc nút chuyển về thành ở góc dưới phải (luôn hiện; ở thành
    nút đó là hình bản đồ)."""
    return (bot.find(arc_sweep.HOME_ICON, threshold=0.8, screen=screen) is not None
            or bot.find(TO_CITY, threshold=0.8, screen=screen) is not None)


def ensure_world(bot) -> bool:
    """Đưa game ra bản đồ thế giới sạch. Màn toàn màn hình (chat, cuộc trò chuyện...: có mũi tên quay lại ở góc trên trái) thì Back; popup làm tối giao
    diện thì Back (boss_scan.ensure_map); ở thành thì bấm nút góc dưới phải. Đã ở bản đồ thì không bấm gì. False nếu không ra được."""
    for _ in range(WORLD_TRIES):
        screen = bot.screenshot()
        if bot.find(BACK_ARROW, threshold=BACK_ARROW_THRESHOLD, screen=screen) is not None:
            bot.back(delay=1)
            continue
        if not boss_scan.on_map(bot, screen):
            if bot.find(DEFEATED_TEXT, screen=screen) is not None:      # popup "boss Viking đã bị hạ" (có chữ Summon): ghi nhớ trước khi Back đóng nó
                setattr(bot, DEFEATED_ATTR, True)
            boss_scan.ensure_map(bot)
            continue
        if on_world(bot, screen):
            return True
        bot.tap_percent(*TO_WORLD_TAP)
        for _ in range(round(WORLD_WAIT / WORLD_POLL)):      # game chuyển từ thành ra bản đồ mất vài giây: chờ tới WORLD_WAIT giây, thấy bản đồ là đi tiếp
            bot.sleep(WORLD_POLL)
            screen = bot.screenshot()
            if boss_scan.on_map(bot, screen) and on_world(bot, screen):
                return True
    return False
