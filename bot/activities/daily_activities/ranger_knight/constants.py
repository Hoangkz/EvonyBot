"""
constants.py — ảnh của nhiệm vụ Daily Activities "Ranger Knight Order" (thư mục ảnh ActivitiesRangerKnight/).
"""
from ..constants import ROOT

KEY = "daily_ranger_knight"   # key nhiệm vụ trong bot/worker/priority.py
LABEL = "Ranger Knight"   # ô tích ở tab Daily Activities, key daily_done
FOLDER = "ActivitiesRangerKnight"
FOLDER_PATH = f"{ROOT}/{FOLDER}"

# ---- Sau Go (run.after_go) --------------------------------------------------------------------
# Go -> màn "Ranger Knight Order" (tab My Tasks): chờ 1 giây / lần, tối đa SCREEN_WAIT giây.
#   - có nút Claim (xanh, bên phải mỗi nhiệm vụ) -> bấm, chờ CLAIM_WAIT giây (không hiện popup), xét lại;
#   - không còn Claim -> bấm Quick Dispatch (góc dưới phải), chờ 1 giây / lần tối đa DISPATCH_WAIT giây tới bảng
#     "Quick Dispatch" -> bấm Send (xanh) -> xong hôm nay; Send xám (hết tướng) -> không bấm, cũng xong hôm nay -> Back BACKS_AFTER lần liên tục.
# Ảnh cắt từ ảnh chụp giả lập 396x704 (2026-10-16). Card.png: thẻ bản cũ (icon số 4 trong lưới).
TITLE = f"{FOLDER_PATH}/Title.png"                  # tiêu đề màn "Ranger Knight Order" (bảng Quick Dispatch mở vẫn thấy: 0,99)
CLAIM = f"{FOLDER_PATH}/Claim.png"                  # nút Claim xanh (khác nền <= 0,46)
QUICK_DISPATCH = f"{FOLDER_PATH}/QuickDispatch.png"   # nút Quick Dispatch góc dưới phải (bảng mở vẫn thấy: 0,99)
DISPATCH_TITLE = f"{FOLDER_PATH}/DispatchTitle.png"   # tiêu đề bảng Quick Dispatch (màn thường <= 0,35)
SEND = f"{FOLDER_PATH}/Send.png"                    # nút Send xanh dưới bảng
SEND_GRAY = f"{FOLDER_PATH}/SendGray.png"            # nút Send xám ("No General available": không còn tướng để cử)
SEND_THRESHOLD = 0.97   # Send xanh và xám khớp chéo 0,91 -> ngưỡng cao hơn THRESHOLD để phân biệt (đúng ảnh: 1,00)
THRESHOLD = 0.8
SCREEN_WAIT = 10       # giây tối đa chờ màn Ranger Knight Order sau Go (xét 1 giây / lần)
DISPATCH_WAIT = 10     # giây tối đa chờ bảng Quick Dispatch sau khi bấm nút (xét 1 giây / lần)
CLAIM_WAIT = 5         # giây chờ sau khi bấm Claim
CLAIM_MAX = 10         # số lần Claim tối đa
SEND_WAIT = 1          # giây chờ sau khi bấm Send
BACKS_AFTER = 3        # xong: Back liên tục chừng này lần
