"""
run.py — nhiệm vụ Event Center "Viking Challenge": triệu hồi boss Viking của mình rồi chia sẻ cho liên minh; xem FLOW.md.

Flow: màn chính -> Event Center -> tab Activities -> cuộn tìm icon Viking Challenge (event_center.common.run_task) -> màn Viking:
- Màn chọn độ khó (chỉ hiện MỘT lần cho cả sự kiện; chọn rồi thì các lần sau vào thẳng màn Summon, không đổi được): bấm huy hiệu
  của `viking_level` -> Confirm -> hộp thoại "Select <Level> level?" (chờ 1 giây, tối đa 5 lần; không ra thì làm lại). Chỉ bấm Confirm
  của hộp thoại khi chữ trong hộp đúng độ khó yêu cầu, sai thì Cancel rồi chọn lại; "Congratulations!" (nhận Viking Poleaxe) đóng bằng cách bấm vùng trống.
- Màn Summon (boss chưa bị hạ thì thay bằng nút Go: bấm Go về chỗ boss rồi chia sẻ lại): bấm Summon -> game về bản đồ thế giới, boss Viking ở giữa màn -> chia sẻ vào liên minh (_share_boss).
Chỉ chạy trong cửa sổ từ giờ reset thứ 2 tới giờ reset thứ 5 (`in_window`); worker (JOB) chạy lại mỗi INTERVAL_MINUTES phút.
"""
from datetime import datetime, timedelta

from ....common import boss_scan
from ....daily_reset import reset_clock
from ...result import NOT_DONE, TaskResult, clear, done, save_errors, take
from ..common import HANDLED, run_task_with_retry
from ..constants import ACTIVITIES
from . import constants as c

NAME = "Viking Summon"
ENABLED_KEY, LEVEL_KEY = "viking_summon", "viking_level"   # trong cấu hình tab Join Monster War


def viking_level(settings: dict) -> str:
    """Độ khó người dùng chọn ở tab; thiếu / sai thì DEFAULT_LEVEL."""
    level = str((settings or {}).get(LEVEL_KEY) or c.DEFAULT_LEVEL)
    return level if level in c.LEVELS else c.DEFAULT_LEVEL


def run(bot, settings: dict) -> TaskResult:
    """`settings` là cấu hình tab Join Monster War. done=True khi đã bấm Summon trong lượt này."""
    clear(bot)
    level = viking_level(settings)
    state = {"select_tries": 0, "congrats_tapped": False}

    def handle(action, pos, screen):
        if action != c.ON_VIKING:
            return None
        return c.DONE if _viking(bot, level, state) else HANDLED

    run_task_with_retry(bot, NAME, ACTIVITIES, c.ICON, handle, targets=[(c.TITLE, c.ON_VIKING)],
                        regions={c.TITLE: c.TITLE_REGION}, icon_threshold=c.ICON_THRESHOLD)
    return take(bot) or NOT_DONE


def _viking(bot, level: str, state: dict) -> bool:
    """Màn Viking Challenge. True khi xong lượt (đã Summon, hoặc bỏ cuộc); False nếu rời màn để run_task xử lý rồi quay lại."""
    for _ in range(c.MAX_STEPS):
        screen = bot.screenshot()
        if bot.find(c.TITLE, screen=screen, region=c.TITLE_REGION) is None:
            return False
        if bot.find(c.CONGRATULATIONS, screen=screen) is not None:
            bot.log(f"{NAME}: close Congratulations")
            if state["congrats_tapped"]:   # bấm vào popup mà vẫn còn: đóng bằng BACK
                bot.back(delay=1)
            else:
                state["congrats_tapped"] = True
                bot.tap(*bot.find(c.CONGRATULATIONS, screen=screen), delay=1)
        elif bot.find(c.POPUP_TEXT, screen=screen, region=c.POPUP_REGION) is not None:
            _answer_level_popup(bot, screen, level)
        elif bot.find(c.SELECT_DIFFICULTY, screen=screen) is not None:
            if state["select_tries"] >= c.SELECT_TRIES:
                bot.record(f"{NAME}: cannot select level {level} after {c.SELECT_TRIES} tries, give up")
                return True
            state["select_tries"] += 1
            _choose_level(bot, level)
        elif bot.find(c.GO, screen=screen, region=c.SUMMON_REGION) is not None:
            _go_to_boss(bot, screen)
            return True
        elif bot.find(c.SUMMON_COST, screen=screen) is not None:
            _summon(bot, screen, level)
            return True
        else:
            bot.log(f"{NAME}: unknown Viking screen, wait")
            bot.sleep(c.WAIT_SECONDS)
    bot.record(f"{NAME}: stopped after {c.MAX_STEPS} steps")
    return True


def _wait(bot, template: str, region=None, *, gone: bool = False, tries: int = c.WAIT_TRIES):
    """Chờ `template` hiện ra (hoặc biến mất nếu `gone`): mỗi lần 1 giây, tối đa WAIT_TRIES lần. Trả vị trí tìm được (hoặc True khi
    `gone` đã biến mất), None nếu hết lần."""
    for _ in range(tries):
        bot.sleep(c.WAIT_SECONDS)
        pos = bot.find(template, region=region)
        if gone and pos is None:
            return True
        if not gone and pos is not None:
            return pos
    return None


def _choose_level(bot, level: str):
    """Bấm huy hiệu `level` rồi Confirm, chờ hộp thoại xác nhận độ khó; không ra thì thôi, vòng lặp ngoài thấy màn chọn và làm lại."""
    bot.log(f"{NAME}: select level {level}")
    name = bot.find(c.LEVEL_NAME[level], region=c.LEVEL_NAME_REGION)
    if name is None:
        bot.log(f"{NAME}: level name {level} not found")
        return
    bot.tap(name[0], name[1] - c.BADGE_ABOVE, delay=1)
    pos = bot.find(c.CONFIRM, region=c.CONFIRM_REGION)
    if pos is None:
        bot.log(f"{NAME}: Confirm button not found")
        return
    bot.tap(*pos, delay=0)
    if _wait(bot, c.POPUP_TEXT, c.POPUP_REGION) is None:
        bot.log(f"{NAME}: level dialog did not show after {c.WAIT_TRIES} waits, retry")


def _asked_level(bot, screen) -> str | None:
    """Độ khó hộp thoại đang hỏi ("Select <Level> level?"), None nếu không khớp ảnh nào."""
    for level, template in c.POPUP_LEVEL.items():
        if bot.find(template, threshold=c.POPUP_LEVEL_THRESHOLD, screen=screen, region=c.POPUP_REGION) is not None:
            return level
    return None


def _answer_level_popup(bot, screen, level: str):
    """Hộp thoại "Select <Level> level?": đúng độ khó yêu cầu thì Confirm (sự kiện này không đổi lại được nữa), sai thì Cancel."""
    asked = _asked_level(bot, screen)
    if asked != level:
        bot.record(f"{NAME}: dialog asks {asked}, want {level}, cancel")
        pos = bot.find(c.POPUP_CANCEL, screen=screen, region=c.POPUP_REGION)
        if pos is not None:
            bot.tap(*pos, delay=1)
        else:
            bot.back(delay=1)
        return
    pos = bot.find(c.POPUP_CONFIRM, screen=screen, region=c.POPUP_REGION)
    if pos is None:
        bot.log(f"{NAME}: dialog without Confirm button")
        return
    bot.record(f"{NAME}: confirm level {level} (cannot change for this event)")
    bot.tap(*pos, delay=0)
    if _wait(bot, c.CONGRATULATIONS) is None:
        bot.log(f"{NAME}: no Congratulations after confirming level")


def _summon(bot, screen, level: str):
    """Màn Summon: bấm Summon, chờ về bản đồ thế giới (chờ 1 giây, tối đa MAP_WAIT_TRIES = 10 lần), chia sẻ boss Viking vào liên minh."""
    for label, template in c.LEVEL_LABEL.items():
        if label != level and bot.find(template, screen=screen, region=c.LEVEL_LABEL_REGION) is not None:
            bot.record(f"{NAME}: this event already uses level {label} (wanted {level}), cannot change")
    pos = bot.find(c.SUMMON, screen=screen, region=c.SUMMON_REGION)
    if pos is None:
        bot.record(f"{NAME}: Summon button not found")
        return
    bot.record(f"{NAME}: Summon ({level})")
    bot.tap(*pos, delay=0)
    if _wait(bot, c.TITLE, c.TITLE_REGION, gone=True, tries=c.MAP_WAIT_TRIES) is None:
        bot.record(f"{NAME}: still on Viking screen after Summon")
        return
    done(bot, label=c.TRIED_KEY)
    _share(bot)


def _find_viking(bot):
    """Vị trí để bấm vào boss Viking vừa gọi trên bản đồ: tìm nhãn "Viking" (chờ 1 giây mỗi lần, tối đa BOSS_NAME_TRIES lần); thấy
    nhiều thì lấy cái gần hình boss (BOSS_ICON) nhất, hình boss gần giữa màn nhất; không thấy lần nào thì giữa màn hình (boss
    vừa gọi luôn ở giữa)."""
    for _ in range(c.BOSS_NAME_TRIES):
        bot.sleep(c.WAIT_SECONDS)
        screen = bot.screenshot()
        names = bot.find_all(c.BOSS_NAME, threshold=c.BOSS_NAME_THRESHOLD, screen=screen)
        h, w = screen.shape[:2]
        if not names:
            continue
        icons = bot.find_all(c.BOSS_ICON, threshold=c.BOSS_ICON_THRESHOLD, screen=screen)
        near = lambda target: (lambda pos: (pos[0] - target[0]) ** 2 + (pos[1] - target[1]) ** 2)
        target = min(icons, key=near((w / 2, h / 2))) if icons else (w / 2, h / 2)
        return min(names, key=near(target))
    bot.log(f"{NAME}: Viking label not found after {c.BOSS_NAME_TRIES} checks, tap the screen center")
    h, w = bot.screenshot().shape[:2]
    return w // 2, h // 2


def _go_to_boss(bot, screen):
    """Boss của mình chưa bị hạ (nút Go thay cho Summon): bấm Go, game về đúng vị trí boss, chia sẻ lại."""
    bot.log(f"{NAME}: Viking boss is still alive, Go to it")
    bot.tap(*bot.find(c.GO, screen=screen, region=c.SUMMON_REGION), delay=0)
    if _wait(bot, c.TITLE, c.TITLE_REGION, gone=True, tries=c.MAP_WAIT_TRIES) is None:
        bot.record(f"{NAME}: still on Viking screen after Go")
        return
    _share(bot)


def _share(bot):
    """Bản đồ thế giới, boss Viking vừa gọi ở giữa màn: bấm vào boss rồi chia sẻ vào liên minh (không đọc / ghi nhớ toạ độ boss)."""
    result = _share_boss(bot, _find_viking(bot))
    bot.record(f"{NAME}: share to alliance: {result}")


def _share_boss(bot, pos) -> str:
    """Gửi boss vào chat liên minh như một tin nhắn: bấm boss, chờ menu nhanh, bấm Share, chọn liên minh, Confirm (boss_scan.share_to_alliance
    tự chờ từng hộp, 1 giây tối đa 5 lần). Không kiểm tra liên minh, không đọc / ghi nhớ toạ độ, không dọn màn hình. "shared" hoặc "failed"."""
    bot.tap(*pos, delay=0)
    for _ in range(boss_scan.POLL_TRIES):
        bot.sleep(boss_scan.POLL)
        found = boss_scan.find_menu_item(bot, bot.screenshot(), boss_scan.SHARE_ICON)
        if found is not None:
            bot.tap(*found, delay=0)
            return "shared" if boss_scan.share_to_alliance(bot) else "failed"
    bot.log(f"{NAME}: Share button not found after tapping {pos}")
    return "failed"


# ---- Cửa sổ sự kiện và luật của việc (bảng bot/worker/priority.py: "run": JOB) ----------------------------------------
def in_window(now: datetime, server_time: str) -> bool:
    """Từ giờ reset thứ 2 tới giờ reset thứ 5 (3 ngày) của tuần chứa `now`."""
    hour, minute = map(int, reset_clock(server_time).split(":"))
    monday = (now - timedelta(days=now.weekday())).replace(hour=hour, minute=minute, second=0, microsecond=0)
    if monday > now:
        monday -= timedelta(days=7)
    return monday <= now < monday + timedelta(days=c.WINDOW_DAYS)


def summon_enabled(settings: dict) -> bool:
    return bool((settings or {}).get(ENABLED_KEY, False))


def _due(ctx, settings: dict) -> bool:
    """Đã bật, đang trong cửa sổ sự kiện và qua INTERVAL_MINUTES phút từ lần thử trước."""
    if not summon_enabled(settings) or not in_window(datetime.now(), ctx.server_time()):
        return False
    try:
        since = datetime.now() - datetime.fromisoformat(ctx.done_at(c.TRIED_KEY))
    except (TypeError, ValueError):
        return True
    return since >= timedelta(minutes=c.INTERVAL_MINUTES)


@save_errors(c.ERROR_KEY)   # lỗi thì lưu `viking_summon_error` vào DB
def _run_viking(ctx, settings: dict):
    ctx.log(f"Viking Summon: level {viking_level(settings)}")
    run(ctx, settings)
    ctx.mark_daily_done(c.TRIED_KEY)   # giờ thử gần nhất: _due so giờ này


JOB = {"run": _run_viking, "enabled": summon_enabled, "done": lambda ctx, settings: False, "due": _due}
