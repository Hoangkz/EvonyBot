"""
no_gems.py — popup "My Liege, you have insufficient Gems. Shall we obtain more?" (nút Cancel đỏ + Buy xanh).

Nhiệm vụ tốn kim cương thấy popup này thì dừng (không Buy): shown() nhận ra, dismiss() bấm Back (= Cancel) và ghi
lịch sử. Nhận ra bằng nút Buy xanh VÀ nút Cancel đỏ bên trái nó, để không nhầm với nút "Buy" ở cửa hàng.
"""
BUY = "Science/buyKc.png"        # nút Buy của popup (cũng là Black Market/buyKc.png): 0,98 trên màn thật
THRESHOLD = 0.9
REGION = (40, 45, 90, 75)        # vùng nút Buy (% màn hình 396x704): tâm (262, 416)
CANCEL_DX = -130                 # tâm nút Cancel (133, 415) cách tâm nút Buy (px)
CANCEL_HALF = (30, 8)            # nửa rộng / cao vùng lấy mẫu màu ở nút Cancel
CANCEL_RED = 30                  # nút Cancel đỏ: R - G trung bình > ngưỡng (ảnh thật ~56 do chữ trắng; không có popup < 0)


def shown(bot, screen=None) -> bool:
    """Màn hình đang có popup không đủ kim cương."""
    screen = bot.screenshot() if screen is None else screen
    buy = bot.find(BUY, threshold=THRESHOLD, screen=screen, region=REGION)
    if buy is None:
        return False
    x, y = buy[0] + CANCEL_DX, buy[1]
    hw, hh = CANCEL_HALF
    box = screen[max(0, y - hh):y + hh, max(0, x - hw):x + hw].astype(int)
    if box.size == 0:
        return False
    return float((box[..., 2] - box[..., 1]).mean()) > CANCEL_RED


OUT_OF_GEMS_FLAG = "_out_of_gems"   # cờ trên ctx: nhiệm vụ vừa chạy gặp thiếu kim cương -> worker loại nó khỏi danh sách


def flag(bot):
    """Báo cho worker: nhiệm vụ đang chạy hết kim cương (popup Buy / nút xám / Cost đỏ). Worker đọc bằng take() sau khi
    nhiệm vụ trả về rồi loại nhiệm vụ khỏi danh sách (không lưu DB; Start lại hoặc sang ngày mới thì kiểm tra lại)."""
    setattr(bot, OUT_OF_GEMS_FLAG, True)


def take(bot) -> bool:
    """Đọc rồi xoá cờ flag(). Worker gọi trước khi chạy nhiệm vụ (bỏ cờ cũ) và sau khi chạy xong."""
    value = getattr(bot, OUT_OF_GEMS_FLAG, False) is True
    setattr(bot, OUT_OF_GEMS_FLAG, False)
    return value


def dismiss(bot, name: str):
    """Đóng popup (Back = Cancel, không Buy), ghi lịch sử và đặt cờ thiếu kim cương cho worker."""
    flag(bot)
    bot.record(f"{name}: not enough gems (buy-gems popup), cancel")
    bot.back(delay=1)


class OutOfGems(Exception):
    """Vòng mua đang chạy thì hiện popup không đủ kim cương (đã Back đóng popup, không Buy)."""


def check(bot, screen, name: str):
    """Thấy popup không đủ kim cương -> đóng (Back) rồi ném OutOfGems để vòng mua dừng."""
    if shown(bot, screen):
        dismiss(bot, name)
        raise OutOfGems()
