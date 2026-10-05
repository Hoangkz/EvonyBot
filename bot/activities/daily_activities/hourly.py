"""
hourly.py — khung chung của các nhiệm vụ Daily chạy theo giờ (ô chọn 0 / 1h / 2h / 3h / 4h ở tab UI, không ưu
tiên — xem run.py _run_hourly): Alliance Donation, Alliance Help.

Một lần thử (try_task):
1. Lưu giờ thử (tried_key) để run.py tính lúc làm lại.
2. Kiểm tra trước: mở danh sách Activity, xem dòng / thẻ của nhiệm vụ (open_task tap_go=False, không bấm Go).
   Xong (hết Go / Claim / tích V / thẻ Completed) -> đánh dấu xong hôm nay (lưu DB), thôi — trong ngày không đi
   kiểm tra lại nữa.
3. Chưa xong -> act(bot) (VD donate lượt free, Help All). act không làm được gì -> dừng (lần sau thử lại).
4. Có làm -> kiểm tra Activity lần nữa: xong -> đánh dấu xong hôm nay.
"""
from .common import Task, mark_task_done, open_task, task_cards, task_done_cards, task_titles
from .constants import TASK_DONE


def try_task(bot, task: Task, tried_key: str, act) -> bool:
    """Một lần thử nhiệm vụ theo giờ `task`. True nếu nhiệm vụ đã xong hôm nay."""
    bot.mark_daily_done(tried_key)
    if check_done(bot, task):
        return True
    if not act(bot):
        return False
    if check_done(bot, task):
        return True
    bot.log(f"{task.label}: Activity row not done yet, try later")
    return False


def check_done(bot, task: Task) -> bool:
    """Mở danh sách Activity xem dòng / thẻ của `task` (không bấm Go), rồi Back đóng bảng. Xong (hết Go) -> đánh
    dấu xong hôm nay, True."""
    result = open_task(bot, task_titles(task), task_cards(task), done_cards=task_done_cards(task),
                       tap_go=False)
    bot.back(delay=1)   # đóng bảng Activity
    if result != TASK_DONE:
        bot.log(f"{task.label}: Activity row not done ({result})")
        return False
    bot.record(f"{task.label}: Activity row done, done for today")
    mark_task_done(bot, task)
    return True
