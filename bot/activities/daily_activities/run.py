"""
run.py — Daily Activities (port từ DailyActivities1234.cs): các việc Daily, chỉ làm thao tác trong game.

Không có hàm run của cả activity và không có phần phân phối: chọn việc nào, thứ tự, đánh dấu "xong hôm nay", hẹn thử lại,
khoảng giờ giữa các lần thử, nhận thưởng cuối là việc của worker (bot/worker/policies.py). Ở đây chỉ liệt kê việc và hàm làm:
- TASKS: các việc Daily theo thứ tự bản C# (cũng là thứ tự ô tích ở tab UI); làm một việc = common.run_task(bot, task)
  -> TaskResult.
- HOURLY: việc chạy theo giờ (Alliance Donation, Alliance Help) và hàm một lần thử -> TaskResult.
- buy_general = buy_daily.run.run (General: mua Stamina + Hammer trong một nhiệm vụ) -> TaskResult; collect_activity_rewards (nhận thưởng cuối).
Mỗi việc là một thư mục con (giống activity Event): constants.py (ảnh) + run.py (handler, TASK).
"""
from .alliance_donation import TASK as ALLIANCE_DONATION
from .alliance_donation.run import donate_free
from .alliance_help import TASK as ALLIANCE_HELP
from .alliance_help.run import help_all
from .black_market import TASK as BLACK_MARKET
from .common import MONSTER_KILLING, Task, collect_activity_rewards, run_task  # noqa: F401 (worker import)
from .buy_daily.run import run as buy_general
from .general_enhancing import TASK as GENERAL_ENHANCING
from .gold_levy import TASK as GOLD_LEVY
from .material_composing import TASK as MATERIAL_COMPOSING
from .monster_killing import TASK as MONSTER
from .offering import TASK as OFFERING
from .patrol import TASK as PATROL
from .resource_collecting import TASK as RESOURCE_COLLECTING
from .resource_gathering import TASK as RESOURCE_GATHERING
from .resource_tax import TASK as RESOURCE_TAX
from .trap_building import TASK as TRAP_BUILDING
from .troop_healing import TASK as TROOP_HEALING
from .troop_training import TASK as TROOP_TRAINING
from .wheel_of_fortune import TASK as WHEEL_OF_FORTUNE

# Thứ tự chạy (= thứ tự bản C#; tab UI SUPPORTED_TASKS chỉ khác ở chỗ đưa Offering lên đầu).
# Resource Gathering phải ngay sau Offering: cả hai đưa về thành, bàn tay nổi thu mọi mỏ một lần.
TASKS: tuple[Task, ...] = (
    MONSTER,
    RESOURCE_COLLECTING,
    OFFERING,
    RESOURCE_GATHERING,
    RESOURCE_TAX,
    GOLD_LEVY,
    TROOP_TRAINING,
    TROOP_HEALING,
    TRAP_BUILDING,
    ALLIANCE_DONATION,
    ALLIANCE_HELP,
    BLACK_MARKET,
    GENERAL_ENHANCING,
    WHEEL_OF_FORTUNE,
    PATROL,
    MATERIAL_COMPOSING,
)

# (nhiệm vụ, hàm một lần thử -> TaskResult) — các việc theo giờ, theo thứ tự chạy.
HOURLY = (
    (ALLIANCE_DONATION, donate_free),
    (ALLIANCE_HELP, help_all),
)

