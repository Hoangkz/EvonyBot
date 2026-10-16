"""
constants.py — hằng số dùng chung của các activity (bot/activities/__init__.py re-export).
"""
# Activity chạy MỘT MÌNH (tab Initialization tự bỏ tích mọi nút khác): worker chạy thẳng hàm của nó, không qua Bubble /
# Auto Times Out / reset server / Join Boss / nhiệm vụ nào khác (bot/worker/bot_worker.py _run_exclusive).
EXCLUSIVE_ACTIVITIES = frozenset({"Recruit General"})
