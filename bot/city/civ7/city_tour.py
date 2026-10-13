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
COMPLETE = False      # bật True khi các route mốc cố định đã chạy thật (hiện Tavern / Rally Spot / Tháp canh <-> Thành chính còn là số tính)
FIXED = {'walls': [851, -550], 'research_factory': [739, 26], 'tavern': [28, -288], 'archer_tower': [1484, -1090], 'watchtower': [1624, -89],
         'rally_spot': [-512, -498], 'art_hall': [974, -87], 'pasture': [1151, -131]}
# walls = 5 cú (180, -110) = (900, -550) trừ ANCHOR_SHIFT (49, 0); research_factory = Bệnh viện [539, 56] + (200, -30); tavern = view ô 10;
# archer_tower = Walls (900, -550) + (584, -540); watchtower = research_factory + (885, -115); rally_spot = tavern - (540, 210);
# art_hall = research_factory + (235, -113); pasture = art_hall + (177, -44).
ANCHOR_SHIFT = {'walls': (49, 0)}
ROUTES = {
    ('research_factory', 'keep'): [(-185, -7)] * 4,   # đo thật trên 21933 (tính từ chuỗi route, chạy từ Research Factory ở (203, 320)): Thành chính ra (197, 345), điểm khớp 0,791
    ('keep', 'research_factory'): [(185, 7)] * 4,     # đảo dấu của chiều về, tổng (740, 28) ~ FIXED['research_factory'] = [739, 26]; chưa chạy thật
    ('keep', 'walls'):  [(180, -110)] * 5,       # người dùng chỉnh bằng run_route.py (civ1 là (204, -122)): tổng (900, -550) = FIXED walls + ANCHOR_SHIFT
    ('walls', 'keep'):  [(-180, 110)] * 5,       # đảo dấu của chiều đi
    ('rally_spot', 'tavern'): [(180, 70)] * 3,        # đo thật trên 21933: Rally Spot ở giữa -> Tavern ra (175, 321), lệch (-22, -24)
    ('tavern', 'rally_spot'): [(-180, -70)] * 3,      # đo thật: Tavern -> Rally Spot ra (180, 316), lệch (-17, -29)
    ('walls', 'archer_tower'): [(146, -135)] * 4,       # đo thật trên 21933 bằng tests/city/run_route.py (người dùng xác nhận): từ Tường thành ra Tháp cung thủ, tổng (584, -540)
    ('watchtower', 'research_factory'): [(-177, 23)] * 5,   # run_route.py trên 21933 (Tháp canh ở (211, 394) lúc bắt đầu): Research Factory ra (263, 363), điểm khớp 0,995
    ('research_factory', 'watchtower'): [(177, -23)] * 5,   # đảo dấu, chưa chạy thật
    ('research_factory', 'art_hall'): [(235, -113)],   # giống civ1; run_route.py trên 21933, người dùng xác nhận đúng (Art Hall ra (234, 335), điểm khớp 0,987)
    ('art_hall', 'research_factory'): [(-235, 113)],   # đảo dấu, chưa chạy thật
    ('art_hall', 'pasture'): [(177, -44)],   # giống civ1; chạy trên 21933 từ Art Hall (234, 335): Pasture ra (201, 403), điểm khớp 0,976, lệch (4, 58) - hơi thấp, người dùng bảo lưu
    ('pasture', 'art_hall'): [(-177, 44)],   # đảo dấu, chưa chạy thật
    ('archer_tower', 'walls'): [(-146, 135)] * 4,       # đảo dấu của chiều đi (người dùng: chiều đi đúng, số (-173, 130) cũ sai), tổng (-584, 540); chưa chạy thật
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
ROUTES[('tavern', 'keep')] = [(-14, 144)] * 2          # TÍNH từ FIXED tavern [28, -288] (view ô 10), CHƯA chạy thật
ROUTES[('keep', 'tavern')] = [(14, -144)] * 2
ROUTES[('rally_spot', 'keep')] = ROUTES[('rally_spot', 'tavern')] + ROUTES[('tavern', 'keep')]
ROUTES[('keep', 'rally_spot')] = ROUTES[('keep', 'tavern')] + ROUTES[('tavern', 'rally_spot')]
DATA = [
    {'plot': 1, 'swipes': [[[112, 311], [269, 370]], [[180, 280], [202, 341]]], 'view': [179, 120], 'seen_21933': 'academy'},
    {'plot': 2, 'swipes': [[[100, 246], [280, 214]], [[100, 246], [280, 214]]], 'view': [539, 56], 'seen_21933': 'hospital'},
    {'plot': 3, 'swipes': [[[134, 404], [247, 275]]], 'view': [652, -73], 'seen_21933': 'stables'},
    {'plot': 4, 'swipes': [[[196, 418], [183, 261]]], 'view': [639, -230], 'seen_21933': 'barracks'},
    {'plot': 5, 'swipes': [[[134, 404], [247, 275]]], 'view': [752, -359], 'seen_21933': 'archer_camp'},
    {'plot': 6, 'swipes': [[[118, 291], [263, 389]]], 'view': [897, -261], 'seen_21933': 'workshop'},
    {'plot': 7, 'swipes': [[[264, 382], [116, 298]], [[264, 382], [116, 298]], [[264, 382], [116, 298]]], 'view': [453, -513], 'seen_21933': 'war_hall'},
    {'plot': 8, 'swipes': [[[268, 385], [111, 294]]], 'view': [296, -604], 'seen_21933': 'embassy'},
    {'plot': 9, 'swipes': [[[231, 255], [148, 425]]], 'view': [213, -434], 'seen_21933': 'market'},
    {'plot': 10, 'swipes': [[[282, 267], [97, 413]]], 'view': [28, -288], 'seen_21933': 'tavern'},
    {'plot': 11, 'swipes': [[[238, 412], [141, 269]]], 'view': [-69, -431], 'seen_21933': 'forge'},
    {'plot': 12, 'swipes': [[[295, 310], [85, 371]]], 'view': [-279, -370], 'seen_21933': 'trap_factory'},
    {'plot': 13, 'swipes': [[[246, 285], [134, 395]]], 'view': [-391, -260], 'seen_21933': 'prison'},
]
