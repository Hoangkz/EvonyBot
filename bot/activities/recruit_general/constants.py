"""
constants.py — ảnh và hằng số của activity "Recruit General" (thư mục ảnh Images/RecruitGeneral/).
"""
NAME = "Recruit General"   # tên activity = tên tab = nút Select Activity (ui/tabs/constants.py)
FOLDER = "RecruitGeneral"
# Ảnh cắt từ ảnh chụp giả lập 396x704 (2026-10-16).
MENU_RECRUIT = f"{FOLDER}/MenuRecruit.png"   # icon "Recruit" (bắt tay) trong menu tròn của Tavern (khác màn <= 0,35)
TITLE = f"{FOLDER}/Title.png"                # tiêu đề màn "Recruit General" (khác màn <= 0,21)
THRESHOLD = 0.8
HOME_BACKS = 6        # số lần Back tối đa để về màn thành sạch
MENU_WAIT = 5         # giây tối đa chờ menu tròn của Tavern sau khi bấm (xét 1 giây / lần)
MENU_TRIES = 3        # số lần bấm Tavern nếu menu chưa hiện
SCREEN_WAIT = 10      # giây tối đa chờ màn Recruit General sau khi bấm icon Recruit (xét 1 giây / lần)

# ---- Ô cảnh báo "Warn me only if the Tavern has the follow General(s)" (màn Recruit General) ----
# Ô tích hay chưa: ảnh dấu tích xanh (BoxChecked.png, cắt ô Epic đã tích: ô đã tích 0,93..1,00; ô chưa tích <= 0,10) tìm trong
# vùng của từng ô (% màn hình x0, y0, x1, y1). Không thấy dấu tích = chưa tích. Bấm theo % màn hình (tâm ô).
BOX_CHECKED = f"{FOLDER}/BoxChecked.png"
EPIC_REGION = (2, 79, 26, 87)
HISTORIC_REGION = (49, 79, 73, 87)
EPIC_BOX = (10.6, 83)       # tâm ô "Epic (Orange) General" (% màn hình)
HISTORIC_BOX = (56.6, 83)   # tâm ô "Historic General"
BOX_TAPS = 3                # số lần bấm tối đa để đổi trạng thái một ô
BOX_WAIT = 3                # giây tối đa chờ ô đổi trạng thái sau khi bấm (xét 1 giây / lần)

# ---- Refresh liên tục ----
# Bấm nút Refresh (chữ "Refresh", 1,00 trên màn Recruit General; màn khác <= 0,34) liên tục, mỗi lần chờ REFRESH_WAIT giây.
# Hiện popup "Your Tavern has a high quality General. Are you sure you want to refresh now?" (có tướng xịn: HIGH_QUALITY_POPUP) ->
# bấm Cancel rồi dừng (không Confirm). Tiêu đề / nút Refresh vẫn khớp 0,99 dưới popup nên phải xét popup TRƯỚC.
# Dừng khi: có popup tướng xịn (đã Cancel), rời màn Recruit General (không thấy tiêu đề: popup / cảnh báo hiện lên), không thấy nút Refresh, hoặc đủ REFRESH_MAX lần.
REFRESH = f"{FOLDER}/Refresh.png"
REFRESH_WAIT = 1   # giây chờ sau mỗi lần bấm Refresh: bấm Refresh cho đến khi ra tướng lịch sử
REFRESH_MAX = 1000   # số lần bấm tối đa mỗi lượt chạy
HIGH_QUALITY_POPUP = f"{FOLDER}/HighQualityPopup.png"   # dòng chữ của popup (1,00; màn Recruit General thường 0,30)
CANCEL = f"{FOLDER}/Cancel.png"                         # nút Cancel đỏ của popup (1,00; màn thường 0,45)
CANCEL_WAIT = 1   # giây chờ sau khi bấm Cancel

# ---- Kiểm tra tướng để mua (sau khi Cancel popup tướng xịn) ----
# Tên tướng hiện trong dải ngay dưới tướng. Tướng CẦN MUA: mỗi tướng một ảnh tên trong GENERALS_DIR (tên file = tên tướng).
# Thấy tên nằm trong danh sách -> luồng mua; không thì Refresh tiếp. Thư mục rỗng = không mua tướng nào.
GENERALS_DIR = f"{FOLDER}/Generals"
NAME_REGION = (25, 68, 75, 74)   # % màn hình (x0, y0, x1, y1): dải tên tướng
NAME_THRESHOLD = 0.9

# ---- Thanh chấm màu 6 tướng trong Tavern (dưới ảnh tướng, trên dải tên) ----
# Mỗi tướng một chấm, màu theo phẩm chất: trắng (xám) / xanh lá / xanh dương / TÍM / VÀNG. Bot KHÔNG lọc theo màu, chỉ quan tâm tướng
# CÓ vương miện (xem CROWNS); màu chỉ ghi log.
# Chấm của tướng đang hiện to hơn, có viền vàng (và vương miện nếu tím / vàng) nên chỉ lấy màu ở TÂM chấm (trung vị 3x3 px, HSV).
# 6 chấm cố định ở một hàng: x theo % chiều rộng, y theo % chiều cao màn hình (đo trên 396x704: x 145 166 188 208 230 251, y 467).
# Màu theo Hue OpenCV (0..179), cần độ bão hoà >= DOT_MIN_SATURATION và sáng >= DOT_MIN_VALUE (ảnh dưới popup bị mờ: sáng ~50..75);
# bão hoà thấp = trắng / xám. Đo: lá 53, dương 101, tím 149, vàng 23.
# SỐ CHẤM = SỐ TƯỚNG ĐÃ MỞ, từ DOT_MIN đến DOT_MAX (tài khoản yếu chỉ 3 chấm). Các chấm luôn nằm ở một hàng, cách đều DOT_SPACING_PCT, căn GIỮA
# màn hình (DOT_CENTER_X_PCT): n chấm thì chấm thứ i ở x = giữa + (i - (n - 1) / 2) * khoảng cách. Đo trên 396x704 với 6 chấm: x 145 166 188 208
# 230 251 (cách 21,2 px, giữa 198). Số chấm = n lớn nhất (DOT_MAX về DOT_MIN) mà MỌI vị trí đều là chấm (run.dot_xs). Một vị trí là chấm khi
# màu ở tâm đọc được (không phải "?") và MỘT trong hai điểm ở hai bên cách DOT_EDGE_PX khác màu tâm rõ (khác nền đồng màu như giày đen, DOT_EDGE_DIFF).
DOT_MIN, DOT_MAX = 3, 6
MIN_GENERALS = 5   # ít hơn chừng này tướng đã mở (3/6, 4/6) thì level quá thấp, không thể roll tướng xịn: ghi log rồi dừng bot
DOT_SPACING_PCT = 5.35
DOT_CENTER_X_PCT = 50.0
DOT_EDGE_PX = 5
DOT_EDGE_DIFF = 40
DOT_Y_PCT = 66.3
DOT_MIN_SATURATION = 100
DOT_WHITE_MAX_SATURATION = 50   # chấm trắng / xám: bão hoà < 50 (đo 4); 50..100 là nền (gỗ, bóng giày) -> "?"
DOT_MIN_VALUE = 30
DOT_HUES = {"gold": (15, 32), "green": (40, 70), "blue": (90, 115), "purple": (135, 165)}

# ---- Vương miện: tướng XỊN (tím / vàng) có vương miện nhỏ vàng trên chấm ----
# Mọi tướng xịn đều có vương miện trên chấm của nó (có thể 2 tướng cùng lúc, hiếm). Chỉ quan tâm tướng CÓ vương miện, KHÔNG xét màu
# chấm (màu chấm chỉ để ghi log: run.dot_colors). Tướng đang HIỆN là tướng có viền vàng quanh chấm (SHOWN_*), không liên quan vương miện.
# Ảnh vương miện (9x11 px): Crown.png tím sáng, Crown2.png vàng mờ (dưới popup), Crown3.png vàng sáng. Điểm khớp: đúng 0,83..1,00,
# chấm khác <= 0,64 -> ngưỡng 0,75. Tìm trong vùng quanh từng chấm (CROWN_REGION_DX px sang hai bên, y CROWN_Y px).
CROWNS = (f"{FOLDER}/Crown.png", f"{FOLDER}/Crown2.png", f"{FOLDER}/Crown3.png")
CROWN_THRESHOLD = 0.75
CROWN_REGION_DX = 10
CROWN_Y = (452, 470)
# Ảnh vương miện khớp không đều (nền sau lưng chấm khác nhau: bóng giày, váy tướng... -> 0,70 ở ảnh 11, 0,52 ở ảnh 15) nên thêm cách đếm MÀU:
# số điểm CAM VÀNG ĐẬM (Hue CROWN_HUE, bão hoà > CROWN_MIN_SATURATION, sáng > CROWN_MIN_VALUE) trong dải CROWN_COLOR_Y (px) rộng +-CROWN_COLOR_DX quanh
# chấm. Vương miện Hue 22..25, bão hoà 230..255, sáng 200..255; viền thêu vàng trên váy tướng (ảnh 15) Hue 15..17, bão hoà ~170 nên bị loại.
# Đo: có vương miện 5..9 điểm, không 0 (mọi ảnh sáng) -> từ CROWN_MIN_PIXELS. Ảnh mờ (dưới popup) không đủ sáng nên dùng ảnh mẫu. Có vương miện = màu
# HOẶC ảnh mẫu khớp.
CROWN_COLOR_Y = (455, 462)
CROWN_COLOR_DX = 6
CROWN_HUE = (20, 30)
CROWN_MIN_SATURATION = 200
CROWN_MIN_VALUE = 150
CROWN_MIN_PIXELS = 3
# Tướng đang hiện: chấm của nó có viền vàng sáng. Lấy 7 điểm trên nửa DƯỚI vòng bán kính 6 px quanh tâm chấm (nửa trên có thể dính
# vương miện vàng), đếm điểm vàng (Hue 15..35, bão hoà > 150, sáng > 40); chấm có nhiều điểm vàng nhất (>= SHOWN_MIN_POINTS) là tướng đang
# hiện. Đo: chấm đang hiện 4..7 điểm (ảnh mờ 2), chấm khác 0.
SHOWN_RING = ((-6, 0), (-5, 3), (-3, 5), (0, 6), (3, 5), (5, 3), (6, 0))
SHOWN_MIN_POINTS = 2

# ---- Chuyển sang tướng khác: kéo ảnh tướng sang trái / phải ----
# Tướng đang hiện là tướng xịn nhất; còn tướng xịn khác (có vương miện) thì kéo ảnh tướng sang trái hoặc phải tới đó: viền vàng của tướng
# đang hiện chuyển theo sang chấm của tướng mới. Tướng đích nằm bên phải thì kéo sang trái, bên trái thì kéo sang phải (giả định: kéo sang
# trái = tướng bên phải); kéo xong thấy tướng đang hiện xa chấm đích hơn thì đổi hướng. Điểm kéo nằm giữa ảnh tướng (không chạm hàng chấm / dải tên): % màn hình (x1, y1, x2, y2).
SWIPE_LEFT = (80, 40, 20, 40)
SWIPE_RIGHT = (20, 40, 80, 40)
SWITCH_MAX = 8     # số lần kéo tối đa để tới một tướng
# Kéo xong có chuyển tướng chưa: chỉ cần chấm của tướng đang hiện (viền vàng, SHOWN_*) sang chấm khác là đủ, KHÔNG kiểm tra ảnh tướng (hai tướng
# giống nhau thì ảnh không đổi). Chờ 1 giây / lần tối đa SWIPE_CHANGE_WAIT giây; hết giờ chấm vẫn đứng yên thì kéo lại (tính vào SWITCH_MAX).
SWIPE_CHANGE_WAIT = 8   # giây tối đa chờ chấm đang hiện đổi sau mỗi lần kéo (xét 1 giây / lần)

# ---- Huy hiệu bên trái tên tướng: tướng có vương miện khi kéo tới sẽ hiện huy hiệu này ----
# Huy hiệu vàng (mũ giáp) ngay trái dải tên của tướng tím / vàng xịn nhất. Vị trí lệch theo độ dài tên (x 83..89) nên tìm trong vùng.
# Huy hiệu vị trí lệch theo độ dài tên (x 83..110) nên tìm trong vùng rộng. Điểm khớp: có 0,86 (tím sáng, vàng mờ), tướng thường (không huy hiệu) <= 0,34. Kéo tới tướng đích xong chờ huy hiệu hiện (hoạt ảnh
# chuyển tướng) tối đa EMBLEM_WAIT giây rồi mới kiểm tra tên; không thấy huy hiệu thì ghi log và vẫn kiểm tra tên.
EMBLEM = f"{FOLDER}/Emblem.png"
EMBLEM_REGION = (18, 67, 40, 73)   # % màn hình (x0, y0, x1, y1)
EMBLEM_THRESHOLD = 0.75
EMBLEM_WAIT = 3                    # giây tối đa chờ huy hiệu (xét 1 giây / lần)

# ---- Mua tướng: bấm vào ảnh tướng -> màn chi tiết tướng (tên, chỉ số, hai nút dưới cùng) ----
# Màn chi tiết có hai kiểu: HAI nút "Recruit General" (trái) + "Buy General Token" (phải), hoặc MỘT nút "Recruit General" ở giữa (một
# số tướng không có Buy General Token). Ảnh là phần CHỮ của nút (không kèm giá vàng, giá khác nhau theo tướng): Recruit General 1,00 ở
# cả hai kiểu, màn Tavern <= 0,43; Buy General Token 1,00 ở kiểu hai nút, kiểu một nút 0,46 -> ngưỡng DETAIL_THRESHOLD.
# Một nút -> bấm thẳng nút đó; hai nút -> bấm theo setting `buy_with` của tab.
DETAIL_RECRUIT = f"{FOLDER}/DetailRecruit.png"      # chữ "Recruit General" của nút ở màn chi tiết tướng
DETAIL_BUY_TOKEN = f"{FOLDER}/DetailBuyToken.png"   # chữ "Buy General Token" (chỉ có ở kiểu hai nút)
DETAIL_THRESHOLD = 0.9
BUY_RECRUIT, BUY_TOKEN = "Recruit General", "Buy General Token"   # giá trị setting `buy_with` (ui/tabs/constants.py RECRUIT_BUY_OPTIONS)
BUY_KEY = "buy_with"
GENERAL_ART = (50, 40)   # % màn hình: giữa ảnh tướng ở màn Tavern, bấm vào để mở chi tiết
DETAIL_WAIT = 8          # giây tối đa chờ màn chi tiết tướng sau khi bấm vào tướng: chờ 1 giây rồi xét; mất nút Refresh của Tavern = đã
#                          ra màn chi tiết -> mua; còn nút Refresh thì chờ thêm 1 giây / lần tới tối đa DETAIL_WAIT giây

# ---- Sau khi bấm nút mua: về lại màn danh sách tướng (Tavern) ----
# Chờ 1 giây, thấy nút Refresh của Tavern = đã về; chưa thì chờ thêm 1 giây / lần tối đa LIST_WAIT giây; vẫn chưa về thì bấm Back.
LIST_WAIT = 10   # giây tối đa chờ về màn danh sách tướng sau khi bấm nút mua
LIST_RELOAD_WAIT = 2   # giây chờ thêm sau khi về màn danh sách tướng: chờ 2s để đợi game load lại dữ liệu, rồi mới làm tiếp

# ---- Giới hạn số tướng mua mỗi lượt chạy ----
# Mua xong vẫn Refresh tiếp (săn tướng xịn kế tiếp); mua đủ BUY_LIMIT tướng trong lượt chạy này thì ghi log rồi dừng activity.
BUY_LIMIT = 3
