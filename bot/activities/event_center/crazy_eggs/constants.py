"""
constants.py — Crazy Eggs image folders, limits and action names.

Toạ độ đo trên màn 396x704 (tests/event_center/crazy_eggs/screens).
"""
from ...event.constants import CONGRATULATIONS
from ..constants import EC

FOLDER = f"{EC}/CrazyEggs"

# Icon quả trứng của "Crazy Eggs" trong danh sách tab Activities của Event Center: khớp 0,934
# trên ảnh thật (03_activities_crazy_eggs.png, góc trên trái (35, 348); icon có hiệu ứng lấp lánh
# nên mỗi khung hình hơi khác); màn khác <= 0,555 -> 0,8.
ICON = f"{FOLDER}/icon.png"
ICON_THRESHOLD = 0.8

# Tiêu đề "Crazy Eggs" (tâm (198, 22)): 1,00; màn event khác <= 0,52.
TITLE = f"{FOLDER}/title.png"
TITLE_REGION = (20, 0, 80, 8)
# Animation trứng vỡ: cả màn tối đi, tiêu đề mờ (10_egg_breaking.png). Template khớp 0,99 cả tiêu
# đề thường lẫn mờ (TM_CCOEFF_NORMED bỏ qua độ sáng) -> đo ĐỘ SÁNG trung bình vùng tiêu đề:
# màn trứng 77, popup Congratulations 49, hộp thoại búa vàng 20 (xét hộp thoại trước), animation 14.
# Tối hơn TITLE_DIM_MEAN -> đang animation: bấm (50 %, 95 %) để bỏ qua. Bấm quá DIM_MAX_TAPS lần
# liên tiếp mà vẫn tối (lớp phủ tối lạ) -> BACK.
TITLE_DIM_MEAN = 35
SKIP_ANIMATION_TAP = (50, 95)   # % màn hình
DIM_MAX_TAPS = 10
# Icon búa trong nhãn "Scout Cost:" dưới quả trứng: có = quả đó đập được (quả đang "Waiting:"
# không có). Trên 4 quả sẵn sàng khớp 0,84..0,95; màn trứng đang chờ <= 0,61 -> 0,8 (chỉ tìm
# khi đang ở màn Crazy Eggs).
HAMMER = f"{FOLDER}/hammer.png"
HAMMER_THRESHOLD = 0.8
# Đập: bấm thẳng vào vị trí icon búa tìm được (bấm chỗ nào của quả cũng đập được, người dùng xác nhận).
EGG_TAP_DELAY = 3   # chờ sau khi bấm trứng; cũng là nhịp chờ thêm trước khi kết luận hết búa
# Đập xong hiện popup "Congratulations!" (danh sách phần thưởng, khác nhau theo quả) che hàng
# trứng trên, tiêu đề "Crazy Eggs" vẫn thấy. Dùng chung ảnh chữ của activity Event: khớp 0,999
# (tests/event_center/crazy_eggs/screens/06_congratulations.png). Popup không tự mất, đóng
# bằng BACK (người dùng xác nhận); chỉ đếm búa khi không còn popup.
# Trứng vỡ (nhận hết vật phẩm): sau animation vỡ hiện popup thưởng thêm "Congratulations on
# activating the egg!" (cao hơn popup thường, che gần hết màn). Ảnh CONGRATULATIONS vẫn khớp 0,939
# nhưng sát ngưỡng 0,9 -> thêm ảnh riêng phần "activating the egg!": 1,00
# (09_egg_activated_rewards.png); màn khác <= 0,45. Cũng đóng bằng BACK.
CONGRATS_POPUPS = (CONGRATULATIONS, f"{FOLDER}/activatedRewards.png")

# Hết búa thường: bấm trứng -> hộp thoại "You don't have enough Hammers. Go get more now?" (Cancel /
# Buy, 11_not_enough_hammers.png) -> bấm Cancel, coi như hết búa. Chữ "enough Hammers": 1,00; màn
# khác <= 0,60 (hộp thoại búa vàng 0,53). Nút Cancel giống mọi hộp thoại khác (1,00 ở nhiều màn)
# -> chỉ tìm khi đã thấy NOT_ENOUGH_HAMMERS, trong vùng nửa trái hộp thoại.
NOT_ENOUGH_HAMMERS = f"{FOLDER}/notEnoughHammers.png"
NOT_ENOUGH_CANCEL = f"{FOLDER}/cancel.png"
NOT_ENOUGH_CANCEL_REGION = (10, 50, 50, 70)

# ---- Búa vàng (Lucky Hammer) ----------------------------------------------
# Mỗi ngày 1 búa vàng đập thêm 1 lần vào một quả ĐANG CHỜ refresh: dùng cho quả 2, sau khi đã
# đập hết quả có búa thường. Bấm thân quả 2 -> hộp thoại "Use the Lucky Hammer to smash an Egg
# in cooldown, but it can only be used once per day. Confirm use?" -> Confirm. Đã dùng thì lưu
# daily_done LUCKY_KEY (thời điểm lưu ở DB): qua mốc reset server (ngày mới) mới dùng lại.
LUCKY_KEY = "crazy_eggs_lucky_hammer"
# Số búa vàng cạnh icon búa vàng ở góc trên phải màn Crazy Eggs (chữ số tâm (289, 249)): "1" = còn,
# dùng xong thành "0" (icon vẫn còn, 10_egg_breaking.png). Chỉ cắt chữ số "1" (cắt cả icon thì
# chữ số chỉ chiếm phần nhỏ, số "0" vẫn có thể khớp cao). Không khớp -> coi như hôm nay đã dùng
# (lưu LUCKY_KEY). "1": 1,00 trên mọi màn trứng (0,995 khi hộp thoại búa vàng mở); số "0" (tăng
# sáng) 0,14; popup che <= 0,66 (chỉ xét khi không còn popup).
LUCKY_LEFT = f"{FOLDER}/luckyHammerOne.png"
LUCKY_LEFT_REGION = (68, 32, 78, 38)
# Chữ "Lucky Hammer" trên hộp thoại: 1,00 (07_lucky_hammer.png); màn khác <= 0,62.
LUCKY_HAMMER = f"{FOLDER}/luckyHammer.png"
# Nút "Confirm" của hộp thoại: giống nút Confirm của mọi hộp thoại khác (khớp 1,00 ở nhiều màn)
# -> chỉ tìm khi đã thấy LUCKY_HAMMER, trong vùng nửa dưới hộp thoại.
LUCKY_CONFIRM = f"{FOLDER}/confirm.png"
LUCKY_CONFIRM_REGION = (50, 50, 100, 70)
# Mỗi quả chứa nhiều vật phẩm; nhận hết thì trứng vỡ, nhãn thành "Activated" (không búa, không
# Waiting) và không đập được nữa -> đập thường tự bỏ qua (không có búa). Búa vàng luôn dùng ở lần
# chạy đầu tiên trong ngày, lúc chưa có quả nào vỡ, nên không cần nhận "Activated".

# Quả của một búa / nhãn theo vị trí tìm thấy (người dùng chốt): cột 1 nếu x < COLUMN_SPLIT % chiều
# rộng màn, hàng 1 nếu y < ROW_SPLIT % chiều cao màn. Quả 1 = cột 1 hàng 1, 2 = cột 2 hàng 1,
# 3 = cột 1 hàng 2, 4 = cột 2 hàng 2. (Không dùng chân dung trên quả: có hoạt ảnh.)
COLUMN_SPLIT = 50
ROW_SPLIT = 70
# Thứ tự đập.
ORDER = (2, 3, 1, 4)
# Nhãn "Waiting:" dưới quả đang chờ (chữ, không hoạt ảnh): 0,87..1,00 trên các quả; màn khác <= 0,71
# -> 0,8. Chỉ dùng để tìm quả 2 đang chờ cho búa vàng (quả đó không có búa); bấm thẳng vào nhãn.
WAITING = f"{FOLDER}/waiting.png"
WAITING_THRESHOLD = 0.8
# Sau khi đập mỗi quả chờ refresh riêng (quả 1 30 phút, 2 4 giờ, 3 1 giờ, 4 2 giờ): game hiện
# "Waiting:" không có búa, nên bot chỉ cần đập quả còn búa.

# Ở màn Event Center mà không thấy tab Activities: đánh dấu hôm nay xong (daily_done DONE_KEY, lưu
# DB), các lần gọi sau trong ngày return ngay, không vào game; qua mốc reset server thì chạy lại.
DONE_KEY = "crazy_eggs_done"

# ---- Actions -----------------------------------------------------------
ON_EGGS = "on_eggs"
DONE = "done"   # giá trị handle trả cho run_task khi đập xong
