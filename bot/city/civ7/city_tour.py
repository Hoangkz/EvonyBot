"""city_tour.py (civ7) — các ô đi vòng khi quét bản đồ thành của nền văn minh 7, dữ liệu tĩnh. Cùng cấu trúc với civ1/city_tour.py
(xem file đó): FIXED, ANCHOR_SHIFT, ROUTES, DATA (13 ô).

Đang đo dở (máy 21933): đã đo đủ 13 ô (thiếu FIXED / ROUTES / ANCHOR_SHIFT). Thứ tự ô civ7 không giống civ1 (ô 2 là Bệnh viện). COMPLETE = False nên tours.py chưa bật civ7; đủ FIXED / ROUTES / 13 ô thì đổi thành True.
- ô 1 (Học viện): từ Thành chính ở giữa màn (ảnh mẫu keep ở (197, 345)) cùng hướng civ1 nhưng ngắn hơn: cú 1 ngón tay (157, 59) thì
  Học viện ra (175, 284), cú 2 (22, 61) thì Học viện ở (198, 347); tổng (179, 120).
  Chiều về (đo thật trên 21933, từ lúc Học viện ở giữa): 1 cú (-179, -120), điểm đầu (279, 400) -> cuối (101, 280) thì Thành chính ra
  (199, 343), lệch (2, -2) so với giữa (197, 345).
- ô 2 (Bệnh viện): từ Học viện ở giữa vuốt 2 cú giống nhau (180, -32), điểm đầu (100, 246) -> cuối (280, 214), thì Bệnh viện ra (216..223, 340),
  người dùng xác nhận đúng ô; tổng (360, -64). Điểm đầu y 246 / 356 / 466 đều làm màn đổi; y 324 (280, 324) từng trúng chỗ game coi là bấm
  nên cú thứ hai không dịch.
  Chiều về (đo thật, người dùng xác nhận chính xác): 2 cú giống nhau (-180, 32), điểm đầu (280, 214) -> cuối (100, 246) thì Học viện ra
  (203, 341), lệch (6, -4) so với giữa.
- ô 3 (Chuồng ngựa / Stables, người dùng chỉ là ô 3): từ Bệnh viện ở giữa vuốt 1 cú (113, -129), điểm đầu (134, 404) -> cuối (247, 275). TÍNH từ hiệu toạ độ trên
  cùng một màn (Chuồng ngựa = Bệnh viện + (-132, +133)), CHƯA chạy lại từ Bệnh viện; đo thật phần cuối: Chuồng ngựa ở (61, 440) -> 1 cú (136, -95) -> (208, 338).
  Ảnh mẫu người dùng chụp (Screenshot_20261013-224522.png, 122x105) khớp 0,971.
- ô 4 (Barracks / Bộ binh, thẳng xuống dưới Chuồng ngựa một chút): từ Chuồng ngựa ở (197, 337) (Barracks ở (199, 501) trên cùng màn) vuốt 1 cú (-13, -157),
  điểm đầu (196, 418) -> cuối (183, 261) thì Barracks ra (185, 332), điểm khớp 0,968, lệch (-12, -13) so với giữa (đo thật trên 21933).
- ô 5 (Trại cung thủ / Archer Camp): từ Barracks (185, 332) vuốt 1 cú (113, -129) giống ô 2 -> 3, điểm đầu (134, 404) -> cuối (247, 275) thì Trại cung thủ ra
  (170, 324), điểm khớp 0,99, lệch (-27, -21) so với giữa (đo thật trên 21933; lệch x nhỉnh hơn dung sai 25 px, scan sẽ kéo bù).
- ô 6 (Xưởng / Workshop; ảnh người dùng chụp Screenshot_20261013-225035.png 104x75 khớp 0,966): từ Trại cung thủ (170, 324) vuốt 1 cú (145, 98), điểm đầu
  (118, 291) -> cuối (263, 389) thì ô 6 ra (209, 353), điểm khớp 0,944, lệch (12, 8) so với giữa (đo thật trên 21933).
- ô 7 (War Hall): từ Xưởng (ô 6) vuốt 3 cú giống nhau của civ1 ô 7: (-148, -84), điểm đầu (264, 382) -> cuối (116, 298), tổng (-444, -252)
  thì War Hall ra (233, 309), điểm khớp 0,959, lệch (36, -36) so với giữa (đo thật trên 21933, người dùng xác nhận đúng ô; scan sẽ kéo bù).
- ô 8 (Embassy / Đại sứ quán, người dùng xác nhận; Chợ KHÔNG phải ô 8): từ War Hall ở giữa chỉ cần 1 cú (-157, -91), điểm đầu (268, 385) -> cuối (111, 294)
  thì Embassy ra (196, 346), điểm khớp 0,997 (đo thật trên 21933, người dùng xác nhận đúng). Chiều về: 1 cú (157, 91), điểm đầu (111, 294) -> cuối (268, 385) thì
  War Hall ra (198, 349), điểm khớp 0,929. Cú civ1 (-200, -113) thừa: Embassy ra (149, 296) rồi phải kéo bù (48, 49).
- ô 9 (Chợ / Market, chợ đen; ảnh người dùng chụp Screenshot_20261013-230859.png 89x50 khớp 0,955): thẳng lên trên Embassy. Từ Embassy ở giữa chỉ cần 1 cú
  (-83, 170), điểm đầu (231, 255) -> cuối (148, 425) thì Chợ ra (190, 358), điểm khớp 0,922, lệch (-7, 13) so với giữa (đo thật trên 21933).
  Chiều về chưa đo thật (War Hall <-> Chợ riêng: 1 cú (240, -82), điểm đầu (70, 381) -> cuối (310, 299) thì từ Chợ về War Hall ra (200, 340)).
- ô 10 (Tavern / Quán rượu, ở góc dưới trái so với Chợ; ảnh người dùng chụp Screenshot_20261013-231005.png 104x69): từ Chợ ở giữa (190, 358) chỉ cần 1 cú
  (-185, 146), điểm đầu (282, 267) -> cuối (97, 413) thì Tavern ra (191, 347), điểm khớp 0,99, lệch (-6, 2) so với giữa (đo thật trên 21933, chờ 5 giây cho camera dừng).
  Chiều về: đảo dấu (185, -146) (97, 413) -> (282, 267): chưa đo riêng.
- ô 11 (Forge / Lò rèn; ảnh người dùng chụp Screenshot_20261013-231209.png 58x98 khớp 0,952): từ Tavern ở giữa vuốt 1 cú (-97, -143), điểm đầu (238, 412) ->
  cuối (141, 269) thì Forge ra (189, 332), điểm khớp 0,918, lệch (-8, -13) so với giữa (đo thật trên 21933).
- ô 12 (Trap Factory; ảnh người dùng chụp Screenshot_20261013-231323.png chỉ là nút Event Center che công trình ở góc phải trên): từ Forge ở giữa (197, 345) chỉ cần 1 cú
  (-210, 61), điểm đầu (295, 310) -> cuối (85, 371) thì Trap Factory ra (207, 342), điểm khớp 0,896, lệch (10, -3) so với giữa (đo thật trên 21933, chờ 5 giây cho camera dừng
  rồi mới chụp; 2 cú (-150, 110) + (-60, -49) thì ra khoảng cùng chỗ).
- ô 13 (Prison / Nhà tù; ảnh người dùng chụp Screenshot_20261013-231458.png 97x43 khớp 1,0 ở (306, 244), bị nút Event Center che một phần): từ Trap Factory ở giữa
  vuốt 1 cú (-112, 110), điểm đầu (246, 285) -> cuối (134, 395) thì Prison ra (224, 363), điểm khớp 0,925, lệch (27, 18) so với giữa (đo thật trên 21933, người dùng xác nhận đúng ô).
- Rally Spot (cố định; ảnh người dùng chụp Screenshot_20261013-231627.png chỉ là chữ "Ma" của nút Mail che Rally Spot ở góc dưới phải): từ Prison (ô 13) 2 cú giống nhau
  (-71, -135), điểm đầu (300, 430) -> cuối (229, 295) thì Rally Spot ra (196, 322), điểm khớp 0,963. Rally Spot -> Tavern: 3 cú giống nhau (180, 70), điểm đầu (100, 305) ->
  cuối (280, 375) (tính từ các `view`: Tavern - Rally Spot = (539, 211)); ngược lại 3 cú (-180, -70), điểm đầu (280, 375) -> cuối (100, 305). Xem ROUTES. FIXED (so với Thành chính) chưa đo.
- Research Factory (cố định): từ Bệnh viện (ô 2) ở giữa vuốt 1 cú (200, -30) (tests/city/run_route.py, người dùng xác nhận đúng toạ độ); Bệnh viện không phải công trình cố định nên KHÔNG đưa vào ROUTES.
  FIXED = view Bệnh viện [539, 56] + (200, -30) = [739, 26] (so với Thành chính, cộng dồn từ các ô nên ước chừng). Về Thành chính: 4 cú (-185, -7), đo thật từ Research Factory (203, 320) ra Thành chính (197, 345).
- Tháp cung thủ (cố định): từ Tường thành 4 cú (146, -135), tổng (584, -540) (tests/city/run_route.py, người dùng xác nhận). FIXED = Walls [969, -612] + (584, -540)
  = [1553, -1152] (ước chừng, chưa tính ANCHOR_SHIFT của Tháp). Chiều về giữ cú đã ghi (-173, 130) * 4, chưa kiểm lại.
- ô 6 -> 7 vẫn cần 3 cú (người dùng xác nhận): 1 cú dài không tới War Hall.
  Barracks cũng đo từ Bệnh viện ở giữa: 2 cú (55, -147), điểm đầu (163, 413) -> cuối (218, 266) thì Barracks ra (197, 342).
"""
COMPLETE = True       # đã chạy city_map.scan thật trên 21933: thấy đủ 13 ô + 8 mốc cố định + shrine (lệch so với view <= ~60 px)
# Đo lại bằng tests/city/measure/auto.py trên 21933 (đi theo ước lượng, tự bù tới lệch <= 12 px, tính cả ANCHOR_SHIFT của Walls), từng đoạn đi + về; rr.py trước đó lệch 50-118 px.
FIXED = {'walls': [931, -585], 'research_factory': [768, 104], 'tavern': [-1, -252], 'archer_tower': [1509, -1115], 'watchtower': [1701, -42],
         'rally_spot': [-566, -495], 'art_hall': [1003, -9], 'pasture': [1204, -132]}
# walls = Thành chính + (980, -585) khi "giữa" tính theo ANCHOR_SHIFT (49, 0) => FIXED = (931, -585); archer_tower = walls + (529, -530); research_factory = (768, 104);
# watchtower = research_factory + (933, -146); art_hall = research_factory + (235, -113); pasture = art_hall + (201, -123); tavern = 2 cú; rally_spot = 3 cú.
ANCHOR_SHIFT = {'walls': (49, 0)}
ROUTES = {
    ('keep', 'walls'): [(193, -115)] * 5,                  # đo thật: tổng (980, -585)
    ('walls', 'keep'): [(-185, 110)] * 5,                  # đo thật: tổng (-963, 576)
    ('walls', 'archer_tower'): [(193, -190)] * 3,          # đo thật: tổng (529, -530)
    ('archer_tower', 'walls'): [(-183, 181)] * 3,          # đo thật: tổng (-572, 567)
    ('keep', 'research_factory'): [(192, 26)] * 4,         # đo thật: tổng (768, 104)
    ('research_factory', 'keep'): [(-191, -27)] * 4,       # đo thật: tổng (-764, -108)
    ('research_factory', 'watchtower'): [(233, -37)] * 4,  # đo thật: tổng (933, -146)
    ('watchtower', 'research_factory'): [(-226, 36)] * 4,  # đo thật: tổng (-902, 142)
    ('research_factory', 'art_hall'): [(235, -113)],       # đo thật
    ('art_hall', 'research_factory'): [(-235, 113)],       # đo thật
    ('art_hall', 'pasture'): [(201, -123)],                # đo thật
    ('pasture', 'art_hall'): [(-206, 115)],                # đo thật
    ('keep', 'tavern'): [(0, -137)] * 2,                   # đo thật: tổng (-1, -252)
    ('tavern', 'keep'): [(0, 134)] * 2,                    # đo thật: tổng (-1, 267)
    ('keep', 'rally_spot'): [(-183, -160)] * 3,            # đo thật: tổng (-566, -495)
    ('rally_spot', 'keep'): [(186, 162)] * 3,              # đo thật: tổng (558, 485)
    ('rally_spot', 'tavern'): [(188, 81)] * 3,             # TÍNH từ hiệu hai mốc (565, 243), chưa chạy thật riêng
    ('tavern', 'rally_spot'): [(-188, -81)] * 3,
}
# Đường về Thành chính của các mốc còn lại (find_keep cần ROUTES[(mốc, 'keep')] cho MỌI mốc trong FIXED): nối các đoạn đã đo, gồm cả chiều ngược.
ROUTES[('watchtower', 'keep')] = ROUTES[('watchtower', 'research_factory')] + ROUTES[('research_factory', 'keep')]
ROUTES[('keep', 'watchtower')] = ROUTES[('keep', 'research_factory')] + ROUTES[('research_factory', 'watchtower')]
ROUTES[('archer_tower', 'keep')] = ROUTES[('archer_tower', 'walls')] + ROUTES[('walls', 'keep')]
ROUTES[('keep', 'archer_tower')] = ROUTES[('keep', 'walls')] + ROUTES[('walls', 'archer_tower')]
ROUTES[('art_hall', 'keep')] = ROUTES[('art_hall', 'research_factory')] + ROUTES[('research_factory', 'keep')]
ROUTES[('keep', 'art_hall')] = ROUTES[('keep', 'research_factory')] + ROUTES[('research_factory', 'art_hall')]
ROUTES[('pasture', 'keep')] = ROUTES[('pasture', 'art_hall')] + ROUTES[('art_hall', 'keep')]
ROUTES[('keep', 'pasture')] = ROUTES[('keep', 'art_hall')] + ROUTES[('art_hall', 'pasture')]
DATA = [
    {'plot': 1, 'swipes': [[[112, 311], [269, 370]], [[180, 280], [202, 341]]], 'view': [179, 120], 'seen_21933': 'academy'},
    {'plot': 2, 'swipes': [[[103, 356], [278, 325]], [[103, 356], [278, 325]]], 'view': [529, 58], 'seen_21933': 'hospital'},
    {'plot': 3, 'swipes': [[[132, 406], [248, 275]]], 'view': [645, -73], 'seen_21933': 'stables'},
    {'plot': 4, 'swipes': [[[183, 419], [197, 262]]], 'view': [659, -230], 'seen_21933': 'barracks'},
    {'plot': 5, 'swipes': [[[131, 405], [249, 276]]], 'view': [777, -359], 'seen_21933': 'archer_camp'},
    {'plot': 6, 'swipes': [[[118, 291], [263, 389]]], 'view': [922, -261], 'seen_21933': 'workshop'},
    {'plot': 7, 'swipes': [[[270, 379], [110, 301]], [[270, 379], [110, 301]], [[270, 379], [110, 301]]], 'view': [441, -496], 'seen_21933': 'war_hall'},
    {'plot': 8, 'swipes': [[[269, 391], [112, 289]]], 'view': [284, -598], 'seen_21933': 'embassy'},
    {'plot': 9, 'swipes': [[[235, 249], [145, 432]]], 'view': [194, -415], 'seen_21933': 'market'},
    {'plot': 10, 'swipes': [[[283, 262], [98, 418]]], 'view': [9, -259], 'seen_21933': 'tavern'},
    {'plot': 11, 'swipes': [[[230, 407], [150, 273]]], 'view': [-71, -393], 'seen_21933': 'forge'},
    {'plot': 12, 'swipes': [[[298, 309], [82, 371]]], 'view': [-287, -331], 'seen_21933': 'trap_factory'},
    {'plot': 13, 'swipes': [[[255, 291], [125, 390]]], 'view': [-417, -232], 'seen_21933': 'prison'},
]
