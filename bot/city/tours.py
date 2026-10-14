"""tours.py — dữ liệu route thành theo nền văn minh: mỗi civ một thư mục (civ1/, civ7/...) có city_tour.py riêng.

ALL: mọi civ đã có thư mục. TOURS: civ đã đo đủ (COMPLETE) — chỉ civ trong TOURS mới được quét route.
FIXED_NAMES: tên mọi công trình cố định của mọi civ (find_keep tìm mốc trước khi biết civ).
"""
from .civ1 import city_tour as civ1
from .civ2 import city_tour as civ2
from .civ7 import city_tour as civ7

ALL = {1: civ1, 2: civ2, 7: civ7}
TOURS = {civ: tour for civ, tour in ALL.items() if tour.COMPLETE}
FIXED_NAMES = tuple(dict.fromkeys(name for tour in ALL.values() for name in tour.FIXED))
