"""
hourly.py — khung chung của các nhiệm vụ Daily chạy theo giờ: Alliance Donation, Alliance Help. Khi nào thử, cách nhau
bao lâu, ghi giờ thử: việc của worker (bot/worker/policies.py); ở đây chỉ có một lần thử.

Một lần thử (try_task):
1. Kiểm tra trước: mở danh sách Activity, xem dòng / thẻ của nhiệm vụ (open_task tap_go=False, không bấm Go).
   Xong (hết Go / Claim / tích V / thẻ Completed) -> TaskResult(done=True), thôi — trong ngày không đi kiểm tra lại.
2. Chưa xong -> act(bot) (VD donate lượt free, Help All). act không làm được gì -> chưa xong (lần sau thử lại).
3. Có làm -> kiểm tra Activity lần nữa: xong -> TaskResult(done=True).
"""
from ..result import NOT_DONE, TaskResult
from .common import Task, open_task, task_cards, task_done_cards, task_titles
from .constants import TASK_DONE


def try_task(bot, task: Task, act) -> TaskResult:
    """Một lần thử nhiệm vụ theo giờ `task`."""
    if check_done(bot, task):
        return TaskResult(done=True, reached=0)
    if not act(bot):
        return NOT_DONE
    if check_done(bot, task):
        return TaskResult(done=True, reached=0)
    bot.log(f"{task.label}: Activity row not done yet, try later")
    return NOT_DONE


def check_done(bot, task: Task) -> bool:
    """Mở danh sách Activity xem dòng / thẻ của `task` (không bấm Go), rồi Back đóng bảng. True nếu dòng đã xong
    (hết Go)."""
    result = open_task(bot, task_titles(task), task_cards(task), done_cards=task_done_cards(task),
                       tap_go=False)
    bot.back(delay=1)   # đóng bảng Activity
    if result != TASK_DONE:
        bot.log(f"{task.label}: Activity row not done ({result})")
        return False
    bot.record(f"{task.label}: Activity row done, done for today")
    return True
