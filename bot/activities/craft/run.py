"""
run.py — "Craft" activity: chế tạo các trang bị đã tích ở tab Craft (settings {"items": {id: số lượng}}).

Chỉ làm MỘT lần (mỗi lần Start), độ ưu tiên thấp nhất: worker chỉ tới nó khi mọi nhiệm vụ khác đã làm xong (dòng "Craft" ở
bot/worker/priority.py: priority 0, once). Chưa tích trang bị nào thì nhiệm vụ không vào danh sách.
"""
from .constants import ITEMS_KEY


def selected(settings: dict) -> dict[str, int]:
    """{id trang bị: số lượng} của các trang bị đã tích."""
    return {item_id: int(qty) for item_id, qty in (settings.get(ITEMS_KEY) or {}).items() if int(qty) > 0}


def run(bot, settings: dict):
    """`bot` is the device's BotContext; `settings` is the "Craft" tab's config."""
    items = selected(settings)
    bot.log(f"Craft: {len(items)} trang bị đã tích ({sum(items.values())} cái)")
    # TODO: luồng chế tạo thật (vào màn Craft, chọn nhóm, tìm icon, bỏ qua ô có Craft/lock.png, bấm chế tạo đủ số lượng).
    bot.log("Craft: chưa có luồng chế tạo, bỏ qua")


# Dòng cho bot/worker/priority.py: chỉ cần tích ít nhất một trang bị.
JOB = {"run": run, "enabled": lambda settings: bool(selected(settings))}
