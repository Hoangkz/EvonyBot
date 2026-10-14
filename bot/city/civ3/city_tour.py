"""city_tour.py (civ3) — các ô đi vòng khi quét bản đồ thành của nền văn minh 3 (máy 21933), dữ liệu tĩnh. Cùng cấu trúc với civ2/city_tour.py:
FIXED, ANCHOR_SHIFT, ROUTES, DATA (13 ô).

Đang đo dở: COMPLETE = False cho tới khi chạy thử tour 13 ô (tour_test.py) và rr.py từng route. Thành chính ở giữa màn (197, 345) khớp 1,0.
- 13 ô: dò zigzag (explore.py) cho 11 ô, Trap Factory / Prison đo thêm bên trái Thành chính. Số dò zigzag có thể lệch (camera cộng dồn, các mốc đo bằng leg.py
  ngắn hơn số dò ~4-10 %), cần chạy tour_test.py để chỉnh `view`.
- Mốc cố định (leg.py, từ Thành chính chuẩn, bù tới lệch <= 12 px): walls (938, -539), research_factory (764, 36), tavern (72, -218), rally_spot (-360, -486),
  art_hall = research_factory + (198, -147), pasture = art_hall + (211, -75), watchtower = research_factory + (806, -183), archer_tower = walls + (572, -648),
  shrine (307, -215), battlefield = walls + (229, -75).
- Tháp cung thủ: ảnh mẫu khớp tháp nào cũng được; "giữa" là tâm cả hai tháp: tháp trái ra (108, 332) khi tâm cặp ở giữa màn => ANCHOR_SHIFT (-89, -13).
  Chiều về archer_tower -> walls tính từ tâm cặp (số đo từ lúc tháp ở giữa trừ phần bù (89, 13)).
"""
COMPLETE = True        # đã chạy city_map.scan thật trên 21933: thấy đủ 13 ô + 10 mốc cố định (lệch so với route <= 45 px)
FIXED = {'walls': [973, -558], 'research_factory': [764, 36], 'tavern': [72, -218], 'archer_tower': [1585, -1251], 'watchtower': [1608, -126],
         'rally_spot': [-360, -486], 'art_hall': [1004, -134], 'pasture': [1215, -209], 'shrine': [308, -216], 'battlefield': [1184, -633]}
ANCHOR_SHIFT = {'archer_tower': (-89, -13)}
# Đo lại bằng tests/city/measure/auto.py (từng đoạn đi + về, bù tới lệch <= 12 px; archer_tower tính theo tâm cặp tháp).
ROUTES = {
    ('keep', 'walls'): [(195, -112)] * 5,
    ('walls', 'keep'): [(-192, 111)] * 5,
    ('walls', 'archer_tower'): [(204, -231)] * 3,
    ('archer_tower', 'walls'): [(-191, 216)] * 3,
    ('keep', 'research_factory'): [(191, 9)] * 4,
    ('research_factory', 'keep'): [(-191, -9)] * 4,
    ('research_factory', 'watchtower'): [(211, -41)] * 4,
    ('watchtower', 'research_factory'): [(-209, 40)] * 4,
    ('research_factory', 'art_hall'): [(240, -170)],
    ('art_hall', 'research_factory'): [(-173, 121)],
    ('art_hall', 'pasture'): [(211, -75)],
    ('pasture', 'art_hall'): [(-211, 75)],
    ('keep', 'tavern'): [(72, -218)],
    ('tavern', 'keep'): [(-76, 251)],
    ('keep', 'rally_spot'): [(-180, -243)] * 2,
    ('rally_spot', 'keep'): [(196, 262)] * 2,
    ('keep', 'shrine'): [(154, -108)] * 2,
    ('shrine', 'keep'): [(-154, 108)] * 2,
    ('walls', 'battlefield'): [(211, -75)],
    ('battlefield', 'walls'): [(-203, 66)],
}
# Đường về / đi Thành chính của các mốc còn lại: nối các đoạn đã đo.
for _a, _b in (('archer_tower', 'walls'), ('battlefield', 'walls'), ('watchtower', 'research_factory'), ('art_hall', 'research_factory')):
    ROUTES[(_a, 'keep')] = ROUTES[(_a, _b)] + ROUTES[(_b, 'keep')]
    ROUTES[('keep', _a)] = ROUTES[('keep', _b)] + ROUTES[(_b, _a)]
ROUTES[('pasture', 'keep')] = ROUTES[('pasture', 'art_hall')] + ROUTES[('art_hall', 'keep')]
ROUTES[('keep', 'pasture')] = ROUTES[('keep', 'art_hall')] + ROUTES[('art_hall', 'pasture')]
DATA = [
    {'plot': 1, 'swipes': [[[70, 309], [310, 371]], [[70, 309], [310, 371]]], 'view': [466, 117], 'seen_21933': 'academy'},
    {'plot': 2, 'swipes': [[[148, 414], [232, 267]]], 'view': [550, -30], 'seen_21933': 'hospital'},
    {'plot': 3, 'swipes': [[[99, 379], [281, 302]]], 'view': [732, -107], 'seen_21933': 'stables'},
    {'plot': 4, 'swipes': [[[281, 391], [99, 290]]], 'view': [550, -208], 'seen_21933': 'barracks'},
    {'plot': 5, 'swipes': [[[126, 382], [254, 299]], [[126, 382], [254, 299]]], 'view': [807, -374], 'seen_21933': 'archer_camp'},
    {'plot': 6, 'swipes': [[[99, 299], [281, 381]]], 'view': [989, -292], 'seen_21933': 'workshop'},
    {'plot': 7, 'swipes': [[[284, 380], [96, 300]], [[284, 380], [96, 300]], [[284, 380], [96, 300]]], 'view': [426, -533], 'seen_21933': 'war_hall'},
    {'plot': 8, 'swipes': [[[269, 377], [112, 303]], [[269, 377], [112, 303]]], 'view': [112, -680], 'seen_21933': 'embassy'},
    {'plot': 9, 'swipes': [[[155, 266], [225, 414]], [[155, 266], [225, 414]]], 'view': [253, -383], 'seen_21933': 'market'},
    {'plot': 10, 'swipes': [[[289, 253], [91, 427]]], 'view': [55, -209], 'seen_21933': 'tavern'},
    {'plot': 11, 'swipes': [[[214, 410], [166, 270]], [[214, 410], [166, 270]]], 'view': [-42, -489], 'seen_21933': 'forge'},
    {'plot': 12, 'swipes': [[[280, 300], [101, 380]]], 'view': [-221, -409], 'seen_21933': 'trap_factory'},
    {'plot': 13, 'swipes': [[[264, 266], [117, 415]]], 'view': [-368, -260], 'seen_21933': 'prison'},
]
