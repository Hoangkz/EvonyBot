"""city_tour.py (civ5) — các ô đi vòng khi quét bản đồ thành của nền văn minh 5 (máy 21933), dữ liệu tĩnh. Cùng cấu trúc với civ4/city_tour.py:
FIXED, ANCHOR_SHIFT, ROUTES, DATA (13 ô).

Đang đo dở: COMPLETE = False cho tới khi chạy rr.py từng route và scan thật. Thành chính ở giữa màn (197, 345) khớp 1,0.
- Đo bằng tests/city/measure/auto.py (đi theo ước lượng số civ4, tự bù / tìm quanh, in tổng vuốt từng đoạn) + sweep.py (quét tìm War Hall) + leg.py.
  Vị trí civ5 KHÁC civ4 nhiều (Học viện (365, 75), War Hall (320, -679) ...).
- Mốc cố định: walls (984, -660), research_factory (912, 28), tavern (91, -267), rally_spot (-410, -506), shrine (360, -239), art_hall = research_factory + (196, -97),
  pasture = art_hall + (204, -108), watchtower = research_factory + (847, -180), battlefield = walls + (228, -45), archer_tower = walls + (513, -487) (tâm cặp tháp).
- Tháp cung thủ: ảnh mẫu khớp tháp trái khi tâm cặp ở giữa màn, ra (121, 305) => ANCHOR_SHIFT (-76, -40).
"""
COMPLETE = True
FIXED = {'walls': [984, -660], 'research_factory': [912, 28], 'tavern': [91, -267], 'archer_tower': [1497, -1147], 'watchtower': [1759, -152],
         'rally_spot': [-410, -506], 'art_hall': [1108, -69], 'pasture': [1312, -177], 'shrine': [360, -239], 'battlefield': [1212, -705]}
ANCHOR_SHIFT = {'archer_tower': (-76, -40)}
ROUTES = {
    ('keep', 'walls'): [(204, -135)] * 5,
    ('walls', 'keep'): [(-196, 133)] * 5,
    ('walls', 'archer_tower'): [(171, -162)] * 3,
    ('archer_tower', 'walls'): [(-171, 162)] * 3,
    ('keep', 'research_factory'): [(226, 8)] * 4,
    ('research_factory', 'keep'): [(-224, -6)] * 4,
    ('research_factory', 'watchtower'): [(211, -44)] * 4,
    ('watchtower', 'research_factory'): [(-210, 45)] * 4,
    ('research_factory', 'art_hall'): [(196, -97)],
    ('art_hall', 'research_factory'): [(-195, 95)],
    ('art_hall', 'pasture'): [(204, -108)],
    ('pasture', 'art_hall'): [(-209, 109)],
    ('keep', 'tavern'): [(46, -134)] * 2,
    ('tavern', 'keep'): [(-45, 131)] * 2,
    ('keep', 'rally_spot'): [(-218, -266)] * 2,
    ('rally_spot', 'keep'): [(210, 254)] * 2,
    ('keep', 'shrine'): [(189, -126)] * 2,
    ('shrine', 'keep'): [(-182, 120)] * 2,
    ('walls', 'battlefield'): [(243, -57)],
    ('battlefield', 'walls'): [(-225, 54)],
}
# Đường về / đi Thành chính của các mốc còn lại: nối các đoạn đã đo.
for _a, _b in (('archer_tower', 'walls'), ('battlefield', 'walls'), ('watchtower', 'research_factory'), ('art_hall', 'research_factory')):
    ROUTES[(_a, 'keep')] = ROUTES[(_a, _b)] + ROUTES[(_b, 'keep')]
    ROUTES[('keep', _a)] = ROUTES[('keep', _b)] + ROUTES[(_b, _a)]
ROUTES[('pasture', 'keep')] = ROUTES[('pasture', 'art_hall')] + ROUTES[('art_hall', 'keep')]
ROUTES[('keep', 'pasture')] = ROUTES[('keep', 'art_hall')] + ROUTES[('art_hall', 'pasture')]
DATA = [
    {'plot': 1, 'swipes': [[[94, 319], [286, 361]], [[94, 319], [286, 361]]], 'view': [385, 84], 'seen_21933': 'academy'},
    {'plot': 2, 'swipes': [[[120, 372], [260, 308]], [[120, 372], [260, 308]]], 'view': [665, -45], 'seen_21933': 'hospital'},
    {'plot': 3, 'swipes': [[[98, 373], [282, 307]]], 'view': [849, -111], 'seen_21933': 'stables'},
    {'plot': 4, 'swipes': [[[283, 393], [98, 287]]], 'view': [664, -217], 'seen_21933': 'barracks'},
    {'plot': 5, 'swipes': [[[113, 372], [268, 308]], [[113, 372], [268, 308]]], 'view': [974, -345], 'seen_21933': 'archer_camp'},
    {'plot': 6, 'swipes': [[[112, 299], [269, 382]]], 'view': [1131, -262], 'seen_21933': 'workshop'},
    {'plot': 7, 'swipes': [[[288, 392], [92, 288]], [[288, 392], [92, 288]], [[288, 392], [92, 288]], [[288, 392], [92, 288]]], 'view': [345, -677], 'seen_21933': 'war_hall'},
    {'plot': 8, 'swipes': [[[274, 359], [107, 321]]], 'view': [178, -715], 'seen_21933': 'embassy'},
    {'plot': 9, 'swipes': [[[175, 271], [205, 409]], [[175, 271], [205, 409]]], 'view': [238, -439], 'seen_21933': 'market'},
    {'plot': 10, 'swipes': [[[246, 256], [134, 424]]], 'view': [126, -271], 'seen_21933': 'tavern'},
    {'plot': 11, 'swipes': [[[224, 406], [157, 274]], [[224, 406], [157, 274]]], 'view': [-8, -535], 'seen_21933': 'forge'},
    {'plot': 12, 'swipes': [[[306, 295], [75, 385]]], 'view': [-239, -445], 'seen_21933': 'trap_factory'},
    {'plot': 13, 'swipes': [[[257, 291], [123, 389]], [[257, 291], [123, 389]]], 'view': [-506, -248], 'seen_21933': 'prison'},
]
