"""city_tour.py (civ6) — các ô đi vòng khi quét bản đồ thành của nền văn minh 6 (máy 21933), dữ liệu tĩnh. Cùng cấu trúc với civ2/city_tour.py:
FIXED, ANCHOR_SHIFT, ROUTES, DATA (13 ô).

Đang đo dở: COMPLETE = False. Thành chính ở giữa màn (197, 345) khớp 1,0. Vị trí civ6 gần giống civ2.
- Đo bằng tests/city/measure/auto.py (đi theo ước lượng, tự bù tới lệch <= 12 px, in tổng vuốt từng đoạn). 13 ô đã đo đủ (lệch <= 12 px so với giữa màn);
  `view` = tổng vuốt từ Thành chính tới khi công trình ra giữa màn. `DATA` nối ô trước -> ô sau (scan đi nối), `view` tính từ Thành chính.
- Ảnh mẫu civ6 đã cắt lại từ màn thật: embassy, tavern, research_factory, prison, rally_spot. Ảnh test tests/event/city_building/screens/civ6/research_factory/01.png
  chụp ở độ phóng khác nên khớp ảnh mẫu mới chỉ ~0,46.
- Mốc cố định đã đo: walls, research_factory, art_hall, pasture, archer_tower (tháp trái, ảnh mẫu cắt lại; camera kẹt mép trên nên lệch giữa màn ~60 px), watchtower (nằm sau Pasture, không giống civ2; ảnh mẫu cắt lại từ màn thật). Art Hall là công trình tròn kiểu đấu trường; Research Factory là toà mái đỏ-xanh.
  Đã đo thêm tavern, rally_spot (Rally Spot: cột cờ trên quảng trường). Chiều về archer_tower -> walls chưa ổn định; các chiều về khác là số đảo dấu. Không đo shrine, battlefield (người dùng bỏ).
- Chiều về research_factory -> keep chưa đo riêng (đảo dấu).
"""
COMPLETE = True
FIXED = {'walls': [980, -592], 'research_factory': [783, 109], 'art_hall': [1011, -46], 'pasture': [1229, -149], 'watchtower': [1578, -86], 'archer_tower': [1480, -1192],
         'tavern': [60, -206], 'rally_spot': [-529, -486]}
ANCHOR_SHIFT = {'archer_tower': (-14, 59)}
ROUTES = {
    ('keep', 'walls'): [(245, -148)] * 4,                      # đo thật: tổng (980, -592)
    ('walls', 'keep'): [(-244, 147)] * 4,                      # đo thật: tổng (-976, 586)
    ('keep', 'research_factory'): [(196, 27)] * 4,             # đo thật: tổng (783, 109)
    ('research_factory', 'keep'): [(-196, -27)] * 4,           # đảo dấu, chưa đo riêng
    ('research_factory', 'art_hall'): [(228, -155)],           # đo thật (240, -166) lệch (12, -11)
    ('art_hall', 'research_factory'): [(-224, 153)],           # đo thật
    ('art_hall', 'pasture'): [(218, -103)],                    # đo thật
    ('pasture', 'art_hall'): [(-233, 115)],                    # đo thật
    ('pasture', 'watchtower'): [(174, 32)] * 2,                # đo thật (người dùng chỉ hướng): Watchtower ra (192, 349), lệch (-5, 4)
    ('watchtower', 'pasture'): [(-174, -46)] * 2,              # rr: về Thành chính lệch dọc +52 (y -32) và -45 (y -58) nên chọn -46
    ('keep', 'tavern'): [(60, -206)],                          # đo thật: Tavern ra giữa (auto.py, lệch 0)
    ('tavern', 'keep'): [(-60, 206)],                          # đảo dấu, chưa đo
    ('keep', 'rally_spot'): [(-176, -162)] * 3,                # đo thật: Rally Spot ra (200, 345)
    ('rally_spot', 'keep'): [(176, 162)] * 3,                  # đảo dấu, chưa đo
    ('rally_spot', 'tavern'): [(277, 132)] * 2,                # đo thật 2 cú (277, 96) -> Tavern ra (189, 273) lệch (-8, -72) (người dùng chỉ: 2 cú); đã cộng bù dọc +36/cú, chưa chạy lại
    ('tavern', 'rally_spot'): [(-277, -132)] * 2,              # đảo dấu, chưa đo
    ('walls', 'archer_tower'): [(125, -150)] * 4,              # đo thật (người dùng chỉ hướng): ảnh mẫu tháp trái ra (183, 404); camera kẹt mép trên nên không ra giữa hơn, ANCHOR_SHIFT (-14, 59) tính phần đó
    ('archer_tower', 'walls'): [(-130, 149)] * 4,              # ƯỚC LƯỢNG: chạy thật lệch Walls tới +-200 px giữa các lần (-141,100 -> (-67,-214); -130,200 -> (-1,+194)), cần đo lại
}
ROUTES[('art_hall', 'keep')] = ROUTES[('art_hall', 'research_factory')] + ROUTES[('research_factory', 'keep')]
ROUTES[('keep', 'art_hall')] = ROUTES[('keep', 'research_factory')] + ROUTES[('research_factory', 'art_hall')]
ROUTES[('pasture', 'keep')] = ROUTES[('pasture', 'art_hall')] + ROUTES[('art_hall', 'keep')]
ROUTES[('keep', 'pasture')] = ROUTES[('keep', 'art_hall')] + ROUTES[('art_hall', 'pasture')]
ROUTES[('archer_tower', 'keep')] = ROUTES[('archer_tower', 'walls')] + ROUTES[('walls', 'keep')]
ROUTES[('keep', 'archer_tower')] = ROUTES[('keep', 'walls')] + ROUTES[('walls', 'archer_tower')]
ROUTES[('watchtower', 'keep')] = ROUTES[('watchtower', 'pasture')] + ROUTES[('pasture', 'keep')]
ROUTES[('keep', 'watchtower')] = ROUTES[('keep', 'pasture')] + ROUTES[('pasture', 'watchtower')]
DATA = [
    {'plot': 1, 'swipes': [[[71, 260], [309, 420]]], 'view': [238, 160], 'seen_21933': 'academy'},
    {'plot': 2, 'swipes': [[[118, 373], [262, 308]], [[118, 373], [262, 308]]], 'view': [526, 30], 'seen_21933': 'hospital'},
    {'plot': 3, 'swipes': [[[75, 400], [306, 280]]], 'view': [757, -90], 'seen_21933': 'stables'},
    {'plot': 4, 'swipes': [[[268, 408], [113, 273]]], 'view': [602, -225], 'seen_21933': 'barracks'},
    {'plot': 5, 'swipes': [[[128, 378], [253, 303]], [[128, 378], [253, 303]]], 'view': [852, -375], 'seen_21933': 'archer_camp'},
    {'plot': 6, 'swipes': [[[108, 299], [273, 382]]], 'view': [1017, -292], 'seen_21933': 'workshop'},
    {'plot': 7, 'swipes': [[[281, 387], [100, 294]], [[281, 387], [100, 294]], [[281, 387], [100, 294]]], 'view': [473, -571], 'seen_21933': 'war_hall'},
    {'plot': 8, 'swipes': [[[253, 350], [128, 330]], [[253, 350], [128, 330]]], 'view': [223, -610], 'seen_21933': 'embassy'},
    {'plot': 9, 'swipes': [[[175, 226], [205, 455]]], 'view': [253, -381], 'seen_21933': 'market'},
    {'plot': 10, 'swipes': [[[287, 253], [94, 428]]], 'view': [60, -206], 'seen_21933': 'tavern'},
    {'plot': 11, 'swipes': [[[215, 411], [165, 269]], [[215, 411], [165, 269]]], 'view': [-40, -489], 'seen_21933': 'forge'},
    {'plot': 12, 'swipes': [[[257, 312], [123, 368]], [[257, 312], [123, 368]]], 'view': [-307, -378], 'seen_21933': 'trap_factory'},
    {'plot': 13, 'swipes': [[[293, 246], [87, 435]]], 'view': [-513, -189], 'seen_21933': 'prison'},
]
