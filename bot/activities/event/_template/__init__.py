"""
_template — MẪU nhiệm vụ Event để copy (không nằm trong TASKS, không chạy thật).

Tạo nhiệm vụ mới (VD Mounted Troop của Gather Troops):
1. Copy `_template/my_task/` -> `<event>/<nhiệm vụ>/` (VD gather_troops/mounted_troop/).
   Cùng độ sâu nên import tương đối (`...common`, `...constants`) giữ nguyên.
2. Copy `tests/event/_template/my_task/` -> `tests/event/<event>/<nhiệm vụ>/`, chép ảnh
   01..05 (màn chính -> event vừa mở) vào screens/ rồi thêm ảnh các bước riêng.
3. Sửa trong 3 file: KEY, tên log, icon event, ảnh/action riêng, hàm handle.
4. Thêm `(<nhiệm vụ>.KEY, <nhiệm vụ>.run)` vào danh sách nhiệm vụ của event trong EVENTS ở event/run.py và một dòng vào
   docstring của `<event>/__init__.py`.
"""
