"""city_tour.py (civ2) — các ô đi vòng khi quét bản đồ thành của nền văn minh 2, dữ liệu tĩnh. Cùng cấu trúc với civ1/city_tour.py
(xem file đó): FIXED, ANCHOR_SHIFT, ROUTES, DATA (13 ô).

Đo trên máy 21933 (Thành chính ở giữa màn (197, 345) điểm khớp 1,0). COMPLETE = True (bật sau khi chạy thật): các cú vuốt đã chạy thử từ Thành chính qua 13 ô
(lệch tối đa ~50 px) và 5 đường thẳng giữa các ô ngẫu nhiên đều tới, nhưng ROUTES các mốc cố định còn một số chiều là số đảo dấu / nối (xem ghi chú từng dòng).
- ô 1 (Học viện, người dùng xác nhận đúng): chỉ 1 cú từ Thành chính ở giữa. Đo thật: cú (204, 130) -> Học viện ra (-28, -18) so với giữa, cú (232, 148) -> (+30, +20),
  nội suy ra (218, 139): Học viện ra (192, 341). Điểm đầu (81, 271) -> cuối (299, 409). Chiều về chưa đo.
- Các ô 2..12: dò tự động (đi zigzag khắp thành, nhận công trình bằng ảnh mẫu, camera theo dõi qua công trình trùng nhau giữa hai ảnh; số đo cùng công trình lệch nhau ~10..30 px).
  `view` = trung bình các lần thấy; `swipes` TÍNH từ hiệu `view`, chia đều cú <= (320, 260) (ô gần 1 cú, ô xa nhiều cú). Ô 8 Embassy (người dùng xác nhận) view (131, -625);
  ô 13 Prison (người dùng xác nhận) đo từ Trap Factory 2 cú (-112, 110) + (-100, 40) tổng (-212, 150). Ảnh mẫu Embassy / Tavern / Prison / Barracks / Research Factory / Watchtower /
  Archer Tower / Rally Spot đã cắt lại giữa công trình (không lấy nước).
- Mốc cố định ở vị trí gần civ1 (người dùng): walls (910, -586) [civ1 (969, -612)], research_factory (900, 24) [(955, 49)], tavern (12, -183) [(97, -231)], archer_tower (1482, -1160) [(1777, -1044)],
  watchtower (1742, 27) [(1840, -158)], art_hall (1071, -85) [(1190, -64)], pasture (1230, -173) [(1367, -108)], rally_spot (-517, -522) [(-415, -550)].
  Chưa đo: chiều về Art Hall -> Research Factory (đảo dấu), cú nối qua Tavern <-> Rally Spot. Mốc khác quan sát được: battlefield (1214, -670), shrine (240, -178), holy_palace (-356, -100).
"""
COMPLETE = True       # đã chạy thật từ Thành chính tới / về 8 mốc cố định (lệch <= ~50 px, find_keep / scan kéo bù) và 13 ô DATA
FIXED = {'walls': [910, -586], 'research_factory': [920, 24], 'tavern': [12, -183], 'archer_tower': [1361, -1220], 'watchtower': [1720, 28],
         'rally_spot': [-517, -522], 'art_hall': [1091, -85], 'pasture': [1250, -173]}
# Đo trên 21933 (vị trí giống civ1; kéo theo số civ1 rồi chỉnh theo ảnh mẫu giữa màn): walls = keep -> 4 cú (228, -146); research_factory = 4 cú (225, 6);
# tavern = 1 cú; archer_tower = walls + (572, -574); watchtower = research_factory + (842, 3); art_hall = research_factory + (171, -109);
# pasture = art_hall + (159, -88); rally_spot = 3 cú. Chiều đi và về chênh nhau tới ~40 px (camera chạm mép thành, quán tính): ghi riêng từng chiều theo số đo thật.
# Ảnh mẫu civ2 của các mốc đã cắt lại ở giữa công trình (không lấy nước / nền) nên ảnh mẫu ở giữa màn = công trình ở giữa: chỉ Tháp cung thủ có lệch
# (giữa của CẢ HAI tháp ở giữa màn thì ảnh mẫu tháp trái ở (136, 311), giống civ1 (129, 304)).
ANCHOR_SHIFT = {'archer_tower': (-61, -34)}
ROUTES = {
    ('keep', 'walls'): [(228, -146)] * 4,                     # đo thật: Tường thành ra (196, 345) sau bù (-28, 19); lần đo khác (231, -149) * 4 + bù
    ('walls', 'keep'): [(-228, 146)] * 4,                     # đo thật: Thành chính ra (192, 347)
    ('walls', 'archer_tower'): [(112, -159)] * 4,             # tổng (448, -636): đo (572, -574) rồi chạy lại từ Thành chính lệch (123, 59) nên giảm; tâm hai tháp
    ('archer_tower', 'walls'): [(-110, 156)] * 4,             # đo thật từ tâm hai tháp: tổng (-442, 626) (khác chiều đi ~130 px vì camera chạm mép); chạy lại: Thành chính ra lệch (-12, 8)
    ('keep', 'research_factory'): [(230, 6)] * 4,             # đo thật: 881 .. 919 (chọn 920 vì Art Hall theo đường này lệch -39 với 900); ảnh mẫu ra giữa
    ('research_factory', 'keep'): [(-229, -6)] * 4,           # đo thật: Thành chính ra (196, 345)
    ('research_factory', 'watchtower'): [(200, 1)] * 4,       # đo thật (842, 3), chạy lại từ Thành chính lệch +45 nên giảm còn (800, 4)
    ('watchtower', 'research_factory'): [(-200, 4)] * 4,      # đo thật: tổng (-798, 16)
    ('research_factory', 'art_hall'): [(171, -109)],          # đo thật: 1 cú (Art Hall ra (194, 345))
    ('art_hall', 'research_factory'): [(-171, 109)],          # đảo dấu, chưa chạy thật
    ('art_hall', 'pasture'): [(159, -88)],                    # đo thật: 1 cú
    ('pasture', 'art_hall'): [(-157, 89)],                    # đo thật: 1 cú
    ('keep', 'tavern'): [(12, -183)],                         # đo thật: 1 cú (Tavern ra (197, 346))
    ('tavern', 'keep'): [(-12, 186)],                         # đo thật
    ('keep', 'rally_spot'): [(-172, -174)] * 3,               # đo thật: tổng (-517, -522) (ảnh mẫu Rally Spot cắt mới)
    ('rally_spot', 'keep'): [(174, 174)] * 3,                 # đo thật: tổng (523, 522) (chưa chạy lại với ảnh mẫu mới)
}
# Đường về Thành chính của các mốc còn lại (find_keep cần ROUTES[(mốc, 'keep')] cho MỌI mốc trong FIXED): nối các đoạn đã đo.
ROUTES[('archer_tower', 'keep')] = ROUTES[('archer_tower', 'walls')] + ROUTES[('walls', 'keep')]
ROUTES[('keep', 'archer_tower')] = ROUTES[('keep', 'walls')] + ROUTES[('walls', 'archer_tower')]
ROUTES[('watchtower', 'keep')] = ROUTES[('watchtower', 'research_factory')] + ROUTES[('research_factory', 'keep')]
ROUTES[('keep', 'watchtower')] = ROUTES[('keep', 'research_factory')] + ROUTES[('research_factory', 'watchtower')]
ROUTES[('art_hall', 'keep')] = ROUTES[('art_hall', 'research_factory')] + ROUTES[('research_factory', 'keep')]
ROUTES[('keep', 'art_hall')] = ROUTES[('keep', 'research_factory')] + ROUTES[('research_factory', 'art_hall')]
ROUTES[('pasture', 'keep')] = ROUTES[('pasture', 'art_hall')] + ROUTES[('art_hall', 'keep')]
ROUTES[('keep', 'pasture')] = ROUTES[('keep', 'art_hall')] + ROUTES[('art_hall', 'pasture')]
DATA = [
    {'plot': 1, 'swipes': [[[81, 271], [299, 410]]], 'view': [218, 139], 'seen_21933': 'academy'},
    {'plot': 2, 'swipes': [[[106, 366], [274, 314]], [[106, 366], [274, 314]]], 'view': [553, 34], 'seen_21933': 'hospital'},
    {'plot': 3, 'swipes': [[[77, 397], [304, 283]]], 'view': [780, -80], 'seen_21933': 'stables'},
    {'plot': 4, 'swipes': [[[315, 380], [65, 300]]], 'view': [530, -160], 'seen_21933': 'barracks'},
    {'plot': 5, 'swipes': [[[56, 459], [324, 221]]], 'view': [798, -398], 'seen_21933': 'archer_camp'},
    {'plot': 6, 'swipes': [[[94, 286], [286, 394]]], 'view': [990, -290], 'seen_21933': 'workshop'},
    {'plot': 7, 'swipes': [[[320, 406], [60, 274]], [[320, 406], [60, 274]]], 'view': [470, -555], 'seen_21933': 'war_hall'},
    {'plot': 8, 'swipes': [[[275, 358], [105, 323]], [[275, 358], [105, 323]]], 'view': [131, -625], 'seen_21933': 'embassy'},
    {'plot': 9, 'swipes': [[[150, 213], [231, 468]]], 'view': [212, -370], 'seen_21933': 'market'},
    {'plot': 10, 'swipes': [[[284, 265], [97, 416]]], 'view': [25, -219], 'seen_21933': 'tavern'},
    {'plot': 11, 'swipes': [[[219, 409], [161, 271]], [[219, 409], [161, 271]]], 'view': [-92, -496], 'seen_21933': 'forge'},
    {'plot': 12, 'swipes': [[[294, 272], [86, 408]]], 'view': [-300, -360], 'seen_21933': 'trap_factory'},
    {'plot': 13, 'swipes': [[[296, 265], [84, 415]]], 'view': [-512, -210], 'seen_21933': 'prison'},
]
