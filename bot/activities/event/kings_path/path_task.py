"""
path_task.py — flow chung của các nhiệm vụ King's Path (City Tax Day 1, Patrol Day 2, ...).
Mỗi nhiệm vụ chỉ khác Day, tab phụ và (nếu tab phụ có nhiều loại nhiệm vụ) tiêu đề dòng:
khai báo một PathTask rồi gọi run(bot, task, state, path).

Từ màn chính tới lúc bấm Go giống hệt các nhiệm vụ Gather Troops (xem
gather_troops/train_troop/run.py); phần đi từ màn chính tới màn event nằm trong
run_task() (event/common.py).

Flow:
1. Màn chính -> quà đăng nhập -> nút dưới Event Center -> danh sách event -> icon
   King's Path (run_task). Chưa có ảnh icon (KINGS_PATH_ICON) -> bỏ qua nhiệm vụ.
2. Màn King's Path vừa mở: đếm ổ khoá trên hàng tab Day. Tab Day của nhiệm vụ còn khoá
   -> lưu "chưa thể thực hiện" (locked_key, tới lần reset server) và dừng.
   Hàng tab Day giống hệt Gather Troops: không thấy tiêu đề "King's Path" (VD nhiệm vụ
   trước dừng ở màn Gather Troops) -> Back.
3. Tab "Day N" chưa chọn -> bấm.
4. Tab phụ của nhiệm vụ chưa chọn -> bấm (theo ảnh; chưa có ảnh thì bấm theo vị trí khi
   Day đang chọn).
5. Tab phụ đang chọn: tìm nút Go của nhiệm vụ — dòng Go trên cùng, hoặc dòng có tiêu đề
   `row_title` (không cuộn: Teamwork làm Patrol trước Donate, sau Claim All chỉ còn ~3 dòng Go
   nằm gọn trên màn — 2 dòng Patrol rồi dòng Donate). Không còn Go nào ->
   đánh dấu xong. Đọc số đã làm ở "a / b" trên nút (OCR): đã đạt mục tiêu (`value` trong
   settings) -> đánh dấu xong. Còn lại -> bấm Go.
6. Sau Go: `after_go(bot, path, done, target)` của nhiệm vụ. Chưa có -> dừng (TODO).
   after_go trả AGAIN (VD Heal vừa Speed Up xong lượt chữa dở) -> không dừng: vòng lặp đi lại từ
   màn chính -> Event Center -> King's Path -> Day -> tab -> OCR lại số đã làm -> Go lần nữa
   (không giới hạn số lần: lặp tới khi đủ mục tiêu; hết 120 s / có boss thì bị ngắt như thường,
   lượt sau làm tiếp).
"""
from dataclasses import dataclass, field
from typing import Callable

from ....context.templates import TEMPLATE_DIR
from ..common import EVENT_OPENED, HANDLED, STOP, EventState, day_locked, read_go_progress, run_task
from ..constants import DAY_TABS_REGION, GO_BUTTON, GO_REGION, KINGS_PATH_ICON
from .constants import (
    DAY_TABS,
    DAY_TABS_SELECTED,
    DAY_THRESHOLD,
    GO_THRESHOLD,
    GO_WAIT,
    ON_DAY,
    ON_TAB,
    OPEN_DAY,
    OPEN_TAB,
    ROW_GO_DY,
    ROW_GO_TOLERANCE,
    ROW_TITLE_THRESHOLD,
    ROWS_REGION,
    SUB_TAB_X,
    SUB_TAB_Y,
    SUB_TABS_REGION,
    TAB_THRESHOLD,
    TITLE,
    TITLE_REGION,
)


# after_go trả AGAIN: đi lại từ đầu (đọc lại tiến độ ở dòng Go rồi bấm Go lần nữa).
AGAIN = "again"


@dataclass(frozen=True)
class PathTask:
    """Phần riêng của một nhiệm vụ King's Path."""
    key: str                    # key trong settings / event.json (VD "kings_path_patrol")
    name: str                   # tên trong log (VD "Patrol")
    day: int                    # ngày mở nhiệm vụ (dùng khi settings thiếu "day")
    tab_index: int              # vị trí tab phụ trong Day: 0, 1, 2 (trái -> phải)
    tab_selected: str           # ảnh tab phụ khi đang chọn
    tab: str | None = None      # ảnh tab phụ khi chưa chọn (None: bấm theo tab_index)
    # Ảnh tiêu đề dòng khi tab phụ có nhiều loại nhiệm vụ (VD Teamwork: Patrol / Donate);
    # None = mọi dòng của tab phụ là của nhiệm vụ -> lấy dòng Go trên cùng.
    row_title: str | None = None
    # Làm nhiệm vụ sau khi bấm Go: (bot, path, done, target) -> None / AGAIN. None = chưa làm.
    after_go: Callable | None = field(default=None, compare=False)

    @property
    def locked_key(self) -> str:
        """Lưu trong daily_done khi tab Day còn khoá: bỏ qua tới lần reset server."""
        return f"{self.key}_locked"


def run(bot, task: dict, state: EventState, path: PathTask):
    """`task` là settings của nhiệm vụ: {"value": int, "day": int}."""
    name, key = path.name, path.key
    if not (TEMPLATE_DIR / KINGS_PATH_ICON).exists():
        bot.log(f"{name}: no King's Path icon image yet ({KINGS_PATH_ICON}), skipped")
        return
    if bot.is_daily_done(key):
        bot.log(f"{name}: already done")
        return
    if bot.is_daily_done(path.locked_key):
        bot.log(f"{name}: day still locked, skipped until server reset")
        return
    day = int(task.get("day") or path.day)
    target = int(task.get("value") or 0)
    progress = {"entered": False, "again": 0}   # again: số lần after_go trả AGAIN (để log)

    def enter(screen):
        """Lần đầu ở màn King's Path trong lượt này: Day khoá -> lưu, STOP."""
        progress["entered"] = True
        if day_locked(bot, screen, day):
            bot.log(f"{name}: Day {day} locked, cannot do this task yet")
            bot.mark_daily_done(path.locked_key)
            return STOP
        return None

    def handle(action, pos, screen):
        if action == EVENT_OPENED:
            return enter(bot.screenshot())   # Day đã mở: quét tiếp
        if action not in _EVENT_ACTIONS:
            return None
        if bot.find(TITLE, screen=screen, region=TITLE_REGION) is None:
            bot.log(f"{name}: event tabs but not King's Path, back")
            bot.back(delay=1)
            return HANDLED
        if not progress["entered"] and enter(screen) == STOP:
            return STOP
        if action in (OPEN_DAY, OPEN_TAB):
            bot.tap(*pos, delay=2)
        elif action == ON_DAY:
            bot.tap(SUB_TAB_X[path.tab_index], SUB_TAB_Y, delay=2)
        elif action == ON_TAB:
            go = _find_go(bot, screen, path)
            if go is None:
                bot.log(f"{name}: no Go left, done")
                bot.mark_daily_done(key)
                return STOP
            done = read_go_progress(bot, screen, go)
            if done is None:
                bot.log(f"{name}: cannot read progress")
            else:
                bot.log(f"{name}: done {done}, target {target}")
                if done >= target:
                    bot.log(f"{name}: target reached, done")
                    bot.mark_daily_done(key)
                    return STOP
            bot.tap(*go, delay=GO_WAIT)
            if path.after_go is None:
                bot.log(f"{name}: after Go not implemented yet, stop")
                return STOP
            if path.after_go(bot, path, done, target) == AGAIN:
                progress["again"] += 1
                bot.log(f"{name}: again from the start (re-read progress, round {progress['again']})")
                return HANDLED
            return STOP
        return HANDLED

    run_task(bot, state, name, KINGS_PATH_ICON, handle,
             targets=_targets(path, day), regions=_regions(path, day),
             thresholds=_thresholds(path, day))


_EVENT_ACTIONS = (OPEN_DAY, ON_DAY, OPEN_TAB, ON_TAB)


def _find_go(bot, screen, path: PathTask):
    """Nút Go của nhiệm vụ trên `screen`: dòng Go trên cùng (row_title None), hoặc nút Go
    cùng dòng với tiêu đề `row_title` trên cùng có Go. None nếu không có."""
    gos = sorted(bot.find_all(GO_BUTTON, threshold=GO_THRESHOLD, screen=screen,
                              region=GO_REGION), key=lambda p: p[1])
    if path.row_title is None:
        return gos[0] if gos else None
    titles = sorted(bot.find_all(path.row_title, threshold=ROW_TITLE_THRESHOLD, screen=screen,
                                 region=ROWS_REGION), key=lambda p: p[1])
    for _, ty in titles:
        for go in gos:
            if abs(go[1] - (ty + ROW_GO_DY)) <= ROW_GO_TOLERANCE:
                return go
    return None


def _targets(path: PathTask, day: int) -> list[tuple[str, str]]:
    """Ảnh riêng: tab phụ đang chọn trước, rồi tab phụ chưa chọn, Day đang chọn, Day."""
    targets = [(path.tab_selected, ON_TAB)]
    if path.tab is not None:
        targets.append((path.tab, OPEN_TAB))
    if day in DAY_TABS_SELECTED:
        targets.append((DAY_TABS_SELECTED[day], ON_DAY))
    if day in DAY_TABS:
        targets.append((DAY_TABS[day], OPEN_DAY))
    return targets


def _regions(path: PathTask, day: int) -> dict:
    regions = {path.tab_selected: SUB_TABS_REGION}
    if path.tab is not None:
        regions[path.tab] = SUB_TABS_REGION
    for images in (DAY_TABS, DAY_TABS_SELECTED):
        if day in images:
            regions[images[day]] = DAY_TABS_REGION
    return regions


def _thresholds(path: PathTask, day: int) -> dict:
    thresholds = {path.tab_selected: TAB_THRESHOLD}
    if path.tab is not None:
        thresholds[path.tab] = TAB_THRESHOLD
    for images in (DAY_TABS, DAY_TABS_SELECTED):
        if day in images:
            thresholds[images[day]] = DAY_THRESHOLD
    return thresholds
