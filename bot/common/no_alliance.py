"""
no_alliance.py — tài khoản chưa có liên minh: bấm nút Liên minh chỉ ra màn "Benefits of being in an Alliance" (Create / Join).
Nhận ra màn đó thì nhớ lại theo thiết bị tới khi app chạy lại (biến module, không lưu DB); mọi việc liên minh bị bỏ qua:
worker lọc nhiệm vụ `needs_alliance` (priority.py), các vòng điều hướng Liên minh gọi check() mỗi bước.
"""
NO_ALLIANCE_IMAGE = "Alliance/NoAlliance.png"   # tiêu đề "Benefits of being in an Alliance"
THRESHOLD = 0.85

_serials: set[str] = set()


ALLIANCE_MENU_IMAGE = "JoinBoss/chientranh.png"  # dòng Alliance War: có trong menu Liên minh của tài khoản có liên minh
WAIT_TRIES = 8                                    # chờ màn Liên minh hiện: 1 giây một lần, tối đa 8 lần
WAIT_INTERVAL = 1


def wait_menu(bot) -> bool:
    """Gọi ngay sau khi bấm nút Liên minh: chờ tới khi thấy menu Liên minh hoặc màn "chưa có liên minh" (WAIT_TRIES lần, mỗi lần
    WAIT_INTERVAL giây). True = chưa có liên minh (đã nhớ + Back ra, nơi gọi bỏ việc); False = vào được menu, hoặc hết giờ chờ
    mà chưa thấy màn nào (vòng điều hướng tự xử lý tiếp)."""
    for _ in range(WAIT_TRIES):
        bot.sleep(WAIT_INTERVAL)
        screen = bot.screenshot()
        if check(bot, screen):
            return True
        if bot.find(ALLIANCE_MENU_IMAGE, screen=screen) is not None:
            return False
    return False


def known(bot) -> bool:
    """Thiết bị này đã biết là không có liên minh (từ lần mở Liên minh trước, kể cả lần Start trước)."""
    return bot.serial in _serials


def check(bot, screen) -> bool:
    """`screen` đang là màn "chưa có liên minh"? Đúng thì nhớ lại, Back ra khỏi màn đó và trả True: nơi gọi bỏ việc liên minh."""
    if bot.serial not in _serials:
        if bot.find(NO_ALLIANCE_IMAGE, threshold=THRESHOLD, screen=screen) is None:
            return False
        _serials.add(bot.serial)
        bot.record("Tài khoản chưa có liên minh: bỏ qua các việc liên minh cho tới khi chạy lại app")
    elif bot.find(NO_ALLIANCE_IMAGE, threshold=THRESHOLD, screen=screen) is None:
        return False
    bot.back(delay=1)
    return True
