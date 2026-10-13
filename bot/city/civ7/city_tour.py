"""city_tour.py (civ7) — các ô đi vòng khi quét bản đồ thành của nền văn minh 7, dữ liệu tĩnh. Cùng cấu trúc với civ1/city_tour.py
(xem file đó): FIXED, ANCHOR_SHIFT, ROUTES, DATA (13 ô).

Đang đo dở (máy 21933): mới có ô 1. COMPLETE = False nên tours.py chưa bật civ7; đủ FIXED / ROUTES / 13 ô thì đổi thành True.
- ô 1 (Học viện): từ Thành chính ở giữa màn (ảnh mẫu keep ở (197, 345)) cùng hướng civ1 nhưng ngắn hơn: cú 1 ngón tay (157, 59) thì
  Học viện ra (175, 284), cú 2 (22, 61) thì Học viện ở (198, 347); tổng (179, 120).
  Chiều về (đo thật trên 21933, từ lúc Học viện ở giữa): 1 cú (-179, -120), điểm đầu (279, 400) -> cuối (101, 280) thì Thành chính ra
  (199, 343), lệch (2, -2) so với giữa (197, 345).
"""
COMPLETE = False
FIXED = {}
ANCHOR_SHIFT = {}
ROUTES = {}
DATA = [
    {'plot': 1, 'swipes': [[[112, 311], [269, 370]], [[180, 280], [202, 341]]], 'view': [179, 120], 'seen_21933': 'academy'},
]
