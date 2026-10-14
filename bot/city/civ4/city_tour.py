"""city_tour.py (civ4) — các ô đi vòng khi quét bản đồ thành của nền văn minh 4 (máy 21933), dữ liệu tĩnh. Cùng cấu trúc với civ3/city_tour.py:
FIXED, ANCHOR_SHIFT, ROUTES, DATA (13 ô).

Đang đo dở: COMPLETE = False cho tới khi chạy rr.py từng route và scan thật. Thành chính ở giữa màn (197, 345) khớp 1,0.
- 13 ô: dò zigzag (explore.py) cho 11 ô, Trap Factory / Prison đo thêm bên trái Thành chính; `view` chỉnh theo kết quả tour_test.py.
- Mốc cố định (leg.py từ Thành chính chuẩn, bù tới lệch <= 12 px): walls (968, -536), research_factory (787, 94), tavern (-5, -225), rally_spot (-396, -480),
  shrine (270, -190), art_hall = research_factory + (205, -135), pasture = art_hall + (230, -112) (KHÁC civ3), watchtower = research_factory + (873, -169),
  battlefield = walls + (229, -75), archer_tower = walls + (676, -688) (tâm cặp tháp).
- Tháp cung thủ: ảnh mẫu khớp tháp trái khi tâm cặp ở giữa màn, ra (131, 291) => ANCHOR_SHIFT (-66, -54). Chiều về đo thật từ tâm cặp: tổng (-676, 688).
"""
COMPLETE = False
FIXED = {'walls': [968, -536], 'research_factory': [787, 94], 'tavern': [-5, -225], 'archer_tower': [1644, -1224], 'watchtower': [1660, -75],
         'rally_spot': [-396, -480], 'art_hall': [992, -41], 'pasture': [1222, -153], 'shrine': [270, -190], 'battlefield': [1197, -611]}
ANCHOR_SHIFT = {'archer_tower': (-66, -54)}
ROUTES = {
    ('keep', 'walls'): [(242, -134)] * 4,
    ('walls', 'keep'): [(-242, 134)] * 4,
    ('walls', 'archer_tower'): [(169, -172)] * 4,
    ('archer_tower', 'walls'): [(-169, 172)] * 4,
    ('keep', 'research_factory'): [(197, 24)] * 4,
    ('research_factory', 'keep'): [(-187, -22)] * 4,
    ('research_factory', 'watchtower'): [(218, -42)] * 4,
    ('watchtower', 'research_factory'): [(-218, 42)] * 4,
    ('research_factory', 'art_hall'): [(205, -135)],
    ('art_hall', 'research_factory'): [(-205, 135)],
    ('art_hall', 'pasture'): [(230, -112)],
    ('pasture', 'art_hall'): [(-247, 118)],
    ('keep', 'tavern'): [(-5, -225)],
    ('tavern', 'keep'): [(5, 225)],
    ('keep', 'rally_spot'): [(-132, -160)] * 3,
    ('rally_spot', 'keep'): [(132, 160)] * 3,
    ('keep', 'shrine'): [(135, -95)] * 2,
    ('shrine', 'keep'): [(-135, 95)] * 2,
    ('walls', 'battlefield'): [(229, -75)],
    ('battlefield', 'walls'): [(-266, 87)],
}
# Đường về / đi Thành chính của các mốc còn lại: nối các đoạn đã đo.
for _a, _b in (('archer_tower', 'walls'), ('battlefield', 'walls'), ('watchtower', 'research_factory'), ('art_hall', 'research_factory')):
    ROUTES[(_a, 'keep')] = ROUTES[(_a, _b)] + ROUTES[(_b, 'keep')]
    ROUTES[('keep', _a)] = ROUTES[('keep', _b)] + ROUTES[(_b, _a)]
ROUTES[('pasture', 'keep')] = ROUTES[('pasture', 'art_hall')] + ROUTES[('art_hall', 'keep')]
ROUTES[('keep', 'pasture')] = ROUTES[('keep', 'art_hall')] + ROUTES[('art_hall', 'pasture')]
DATA = [
    {'plot': 1, 'swipes': [[[102, 302], [278, 379]]], 'view': [176, 77], 'seen_21933': 'academy'},
    {'plot': 2, 'swipes': [[[90, 353], [290, 328]], [[90, 353], [290, 328]]], 'view': [575, 27], 'seen_21933': 'hospital'},
    {'plot': 3, 'swipes': [[[104, 416], [276, 265]]], 'view': [747, -124], 'seen_21933': 'stables'},
    {'plot': 4, 'swipes': [[[237, 392], [144, 288]]], 'view': [654, -228], 'seen_21933': 'barracks'},
    {'plot': 5, 'swipes': [[[76, 399], [304, 282]]], 'view': [882, -345], 'seen_21933': 'archer_camp'},
    {'plot': 6, 'swipes': [[[104, 297], [276, 384]]], 'view': [1054, -258], 'seen_21933': 'workshop'},
    {'plot': 7, 'swipes': [[[293, 389], [87, 292]], [[293, 389], [87, 292]], [[293, 389], [87, 292]]], 'view': [436, -549], 'seen_21933': 'war_hall'},
    {'plot': 8, 'swipes': [[[298, 392], [82, 288]]], 'view': [220, -653], 'seen_21933': 'embassy'},
    {'plot': 9, 'swipes': [[[149, 232], [231, 449]]], 'view': [302, -436], 'seen_21933': 'market'},
    {'plot': 10, 'swipes': [[[266, 282], [114, 398]], [[266, 282], [114, 398]]], 'view': [-2, -205], 'seen_21933': 'tavern'},
    {'plot': 11, 'swipes': [[[192, 410], [188, 270]], [[192, 410], [188, 270]]], 'view': [-9, -484], 'seen_21933': 'forge'},
    {'plot': 12, 'swipes': [[[291, 266], [90, 414]]], 'view': [-210, -336], 'seen_21933': 'trap_factory'},
    {'plot': 13, 'swipes': [[[305, 298], [76, 382]]], 'view': [-439, -252], 'seen_21933': 'prison'},
]
