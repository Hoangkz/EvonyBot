"""city_tour.py — các ô đi vòng khi quét bản đồ thành (Black Market), dữ liệu tĩnh.

DATA: list ô theo thứ tự quét; mỗi ô có `plot` (số ô), `swipes` (các cú vuốt đưa ô về
giữa màn), `view` (toạ độ bản đồ khi camera đúng giữa ô), `seen_21943` (công trình thấy
ở ô đó trên máy 21943). Trước đây là file .json cùng tên; đổi sang .py để Nuitka compile
cùng code, không cần ship file riêng lúc build.
"""
DATA = [  
    {'plot': 1, 'swipes': [[[16, 300], [330, 418]]], 'view': [326, 123], 'seen_21943': 'academy'},
    {'plot': 2, 'swipes': [[[55, 440], [325, 290]]], 'view': [643, 3], 'seen_21943': 'defense_force'},
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
