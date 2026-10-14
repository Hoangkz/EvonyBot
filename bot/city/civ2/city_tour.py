"""city_tour.py (civ2) — các ô đi vòng khi quét bản đồ thành của nền văn minh 2, dữ liệu tĩnh. Cùng cấu trúc với civ1/city_tour.py
(xem file đó): FIXED, ANCHOR_SHIFT, ROUTES, DATA (13 ô).

Đang đo dở (máy 21933, Thành chính ở giữa màn (197, 345) điểm khớp 1,0): COMPLETE = False nên tours.py chưa bật civ2; đủ FIXED / ROUTES /
13 ô thì đổi thành True. Thứ tự ô civ2 chưa biết có giống civ1 hay không - đo từng ô rồi ghi ở đây.
- ô 1 (Học viện, người dùng xác nhận đúng): chỉ 1 cú từ Thành chính ở giữa. Đo thật trên 21933: cú (204, 130) -> Học viện ra (-28, -18) so với giữa, cú (232, 148) -> (+30, +20),
  nội suy ra (218, 139): Học viện ra (192, 341), điểm khớp 0,915, lệch (-5, -4) (lúc xuất phát Thành chính lệch (-21, -14) nên số thật có thể chênh chút).
  Điểm đầu (81, 271) -> cuối (299, 409). Chiều về chưa đo (cú (-248, -159) từ Học viện lệch lên, Thành chính ra lệch (-21, -14)).
"""
COMPLETE = False
FIXED = {}
ANCHOR_SHIFT = {}
ROUTES = {}
DATA = [
    {'plot': 1, 'swipes': [[[81, 271], [299, 409]]], 'view': [218, 139], 'seen_21933': 'academy'},
]
