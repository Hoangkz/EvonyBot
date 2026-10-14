"""city_tour.py (civ4) — các ô đi vòng khi quét bản đồ thành của nền văn minh 4 (máy 21933), dữ liệu tĩnh. Cùng cấu trúc với civ3/city_tour.py:
FIXED, ANCHOR_SHIFT, ROUTES, DATA (13 ô).

Đang đo dở: COMPLETE = False cho tới khi chạy rr.py từng route và scan thật. Thành chính ở giữa màn (197, 345) khớp 1,0.
- 13 ô: dò zigzag (explore.py) cho 11 ô, Trap Factory / Prison đo thêm bên trái Thành chính; `view` chỉnh theo kết quả tour_test.py.
- Mốc cố định (leg.py từ Thành chính chuẩn, bù tới lệch <= 12 px): walls (968, -536), research_factory (787, 94), tavern (-5, -225), rally_spot (-396, -480),
  shrine (270, -190), art_hall = research_factory + (205, -135), pasture = art_hall + (230, -112) (KHÁC civ3), watchtower = research_factory + (873, -169),
  battlefield = walls + (229, -75), archer_tower = walls + (676, -688) (tâm cặp tháp).
- Tháp cung thủ: ảnh mẫu khớp tháp trái khi tâm cặp ở giữa màn, ra (131, 291) => ANCHOR_SHIFT (-66, -54). Chiều về đo thật từ tâm cặp: tổng (-676, 688).
"""
COMPLETE = True        # đã chạy city_map.scan thật trên 21933: thấy đủ 13 ô + 10 mốc cố định (Prison khớp ~0,85 nên 1 lần quét trượt)
FIXED = {'walls': [987, -546], 'research_factory': [745, 90], 'tavern': [-5, -225], 'archer_tower': [1667, -1236], 'watchtower': [1615, -57],
         'rally_spot': [-411, -499], 'art_hall': [950, -45], 'pasture': [1205, -163], 'shrine': [270, -190], 'battlefield': [1216, -621]}
ANCHOR_SHIFT = {'archer_tower': (-66, -54)}
ROUTES = {
    ('keep', 'walls'): [(197, -109)] * 5,
    ('walls', 'keep'): [(-197, 109)] * 5,
    ('walls', 'archer_tower'): [(170, -173)] * 4,
    ('archer_tower', 'walls'): [(-180, 183)] * 4,
    ('keep', 'research_factory'): [(186, 22)] * 4,
    ('research_factory', 'keep'): [(-192, -23)] * 4,
    ('research_factory', 'watchtower'): [(217, -37)] * 4,
    ('watchtower', 'research_factory'): [(-220, 43)] * 4,
    ('research_factory', 'art_hall'): [(205, -135)],
    ('art_hall', 'research_factory'): [(-215, 134)],
    ('art_hall', 'pasture'): [(255, -118)],
    ('pasture', 'art_hall'): [(-230, 112)],
    ('keep', 'tavern'): [(-5, -225)],
    ('tavern', 'keep'): [(5, 225)],
    ('keep', 'rally_spot'): [(-206, -250)] * 2,
    ('rally_spot', 'keep'): [(210, 254)] * 2,
    ('keep', 'shrine'): [(135, -95)] * 2,
    ('shrine', 'keep'): [(-135, 95)] * 2,
    ('walls', 'battlefield'): [(229, -75)],
    ('battlefield', 'walls'): [(-229, 75)],
}
# Đường về / đi Thành chính của các mốc còn lại: nối các đoạn đã đo.
for _a, _b in (('archer_tower', 'walls'), ('battlefield', 'walls'), ('watchtower', 'research_factory'), ('art_hall', 'research_factory')):
    ROUTES[(_a, 'keep')] = ROUTES[(_a, _b)] + ROUTES[(_b, 'keep')]
    ROUTES[('keep', _a)] = ROUTES[('keep', _b)] + ROUTES[(_b, _a)]
ROUTES[('pasture', 'keep')] = ROUTES[('pasture', 'art_hall')] + ROUTES[('art_hall', 'keep')]
ROUTES[('keep', 'pasture')] = ROUTES[('keep', 'art_hall')] + ROUTES[('art_hall', 'pasture')]
DATA = [
    {'plot': 1, 'swipes': [[[102, 302], [278, 379]]], 'view': [168, 73], 'seen_21933': 'academy'},
    {'plot': 2, 'swipes': [[[93, 353], [287, 328]], [[93, 353], [287, 328]]], 'view': [555, 23], 'seen_21933': 'hospital'},
    {'plot': 3, 'swipes': [[[104, 415], [276, 265]]], 'view': [727, -127], 'seen_21933': 'stables'},
    {'plot': 4, 'swipes': [[[234, 391], [146, 290]]], 'view': [639, -228], 'seen_21933': 'barracks'},
    {'plot': 5, 'swipes': [[[129, 370], [251, 310]], [[129, 370], [251, 310]]], 'view': [882, -349], 'seen_21933': 'archer_camp'},
    {'plot': 6, 'swipes': [[[104, 295], [276, 385]]], 'view': [1054, -259], 'seen_21933': 'workshop'},
    {'plot': 7, 'swipes': [[[295, 390], [86, 291]], [[295, 390], [86, 291]], [[295, 390], [86, 291]]], 'view': [426, -555], 'seen_21933': 'war_hall'},
    {'plot': 8, 'swipes': [[[306, 396], [75, 285]]], 'view': [195, -666], 'seen_21933': 'embassy'},
    {'plot': 9, 'swipes': [[[147, 225], [234, 455]]], 'view': [282, -436], 'seen_21933': 'market'},
    {'plot': 10, 'swipes': [[[267, 285], [113, 395]], [[267, 285], [113, 395]]], 'view': [-26, -216], 'seen_21933': 'tavern'},
    {'plot': 11, 'swipes': [[[190, 414], [190, 266]], [[190, 414], [190, 266]]], 'view': [-27, -512], 'seen_21933': 'forge'},
    {'plot': 12, 'swipes': [[[297, 262], [84, 418]]], 'view': [-240, -356], 'seen_21933': 'trap_factory'},
    {'plot': 13, 'swipes': [[[252, 318], [128, 362]], [[252, 318], [128, 362]]], 'view': [-487, -267], 'seen_21933': 'prison'},
]
