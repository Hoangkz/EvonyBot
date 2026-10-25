"""Tìm nút vào Super Value Return trên màn thành chính (có nút •••). Xét lần lượt, gặp trường hợp nào trước thì dùng luôn:

TH1. Icon Login Gifts ở góc trên bên phải (LOGIN_TOP, vùng TOP_RIGHT): chính là nút vào.
TH2. Một icon trong thư mục LAUNCHER_DIR ở vùng LAUNCHER_REGION: chính là nút vào; bấm vào tâm chỗ khớp. Nhiều chỗ khớp (một
     hay nhiều icon) thì lấy chỗ có x bé nhất. Ảnh mẫu chỉ là vùng nhỏ trong icon: không có chữ dưới icon, không chạm chấm đỏ
     (cắt thêm thì thả vào thư mục).
TH3. Mũi tên đi lên (ARROW_UP, vùng ARROW_UP_REGION): nút ngay dưới mũi tên (thấp hơn BELOW_ARROW px) là nút vào.
TH4. Mũi tên đi xuống (ARROW_DOWN, vùng ARROW_DOWN_REGION; hàng nút phụ đang mở nên mũi tên nằm cao hơn): bấm vào, nghỉ 1s để
     nó thành mũi tên đi lên, rồi xét lại TH3.
TH5. Nút Valuable Event (find_valuable_event): nút vào nằm cùng hàng, lấy y của icon Valuable Event, x = VALUABLE_ROW_X.

Toạ độ / vùng đo trên màn 396x704 (ảnh tests/event/gather_troops/cultivate_generals/screens/01_main_login_gift.png,
tests/gift_claims/screens/super_value_return_arrow_up.png, super_value_return_arrow_down.png).
"""
from ....context.templates import TEMPLATE_DIR
from ....ocr.find_valuable_event import find_valuable_event
from ..common import REFERENCE_WIDTH, ROOT, find, find_all

LOGIN_TOP = "SuperValueReturn/login_gifts_top"   # nửa dưới icon + chữ "Login Gifts" (bỏ chấm đỏ góc trên)
TOP_RIGHT = (70, 10, 100, 50)                     # % màn: TH1
LAUNCHER_DIR = "SuperValueReturn/launcher_icons" # TH2: danh sách icon (mọi *.png trong thư mục)
LAUNCHER_REGION = (0, 70, 50, 88)                 # % màn: TH2
ARROW_UP = "SuperValueReturn/arrow_up"
ARROW_UP_REGION = (0, 70, 30, 88)                 # % màn: TH3 (mũi tên lên ở y ~515 / 704)
ARROW_DOWN = "SuperValueReturn/arrow_down"
ARROW_DOWN_REGION = (0, 55, 30, 80)               # % màn: TH4 (mũi tên xuống ở y ~456 / 704, cao hơn mũi tên lên một hàng nút)
BELOW_ARROW = 40                                  # px: TH3 tâm nút vào thấp hơn tâm mũi tên lên chừng này
VALUABLE_ROW_X = 40                               # px: TH5 x của nút vào
VALUABLE_ICON_ABOVE = 30                          # px: find_valuable_event trả về tâm chữ "Event", icon cao hơn chừng này
THRESHOLD = 0.8
# TH2: icon thật khớp 1.0; mẫu cắt nhỏ trong icon nên chỗ khác cũng khớp được tới 0.72 (login_gifts gần mũi tên trên màn
# Hall of Historic Generals).
LAUNCHER_THRESHOLD = 0.85
ARROW_SETTLE = 1.0                                # giây nghỉ sau khi bấm mũi tên xuống


def _launchers() -> list[str]:
    """Tên các icon TH2 (đọc lại thư mục mỗi lần: ảnh mới thả vào dùng được ngay)."""
    return [f"{LAUNCHER_DIR}/{path.stem}" for path in sorted((TEMPLATE_DIR / ROOT / LAUNCHER_DIR).glob("*.png"))]


def find_super_value_return(bot) -> "tuple[int, int] | None":
    """Toạ độ bấm để vào Super Value Return trên màn thành chính, hoặc None. Có thể bấm mũi tên xuống (TH4) trước khi trả về."""
    screen = bot.screenshot()
    scale = screen.shape[1] / REFERENCE_WIDTH

    pos = find(bot, LOGIN_TOP, screen, threshold=THRESHOLD, region=TOP_RIGHT)
    if pos is not None:
        bot.record(f"Gift Claims: Super Value Return - TH1 icon Login Gifts góc trên phải tại {pos}")
        return pos

    icons = [(pos, name) for name in _launchers()
             for pos in find_all(bot, name, screen, threshold=LAUNCHER_THRESHOLD, region=LAUNCHER_REGION)]
    if icons:
        pos, name = min(icons, key=lambda item: item[0][0])
        bot.record(f"Gift Claims: Super Value Return - TH2 icon {name} tại {pos}")
        return pos

    for check in range(2):   # lần 2: sau khi đã bấm mũi tên xuống (TH4)
        up = find(bot, ARROW_UP, screen, threshold=THRESHOLD, region=ARROW_UP_REGION)
        if up is not None:
            target = (up[0], up[1] + round(BELOW_ARROW * scale))
            bot.record(f"Gift Claims: Super Value Return - TH3 nút dưới mũi tên lên tại {target}")
            return target
        if check:
            break
        down = find(bot, ARROW_DOWN, screen, threshold=THRESHOLD, region=ARROW_DOWN_REGION)
        if down is None:
            break
        bot.record(f"Gift Claims: Super Value Return - TH4 bấm mũi tên xuống tại {down}")
        bot.tap(*down)
        bot.sleep(ARROW_SETTLE)
        screen = bot.screenshot()

    valuable = find_valuable_event(screen)
    if valuable is not None:
        target = (round(VALUABLE_ROW_X * scale), max(0, valuable[1] - round(VALUABLE_ICON_ABOVE * scale)))
        bot.record(f"Gift Claims: Super Value Return - TH5 cùng hàng Valuable Event tại {target}")
        return target
    bot.record("Gift Claims: không tìm thấy nút vào Super Value Return")
    return None
