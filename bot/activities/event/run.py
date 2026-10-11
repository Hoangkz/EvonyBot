"""
run.py — nhiệm vụ của "Event" (Gather Troops, King's Path): chỉ làm thao tác trong game, trả TaskResult.

Không có hàm run của cả activity và không có phần phân phối: nhiệm vụ nào được chọn (ô tích), bỏ qua nhiệm vụ đã xong /
đã đạt mục tiêu / Day khoá, ghi kết quả, khi nào nhận thưởng event là việc của worker (bot/worker/policies.py). EVENTS liệt kê
nhiệm vụ của từng event theo thứ tự; perform_task chạy một nhiệm vụ, claim_event nhận thưởng của một event (claim.py).

Mỗi nhiệm vụ là một file riêng (gather_troops/..., kings_path/...) với hàm `run(bot, task, state)`; phần đi từ màn
hình chính tới nút event dùng chung ở common.py. `state` (EventState) giữ quà đăng nhập chỉ nhận 1 lần mỗi lượt.
"""
from . import claim
from ..result import NOT_DONE, TaskResult, clear, take_all
from .common import EventState
from .constants import GATHER_TROOPS_ICON, KINGS_PATH_ICON
from .gather_troops import cultivate_generals, ground_troop, mounted_troop, ranged_troop, siege_machine, defense_force
from .kings_path import black_market, city_tax, donate, heal, patrol, refine, train_troop, wheel

# (key event, tên log, icon trong danh sách event, [(key nhiệm vụ trong settings / event.py,
# hàm chạy nhiệm vụ)] theo thứ tự chạy).
EVENTS = [
    ("gather_troops", "Gather Troops", GATHER_TROOPS_ICON, [
        (cultivate_generals.KEY, cultivate_generals.run),
        (ground_troop.KEY, ground_troop.run),
        (mounted_troop.KEY, mounted_troop.run),
        (ranged_troop.KEY, ranged_troop.run),
        (siege_machine.KEY, siege_machine.run),
        (defense_force.KEY, defense_force.run),
    ]),
    ("kings_path", "King's Path", KINGS_PATH_ICON, [
        (city_tax.KEY, city_tax.run),
        (patrol.KEY, patrol.run),
        (donate.KEY, donate.run),
        (train_troop.KEY, train_troop.run),
        (heal.KEY, heal.run),
        (wheel.KEY, wheel.run),
        (refine.KEY, refine.run),
        (black_market.KEY, black_market.run),
    ]),
]
# Mọi nhiệm vụ theo thứ tự chạy.
TASKS = [task for *_, tasks in EVENTS for task in tasks]


def perform_task(bot, key: str, run_task, config) -> TaskResult:
    """Chạy một nhiệm vụ Event `key`: `run_task(bot, cấu hình riêng của nhiệm vụ, EventState)`. done=True khi nhiệm vụ
    báo xong; mọi kết quả báo giữa chừng (xong / hết Go / đạt mục tiêu / Day khoá) nằm trong `outcomes` để worker ghi."""
    clear(bot)
    bot.check()
    run_task(bot, config, EventState())
    outcomes = tuple(take_all(bot))
    done = any(o.done and o.key == key for o in outcomes)
    return TaskResult(done=done, outcomes=outcomes) if outcomes else NOT_DONE


def claim_event(bot, event: str, name: str, icon: str):
    """Nhận thưởng của `event` (chấm đỏ + rương mốc), vào bảng event nếu chưa ở đó."""
    bot.check()
    claim.run(bot, EventState(), name, icon, claim.CHESTS.get(event, ()), claim.TITLES.get(event))
