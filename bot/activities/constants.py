"""
constants.py — hằng số dùng chung của các activity (bot/activities/__init__.py re-export).
"""
# Activity chạy MỘT MÌNH (tab Initialization tự bỏ tích mọi nút khác): worker chạy thẳng hàm của nó, không qua Bubble /
# Auto Times Out / reset server / Join Boss / nhiệm vụ nào khác (bot/worker/bot_worker.py _run_exclusive).
EXCLUSIVE_ACTIVITIES = frozenset({"Recruit General", "Attack Boss"})
# Trong các activity chạy một mình, những activity này VẪN ưu tiên Bubble / Auto Times Out / reset server (worker gọi qua guards.call, bị ngắt thì xử lý rồi chạy lại từ đầu).
GUARDED_EXCLUSIVE = frozenset({"Attack Boss"})
