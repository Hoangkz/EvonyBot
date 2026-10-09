"""
constants.py — event 3 ngày (Event Center, tab Limited): ảnh, toạ độ, ngưỡng, action.

Toạ độ đo trên màn 396x704. Ảnh mẫu cắt từ ảnh chụp "Precious Vegetation" (tests/event_center/three_day).
"""
from pathlib import Path

from ....common import images_in
from ....context.templates import TEMPLATE_DIR
from ..constants import EC

FOLDER = f"{EC}/ThreeDay"

# Icon event trong danh sách tab Limited: MỖI event 3 ngày một icon khác -> mọi .png trong thư mục
# này đều được tìm (thêm event mới = thả ảnh icon vào đây, không cần sửa code). Cắt phần dưới trái
# icon, bỏ góc trên phải (chấm đỏ thông báo): 1,00; màn khác <= 0,43 -> 0,8.
ICONS_DIR = f"{FOLDER}/Icons"
ICON_THRESHOLD = 0.8


def icons() -> list[str]:
    return images_in(ICONS_DIR)


# Màn event có 2 tab: tab nhiệm vụ (trái, tên đổi theo event, đang chọn khi vừa vào) và "Redeem"
# (phải). Nhận màn bằng chữ "Redeem" (chưa chọn / đang chọn khớp chéo 0,97 -> dùng cả hai, rồi phân
# biệt bằng MÀU nền tab: EVENT_TAB_ON_RED). 1,00 trên màn của nó; màn khác <= 0,61.
REDEEM_TAB = f"{FOLDER}/redeemTab.png"
REDEEM_TAB_ON = f"{FOLDER}/redeemTabOn.png"
TABS_REGION = (60, 33, 90, 41)   # % màn hình: quanh chữ "Redeem" (292, 259)
TAB_THRESHOLD = 0.9
TASK_TAB_TAP = (100, 259)
REDEEM_TAB_TAP = (292, 259)
# Tab đang chọn nền cam: đo mảnh trống bên trái chữ Redeem, trung bình kênh đỏ (R) của
# CROP (x, y, w, h) từ góc trên trái màn: chọn ~100, chưa chọn ~44.
REDEEM_TAB_COLOR_BOX = (212, 252, 20, 14)
TAB_ON_RED = 70

# Dòng nhiệm vụ: KHÔNG nhận từng mốc (nền sau chữ có vệt sáng xanh chạy nên ảnh tiêu đề từng mốc chỉ
# khớp 0,87 ở vài vị trí cuộn) mà nhận chữ CHUNG của 3 dòng cùng loại ("Donate to the Alliance" /
# "Heal"); nút Go cùng dòng ở dưới tâm chữ ROW_GO_DY px. 3 mốc dùng chung một bộ đếm nên OCR ở Go nào
# cũng cho cùng giá trị đã làm. Dòng "Heal" chung khớp 0,82 .. 1,00 (ảnh _2 thêm cho vị trí 0,82); khớp giả
# 0,80 ở tab Redeem -> chỉ tìm trong ROWS_REGION, ngưỡng 0,85. Donate 0,93 .. 1,00. Nút Go dùng chung
# Event/goButton.png.
ROWS_REGION = (0, 40, 60, 100)
ROW_TEXT_THRESHOLD = 0.85
ROW_PITCH_TASK = 110.7  # khoảng cách các dòng nhiệm vụ
ROW_TOLERANCE = 8       # lệch y cho phép khi gộp các khớp trùng của cùng một chữ
ROW_GO_DY = 43              # nút Go ở dưới tâm tiêu đề (đo 42..43)
ROW_GO_TOLERANCE = 8
GO_WAIT = 5
GO_TRIES = 3   # số lần bấm Go tối đa mỗi nhiệm vụ trong 1 lượt: quá thì coi là không đạt được, xong hôm nay
MAX_ROUNDS = 20   # an toàn: số vòng quét tối đa trong 1 lượt
TASK_SEARCH_TRIES = 3   # không thấy nhiệm vụ nào: Back rồi làm lại tối đa số lần này, rồi báo lỗi, sang nhận quà
SETTLE_INTERVAL = 1.0   # giây giữa 2 ảnh khi chờ màn hình đứng yên sau Go
SETTLE_MAX = 10         # số lần kiểm tối đa
ROW_TEXT = {"three_day_alliance": f"{FOLDER}/Rows/donateText.png",
            "three_day_heal": f"{FOLDER}/Rows/healText.png"}
TIERS = {"three_day_alliance": {10: 0, 30: 1, 60: 2},
         "three_day_heal": {5000: 0, 10000: 1, 30000: 2}}


def row_texts(key: str) -> list[str]:
    """Ảnh chữ chung của nhiệm vụ: <tên>.png và <tên>_N.png (thêm ảnh = thả file vào Rows/)."""
    base = ROW_TEXT[key]
    stem = Path(base).stem
    return [base, *(f"{Path(base).parent.as_posix()}/{p.name}"
                    for p in sorted((TEMPLATE_DIR / base).parent.glob(f"{stem}_*.png")))]


# Tiến độ "13 / 60" ngay trên nút Go: cắt (dx, dy, w, h) từ tâm nút Go. Đọc bằng
# bot.ocr.read_progress (đã thêm mẫu "1", "3" cho kiểu chữ này; cao 12 là vừa chữ, cao hơn thì lẫn
# hoạ tiết góc phải).
PROGRESS_FROM_GO = (-71, -49, 111, 12)

# Nút Claim xanh (nhận quà từng dòng, KHÔNG dùng Claim All): 1,00; màn khác trong event <= 0,60.
CLAIM = f"{FOLDER}/claim.png"
CLAIM_THRESHOLD = 0.8   # máy 21943: nút Claim thật chỉ khớp 0,86 (máy 21923 1,00) -> 0,8; nút xám Claimed loại theo x
CLAIM_REGION = (70, 35, 100, 100)
CLAIM_WAIT = 2
CLAIMED = f"{FOLDER}/claimed.png"   # nút xám "Claimed" (21x52 chữ): 1,00 / 0,97 / 0,91 trên các dòng đã nhận
CLAIMED_THRESHOLD = 0.78   # dòng giữa 3 dòng Claimed chỉ khớp 0,84 (máy 21943, nền khác); Go / Claim trong event <= 0,67
CLAIMED_EXTRA_SCROLLS = 3   # thấy Claimed rồi vẫn cuộn thêm tối đa số màn này để thấy dòng đã nhận của nhiệm vụ còn lại
CLAIM_X = 332       # tâm x nút Claim xanh: máy 21923 334, máy 21943 330 (lệch 4 px giữa các máy). Ảnh "Claim" cũng khớp
CLAIM_X_TOL = 5     # phần đầu nút xám "Claimed" nhưng tâm lệch về trái ~8 px (326 / 322) -> loại theo x (|x - 332| <= 5)
CLAIM_SAME_MAX = 6   # bấm Claim cùng chỗ quá số lần này mà nút vẫn còn -> bỏ qua

# Cuộn danh sách nhiệm vụ / quà (ngón tay kéo lên = xuống cuối danh sách; mỗi lần ~280 px < cao 1
# cửa sổ 400 px nên không sót dòng). Màn không đổi sau khi cuộn = hết danh sách.
SWIPE = (50, 75, 50, 55)       # ~141 px: dài / nhanh hơn thì danh sách trôi lố (máy thật: bỏ sót dòng)
SWIPE_BACK = (50, 55, 50, 75)
# Đã thấy dòng của nhiệm vụ: cuộn bước nhỏ để có màn thấy đủ 3 dòng cùng nhiệm vụ (cửa sổ chỉ rộng ~145 px mà bước
# cuộn thường thực trôi ~185 px nên 3 dòng Claimed cứ bị cắt đầu / cuối: máy 21943).
SWIPE_FINE = (50, 70, 50, 57)   # ~92 px vuốt -> ~120 px danh sách trôi
SWIPE_DURATION = 1.0
SWIPE_WAIT = 1.5
SAME_DIFF = 2.0         # độ lệch điểm ảnh trung bình < mức này = màn không đổi
MAX_ITERATIONS = 40     # số bước tối đa một lần quét danh sách (cuộn + bấm Claim)
BACK_TO_TOP = 15        # số lần kéo ngược tối đa để về đầu danh sách

# Đổi quà: mỗi dòng có icon quà (cột trái x ~50) và nút Redeem (x 334, dưới tâm icon ~3 px). Nút
# xanh = đổi được, nút xám = không đủ vé / hết lượt. Phân biệt bằng màu (G - R ở mảnh bên trái chữ:
# xanh ~21, xám ~0). Icon 48x48 cắt từ ảnh thật: đúng 1,00; icon khác cùng khung (500k Food /
# Lumber / Ore / Silver) <= 0,83; dòng bị cắt dở ở mép <= 0,95 -> 0,96.
REWARD_DIR = f"{FOLDER}/Reward"
REWARD_THRESHOLD = 0.88   # máy 21943 icon quà chỉ khớp 0,92 - 0,94 (máy 21923 1,00); icon khác cùng khung <= 0,83
REWARD_REGION = (0, 35, 30, 100)
REDEEM_BUTTON_X = 334
REDEEM_BUTTON_DY = 3
REDEEM_COLOR_BOX = (-29, -6, 10, 12)   # (dx, dy, w, h) so với tâm nút
REDEEM_GREEN_DIFF = 10
REDEEM_WAIT = 2
MAX_REDEEMS_PER_ITEM = 30
GREY_STOP = 5   # quà xám (chưa đổi được lần nào) liên tiếp thì dừng đổi quà
# Bấm Redeem -> popup chọn số lượng (tên quà, thanh trượt "1 / 2", nút xanh ghi giá): bấm cạnh dấu
# "+" (đầu phải thanh trượt) để chọn đổi TẤT CẢ, rồi bấm nút xanh. Nhận popup bằng nút "+" (30x30,
# đúng 1,00; cũng có ở màn speed up nên chỉ chờ ngay sau khi bấm Redeem).
QTY_PLUS = f"{FOLDER}/qtyPlus.png"
QTY_WAIT = 3                    # giây chờ popup
QTY_MAX_TAP = (276, 354)        # cạnh dấu "+" (đầu phải thanh trượt)
QTY_CONFIRM_TAP = (198, 452)    # nút xanh giữa popup
# Vị trí hàng quà: hàng k có tâm icon ở y = ROW_FIRST_Y + ROW_PITCH * k khi chưa cuộn (đo: 347,
# 458, 568 -> bước 110,5-111). Tới hàng k: cuộn sao cho hàng nằm ở ROW_TARGET_Y, vuốt chậm
# (DRAG_DURATION) quanh giữa màn để ít trôi; thấy icon thì lấy toạ độ thật làm mốc mới; không thấy
# thì đo lại vị trí và vuốt tiếp (xem GOTO_TRIES / NUDGE bên dưới).
ROW_FIRST_Y = 347
ROW_PITCH = 110.7
ROW_TARGET_Y = 450
SCREEN_H = 704
DRAG_MID = 62         # % chiều cao: giữa vùng danh sách
DRAG_MAX = 200        # px mỗi lần vuốt tối đa (dài hơn thì trôi lố)
DRAG_MIN = 20         # lệch dưới mức này thì không vuốt
DRAG_DURATION = 1.2
# Đo thật (ảnh máy 21923): danh sách trôi ~1,5 - 1,7 lần quãng vuốt (quán tính) -> hệ số ban đầu DRAG_FACTOR, tự
# hiệu chỉnh sau mỗi lần vuốt (EMA, chỉ khi vuốt > FACTOR_MIN_DRAG px). Tới hàng: tối đa GOTO_TRIES vòng (đo vị
# trí, vuốt, đo lại); lệch dưới GOTO_TOL px mà vẫn chưa thấy icon thì xê dịch NUDGE px (đổi chiều mỗi vòng).
# Icon coi là bấm được khi y trong ROW_VISIBLE (không sát mép trên / dưới màn).
DRAG_FACTOR = 1.5
FACTOR_MIN_DRAG = 60
GOTO_TRIES = 7
LOCATE_TRIES = 5   # lần đo vị trí danh sách quà lúc mới sang tab Redeem (chưa thấy icon nào thì chờ rồi đo lại)
LOCATE_WAIT = 1.5
GOTO_TRIES_AFTER = 3   # số vòng tìm lại icon khi đã đổi quà đó rồi
GOTO_TOL = 40
NUDGE = 120
ROW_VISIBLE = (300, 660)
# Popup sau khi đổi (chưa có ảnh chụp): băng "Congratulations!" thì Back; không thấy tab Redeem
# (có popup che) thì Back (tối đa POPUP_BACKS lần).
POPUP_BACKS = 3

# Xong cả event hôm nay (mọi nhiệm vụ bật đã xong + đã nhận quà + đã đổi quà), hoặc không thấy tab /
# icon event (hết event): lưu daily_done, tới lần reset server mới chạy lại.
DONE_KEY = "three_day_done"
GROUP_KEY = "three_day"
REDEEM_KEY = "three_day_redeem"
ALLIANCE_KEY = "three_day_alliance"
HEAL_KEY = "three_day_heal"

# ---- Actions -----------------------------------------------------------
ON_EVENT = "on_event"
NOT_FOUND = "not_found"   # _scan_tasks: không thấy nhiệm vụ nào
STOP = "stop"


def reward_rows() -> dict[str, int]:
    """{id quà: hàng trong danh sách Redeem của game} (trường "row" trong event.py, group
    "three_day"; 0 = hàng đầu): bot nhớ vị trí mặc định của từng quà. Thứ tự trong json là thứ tự
    ưu tiên mặc định ở UI, không liên quan tới hàng. Quà mới: thêm "row" đúng hàng của nó."""
    # import trong hàm: bot không import ui ở mức module (tránh import vòng ui <-> bot).
    from ui.tabs.event import DATA
    group = next(g for g in DATA["groups"] if g.get("key") == GROUP_KEY)
    return {i["id"]: int(i["row"]) for i in group["redeem"]["items"]}
