"""Vòng kiểm tra chung của một hoạt động quà (valuable_event / event_center).

Mỗi nhiệm vụ trong danh sách có một key trong ``daily_done``. Key có dấu thời gian sau mốc reset server = đã xong hôm nay
(``bot.is_daily_done``), nên sang ngày mới tự hết hạn. Luật:

- Nhiệm vụ đã xong hôm nay: bỏ qua.
- Chưa xong: tìm event đó. Thấy thì nhận quà, đánh dấu xong, đếm "không thấy" về 0.
- Không thấy (đã back về): ghi "không thấy" lần 1, rồi kiểm tra lần 2, lần 3. Đủ 3 lần đều không thấy = hôm nay event đó không
  có, đánh dấu xong.

Số lần không thấy lưu trong DB dưới dạng ba key ``<key>_miss_1..3`` (cũng tự hết hạn theo mốc reset), nên nhường Boss giữa
chừng hay khởi động lại vẫn đếm tiếp được.
"""
from typing import Callable, Iterable

from .common import mark_task_done

MAX_MISSES = 3


def _miss_keys(key: str) -> list[str]:
    return [f"{key}_miss_{index}" for index in range(1, MAX_MISSES + 1)]


def misses(bot, key: str) -> int:
    """Số lần đã kiểm tra mà không thấy event trong ngày hiện tại."""
    return sum(1 for miss_key in _miss_keys(key) if bot.is_daily_done(miss_key))


def add_miss(bot, key: str) -> int:
    """Ghi thêm một lần không thấy; trả về tổng số lần."""
    count = misses(bot, key) + 1
    bot.mark_daily_done(_miss_keys(key)[min(count, MAX_MISSES) - 1])
    return count


def reset_misses(bot, key: str):
    """Thấy event: đưa số lần không thấy về 0."""
    for miss_key in _miss_keys(key):
        if bot.done_at(miss_key) is not None:
            bot.forget_daily(miss_key)


def run_zone(bot, zone_key: str, tasks: Iterable[tuple[str, str]],
             sweep: Callable[[object, list[str]], set[str]], *,
             max_sweeps: int = MAX_MISSES) -> bool:
    """Chạy tối đa 3 lượt kiểm tra cho các nhiệm vụ chưa xong; True khi cả hoạt động xong hôm nay.

    ``tasks``: (key, nhãn). ``sweep(bot, pending_keys)`` làm MỘT lượt: tìm từng event trong ``pending_keys``, thấy thì nhận
    quà và ``mark_task_done`` đúng key đó; trả về tập key đã thực sự dò (trang cha mở được). Event không nằm trong tập này
    (không mở nổi trang cha) KHÔNG bị tính là "không thấy"."""
    tasks = list(tasks)
    if bot.is_daily_done(zone_key):
        return True
    for _ in range(max_sweeps):
        pending = [(key, label) for key, label in tasks if not bot.is_daily_done(key)]
        if not pending:
            break
        bot.check()
        inspected = sweep(bot, [key for key, _ in pending])
        for key, label in pending:
            if bot.is_daily_done(key):
                reset_misses(bot, key)
                bot.record(f"Gift Claims: {label} đã DONE trong lượt kiểm tra này")
                continue
            if key not in inspected:
                continue
            attempt = min(misses(bot, key) + 1, MAX_MISSES)
            bot.record(f"Gift Claims: kiểm tra {label} không xuất hiện "
                       f"(lượt {attempt}/{MAX_MISSES})")
            count = add_miss(bot, key)
            bot.record(f"Gift Claims: không thấy {label} (lần {count}/{MAX_MISSES})")
            if count >= MAX_MISSES:
                bot.record(f"Gift Claims: {label} không có hôm nay; đánh dấu xong")
                mark_task_done(bot, key)
        if not inspected:
            break
    if all(bot.is_daily_done(key) for key, _ in tasks):
        bot.mark_daily_done(zone_key)
        return True
    return False
