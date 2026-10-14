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
COMPLETE = False
FIXED = {'walls': [938, -539], 'research_factory': [764, 36], 'tavern': [72, -218], 'archer_tower': [1510, -1187], 'watchtower': [1570, -147],
         'rally_spot': [-360, -486], 'art_hall': [962, -111], 'pasture': [1173, -186], 'shrine': [307, -215], 'battlefield': [1167, -614]}
ANCHOR_SHIFT = {'archer_tower': (-89, -13)}
ROUTES = {
    ('keep', 'walls'): [(234, -135)] * 4,
    ('walls', 'keep'): [(-249, 143)] * 4,
    ('walls', 'archer_tower'): [(143, -162)] * 4,
    ('archer_tower', 'walls'): [(-144, 154)] * 4,
    ('keep', 'research_factory'): [(191, 9)] * 4,
    ('research_factory', 'keep'): [(-191, -9)] * 4,
    ('research_factory', 'watchtower'): [(202, -46)] * 4,
    ('watchtower', 'research_factory'): [(-202, 38)] * 4,
    ('research_factory', 'art_hall'): [(198, -147)],
    ('art_hall', 'research_factory'): [(-213, 150)],
    ('art_hall', 'pasture'): [(211, -75)],
    ('pasture', 'art_hall'): [(-211, 75)],
    ('keep', 'tavern'): [(72, -218)],
    ('tavern', 'keep'): [(-72, 218)],
    ('keep', 'rally_spot'): [(-120, -162)] * 3,
    ('rally_spot', 'keep'): [(120, 162)] * 3,
    ('keep', 'shrine'): [(154, -108)] * 2,
    ('shrine', 'keep'): [(-154, 108)] * 2,
    ('walls', 'battlefield'): [(229, -75)],
    ('battlefield', 'walls'): [(-207, 67)],
}
# Đường về / đi Thành chính của các mốc còn lại: nối các đoạn đã đo.
for _a, _b in (('archer_tower', 'walls'), ('battlefield', 'walls'), ('watchtower', 'research_factory'), ('art_hall', 'research_factory')):
    ROUTES[(_a, 'keep')] = ROUTES[(_a, _b)] + ROUTES[(_b, 'keep')]
    ROUTES[('keep', _a)] = ROUTES[('keep', _b)] + ROUTES[(_b, _a)]
ROUTES[('pasture', 'keep')] = ROUTES[('pasture', 'art_hall')] + ROUTES[('art_hall', 'keep')]
ROUTES[('keep', 'pasture')] = ROUTES[('keep', 'art_hall')] + ROUTES[('art_hall', 'pasture')]
DATA = [
    {'plot': 1, 'swipes': [[[70, 309], [310, 371]], [[70, 309], [310, 371]]], 'view': [481, 123], 'seen_21933': 'academy'},
    {'plot': 2, 'swipes': [[[149, 414], [232, 267]]], 'view': [564, -24], 'seen_21933': 'hospital'},
    {'plot': 3, 'swipes': [[[99, 379], [282, 301]]], 'view': [747, -102], 'seen_21933': 'stables'},
    {'plot': 4, 'swipes': [[[275, 390], [106, 291]]], 'view': [578, -201], 'seen_21933': 'barracks'},
    {'plot': 5, 'swipes': [[[64, 421], [316, 259]]], 'view': [830, -363], 'seen_21933': 'archer_camp'},
    {'plot': 6, 'swipes': [[[98, 299], [282, 381]]], 'view': [1014, -281], 'seen_21933': 'workshop'},
    {'plot': 7, 'swipes': [[[330, 399], [50, 281]], [[330, 399], [50, 281]]], 'view': [454, -518], 'seen_21933': 'war_hall'},
    {'plot': 8, 'swipes': [[[346, 412], [34, 268]]], 'view': [142, -662], 'seen_21933': 'embassy'},
    {'plot': 9, 'swipes': [[[154, 266], [226, 414]], [[154, 266], [226, 414]]], 'view': [285, -366], 'seen_21933': 'market'},
    {'plot': 10, 'swipes': [[[278, 262], [102, 419]]], 'view': [109, -209], 'seen_21933': 'tavern'},
    {'plot': 11, 'swipes': [[[214, 406], [166, 274]], [[214, 406], [166, 274]]], 'view': [13, -472], 'seen_21933': 'forge'},
    {'plot': 12, 'swipes': [[[278, 302], [102, 379]]], 'view': [-163, -395], 'seen_21933': 'trap_factory'},
    {'plot': 13, 'swipes': [[[263, 266], [117, 415]]], 'view': [-309, -246], 'seen_21933': 'prison'},
]
