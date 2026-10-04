"""
daily_activities — "Daily Activities" activity (bố cục giống activity Event: mỗi nhiệm vụ một thư mục).

- run.py:       entry point `run(bot, settings)`: General, thứ tự nhiệm vụ (TASKS), nhận thưởng
- common.py:    vòng lặp chung của một nhiệm vụ (run_task), mở Activity, dòng Go, cuộn, nhận thưởng
- constants.py: thư mục ảnh, tên action, key daily_done dùng chung
- general.py:   Buy Stamina / Buy All Hammers
- OPEN_TASK.md: flow mở nhiệm vụ / bấm Go / đánh dấu xong (đọc trước)
- <nhiệm vụ>/:  constants.py (ảnh) + run.py (handler, TASK) — monster_killing, resource_collecting,
                offering, resource_gathering, resource_tax, gold_levy, troop_training, troop_healing,
                trap_building, alliance_donation, black_market, general_enhancing, wheel_of_fortune,
                patrol, material_composing
"""
from .run import run

__all__ = ["run"]
