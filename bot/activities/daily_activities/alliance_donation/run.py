"""
run.py — Daily Activities "Alliance Donation" (việc theo giờ: ô chọn 0 / 1h / 2h / 3h / 4h ở tab UI).

Flow (donate_free):
1. Màn chính -> Liên minh -> kéo xuống tìm Alliance Science (event/kings_path/donate/alliance.py _open_science).
2. Bấm "Donate" thẻ khoa học trên cùng tới khi hết lượt miễn phí (nút thành kim cương / hộp xác nhận kim cương -> Back).
   KHÔNG mua lượt bằng kim cương.
3. Donate được: LƯU VÀO DB giờ vừa donate (TRIED_KEY, trong daily_done); worker chỉ so giờ này với số giờ trên tab để biết khi nào
   donate lại (lượt free hồi theo thời gian). Việc này không có "xong hôm nay": mỗi N giờ lại donate.
4. Ra danh sách nhiệm vụ Activity nhận thưởng (collect_activity_rewards: Claim All + rương điểm). KHÔNG tìm dòng nhiệm vụ
   rồi bấm Go, cũng không mở bảng để kiểm tra dòng đã xong chưa.
Không tới được Alliance Science hoặc hết lượt free ngay: Back, không nhận thưởng; chờ tới giờ kế tiếp (giờ lưu bởi
common.hourly_job). Lỗi thì lưu `<key>_error` vào DB (xem ../../result.py save_errors).
"""
from ...event.kings_path.donate.alliance import _open_science
from ...event.kings_path.donate.constants import DONATE_WAIT, MAX_MISSES
from ...event.kings_path.donate.donating import read_screen
from ...result import NOT_DONE, TaskResult
from ..common import Task, collect_activity_rewards
from .constants import FOLDER, KEY, LABEL, MAX_FREE_DONATIONS, TRIED_KEY


# TASK chỉ để hourly_job biết nhãn / key của việc (nhãn là ô chọn giờ ở tab và key "xong" trong daily_done).
TASK = Task(LABEL, FOLDER, key=KEY)


def donate_free(bot) -> TaskResult:
    """Một lần donate: Liên minh -> Alliance Science -> Donate hết lượt free -> lưu giờ vào DB -> nhận thưởng. Luôn trả
    NOT_DONE: việc theo giờ không có "xong hôm nay"; lượt sau tới giờ thì donate tiếp."""
    if not _open_science(bot):
        return NOT_DONE
    donated = _donate_free_times(bot)
    bot.back(delay=1)   # đóng Alliance Science
    if not donated:
        bot.log(f"{LABEL}: no free donations now, try later")
        return NOT_DONE
    bot.record(f"{LABEL}: donated {donated} free time(s), claiming rewards")
    bot.mark_daily_done(TRIED_KEY)   # LƯU DB: đã donate lúc mấy giờ (worker so giờ này để biết tới giờ donate lại chưa)
    collect_activity_rewards(bot)    # ra danh sách nhiệm vụ nhận thưởng
    return NOT_DONE


def _donate_free_times(bot) -> int:
    """Màn Alliance Science: bấm Donate thẻ trên cùng tới khi hết lượt miễn phí. Trả số lần đã donate."""
    donated = misses = 0
    while donated < MAX_FREE_DONATIONS:
        action, pos = read_screen(bot, bot.screenshot())
        if action is None:
            misses += 1
            if misses > MAX_MISSES:
                bot.record(f"{LABEL}: Alliance Science not recognised, stop ({donated} donated)")
                break
            bot.sleep(1)
            continue
        misses = 0
        if action == "donate":
            bot.tap(*pos, delay=DONATE_WAIT)
            donated += 1
            continue
        if action == "okay":
            bot.back(delay=1)   # hộp tiêu kim cương: không mua
        break                   # "gems": hết lượt miễn phí
    return donated
