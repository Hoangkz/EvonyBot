"""
common.py — phần dùng chung của mọi nhiệm vụ Daily Activities (port từ DailyActivities1234.cs):
vòng lặp chụp màn -> ảnh khớp đầu tiên -> action (run_task), mở bảng Activity, mở dòng nhiệm vụ
bằng nút Go, cuộn danh sách, nhận thưởng cuối.

Mỗi nhiệm vụ (thư mục con) khai báo một Task: ảnh xong (done), ảnh + action (actions) và handler
xử lý các action riêng của nó. Action chung (DONE / BACK / TAP / SCROLL / OPEN ...) do run_task xử
lý; action khác chuyển cho handler (handler trả True = dừng nhiệm vụ lượt này, chưa xong).
"""
from dataclasses import dataclass
from functools import lru_cache
from typing import Callable

import cv2

from ...common import click_images, delay, exit_images, find_first, go_home
from ...context.templates import TEMPLATE_DIR
from .constants import (
    ACTIVITY_LIST,
    ACTIVITY_TAB,
    BACK,
    CLAIM_ALL,
    CLAIM_ALL_MIN_SATURATION,
    CLAIM_ALL_SIZE,
    CLAIM_BUTTON,
    DONE,
    GO_BUTTON,
    LIST_END_SAME,
    LIST_MAX_SCROLLS,
    LIST_RETRIES,
    LIST_SWIPE,
    MAIN_MORE,
    OLD_ACTIVITY_TITLE,
    OLD_CARD,
    OLD_CARD_THRESHOLD,
    OLD_CONGRATS,
    OLD_DONE_BADGE,
    OLD_DONE_CARD,
    OLD_DONE_CARD_THRESHOLD,
    OLD_DONE_TAP,
    OLD_DONE_THRESHOLD,
    OLD_DONE_WAIT,
    OLD_MENU_ACTIVITY,
    OLD_MENU_THRESHOLD,
    OLD_POPUP_GO,
    ROW_TITLE,
    OLD_POPUP_TIMEOUT,
    OLD_POPUP_WAIT,
    OPEN,
    OPEN_ACTIVITY_TRIES,
    OPEN_COLLECTING_HELPER,
    OPEN_MONSTER_FIRST,
    OPEN_MONSTER_SECOND,
    QUESTS_BUTTON,
    QUESTS_BUTTON_REGION,
    ROOT,
    ROW_BUTTON_DY,
    ROW_BUTTON_TOLERANCE,
    ROW_SETTLE_WAIT,
    ROW_ANCHORS,
    ROW_COMPLETE,
    ROW_MOVED,
    ROW_OPENED,
    ROW_TITLE_MAX_Y,
    SCROLL,
    TAP,
    TASK_DONE,
    TASK_HAS_GO,
    TASK_NO_LIST,
    TASK_NOT_FOUND,
    TASK_OPENED,
    TASK_UNKNOWN,
    TICK_BUTTON,
    TICK_DY,
    USE_ALL,
    VERIFY_COLLECTING,
)

MONSTER_KILLING = "Monster Killing"   # nhãn nhiệm vụ đánh quái (run_task / run.py xử lý riêng)


@dataclass(frozen=True)
class Task:
    label: str          # tên nhiệm vụ (ô tích ở tab Daily Activities, key daily_done)
    folder: str         # thư mục ảnh dưới DailyActivites/
    done: tuple[str, ...]                    # ảnh "đã xong"
    actions: tuple[tuple[str, str], ...]     # (ảnh, action) theo thứ tự ưu tiên
    handler: Callable                        # handler(bot, action, pos, screen) -> bool
    after_open_tap: tuple[float, float] | None = (50, 50)   # % màn hình bấm sau Go (None = không)
    key: str = ""   # key nhiệm vụ trong bot/worker/priority.json (VD "daily_offering")


def run_task(bot, task: Task) -> bool:
    """True khi thấy ảnh Finish của task (đã hoàn thành trong ngày)."""
    targets = task_targets(task)
    last_scroll_pos = None
    scroll_stalls = 0
    while True:
        screen = bot.screenshot()
        # OPEN needs the template's top-left Y, matching the C# FindOutPoint
        # contract. The row crop and fallback Go coordinate are relative to it.
        active_targets = (monster_targets(targets, bot)
                          if task.label == MONSTER_KILLING else targets)
        action, pos = find_first(bot, screen, active_targets, top_left=ROW_ANCHORS,
                                 position_cache=image_positions(bot), fallback_full=True)
        if action == DONE:
            return True
        if action == BACK:
            bot.back(delay=1)
        elif action == TAP:
            delay(bot, 2)
            bot.tap(*pos, delay=2)
        elif action == SCROLL:
            if (last_scroll_pos is not None and pos is not None
                    and abs(pos[0] - last_scroll_pos[0]) <= 3
                    and abs(pos[1] - last_scroll_pos[1]) <= 3):
                scroll_stalls += 1
            else:
                scroll_stalls = 0
            last_scroll_pos = pos
            if scroll_stalls >= 2:
                bot.log("Daily Activities: end of list reached; returning to top")
                scroll_to_top(bot)
                last_scroll_pos = None
                scroll_stalls = 0
            else:
                scroll_up(bot)
        elif action == OPEN:
            row_state = open_task_row(bot, screen, pos, task.after_open_tap, task.folder)
            if row_state == ROW_COMPLETE:
                return True
        elif action in (OPEN_MONSTER_FIRST, OPEN_MONSTER_SECOND):
            if action == OPEN_MONSTER_SECOND:
                # Supports resuming after the first 2-kill task was already
                # claimed in an earlier run.
                bot._daily_monster_marches = max(
                    2, getattr(bot, "_daily_monster_marches", 0))
                bot._daily_monster_first_claimed = True
                bot._daily_monster_deferred = False
            row_state = open_task_row(bot, screen, pos, None, task.folder)
            if row_state == ROW_COMPLETE:
                if action == OPEN_MONSTER_FIRST:
                    claim_task_row(bot, screen, pos)
                    bot._daily_monster_marches = 2
                    bot._daily_monster_first_claimed = True
                    bot._daily_monster_deferred = True
                    bot.log("Daily Activities: Monster Killing deferred after 2 attacks")
                    delay(bot, 2)
                    return False
                return True
        elif action == VERIFY_COLLECTING:
            # ClaimCollecting is the real Resource Collecting task. The
            # Research technologies row is only a shortcut to Collection.
            row_state = open_task_row(bot, screen, pos, None, task.folder,
                                      open_when_available=False)
            if row_state == ROW_COMPLETE:
                return True
            if row_state == ROW_OPENED:
                bot.log("Daily Activities: Resource Collecting still has Go")
                scroll_to_top(bot)
        elif action == OPEN_COLLECTING_HELPER:
            # Indirect Research technologies row: use its Go button only to
            # reach Academy/Collection; never use this row as completion proof.
            row_state = open_task_row(bot, screen, pos, task.after_open_tap, task.folder)
            if row_state == ROW_COMPLETE:
                scroll_up(bot, 2)
        elif action is None:
            # A task's Go button often spends a few seconds transitioning to
            # the world/search screen. Pressing Android Back during that gap
            # opens Evony's Quit dialog and hides every Daily control.
            delay(bot, 1)
        elif task.handler(bot, action, pos, screen):
            return False


@lru_cache(maxsize=None)
def task_targets(task: Task) -> tuple[tuple[str, str], ...]:
    folder = f"{ROOT}/{task.folder}"
    # Tên có "/" là đường dẫn đầy đủ dưới Images/ (ảnh dùng chung, VD CityTax/), không thì trong thư mục task.
    result = [(name if "/" in name else f"{folder}/{name}", DONE) for name in task.done]
    result.extend((name if "/" in name else f"{folder}/{name}", action)
                  for name, action in task.actions)
    # Initial Daily start can begin on either city/world layout. These are the
    # actual Quests/Daily buttons (including the exact crop supplied by the
    # user); without them the generic recovery path runs before a task has
    # opened the Activity list.
    result.extend((f"{USE_ALL}/{name}", TAP) for name in (
        "QuestButtonDaily.png", "QuestButtonCurrent.png", "QuestButtonCity.png"))
    result.extend((path, BACK) for path in exit_images())
    result.extend((path, TAP) for path in click_images())
    # On the selected Activity tab, Click_Activities1 (the word "Activity")
    # and Click_ActivitiesLight (a task reward star) are both visible. Check
    # the star first so the list advances instead of tapping the selected tab
    # forever. Task labels stay ahead of this entry and therefore still open
    # immediately when their row is visible.
    result.append((f"{folder}/Click_ActivitiesLight.png", SCROLL))
    # Claim All belongs to the final reward phase. Tapping it while checking an
    # individual task can remove that completed row before its no-Go state is
    # observed, leaving the task runner unable to prove completion.
    for name in ("Click_Activities.png", "Click_Activities1.png", "Click_Activities2.png"):
        result.append((f"{folder}/{name}", TAP))
    result.append((f"{folder}/CheckAgain.png", BACK))
    return tuple(result)


# Action của ảnh tiêu đề dòng nhiệm vụ trong danh sách Activity.
ROW_TITLE_ACTIONS = (OPEN, OPEN_MONSTER_FIRST, OPEN_MONSTER_SECOND, VERIFY_COLLECTING,
                     OPEN_COLLECTING_HELPER)


def task_titles(task: Task) -> list[str]:
    """Ảnh tiêu đề dòng của nhiệm vụ trong danh sách Activity (đường dẫn dưới Images/) — dùng cho
    open_task. Có <thư mục ảnh>/Title.png (cắt từ danh sách thật) thì chỉ dùng ảnh đó; không thì
    lấy ảnh trong ACTIONS có action tiêu đề dòng (ảnh bản C#), theo thứ tự ACTIONS."""
    path = f"{ROOT}/{task.folder}/{ROW_TITLE}"
    if (TEMPLATE_DIR / path).exists():
        return [path]
    return [f"{ROOT}/{task.folder}/{name}" for name, action in task.actions
            if action in ROW_TITLE_ACTIONS]


def task_cards(task: Task) -> list[str]:
    """Ảnh thẻ của nhiệm vụ trên lưới Activity bản cũ (<thư mục ảnh>/Card.png), [] nếu chưa có."""
    path = f"{ROOT}/{task.folder}/{OLD_CARD}"
    return [path] if (TEMPLATE_DIR / path).exists() else []


def task_done_cards(task: Task) -> list[str]:
    """Ảnh thẻ đã nhận thưởng (tích "Completed") của nhiệm vụ trên lưới bản cũ (<thư mục ảnh>/Done.png), []
    nếu chưa có."""
    path = f"{ROOT}/{task.folder}/{OLD_DONE_CARD}"
    return [path] if (TEMPLATE_DIR / path).exists() else []


def image_positions(bot) -> dict[str, tuple[int, int]]:
    """Per-worker image positions used by adaptive region matching."""
    cache = getattr(bot, "_daily_image_positions", None)
    if cache is None:
        cache = {}
        bot._daily_image_positions = cache
    return cache


def monster_targets(targets, bot):
    """Hide the first monster row after its 2-kill reward was processed."""
    if not getattr(bot, "_daily_monster_first_claimed", False):
        return targets
    first = f"{ROOT}/ActivitiesAttackMonster/ActivitiesAttackMonster.png"
    return tuple((path, action) for path, action in targets if path != first)


def open_task_row(bot, screen, pos, after_open_tap=(50, 50), task_folder=None,
                  open_when_available: bool = True) -> str:
    """Open a task row, or confirm completion when its ``Go`` is gone.

    A completed task keeps its label but replaces ``Go`` with ``Claim``. The
    old coordinate fallback therefore clicked Claim and re-ran finished work.
    The label is our row anchor; once the complete row is visible, absence of
    Go is the server/UI completion signal.
    """
    _, y = pos
    if y > 500:
        bot.swipe_percent(70, 70, 65, 65, duration=1.0, delay=2)
        return ROW_MOVED
    _, width = screen.shape[:2]
    # `pos` is the top-left of the task label (as in the C# implementation),
    # so the whole 100 px row — including the tiny 20x15 Go image — is kept.
    row_y = max(0, y)
    row = bot.crop(screen, 0, row_y, width, 100)
    go_templates = []
    if task_folder:
        go_templates.append(f"{ROOT}/{task_folder}/Go.png")
    go_templates.append(f"{USE_ALL}/Go.png")
    go = next((match for path in go_templates
               if (match := bot.find(path, screen=row)) is not None), None)
    if go is None:
        bot.log("Daily Activities: task row has no Go button; completed")
        return ROW_COMPLETE
    if not open_when_available:
        return ROW_OPENED
    bot.tap(go[0], go[1] + row_y, delay=4)
    if after_open_tap is not None:
        bot.tap_percent(*after_open_tap, delay=1)
    return ROW_OPENED


def claim_task_row(bot, screen, pos) -> bool:
    """Claim one completed row so Evony can reveal its follow-up task."""
    _, y = pos
    row_y = max(0, y)
    row = bot.crop(screen, 0, row_y, screen.shape[1], 100)
    claim = bot.find(f"{ROOT}/ActivitiesSourceCollecting/Claim.png", screen=row)
    if claim is None:
        return False
    bot.tap(claim[0], claim[1] + row_y, delay=3)
    return True


def open_daily_activity(bot, attempts: int = 6, close_search: bool = False) -> bool:
    """Open Quests by image, select Activity, and verify the list is ready.

    The bottom-left control moves between the city and world layouts. A fixed
    8%,88% tap can therefore hit Settings. Never guess its coordinate.
    """
    activity_tab = f"{USE_ALL}/Click_Activities1.png"
    activity_marker = f"{USE_ALL}/Click_ActivitiesLight.png"
    quest_buttons = (f"{USE_ALL}/QuestButtonDaily.png",
                     f"{USE_ALL}/QuestButtonCurrent.png",
                     f"{USE_ALL}/QuestButtonCity.png",
                     f"{USE_ALL}/Click_Activities.png")
    search_closed = False
    for _ in range(attempts):
        screen = bot.screenshot()
        if bot.find(activity_marker, screen=screen) is not None:
            return True
        tab = bot.find(activity_tab, screen=screen)
        if tab is not None:
            bot.tap(*tab, delay=2)
            continue
        quest = next((match for path in quest_buttons
                      if (match := bot.find(path, threshold=0.72, screen=screen,
                                            region=(0, 70, 25, 100))) is not None), None)
        if quest is not None:
            bot.tap(*quest, delay=3)
            continue
        if close_search and not search_closed:
            # Current Evony leaves the bottom Search drawer over Quests.
            # Android Back opens the Quit dialog, so return to the city using
            # the verified world-map control instead.
            territory = bot.find(
                f"{ROOT}/ActivitiesAttackMonster/BackToTerritoryCurrent.png",
                threshold=0.72, screen=screen, region=(70, 10, 100, 35))
            if territory is not None:
                bot.tap(*territory, delay=4)
            else:
                delay(bot, 1)
            search_closed = True
            continue
        delay(bot, 1)
    bot.log("Daily Activities: Quests/Activity button was not found")
    return False


def scroll_up(bot, count: int = 1):
    for _ in range(count):
        bot.swipe_percent(70, 70, 55, 55, duration=1.0, delay=1)


def scroll_to_top(bot, count: int = 12):
    for _ in range(count):
        bot.swipe_percent(55, 55, 70, 70, duration=0.35, delay=0.15)


def replace_text(bot, text: str, deletes: int = 8):
    for _ in range(deletes):
        bot.shell("input keyevent KEYCODE_DEL")
    bot.shell(f"input text {text}")
    bot.shell("input keyevent KEYCODE_ENTER")


def tap_first(bot, templates: tuple[str, ...], attempts: int, after=None,
              missing=None, delay_seconds: float = 2) -> bool:
    """Bounded equivalent of the C# inner template-tapping loops."""
    hits = idle = 0
    while hits < attempts and idle < 8:
        screen = bot.screenshot()
        _, pos = find_first(bot, screen, [(path, "match") for path in templates],
                            position_cache=image_positions(bot), fallback_full=True)
        if pos is None:
            idle += 1
            if missing:
                missing()
            delay(bot)
            continue
        bot.tap(*pos, delay=delay_seconds)
        hits += 1
        idle = 0
        if after:
            after()
    return hits >= attempts


def collect_activity_rewards(bot):
    """Bước cuối: nhận thưởng dòng nhiệm vụ (Claim All) rồi mở mọi rương điểm Activity."""
    folder = f"{ROOT}/CollectionActivities"
    targets = [
        (f"{folder}/Click_ActivitiesLight.png", DONE),
        (f"{folder}/Click_Activities2.png", TAP),
        (f"{folder}/Click_Activities1.png", TAP),
        (f"{folder}/Click_Activities.png", TAP),
        *[(path, BACK) for path in exit_images()],
        *[(path, TAP) for path in click_images()],
    ]
    while True:
        screen = bot.screenshot()
        reward_popup = bot.find(f"{folder}/CongratulationsCurrent.png", screen=screen)
        if reward_popup is not None:
            bot.back(delay=2)
            continue
        # Claim task rows first because their activity points can unlock an
        # additional chest in the same pass.
        claim_all = bot.find(f"{folder}/Claim_All.png", screen=screen)
        if claim_all is not None:
            bot.tap(*claim_all, delay=2)
            continue
        # All claimable chests share the same open/glowing body. Restricting
        # the search to the chest row avoids confusing a claimed chest with a
        # different number and automatically supports the new 145 chest.
        chests = bot.find_all(f"{folder}/OpenChestCurrent.png", threshold=0.72,
                              screen=screen, region=(8, 37, 92, 47))
        if chests:
            # One chest per fresh screenshot: each tap opens a reward popup,
            # so stale coordinates for the remaining chests are not reusable.
            bot.tap(*sorted(chests)[0], delay=2)
            continue
        action, pos = find_first(bot, screen, targets,
                                 position_cache=image_positions(bot), fallback_full=True)
        if action == DONE:
            return
        if action == BACK:
            bot.back(delay=1)
        elif action == TAP:
            delay(bot, 2)
            bot.tap(*pos, delay=2)
        else:
            go_home(bot, screen)
            delay(bot)


# ---- Mở một nhiệm vụ: phiên bản giao diện MỚI (danh sách) và CŨ (lưới thẻ) -------------------
NEW_UI, OLD_UI = "new", "old"


def open_activity_list(bot) -> str | None:
    """Từ màn chính mở bảng Activity, tự nhận ra phiên bản giao diện:
    - MỚI: nút Quests góc dưới trái -> popup Quests -> tab Activity -> danh sách (NEW_UI);
    - CŨ: không có nút Quests -> nút "•••" -> bảng chức năng -> "Activity" -> lưới thẻ (OLD_UI).
    Ở màn khác: go_home (popup / màn khác về màn chính). None nếu không mở được.
    Bảng đã mở sẵn ngay lần nhìn đầu (có thể đang ở giữa danh sách): Back đóng rồi mở lại từ đầu (không
    bao giờ cuộn lên)."""
    for attempt in range(OPEN_ACTIVITY_TRIES):
        screen = bot.screenshot()
        ui = (NEW_UI if bot.find(ACTIVITY_LIST, screen=screen) is not None
              else OLD_UI if bot.find(OLD_ACTIVITY_TITLE, screen=screen) is not None else None)
        if ui is not None:
            if attempt == 0:
                bot.back(delay=1)
                continue
            return ui
        tab = bot.find(ACTIVITY_TAB, screen=screen)
        if tab is not None:
            bot.tap(*tab, delay=2)
            continue
        item = bot.find(OLD_MENU_ACTIVITY, threshold=OLD_MENU_THRESHOLD, screen=screen)
        if item is not None:
            bot.tap(*item, delay=3)
            continue
        more = bot.find(MAIN_MORE, screen=screen)
        if more is not None:
            quests = bot.find(QUESTS_BUTTON, screen=screen, region=QUESTS_BUTTON_REGION)
            bot.tap(*(quests if quests is not None else more), delay=3)
            continue
        go_home(bot, screen)
        delay(bot, 1)
    bot.record("Daily Activities: Activity list not opened")
    return None


def open_task(bot, titles, cards=(), max_scrolls: int = LIST_MAX_SCROLLS, done_cards=(),
              tap_go: bool = True) -> str:
    """Mở nhiệm vụ tới lúc bấm Go (sau Go hai phiên bản giống nhau, phần riêng của nhiệm vụ làm tiếp).
    `titles`: ảnh tiêu đề dòng (bản mới, task_titles); `cards`: ảnh thẻ (bản cũ, task_cards);
    `done_cards`: ảnh thẻ đã nhận thưởng (bản cũ, task_done_cards) -> TASK_DONE.
    Bản MỚI (_search_list): Claim All bấm trước; cuộn tìm tiêu đề; nút ngay dưới tiêu đề là Go ->
    bấm. Bản CŨ (_search_grid): lướt lưới tìm thẻ -> bấm thẻ -> popup -> Go.
    Lướt hết không thấy: Back rồi mở lại bảng Activity, tìm thêm LIST_RETRIES lần.
    Trả TASK_OPENED (đã bấm Go), TASK_DONE (dòng / popup không còn Go), TASK_NOT_FOUND (lướt hết
    LIST_RETRIES + 1 lượt không thấy), TASK_UNKNOWN (thấy dòng mà không nhận ra nút / thiếu ảnh thẻ),
    TASK_NO_LIST (không mở được bảng Activity).
    `tap_go=False`: chỉ kiểm tra nhiệm vụ xong chưa — dòng còn Go (bản mới) / thẻ chưa nhận (bản cũ) thì không
    bấm gì, trả TASK_HAS_GO."""
    titles = (titles,) if isinstance(titles, str) else tuple(titles)
    cards = (cards,) if isinstance(cards, str) else tuple(cards)
    done_cards = (done_cards,) if isinstance(done_cards, str) else tuple(done_cards)
    bot._daily_claim_all_stuck = False   # Claim All kẹt chỉ bỏ qua trong lượt mở nhiệm vụ này
    for attempt in range(LIST_RETRIES + 1):
        ui = open_activity_list(bot)
        if ui is None:
            return TASK_NO_LIST
        if ui == OLD_UI:
            if not cards:
                bot.record("Daily Activities: task has no card image for the old Activity screen")
                return TASK_UNKNOWN
            wanted = cards
            result = _search_grid(bot, cards, max_scrolls, done_cards, tap_go)
        else:
            if not titles:
                bot.record("Daily Activities: task has no row title image for the Activity list")
                return TASK_UNKNOWN
            wanted = titles
            result = _search_list(bot, titles, max_scrolls, tap_go)
        if result != TASK_NOT_FOUND:
            return result
        if attempt < LIST_RETRIES:
            # Có thể cuộn trượt qua dòng: Back đóng bảng Activity, vòng sau mở lại từ đầu.
            bot.log(f"Daily Activities: {wanted[0]} not found, back and retry "
                    f"{attempt + 1}/{LIST_RETRIES}")
            bot.back(delay=1)
    return TASK_NOT_FOUND


def _search_list(bot, titles, max_scrolls: int, tap_go: bool = True) -> str:
    """Danh sách Activity (bản mới): mỗi màn thấy Claim All thì bấm trước (bấm mà vẫn còn = lỗi game,
    bỏ qua tới hết lượt này); tìm tiêu đề dòng; thấy (và trên ROW_TITLE_MAX_Y): nút ngay dưới
    (ROW_BUTTON_DY) là Go -> bấm, TASK_OPENED; Claim / tích V -> TASK_DONE; không nhận ra nút ->
    TASK_UNKNOWN. Tiêu đề sát đáy (y > ROW_TITLE_MAX_Y) thì cuộn tiếp, trừ khi đã hết danh sách. Không
    thấy thì cuộn xuống; hết danh sách -> TASK_NOT_FOUND."""
    claim_all_stuck = getattr(bot, "_daily_claim_all_stuck", False)
    previous = None
    scrolls = 0
    settled = False   # đã chờ danh sách đứng yên rồi xét lại dòng (khi không nhận ra nút)
    while True:
        screen = bot.screenshot()
        if not claim_all_stuck:
            claim_all = _active_claim_all(bot, screen)
            if claim_all is not None:
                bot.log("Daily Activities: Claim All")
                bot.tap(*claim_all, delay=2)
                screen = bot.screenshot()   # bấm Claim All không hiện popup
                if _active_claim_all(bot, screen) is not None:
                    bot.log("Daily Activities: Claim All still there, ignoring it")
                    claim_all_stuck = bot._daily_claim_all_stuck = True
        title = next((pos for path in titles
                      if (pos := bot.find(path, screen=screen)) is not None), None)
        at_end = previous is not None and _same_list(previous, screen)
        # Tiêu đề sát đáy (nút có thể bị thanh Claim All che): cuộn tiếp; đã hết danh sách thì xét luôn.
        if title is not None and (title[1] <= ROW_TITLE_MAX_Y or at_end):
            button = _row_button(bot, screen, title, tap_go)
            if button == "go":
                return TASK_OPENED if tap_go else TASK_HAS_GO
            if button in ("claim", "tick"):
                bot.log(f"Daily Activities: task row shows {button}; done")
                return TASK_DONE
            if not settled:
                # Danh sách có thể còn trôi sau khi cuộn (ảnh nhoè, nút không khớp): chờ rồi xét lại một lần.
                settled = True
                bot.sleep(ROW_SETTLE_WAIT)
                continue
            bot.record(f"Daily Activities: task row {title} has no Go / Claim / tick, not marking done")
            return TASK_UNKNOWN
        if scrolls >= max_scrolls or at_end:
            break
        previous = screen
        bot.swipe_percent(*LIST_SWIPE, duration=1.0, delay=1)
        scrolls += 1
    bot.log(f"Daily Activities: {titles[0] if titles else '?'} not found in Activity list")
    return TASK_NOT_FOUND


def _search_grid(bot, cards, max_scrolls: int, done_cards=(), tap_go: bool = True) -> str:
    """Lưới thẻ Activity (bản cũ): popup "Congratulations!" (OLD_CONGRATS) -> Back. Ở đầu lưới (chưa cuộn)
    thấy thẻ "100%" (OLD_DONE_BADGE) thì bấm giữa thẻ nhận trước (bấm mà vẫn còn -> bỏ qua tới hết lượt này); thẻ chưa nhận luôn nằm đầu lưới, đã cuộn
    mà thấy "100%" là thẻ đã nhận rồi -> không bấm. Lướt tìm thẻ (OLD_CARD_THRESHOLD) -> bấm -> popup: chờ Go (tối đa
    OLD_POPUP_TIMEOUT giây) -> bấm, TASK_OPENED; không có Go -> Back, TASK_UNKNOWN (chưa có ảnh popup
    "đã xong" nên không đoán). Hết lưới không thấy -> TASK_NOT_FOUND."""
    previous = None
    scrolls = 0
    done_stuck = False
    while True:
        screen = bot.screenshot()
        if bot.find(OLD_CONGRATS, screen=screen) is not None:
            # Popup "Congratulations!" sau khi nhận thẻ 100%: Back đóng (vẫn ở lưới).
            bot.log("Daily Activities: Congratulations popup, back")
            bot.back(delay=1)
            previous = None
            continue
        if not done_stuck and scrolls == 0:
            badge = bot.find(OLD_DONE_BADGE, threshold=OLD_DONE_THRESHOLD, screen=screen)
            if badge is not None:
                bot.log("Daily Activities: claim 100% task card")
                bot.tap(badge[0] + OLD_DONE_TAP[0], badge[1] + OLD_DONE_TAP[1], delay=OLD_DONE_WAIT)
                again = bot.find(OLD_DONE_BADGE, threshold=OLD_DONE_THRESHOLD, screen=bot.screenshot())
                if again is not None and abs(again[0] - badge[0]) + abs(again[1] - badge[1]) < 10:
                    bot.log("Daily Activities: 100% card still there, ignoring it")
                    done_stuck = True
                previous = None   # màn đã đổi: xét lại từ đầu
                continue
        if any(bot.find(path, threshold=OLD_DONE_CARD_THRESHOLD, screen=screen) is not None
               for path in done_cards):
            bot.log("Daily Activities: task card shows Completed; done")
            return TASK_DONE
        card = next((pos for path in cards
                     if (pos := bot.find(path, threshold=OLD_CARD_THRESHOLD, screen=screen))
                     is not None), None)
        if card is not None and not tap_go:
            # Chỉ kiểm tra: thẻ chưa nhận (thẻ "Completed" đã xét ở trên) = chưa xong; không bấm thẻ / mở popup.
            return TASK_HAS_GO
        if card is not None:
            bot.tap(*card, delay=OLD_POPUP_WAIT)
            go = bot.wait_for(OLD_POPUP_GO, timeout=OLD_POPUP_TIMEOUT)
            if go is not None:
                bot.tap(*go, delay=4)
                return TASK_OPENED
            # TODO: ảnh popup của nhiệm vụ đã xong (bản cũ) -> TASK_DONE; chưa có thì không đoán.
            bot.record("Daily Activities: task popup has no Go, not marking done")
            bot.back(delay=1)
            return TASK_UNKNOWN
        if scrolls >= max_scrolls or (previous is not None and _same_list(previous, screen)):
            break
        previous = screen
        bot.swipe_percent(*LIST_SWIPE, duration=1.0, delay=1)
        scrolls += 1
    bot.log(f"Daily Activities: {cards[0]} not found in Activity grid")
    return TASK_NOT_FOUND


def _active_claim_all(bot, screen):
    """Tâm nút Claim All còn sáng (có thưởng để nhận), hoặc None. Nút xám cũng khớp ảnh mẫu (0,86) nên xét thêm độ
    bão hoà màu trong khung nút: xám -> None."""
    pos = bot.find(CLAIM_ALL, screen=screen)
    if pos is None:
        return None
    w, h = CLAIM_ALL_SIZE
    box = bot.crop(screen, pos[0] - w // 2, pos[1] - h // 2, w, h)
    if float(cv2.cvtColor(box, cv2.COLOR_BGR2HSV)[..., 1].mean()) < CLAIM_ALL_MIN_SATURATION:
        return None
    return pos


def _row_button(bot, screen, title, tap_go: bool = True) -> str | None:
    """Nút ngay dưới tiêu đề dòng: Go -> bấm (`tap_go`), trả "go"; Claim -> "claim"; tích V -> "tick"; không
    nhận ra -> None."""
    x, y = title
    # (tên, ảnh, khoảng cách dưới tâm tiêu đề): tích V nằm cao hơn nút Go / Claim.
    buttons = [("go", GO_BUTTON, ROW_BUTTON_DY), ("claim", CLAIM_BUTTON, ROW_BUTTON_DY)]
    if (TEMPLATE_DIR / TICK_BUTTON).exists():
        buttons.append(("tick", TICK_BUTTON, TICK_DY))
    for name, path, dy in buttons:
        want = y + dy
        for bx, by in bot.find_all(path, screen=screen):
            if abs(by - want) <= ROW_BUTTON_TOLERANCE:
                if name == "go" and tap_go:
                    bot.tap(bx, by, delay=4)
                return name
    return None


def _same_list(before, after) -> bool:
    """Danh sách không đổi sau khi cuộn (đã tới cuối): so vùng giữa danh sách."""
    a, b = before[340:600], after[340:600]
    return float(cv2.matchTemplate(a, b, cv2.TM_CCOEFF_NORMED).max()) >= LIST_END_SAME


# ---- Đánh dấu xong hôm nay -------------------------------------------------------------------
def reached_key(task: Task, target: int) -> str:
    """Key daily_done: hôm nay nhiệm vụ đã xong với mục tiêu `target` (0 = không còn gì để làm)."""
    return f"{task.key}_reached_{target}"


def mark_task_done(bot, task: Task, target: int = 0):
    """Xong hôm nay (daily_done nhãn nhiệm vụ) kèm mục tiêu `target`."""
    bot.mark_daily_done(task.label)
    bot.mark_daily_done(reached_key(task, target))


def open_task_or_finish(bot, task: Task) -> bool:
    """open_task cho `task`. True khi đã bấm Go (làm tiếp phần sau Go).
    - Dòng không còn Go mà thấy rõ Claim / tích V (TASK_DONE) -> đánh dấu xong hôm nay, mục tiêu 0.
    - Lướt hết (kể cả LIST_RETRIES lần thử lại) không thấy (TASK_NOT_FOUND) -> bỏ qua lượt này, KHÔNG
      đánh dấu (có thể cuộn trượt; lần chạy sau tìm lại).
    - Không nhận ra nút / thiếu ảnh thẻ (TASK_UNKNOWN), không mở được bảng Activity -> không đánh dấu."""
    result = open_task(bot, task_titles(task), task_cards(task), done_cards=task_done_cards(task))
    if result == TASK_OPENED:
        return True
    if result == TASK_DONE:
        bot.record(f"Daily Activities: {task.label} has no Go, done today")
        mark_task_done(bot, task, 0)
    elif result == TASK_NOT_FOUND:
        bot.record(f"Daily Activities: {task.label} not found after {LIST_RETRIES + 1} tries, skipped")
    return False
