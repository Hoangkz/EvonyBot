"""city_tour.py — các ô đi vòng khi quét bản đồ thành (Black Market), dữ liệu tĩnh.

DATA: list ô theo thứ tự quét; mỗi ô có `plot` (số ô), `swipes` (các cú vuốt đưa ô về
giữa màn), `view` (toạ độ bản đồ khi camera đúng giữa ô), `seen_21943` (công trình thấy
ở ô đó trên máy 21943). Trước đây là file .json cùng tên; đổi sang .py để Nuitka compile
cùng code, không cần ship file riêng lúc build.

FIXED: công trình cố định (đứng yên trên mọi tài khoản, dùng làm mốc tìm Thành chính khi không còn nhiệm vụ nào có Go) — walls /
research_factory KHÔNG quét, không có ô trong DATA: toạ độ bản đồ (cùng hệ với
`view`) đo trên 21943, scan() thêm sẵn vào bản đồ để goto đi tới / đi từ chúng.
- walls = ô 6 (Chuồng ngựa) [929, -380] + (40, -232): từ ô 6 chính giữa vuốt chậm 1 cú (170, 456) -> (210, 224) thì cổng
  Walls vào giữa màn.
- research_factory = ô 4 (Trại cung thủ) [873, -107] + (82, 156): từ ô 4 chính giữa vuốt chậm 1 cú (137, 268) -> (243, 412)
  thì Research Factory vào giữa màn.
- archer_tower = [1777, -1044] (Tháp cung thủ trái, góc trên phải thành): Walls + (808, -432), đo trên 21923 từ lúc Tường thành ở giữa
  (cổng ở giữa màn = ảnh mẫu ở (246, 345), ANCHOR_SHIFT) vuốt 4 cú (195, -104) thì Tháp ở (218, 361).
- art_hall = [1190, -64] (Art Hall, cố định): Research Factory + (235, -113), đo trên 21923 hai lần (xuất phát từ Research Factory lệch rồi
  trừ độ lệch): đo 2 lần ra (253..264, -122) nhưng chiều về 1 cú (-258, 122) quá 23 px nên giảm còn (±235, ∓113).
- pasture = [1367, -108] (Pasture, cố định): Art Hall + (177, -44): từ Art Hall vuốt 1 cú (235, -113) thì Pasture ra ở (255, 276), thêm 1 cú
  (-58, 69) mới giữa (194, 348); tổng (177, -44). Chiều về 1 cú (-177, 44) thì Art Hall ra (205, 312), người dùng xác nhận chuẩn.
- rally_spot = [-415, -550] (Rally Spot, cố định): Tavern + (-512, -319), đo trên 21923: từ Tavern 2 cú (-222, -115) (cùng hướng
  Tavern -> Prison, gấp đôi) thì Rally Spot ra (277, 423), thêm 1 cú (-80, -78) mới giữa (191, 340) (người dùng xác nhận).
- watchtower = [1840, -158] (Tháp canh, mép đông thành, ở bên phải Research Factory): Research Factory + (885, -207), đo trên 21923: từ
  Tháp canh vuốt 5 cú (-190, 0) rồi 1 cú (92, 185) thì Research Factory ra ở (204, 358), lệch (7, 13) (Tháp canh lúc bắt đầu ở (177, 380)).
- ANCHOR_SHIFT: tâm "chính giữa" người dùng chọn không trùng tâm ảnh mẫu. walls (49, 0): cổng ở giữa màn thì ảnh mẫu `walls` ở
  (246, 345). archer_tower (-68, -41): giữa của CẢ HAI tháp ở giữa màn thì ảnh mẫu tháp trái ở (129, 304) (tháp phải ở (256, 383)).
  Mọi đường tới / từ các công trình này trong ROUTES tính theo tâm đó; find_keep kéo công trình vào đúng tâm đó trước khi vuốt.
- tavern = [97, -231]: đo trực tiếp trên 21923, thấy cả Thành chính (188, 238) và Tavern (91, 469) trên cùng một màn:
  Tavern - Keep = -(91 - 188, 469 - 238). (Không dùng view ô 11 [143, -166]: đó là tâm camera của ô, lệch ~80 px.) Tavern vẫn
  là một ô của DATA (scan đi qua và ghi toạ độ quét được); FIXED chỉ để find_keep dùng làm mốc tìm Thành chính.

CIVILIZATION: bố cục thành khác nhau theo nền văn minh nên mỗi civ có thư mục riêng (bot/city/civ<N>/city_tour.py) với FIXED /
ANCHOR_SHIFT / ROUTES / DATA riêng; file này là civ1 (đo trên máy 21913 / 21923 / 21943). bot/city/tours.py gom các civ đã đo đủ
(COMPLETE = True); civ chưa đo đủ thì scan_city ghi log rồi bỏ.
"""
COMPLETE = True
FIXED = {'walls': [969, -612], 'research_factory': [955, 49], 'tavern': [97, -231], 'archer_tower': [1777, -1044], 'watchtower': [1840, -158], 'art_hall': [1190, -64], 'pasture': [1367, -108], 'rally_spot': [-415, -550]}
# Công trình có tâm ảnh mẫu lệch khỏi tâm nhìn thấy: kéo "vào giữa" nghĩa là ảnh mẫu ở giữa màn + độ lệch này (Tường thành: cổng ở
# giữa màn khi ảnh mẫu nằm lệch phải 49 px). Các đường trong ROUTES bắt đầu / kết thúc ở tâm này.
ANCHOR_SHIFT = {'walls': (49, 0), 'archer_tower': (-68, -41)}
# Đường đi cố định giữa Thành chính và các công trình cố định (đứng yên mãi mãi nên cú vuốt không đổi): (từ, tới) -> các cú
# vuốt chậm (ngón tay dx, dy; đối xứng quanh tâm màn, city_map.swipe), đo trên 21923, bắt đầu khi công trình `từ` đang ở giữa màn.
ROUTES = {
    ('keep', 'walls'): [(204, -122)] * 5,               # tổng (1020, -610) = [969, -612] + ANCHOR_SHIFT walls
    ('walls', 'keep'): [(-204, 122)] * 5,
    ('tavern', 'keep'): [(-97, 231)],                   # = -[97, -231]
    ('keep', 'tavern'): [(97, -231)],
    ('research_factory', 'keep'): [(-238, -12)] * 4,    # tổng (-952, -48) ~ -[955, 49]
    ('keep', 'research_factory'): [(193, 6)] * 5,       # tổng (965, 30) ~ [955, 49]
    ('archer_tower', 'walls'): [(-173, 118)] * 4,       # tổng (-692, 472), đã thử thật: từ giữa 2 tháp tới Tường thành (ảnh mẫu ở (258, 354), lệch (12, 9))
    ('walls', 'archer_tower'): [(173, -118)] * 4,
}
ROUTES[('watchtower', 'research_factory')] = [(-177, 41)] * 5      # đã thử thật trên 21923 (Tháp canh ở (177, 380) lúc bắt đầu): tổng (-885, 207)
ROUTES[('research_factory', 'watchtower')] = [(177, -41)] * 5
ROUTES[('watchtower', 'keep')] = ROUTES[('watchtower', 'research_factory')] + ROUTES[('research_factory', 'keep')]
ROUTES[('keep', 'watchtower')] = ROUTES[('keep', 'research_factory')] + ROUTES[('research_factory', 'watchtower')]
ROUTES[('research_factory', 'art_hall')] = [(235, -113)]            # 1 cú (gần): (258, -122) quá 23 px nên giảm theo ảnh (đo trên 21923)
ROUTES[('art_hall', 'research_factory')] = [(-235, 113)]
ROUTES[('art_hall', 'pasture')] = [(177, -44)]                      # 1 cú, đã thử thật trên 21923 cả hai chiều (Art Hall ra (205, 312) khi người dùng thấy chuẩn)
ROUTES[('pasture', 'art_hall')] = [(-177, 44)]
ROUTES[('tavern', 'rally_spot')] = [(-256, -160)] * 2             # cùng hướng tavern -> prison (ô 12) nhưng gấp đôi; đã thử thật trên 21923
ROUTES[('rally_spot', 'tavern')] = [(256, 160)] * 2
ROUTES[('keep', 'rally_spot')] = [(-138, -183)] * 3                 # đường thẳng, đã thử thật trên 21923 (Rally Spot ra (202, 319))
ROUTES[('rally_spot', 'keep')] = [(138, 183)] * 3
ROUTES[('art_hall', 'keep')] = ROUTES[('art_hall', 'research_factory')] + ROUTES[('research_factory', 'keep')]
ROUTES[('pasture', 'keep')] = ROUTES[('pasture', 'art_hall')] + ROUTES[('art_hall', 'keep')]
ROUTES[('keep', 'art_hall')] = ROUTES[('keep', 'research_factory')] + ROUTES[('research_factory', 'art_hall')]
ROUTES[('keep', 'pasture')] = ROUTES[('keep', 'art_hall')] + ROUTES[('art_hall', 'pasture')]
ROUTES[('archer_tower', 'keep')] = ROUTES[('archer_tower', 'walls')] + ROUTES[('walls', 'keep')]   # qua Tường thành
ROUTES[('keep', 'archer_tower')] = ROUTES[('keep', 'walls')] + ROUTES[('walls', 'archer_tower')]
DATA = [  
    {'plot': 1, 'swipes': [[[16, 300], [330, 418]]], 'view': [326, 123], 'seen_21943': 'academy'},
    {'plot': 2, 'swipes': [[[55, 440], [325, 290]]], 'view': [643, 3], 'seen_21943': 'trap_factory'},
    {'plot': 3, 'swipes': [[[182, 441], [198, 238]]], 'view': [653, -202], 'seen_21943': 'barracks'},
    {'plot': 4, 'swipes': [[[70, 300], [293, 377]]], 'view': [873, -107], 'seen_21943': 'archer_camp'},
    {'plot': 5, 'swipes': [[[55, 440], [300, 302]]], 'view': [1150, -265], 'seen_21943': 'workshop'},
    {'plot': 6, 'swipes': [[[300, 440], [118, 297]]], 'view': [929, -380], 'seen_21943': 'stables'},
    {'plot': 7, 'swipes': [[[264, 382], [116, 298]], [[264, 382], [116, 298]], [[264, 382], [116, 298]]], 'view': [486, -590], 'seen_21943': 'hospital'},
    {'plot': 8, 'swipes': [[[290, 396], [90, 283]]], 'view': [297, -689], 'seen_21943': 'market'},
    {'plot': 9, 'swipes': [[[275, 218], [105, 463]]], 'view': [125, -448], 'seen_21943': 'war_hall'},
    {'plot': 10, 'swipes': [[[120, 283], [262, 398]]], 'view': [289, -331], 'seen_21943': 'embassy'},
    {'plot': 11, 'swipes': [[[300, 230], [152, 405]]], 'view': [143, -166], 'seen_21943': 'tavern'},
    {'plot': 12, 'swipes': [[[310, 470], [88, 355]]], 'view': [-95, -335], 'seen_21943': 'prison'},
    {'plot': 13, 'swipes': [[[333, 352], [2, 462]]], 'view': [-404, -238], 'seen_21943': 'forge'}
]
