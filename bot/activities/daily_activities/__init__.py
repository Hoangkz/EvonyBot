"""
daily_activities — "Daily Activities" activity (bố cục giống activity Event: mỗi nhiệm vụ một thư mục).

- common.py:    vòng lặp chung của một việc (run_task -> TaskResult), mở Activity, dòng Go, cuộn, nhận thưởng cuối; cuối file là
                luật của các việc Daily cho bảng bot/worker/priority.py (daily_job, hourly_job, REWARDS_JOB, GIFTS_JOB): việc TỰ
                LƯU kết quả vào DB, worker chỉ kiểm tra đã xong chưa (bot/worker/tasks.py).
- constants.py: thư mục ảnh, tên action, key daily_done dùng chung
- buy_daily/:   General: mua Stamina + Hammer (run.py + luật ở cuối file)
- OPEN_TASK.md: flow mở nhiệm vụ / bấm Go / đánh dấu xong (đọc trước)
- <nhiệm vụ>/:  constants.py (ảnh) + run.py (handler, TASK) — monster_killing, resource_collecting,
                offering, resource_gathering, resource_tax, gold_levy, troop_training, troop_healing,
                trap_building, alliance_donation, black_market, general_enhancing, wheel_of_fortune,
                patrol, material_composing
"""
