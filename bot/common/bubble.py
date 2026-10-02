"""
bubble.py — bubble (khiên / Truce Agreement) của thành.

keep_bubble() làm cả hai việc trong một lần vào game:
1. Màn hình chính: bấm icon buff (Bubble/1.png) -> màn City Buff.
2. City Buff: dòng Truce Agreement có thanh thời gian -> OCR. Còn hơn
   `renew_before` giây thì xong (không dùng). Không có thời gian / còn ít
   hơn thì bấm icon Truce -> màn Use Item.
3. Use Item: 4 loại xếp từ bé đến lớn (8h, 24h, 3d, 7d); bấm nút bên phải
   loại đã chọn (Use, hoặc giá kim cương nếu hết đồ).
4. Popup Confirm (tối đa 2: thay bubble đang có, rồi dùng / mua) -> Confirm.
5. Quay lại Use Item: đọc "Remaining Time" mới, lưu, thoát ra.
Không đủ kim cương để mua -> ném NotEnoughGems (worker bỏ tích Bubble).
"""
from ..context.templates import TEMPLATE_DIR
from ..ocr.read_bubble_time import ink as has_text
from ..ocr.read_bubble_time import run as read_bubble_time
from .click_images import click_images
from .delay import delay
from .exit_images import exit_images
from .find_first import find_first
from .go_home import go_home

# Thời lượng mỗi loại bubble (giây), khớp ô select ở tab Initialization.
BUBBLE_DURATIONS = {
    "8h": 8 * 3600,
    "24h": 24 * 3600,
    "3d": 3 * 86400,
    "7d": 7 * 86400,
}

BUFF_ICON = "Bubble/1.png"      # icon buff dưới avatar ở màn hình chính
TRUCE = "Bubble/truce.png"      # icon Truce Agreement ở màn City Buff
USE_ITEM = "Bubble/useItem.png" # tiêu đề "Use Item"
CONFIRM = "Bubble/confirm.png"  # nút Confirm của popup thay / dùng / mua bubble
# Màn báo không đủ kim cương. Chưa có ảnh: khi thêm file này vào Images/ thì
# bot tự nhận ra (xem _targets).
NO_GEMS = "Bubble/noGems.png"
# Tiêu đề từng loại ở màn Use Item -> (ảnh, khoảng cách từ góc trên-trái tiêu đề
# tới giữa nút Use / kim cương cùng dòng). Tiêu đề "Hour" xuống 2 dòng nên nút thấp hơn.
TYPE_ROWS = {
    "8h": ("Bubble/8h.png", (227, 46)),
    "24h": ("Bubble/24h.png", (227, 46)),
    "3d": ("Bubble/3d.png", (227, 38)),
    "7d": ("Bubble/7d.png", (227, 38)),
}
# Thanh thời gian so với góc trên-trái của ảnh mốc: (dx, dy, w, h).
CITY_BUFF_BAR = (80, 40, 221, 26)     # bên phải icon Truce
USE_ITEM_BAR = (-140, 50, 366, 36)    # dưới tiêu đề Use Item, gồm chữ "Remaining Time:"

OPEN_BUFF = "open_buff"
CITY_BUFF = "city_buff"
USE = "use_item"
CONFIRMED = "confirm"
NOT_ENOUGH = "no_gems"
TAP = "tap"
BACK = "back"
MAX_ROUNDS = 40       # số vòng tối đa trước khi bỏ cuộc (worker thử lại sau)
MAX_CONFIRMS = 3      # bình thường tối đa 2 popup; hơn nữa là có gì đó lạ
READ_RETRIES = 3      # số lần đọc lại thời gian sau khi dùng

# Icon buff khớp ~0.91, vị trí khác <= 0.56. Icon Truce khớp 0.90 với icon
# 8h ở Use Item; "3 Day" / "7 Day" khớp chéo nhau ~0.90 -> ngưỡng 0.95.
REGIONS = {BUFF_ICON: (0, 5, 15, 20)}
THRESHOLDS = {BUFF_ICON: 0.8, TRUCE: 0.95}
TYPE_THRESHOLD = 0.95


class NotEnoughGems(Exception):
    """Phải mua bubble bằng kim cương mà không đủ."""


def _targets() -> list[tuple[str, str]]:
    """(ảnh, action); ảnh đứng trước được ưu tiên hơn. Popup Confirm trước
    hết: màn dưới popup bị tối đi nhưng tiêu đề Use Item vẫn khớp."""
    return [
        *([(NO_GEMS, NOT_ENOUGH)] if (TEMPLATE_DIR / NO_GEMS).exists() else []),
        (CONFIRM, CONFIRMED),
        (USE_ITEM, USE),
        (TRUCE, CITY_BUFF),
        *[(path, BACK) for path in exit_images()],
        *[(path, TAP) for path in click_images()],
        (BUFF_ICON, OPEN_BUFF),
    ]


def _read(bot, screen, anchor, bar) -> int | None:
    dx, dy, w, h = bar
    return read_bubble_time(bot.crop(screen, anchor[0] + dx, anchor[1] + dy, w, h))


def _city_buff_time(bot, screen, anchor) -> int | None:
    """Thời gian ở dòng Truce Agreement: 0 nếu không có thanh thời gian, None
    nếu có mà đọc không được."""
    dx, dy, w, h = CITY_BUFF_BAR
    crop = bot.crop(screen, anchor[0] + dx, anchor[1] + dy, w, h)
    if not has_text(crop):
        return 0
    return read_bubble_time(crop)


def _leave(bot, count: int):
    """BACK `count` lần để về màn hình chính."""
    for _ in range(count):
        bot.back()
        delay(bot, 1)


def keep_bubble(bot, bubble_type: str, renew_before: int) -> int | None:
    """Đảm bảo có bubble: đọc thời gian còn lại; còn <= `renew_before` giây (hoặc
    không có) thì dùng bubble loại `bubble_type`. Trả về số giây còn lại sau
    cùng (0 = không có bubble), None nếu không đọc được."""
    image, offset = TYPE_ROWS[bubble_type]
    targets = _targets()
    top_left = {USE, CITY_BUFF}
    renewing = False        # City Buff đã quyết định phải dùng bubble mới
    confirms = 0
    reads = 0
    known = None            # thời gian đọc được gần nhất
    screen = bot.screenshot()
    for _ in range(MAX_ROUNDS):
        action, pos = find_first(bot, screen, targets, top_left=top_left,
                                 regions=REGIONS, thresholds=THRESHOLDS)
        if action == NOT_ENOUGH:
            bot.log(f"Bubble: không đủ kim cương để mua {bubble_type}")
            _leave(bot, 3)      # đóng thông báo, rồi Use Item -> City Buff -> màn hình chính
            raise NotEnoughGems()
        if action == CONFIRMED:
            confirms += 1
            if confirms > MAX_CONFIRMS:
                bot.record("Bubble: quá nhiều popup Confirm, dừng")
                return known
            bot.tap(*pos)
            delay(bot, 2)
        elif action == USE:
            if not renewing:
                # Tới Use Item mà chưa xem City Buff -> lùi lại để đọc thời gian trước.
                bot.back()
                delay(bot, 1)
            elif confirms:
                # Đã dùng: đọc thời gian mới.
                remaining = _read(bot, screen, pos, USE_ITEM_BAR)
                if remaining is not None and remaining > renew_before:
                    bot.record(f"Bubble: đã dùng {bubble_type}, còn {remaining} giây")
                    _leave(bot, 2)
                    return remaining
                reads += 1
                if reads >= READ_RETRIES:
                    # Không đọc được thời gian mới: tính theo loại vừa dùng.
                    bot.record(f"Bubble: đã dùng {bubble_type}, không đọc được thời gian mới")
                    _leave(bot, 2)
                    return BUBBLE_DURATIONS[bubble_type]
                delay(bot, 1)
            else:
                row = bot.find(image, threshold=TYPE_THRESHOLD, screen=screen, center=False)
                if row is None:
                    bot.record(f"Bubble: không thấy dòng {bubble_type} ở Use Item")
                    _leave(bot, 2)
                    return known
                bot.tap(row[0] + offset[0], row[1] + offset[1])
                delay(bot, 2)
        elif action == CITY_BUFF:
            remaining = _city_buff_time(bot, screen, pos)
            if remaining is None:
                bot.record("Bubble: không đọc được thời gian ở City Buff")
                _leave(bot, 1)
                return None
            known = remaining
            if remaining > renew_before and not confirms:
                bot.log(f"Bubble: còn {remaining} giây, chưa cần dùng")
                _leave(bot, 1)
                return remaining
            if confirms:
                # Đã dùng xong mà lại về City Buff: thời gian ở đây là thời gian mới.
                _leave(bot, 1)
                return remaining
            renewing = True
            w, h = bot.template_size(TRUCE)
            bot.tap(pos[0] + w // 2, pos[1] + h // 2)
            delay(bot, 2)
        elif action == TAP:
            bot.tap(*pos)
            delay(bot, 2)
        elif action == BACK:
            bot.back()
            delay(bot, 1)
        elif action == OPEN_BUFF:
            bot.tap(*pos)
            delay(bot, 2)
        else:
            # Không thấy ảnh nào -> về màn hình chính.
            go_home(bot, screen)
            delay(bot, 0.3)
        screen = bot.screenshot()
    bot.record("Bubble: quá số vòng, dừng")
    return known
