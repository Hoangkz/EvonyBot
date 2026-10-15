"""
common.py — phần dùng chung của mọi nhiệm vụ Daily Activities: mở bảng Activity (giao diện mới "Quests" / cũ "•••"),
mở dòng / thẻ nhiệm vụ bằng nút Go (open_task), cuộn danh sách, nhận thưởng cuối.

Mỗi nhiệm vụ (thư mục con) khai báo một Task (nhãn, thư mục ảnh, key) và hàm `after_go(bot)` làm phần sau khi bấm Go;
daily_job nối hai thứ đó thành việc cho bot/worker/priority.py.
"""
from dataclasses import dataclass

import cv2

from ...common import click_images, delay, exit_images, find_first, go_home
from ...context.templates import TEMPLATE_DIR
from .. import gift_claims
from ..result import NOT_DONE, TaskResult, clear, done, save_errors, take
from .constants import (
    GENERAL,
    REWARDS,
    ACTIVITY_LIST,
    ACTIVITY_TAB,
    ACTIVITY_TAB_REGION,
    ACTIVITY_TAB_THRESHOLD,
    BACK,
    CLAIM_ALL,
    CLAIM_ALL_MIN_SATURATION,
    CLAIM_ALL_SIZE,
    CLAIM_ALL_TAPS,
    CLAIM_ALL_THRESHOLD,
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
    OPEN_ACTIVITY_TRIES,
    QUESTS_BUTTON,
    QUESTS_BUTTON_REGION,
    ROOT,
    ROW_BUTTON_DY,
    ROW_BUTTON_TOLERANCE,
    ROW_SETTLE_WAIT,
    ROW_TITLE_MAX_Y,
    TAP,
    TASK_DONE,
    TASK_HAS_GO,
    TASK_TICK,
    TICK_TRIES,
    TASK_NO_LIST,
    TASK_NOT_FOUND,
    TASK_OPENED,
    TASK_UNKNOWN,
    TICK_BUTTON,
    TICK_DY,
)


@dataclass(frozen=True)
class Task:
    label: str          # tên nhiệm vụ (ô tích ở tab Daily Activities); key "xong hôm nay" trong daily_done là `key`
    folder: str         # thư mục ảnh dưới DailyActivites/ (Title.png: tiêu đề dòng, Card.png / Done.png: thẻ bản cũ)
    key: str = ""       # key nhiệm vụ trong bot/worker/priority.py (VD "daily_offering")


def task_titles(task: Task) -> list[str]:
    """Ảnh tiêu đề dòng của nhiệm vụ trong danh sách Activity (đường dẫn dưới Images/): <thư mục ảnh>/Title.png (cắt từ
    danh sách thật), [] nếu chưa có."""
    path = f"{ROOT}/{task.folder}/{ROW_TITLE}"
    return [path] if (TEMPLATE_DIR / path).exists() else []


def task_cards(task: Task) -> list[str]:
    """Ảnh thẻ của nhiệm vụ trên lưới Activity bản cũ (<thư mục ảnh>/Card.png), [] nếu chưa có."""
    path = f"{ROOT}/{task.folder}/{OLD_CARD}"
    return [path] if (TEMPLATE_DIR / path).exists() else []


def task_done_cards(task: Task) -> list[str]:
    """Ảnh thẻ đã nhận thưởng (tích "Completed") của nhiệm vụ trên lưới bản cũ (<thư mục ảnh>/Done.png), []
    nếu chưa có."""
    path = f"{ROOT}/{task.folder}/{OLD_DONE_CARD}"
    return [path] if (TEMPLATE_DIR / path).exists() else []


def collect_activity_rewards(bot):
    """Bước cuối: nhận thưởng dòng nhiệm vụ (Claim All) rồi mở mọi rương điểm Activity."""
    folder = f"{ROOT}/CollectionActivities"
    targets = [
        (f"{folder}/Click_ActivitiesLight.png", DONE),
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
        # Popup Quests 2 tab (không Chapter Quests) đang ở tab Main Quest: chữ "Activity" khớp ~0,90, sát ngưỡng mặc định 0,9
        # nên các ảnh tab bên dưới bỏ sót, rơi vào BACK (đóng Quests) rồi mở lại -> lặp mãi. Bấm tab bằng ngưỡng riêng.
        if bot.find(f"{folder}/Click_ActivitiesLight.png", screen=screen) is None:
            tab = bot.find(ACTIVITY_TAB, threshold=ACTIVITY_TAB_THRESHOLD, screen=screen, region=ACTIVITY_TAB_REGION)
            if tab is not None:
                bot.log("Daily Activities: Activity tab, tapping it")
                bot.tap(*tab, delay=2)
                continue
        action, pos = find_first(bot, screen, targets, fallback_full=True)
        if action == DONE:
            return
        if action == BACK:
            bot.back(delay=1)
        elif action == TAP:
            delay(bot, 2)
            bot.tap(*pos, delay=2)
        else:
            # Không phải bảng Activity: mở bảng bằng open_activity_list (tự nhận giao diện mới "Quests" / cũ "•••"),
            # không bấm icon Quests theo ảnh mẫu (màn thành của giao diện cũ cũng có icon đó).
            open_activity_list(bot)


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
        tab = bot.find(ACTIVITY_TAB, threshold=ACTIVITY_TAB_THRESHOLD, screen=screen, region=ACTIVITY_TAB_REGION)
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
    Bản MỚI: Claim All kiểm tra một lần lúc vừa mở danh sách (_claim_all_first), rồi _search_list: cuộn tìm tiêu đề; nút ngay dưới tiêu đề là Go ->
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
    attempt = ticks = 0
    while attempt <= LIST_RETRIES:
        ui = open_activity_list(bot)
        if ui is None:
            return TASK_NO_LIST
        if ui == NEW_UI:
            _claim_all_first(bot)
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
        if result == TASK_TICK:
            # Dòng hiện dấu tích: có thể nhận nhầm / danh sách chưa cập nhật -> Back, mở lại, tìm Go tiếp; đủ TICK_TRIES lần
            # liên tiếp vẫn tích thì coi nhiệm vụ đã xong. Chỉ kiểm tra (tap_go=False) thì không cần thử lại.
            ticks += 1
            if ticks >= TICK_TRIES or not tap_go:
                bot.log(f"Daily Activities: task row shows tick {ticks} time(s); done")
                return TASK_DONE
            bot.log(f"Daily Activities: task row shows tick ({ticks}/{TICK_TRIES}), back and retry")
            bot.back(delay=1)
            continue
        if result != TASK_NOT_FOUND:
            return result
        if attempt < LIST_RETRIES:
            # Có thể cuộn trượt qua dòng: Back đóng bảng Activity, vòng sau mở lại từ đầu.
            bot.log(f"Daily Activities: {wanted[0]} not found, back and retry "
                    f"{attempt + 1}/{LIST_RETRIES}")
            bot.back(delay=1)
        attempt += 1
    return TASK_NOT_FOUND


def _search_list(bot, titles, max_scrolls: int, tap_go: bool = True) -> str:
    """Danh sách Activity (bản mới; Claim All đã xử lý một lần lúc vừa mở danh sách, _claim_all_first, không
    kiểm tra lại khi cuộn); tìm tiêu đề dòng; thấy (và trên ROW_TITLE_MAX_Y): nút ngay dưới
    (ROW_BUTTON_DY) là Go -> bấm, TASK_OPENED; Claim / tích V -> TASK_DONE; không nhận ra nút ->
    TASK_UNKNOWN. Tiêu đề sát đáy (y > ROW_TITLE_MAX_Y) thì cuộn tiếp, trừ khi đã hết danh sách. Không
    thấy thì cuộn xuống; hết danh sách -> TASK_NOT_FOUND."""
    previous = None
    scrolls = 0
    settled = False   # đã chờ danh sách đứng yên rồi xét lại dòng (khi không nhận ra nút)
    while True:
        screen = bot.screenshot()
        title = next((pos for path in titles
                      if (pos := bot.find(path, screen=screen)) is not None), None)
        at_end = previous is not None and _same_list(previous, screen)
        # Tiêu đề sát đáy (nút có thể bị thanh Claim All che): cuộn tiếp; đã hết danh sách thì xét luôn.
        if title is not None and (title[1] <= ROW_TITLE_MAX_Y or at_end):
            button = _row_button(bot, screen, title, tap_go)
            if button == "go":
                return TASK_OPENED if tap_go else TASK_HAS_GO
            if button == "tick":
                bot.log("Daily Activities: task row shows tick")
                return TASK_TICK
            if button == "claim":
                bot.log("Daily Activities: task row shows claim; done")
                return TASK_DONE
            if not settled:
                # Danh sách có thể còn trôi sau khi cuộn (ảnh nhoè, nút không khớp): chờ rồi xét lại một lần.
                settled = True
                bot.sleep(ROW_SETTLE_WAIT)
                continue
            bot.record(f"Daily Activities: task row {title} has no Go / Claim / tick, not marking done")
            return TASK_UNKNOWN
        # Tiêu đề luôn xét trước (tiêu đề và tích có thể cùng một màn); chỉ khi KHÔNG thấy tiêu đề mà đã thấy một dấu tích V: danh sách xếp nhiệm vụ đã xong ở / dưới dấu tích,
        # nên nhiệm vụ này (chưa thấy Go ở trên) đã xong. Có thể cuộn trượt qua dòng Go nên open_task kiểm tra lại (TICK_TRIES).
        if title is None and (TEMPLATE_DIR / TICK_BUTTON).exists() and bot.find(TICK_BUTTON, screen=screen) is not None:
            bot.log("Daily Activities: tick seen before the task row")
            return TASK_TICK
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
    """Tâm nút Claim All còn sáng (màu xanh, có thưởng để nhận), hoặc None. Nút xám cũng khớp ảnh mẫu (0,86) nên xét thêm
    độ bão hoà màu trong khung nút: xám -> None. Log độ khớp + độ bão hoà để biết vì sao bấm / không bấm."""
    pos = bot.find(CLAIM_ALL, threshold=CLAIM_ALL_THRESHOLD, screen=screen)
    if pos is None:
        return None
    w, h = CLAIM_ALL_SIZE
    box = bot.crop(screen, pos[0] - w // 2, pos[1] - h // 2, w, h)
    saturation = float(cv2.cvtColor(box, cv2.COLOR_BGR2HSV)[..., 1].mean())
    active = saturation >= CLAIM_ALL_MIN_SATURATION
    bot.log(f"Daily Activities: Claim All at {pos}, saturation {saturation:.0f} -> {'green' if active else 'gray'}")
    return pos if active else None


def _claim_all_first(bot):
    """Vừa mở danh sách Activity (bản mới): chờ danh sách đứng yên rồi kiểm tra Claim All; xanh thì bấm (lặp tới
    CLAIM_ALL_TAPS lần, tới khi hết xanh), xám / không thấy thì thôi. Làm trước khi tìm nhiệm vụ."""
    bot.sleep(1)
    for _ in range(CLAIM_ALL_TAPS):
        claim_all = _active_claim_all(bot, bot.screenshot())
        if claim_all is None:
            return
        bot.log("Daily Activities: Claim All")
        bot.tap(*claim_all, delay=2)


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


# ---- Báo xong hôm nay (chỗ chạy việc, common.py daily_job, lưu vào DB ngay) --------------------------------------
def mark_task_done(bot, task: Task, target: int = 0):
    """Luồng bên trong báo nhiệm vụ đã xong hôm nay, kèm mục tiêu `target` (result.done). Không ghi gì vào DB."""
    return done(bot, target, label=task.label, key=task.key)


def open_task_or_finish(bot, task: Task) -> bool:
    """open_task cho `task`. True khi đã bấm Go (làm tiếp phần sau Go).
    - Dòng không còn Go mà thấy rõ Claim / tích V (TASK_DONE) -> báo xong hôm nay, mục tiêu 0.
    - Lướt hết (kể cả LIST_RETRIES lần thử lại) không thấy (TASK_NOT_FOUND) -> bỏ qua lượt này, KHÔNG
      báo xong (có thể cuộn trượt; lần chạy sau tìm lại).
    - Không nhận ra nút / thiếu ảnh thẻ (TASK_UNKNOWN), không mở được bảng Activity -> không báo xong."""
    result = open_task(bot, task_titles(task), task_cards(task), done_cards=task_done_cards(task))
    if result == TASK_OPENED:
        return True
    if result == TASK_DONE:
        bot.record(f"Daily Activities: {task.label} has no Go, done today")
        mark_task_done(bot, task, 0)
    elif result == TASK_NOT_FOUND:
        bot.record(f"Daily Activities: {task.label} not found after {LIST_RETRIES + 1} tries, skipped")
    return False


# ---- Một lần thử của việc Daily theo giờ (Alliance Donation / Help) ------------------------------------------------
# Khung chung: 1. kiểm tra trước: mở danh sách Activity, xem dòng / thẻ của việc (open_task tap_go=False, không bấm Go); xong
# (hết Go / Claim / tích V / thẻ Completed) thì dừng, trong ngày không đi kiểm tra lại; 2. chưa xong thì làm việc thật
# (`act(bot)`: donate lượt free, Help All); không làm được gì thì chưa xong (lần sau thử lại); 3. có làm thì kiểm tra lại.
# Khi nào thử và lưu kết quả vào DB: hourly_job bên dưới.
def try_task(bot, task: Task, act) -> TaskResult:
    """Một lần thử việc theo giờ `task`."""
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


# =============================================================================================
# Luật của các việc Daily cho bảng bot/worker/priority.py: dict {run, enabled, done, every}. Nhiệm vụ TỰ LƯU kết quả vào DB
# (daily_done) ngay chỗ chạy; worker chỉ kiểm tra `done` (đọc DB) rồi chạy hoặc bỏ qua.
# =============================================================================================

def hourly_hours(settings: dict, consts) -> int:
    """Số giờ giữa hai lần làm một việc theo giờ (ô chọn ở tab UI, luôn lưu khoá; thiếu khoá -> 0 = không làm, mặc định 4h
    do UI đặt). Cấu hình cũ (ô tích): True -> INTERVAL_DEFAULT, False -> 0."""
    value = settings.get(consts.INTERVAL_KEY, 0)
    if isinstance(value, bool):
        return consts.INTERVAL_DEFAULT if value else 0
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


_KEY_BY_LABEL: dict[str, str] = {}   # nhãn ô tích ở tab -> key daily_done; daily_job / hourly_job điền khi dựng việc


def selected_labels(settings: dict) -> set[str]:
    """Nhãn các việc Daily đã tích: ô tích (giá trị bool True) của tab Daily Activities, trừ mục General. Việc theo giờ là ô chọn
    giờ (số), không phải ô tích."""
    return {name for name, value in settings.items() if name != GENERAL and isinstance(value, bool) and value}


def record_result(ctx, key: str, result: TaskResult):
    """Lưu kết quả vào DB: xong thì "xong hôm nay" (`key`) và mục tiêu đã đạt (`<key>_reached_<mục tiêu>`)."""
    if not result.done:
        return
    ctx.mark_daily_done(key)
    if result.reached is not None:
        ctx.mark_daily_done(f"{key}_reached_{result.reached}")


def _reached(ctx, prefix: str) -> list[int]:
    """Các mốc N đã lưu hôm nay dưới dạng key `<prefix><N>` trong daily_done (VD "daily_offering_reached_6")."""
    return [int(k[len(prefix):]) for k in ctx.daily_keys()
            if k.startswith(prefix) and k[len(prefix):].isdigit() and ctx.is_daily_done(k)]


def _reached_enough(ctx, prefix: str, target: int) -> bool:
    """Đã đạt mục tiêu `target`: chưa lưu mốc nào (xong theo cách khác) hoặc mốc 0 (không còn gì để làm) hoặc mốc lớn nhất >=
    mục tiêu. `target` <= 0 thì luôn đủ."""
    if target <= 0:
        return True
    marks = _reached(ctx, prefix)
    return not marks or 0 in marks or max(marks) >= target


def _int(value) -> int:
    """Số nguyên >= 0 từ giá trị ô cấu hình (sai kiểu / trống -> 0)."""
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def daily_job(task: Task, after_go, target: str | None = None) -> dict:
    """Một việc Daily. `after_go(bot)`: open_task_or_finish bấm Go trong danh sách Activity rồi `after_go` làm phần sau Go.
    `target`: tên ô cấu hình của tab chứa mục tiêu (VD "Offer Gems") — xong khi mục tiêu đã đạt lưu trong DB >=
    số ở ô đó, nên tăng số ở tab là tự thành chưa xong, giảm lại là xong. Việc làm trong game không cần biết điều này."""
    _KEY_BY_LABEL[task.label] = task.key

    @save_errors(task.key)   # lỗi thì lưu `<key>_error` vào DB
    def run(ctx, settings):
        ctx.log(f"Daily Activities: {task.label}")
        clear(ctx)
        if open_task_or_finish(ctx, task):
            after_go(ctx)
        result = take(ctx) or NOT_DONE
        record_result(ctx, task.key, result)   # xong thì lưu "xong hôm nay" (key) vào DB

    def done(ctx, settings):
        return ctx.is_daily_done(task.key) and _reached_enough(
            ctx, f"{task.key}_reached_", _int(settings.get(target)) if target else 0)

    return {"run": run, "enabled": lambda settings: settings.get(task.label) is True, "done": done}


def hourly_job(task: Task, attempt, consts) -> dict:
    """Việc Daily theo giờ (Alliance Donation / Help): `attempt(ctx)` là một lần thử; `consts` là module constants của việc
    (INTERVAL_KEY / INTERVAL_DEFAULT: ô chọn giờ ở tab UI; TRIED_KEY: key lưu giờ vừa làm)."""

    _KEY_BY_LABEL[task.label] = task.key

    @save_errors(task.key)   # lỗi thì lưu `<key>_error` vào DB
    def run(ctx, settings):
        ctx.log(f"Daily Activities: {task.label} (every {hourly_hours(settings, consts)}h)")
        record_result(ctx, task.key, attempt(ctx))   # xong thì lưu "xong hôm nay" vào DB
        # Lưu giờ vừa làm vào DB (`<key>_tried`): worker chỉ so giờ này để biết tới giờ làm lại chưa. Bị ngắt / lỗi giữa
        # chừng thì tới đây không chạy tới, chưa lưu giờ: lượt sau làm tiếp.
        ctx.mark_daily_done(consts.TRIED_KEY)

    hours = lambda settings: hourly_hours(settings, consts)
    return {"run": run, "enabled": lambda settings: hours(settings) > 0,
            "done": lambda ctx, settings: ctx.is_daily_done(task.key), "every": hours}


def daily_selected_done(ctx, settings: dict) -> bool:
    """Mọi việc Daily đã tích (trừ việc theo giờ) đã xong hôm nay — đọc từ DB (key của nhiệm vụ)."""
    return all(ctx.is_daily_done(_KEY_BY_LABEL.get(label, label)) for label in selected_labels(settings))


@save_errors("daily_rewards")
def _run_rewards(ctx, settings):
    """Nhận thưởng Activity (dòng nhiệm vụ + rương điểm): mỗi ngày một lần, nhận xong là lưu "đã nhận" (dù còn việc Daily dở)."""
    collect_activity_rewards(ctx)
    ctx.mark_daily_done(REWARDS)


@save_errors("daily_gift_claims")
def _run_gifts(ctx, settings):
    """Nhận quà cuối ngày: chỉ khi mọi việc Daily đã tích và thưởng Activity đã xong (chưa thì worker xếp xuống cuối)."""
    if daily_selected_done(ctx, settings) and ctx.is_daily_done(REWARDS):
        gift_claims.run(ctx)


def _any_selected(settings: dict) -> bool:
    return bool(selected_labels(settings))


def _rewards_done_or_not_ready(ctx, settings) -> bool:
    """Xong hôm nay, hoặc chưa có việc Daily đã tích nào xong: worker bỏ qua, không mở bảng Activity nhận thưởng khi chưa có gì để
    nhận. Mỗi vòng worker đọc lại, có một việc xong là tự quay lại."""
    if ctx.is_daily_done(REWARDS):
        return True
    return not any(ctx.is_daily_done(_KEY_BY_LABEL.get(label, label)) for label in selected_labels(settings))


def _gifts_done_or_not_ready(ctx, settings) -> bool:
    """Xong hôm nay, hoặc chưa tới lúc nhận (Daily đã tích chưa xong hết / thưởng Activity chưa nhận): worker bỏ qua, không
    gọi run chạy không để đếm lần thử. Mỗi vòng worker đọc lại, hết điều kiện chặn là tự quay lại."""
    return (ctx.is_daily_done(gift_claims.KEY)
            or not (daily_selected_done(ctx, settings) and ctx.is_daily_done(REWARDS)))


REWARDS_JOB = {"run": _run_rewards, "enabled": _any_selected, "done": _rewards_done_or_not_ready}
GIFTS_JOB = {"run": _run_gifts, "enabled": _any_selected, "done": _gifts_done_or_not_ready}
