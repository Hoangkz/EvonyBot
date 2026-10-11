"""
task_def.py — TaskDef: một dòng khai báo nhiệm vụ của worker (không import activity nào, để mọi gói dùng được).

Mỗi nhóm (activity / event_center) khai báo nhiệm vụ của mình trong file `tasks.py` riêng (danh sách TASKS);
bot/worker/registry.py chỉ gom các danh sách đó lại. Thêm một nhiệm vụ mới = thêm một TaskDef vào tasks.py của
nhóm có nhiệm vụ đó, không sửa registry.py (chỉ nhóm mới hoàn toàn mới cần thêm một dòng import vào registry.py).
"""
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class TaskDef:
    key: str                          # key nhiệm vụ (trùng key trong bot/worker/priority.py: lấy độ ưu tiên)
    group: str                        # activity / tab cấu hình (chỉ để chia loại)
    enabled: Callable[[dict], bool]   # enabled(cấu hình tab của nhóm) -> nhiệm vụ này đã được tích?
    run: Callable                     # run(bot, cấu hình tab của nhóm): chạy thẳng nhiệm vụ này
    once: bool = False                # xong rồi thì không làm lại khi qua mốc reset (chỉ chạy lại khi Start lại)
    repeat: bool = False              # hẹn chạy lại (bot.again_after) mà vẫn giữ độ ưu tiên của nó


def always(settings: dict) -> bool:
    """enabled cho nhiệm vụ không có ô tích riêng (chọn activity là chạy)."""
    return True
