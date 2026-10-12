"""
event — "Event" activity.

- run.py:           EVENTS (nhiệm vụ từng event), perform_task / claim_event -> TaskResult; chọn nhiệm vụ, bỏ qua nhiệm vụ đã xong,
                    ghi kết quả, khi nào nhận thưởng: nhiệm vụ tự lưu vào DB, worker (bot/worker/tasks.py) chỉ kiểm tra đã xong chưa
- common.py:        phần dùng chung (quà đăng nhập, tìm Event Center, bấm nút event)
- constants.py:     image folders, limits and action names
- gather_troops/:   nhiệm vụ event Gather Troops, mỗi nhiệm vụ một thư mục
                    (cultivate_generals/run.py + constants.py, ...)
"""
