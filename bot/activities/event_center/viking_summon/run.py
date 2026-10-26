"""
run.py — nhiệm vụ Event Center "Viking Challenge": triệu hồi boss Viking của mình rồi chia sẻ cho liên minh; xem FLOW.md.

Flow: màn chính -> Event Center -> tab Activities -> cuộn tìm icon Viking Challenge (event_center.common.run_task) -> màn Viking:
- Màn chọn độ khó (chỉ hiện MỘT lần cho cả sự kiện; chọn rồi thì các lần sau vào thẳng màn Summon, không đổi được): bấm huy hiệu
  của `viking_level` -> Confirm -> hộp thoại "Select <Level> level?" (chờ 1 giây, tối đa 5 lần; không ra thì làm lại). Chỉ bấm Confirm
  của hộp thoại khi chữ trong hộp đúng độ khó yêu cầu, sai thì Cancel rồi chọn lại; "Congratulations!" (nhận Viking Poleaxe) đóng bằng cách bấm vùng trống.
- Màn Summon (boss chưa bị hạ thì thay bằng nút Go: bấm Go về chỗ boss rồi chia sẻ lại): bấm Summon -> game về bản đồ thế giới, boss Viking ở giữa màn -> Ask for Help (bấm boss -> Attack -> Ask for Help -> Confirm, bỏ qua nếu nhãn đã "Asking for help") -> chia sẻ vào liên minh (_share_boss).
Chỉ chạy khi `summon_enabled` (Join Monster War + đánh boss Viking + Summon) trong cửa sổ từ giờ reset thứ 2 tới giờ reset thứ 5 (`in_window`); worker (JOB) mỗi lần kiểm tra boss xong mới đếm INTERVAL_MINUTES = 8 phút tới lần kế, boss đã chia sẻ thì chỉ chia sẻ lại ở lần kiểm tra thứ 4.
"""
from datetime import datetime, timedelta

from ....common import boss_scan, click_images, exit_images, find_first
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
    # need_share: đã tới bản đồ mà chưa chia sẻ xong (lần kiểm tra sau thấy Go thì bấm Go ngay, không đợi đếm); share_tries: số lần chia sẻ đã thử;
    # asked: đã xử lý Ask for Help.
    state = {"select_tries": 0, "congrats_tapped": False, "need_share": False, "share_tries": 0, "asked": False}

    def handle(action, pos, screen):
        if action == c.ON_DEFEATED:   # popup boss bị hạ hiện ở bất cứ màn nào: xét trước mọi ảnh khác
            return c.DONE if _defeated(bot, screen, state) else HANDLED
        if action != c.ON_VIKING:
            return None
        return c.DONE if _viking(bot, level, state) else HANDLED

    run_task_with_retry(bot, NAME, ACTIVITIES, c.ICON, handle, targets=[(c.DEFEATED_TEXT, c.ON_DEFEATED), (c.TITLE, c.ON_VIKING)],
                        regions={c.TITLE: c.TITLE_REGION}, icon_threshold=c.ICON_THRESHOLD)
    return take(bot) or NOT_DONE


def _viking(bot, level: str, state: dict) -> bool:
    """Màn Viking Challenge. True khi xong lượt (đã Summon / chia sẻ xong, hoặc bỏ cuộc); False nếu rời màn để run_task xử lý rồi quay lại (cả khi
    chưa chia sẻ xong: quay lại đây bấm Go rồi chia sẻ tiếp)."""
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
            if state["need_share"] or _time_to_share_again(bot):
                return _go_to_boss(bot, screen, state)
            return True
        elif bot.find(c.SUMMON_COST, screen=screen) is not None:
            setattr(bot, c.CHECKS_ATTR, 0)   # thấy nút Summon = boss cũ đã mất: bộ đếm về 0, đếm lại từ lần kiểm tra đầu
            return _summon(bot, screen, level, state)
        else:
            bot.log(f"{NAME}: unknown Viking screen, wait")
            bot.sleep(c.WAIT_SECONDS)
    bot.record(f"{NAME}: stopped after {c.MAX_STEPS} steps")
    return True


def _defeated(bot, screen, state: dict) -> bool:
    """Popup "boss Viking đã bị hạ, tốn thể lực Summon cấp N?": bấm Summon, chờ về bản đồ, rồi như Summon ở màn Viking: boss mới thì Ask for Help +
    chia sẻ từ đầu, đếm lại các lần kiểm tra từ 0. True khi xong lượt; False nếu chưa chia sẻ xong (quay lại màn Viking bấm Go)."""
    pos = bot.find(c.DEFEATED_SUMMON, screen=screen)
    if pos is None:
        bot.log(f"{NAME}: defeated popup without Summon button, back")
        bot.back(delay=1)
        return False
    bot.record(f"{NAME}: Viking defeated popup, Summon")
    bot.tap(*pos, delay=0)
    setattr(bot, c.CHECKS_ATTR, 0)   # boss cũ đã mất: đếm lại từ lần kiểm tra đầu
    if not _wait_map(bot):
        bot.record(f"{NAME}: world map not shown after Summon from popup")
        return True
    done(bot, label=c.TRIED_KEY)
    state.update(need_share=True, share_tries=0, asked=False)
    return _share(bot, state)


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


def _wait_map(bot) -> bool:
    """Sau Summon / Go: chờ về tới bản đồ thế giới (thấy nút "•••"), qua màn trắng và sương nếu từ thành ra. Thấy ảnh click thì bấm, ảnh exit thì
    Back (ưu tiên hơn "•••") cho tới khi thấy "•••" lần đầu; thấy "•••" luôn thì xong luôn. False nếu hết MAP_READY_STEPS bước."""
    targets = [*[(path, c.TAP) for path in click_images()], *[(path, c.BACK) for path in exit_images()], (c.MAP_READY, c.ON_MAP)]
    for _ in range(c.MAP_READY_STEPS):
        action, pos = find_first(bot, bot.screenshot(), targets, thresholds={c.MAP_READY: c.MAP_READY_THRESHOLD})
        if action == c.ON_MAP:
            return True
        if action == c.TAP:
            bot.log(f"{NAME}: tap popup button at {pos}")
            bot.tap(*pos, delay=1)
        elif action == c.BACK:
            bot.log(f"{NAME}: close popup with Back")
            bot.back(delay=1)
        else:
            bot.sleep(c.WAIT_SECONDS)
    return False


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


def _summon(bot, screen, level: str, state: dict) -> bool:
    """Màn Summon: bấm Summon, chờ về bản đồ thế giới (nút \"•••\"; qua màn trắng, sương, popup), chia sẻ boss Viking vào liên minh."""
    for label, template in c.LEVEL_LABEL.items():
        if label != level and bot.find(template, screen=screen, region=c.LEVEL_LABEL_REGION) is not None:
            bot.record(f"{NAME}: this event already uses level {label} (wanted {level}), cannot change")
    pos = bot.find(c.SUMMON, screen=screen, region=c.SUMMON_REGION)
    if pos is None:
        bot.record(f"{NAME}: Summon button not found")
        return True
    bot.record(f"{NAME}: Summon ({level})")
    bot.tap(*pos, delay=0)
    if not _wait_map(bot):
        bot.record(f"{NAME}: world map not shown after Summon")
        return True
    done(bot, label=c.TRIED_KEY)
    state.update(need_share=True, share_tries=0, asked=False)   # boss mới: Ask for Help + chia sẻ từ đầu
    return _share(bot, state)


def _find_viking(bot, fallback: bool = True):
    """Vị trí để bấm vào boss Viking vừa gọi trên bản đồ: tìm nhãn "Viking" (mỗi lần chờ bản đồ đứng yên, tối đa BOSS_NAME_TRIES lần); thấy
    nhiều thì lấy cái gần hình boss (BOSS_ICON) nhất, hình boss gần giữa màn nhất; không thấy lần nào thì giữa màn hình (boss
    vừa gọi luôn ở giữa) nếu `fallback`, không thì None."""
    for _ in range(c.BOSS_NAME_TRIES):
        screen = boss_scan.settle(bot)   # chờ camera trượt xong rồi mới tìm: tìm lúc bản đồ còn trôi thì bấm trượt boss
        names = bot.find_all(c.BOSS_NAME, threshold=c.BOSS_NAME_THRESHOLD, screen=screen)
        h, w = screen.shape[:2]
        if not names:
            continue
        icons = bot.find_all(c.BOSS_ICON, threshold=c.BOSS_ICON_THRESHOLD, screen=screen)
        near = lambda target: (lambda pos: (pos[0] - target[0]) ** 2 + (pos[1] - target[1]) ** 2)
        target = min(icons, key=near((w / 2, h / 2))) if icons else (w / 2, h / 2)
        return min(names, key=near(target))
    if not fallback:
        return None
    bot.log(f"{NAME}: Viking label not found after {c.BOSS_NAME_TRIES} checks, tap the screen center")
    h, w = bot.screenshot().shape[:2]
    return w // 2, h // 2


def _time_to_share_again(bot) -> bool:
    """Boss còn sống (nút Go): True nếu chưa chia sẻ lần nào trong lượt chạy này, hoặc đây là lần kiểm tra thứ SHARE_AFTER_CHECKS kể từ lần
    chia sẻ trước; các lần kiểm tra giữa chỉ đếm."""
    checks = getattr(bot, c.CHECKS_ATTR, None)
    if checks is None:
        return True
    if checks + 1 >= c.SHARE_AFTER_CHECKS:
        return True
    setattr(bot, c.CHECKS_ATTR, checks + 1)
    bot.log(f"{NAME}: Viking boss still alive, shared before: check {checks + 1}/{c.SHARE_AFTER_CHECKS}, only look")
    return False


def _go_to_boss(bot, screen, state: dict) -> bool:
    """Boss của mình chưa bị hạ (nút Go thay cho Summon): bấm Go, game về đúng vị trí boss, chia sẻ lại (chỉ ở lần kiểm tra thứ SHARE_AFTER_CHECKS sau lần chia sẻ trước, xem _time_to_share_again)."""
    bot.log(f"{NAME}: Viking boss is still alive, Go to it")
    bot.tap(*bot.find(c.GO, screen=screen, region=c.SUMMON_REGION), delay=0)
    if not _wait_map(bot):
        bot.record(f"{NAME}: world map not shown after Go")
        return True
    return _share(bot, state)


def _share(bot, state: dict) -> bool:
    """Bản đồ thế giới, boss Viking ở giữa màn: Ask for Help (một lần, nếu chưa), rồi chia sẻ vào liên minh. Chia sẻ chưa được (VD bấm trượt
    vì camera chưa vào giữa boss) thì về bản đồ sạch (_wait_map), tìm lại boss và chia sẻ lại; không thấy boss thì trả False: quay lại màn
    Viking bấm Go (camera vào đúng boss) rồi chia sẻ tiếp. Tổng cộng tối đa SHARE_TRIES lần chia sẻ. True khi xong (chia sẻ được, hoặc hết lần thử)."""
    state["need_share"] = True
    while state["share_tries"] < c.SHARE_TRIES:
        first = state["share_tries"] == 0
        pos = _find_viking(bot, fallback=first)   # lần đầu không thấy nhãn thì bấm giữa màn; các lần sau không bấm mò nữa
        if pos is None:
            bot.record(f"{NAME}: Viking label not found, go back to the Viking screen and press Go")
            return False
        if not state["asked"]:
            bot.record(f"{NAME}: ask for help: {_ask_for_help(bot, pos)}")
            state["asked"] = True
        state["share_tries"] += 1
        result = _share_boss(bot, pos)
        bot.record(f"{NAME}: share to alliance: {result} ({state['share_tries']}/{c.SHARE_TRIES})")
        if result == "shared":
            state["need_share"] = False
            setattr(bot, c.CHECKS_ATTR, 0)   # bắt đầu đếm lại các lần kiểm tra tới lần chia sẻ kế
            return True
        _wait_map(bot)   # về bản đồ sạch (đóng popup) rồi tìm lại boss
    bot.record(f"{NAME}: cannot share after {c.SHARE_TRIES} tries, give up")
    state["need_share"] = False
    return True


def _menu_item(bot, icon: str):
    """Chờ nút `icon` của menu nhanh (hiện sau khi bấm boss): kiểm tra mỗi POLL giây; None nếu không hiện."""
    for _ in range(boss_scan.POLL_TRIES):
        bot.sleep(boss_scan.POLL)
        found = boss_scan.find_menu_item(bot, bot.screenshot(), icon)
        if found is not None:
            return found
    return None


def _asking(bot, pos) -> bool:
    """Nhãn "(Asking for help)" nằm gần nhãn boss ở `pos`: boss đã nhờ giúp rồi."""
    hits = bot.find_all(c.ASKING, threshold=c.ASKING_THRESHOLD)
    return any(abs(x - pos[0]) <= c.ASKING_NEAR and abs(y - pos[1]) <= c.ASKING_NEAR for x, y in hits)


def _ask_for_help(bot, pos) -> str:
    """Bấm boss -> Attack -> Ask for Help -> Confirm (tốn 1 Viking Poleaxe). Nhãn boss đã "(Asking for help)" thì không nhờ lại.
    "asked", "already" hoặc "failed"; mỗi lần chờ 1 giây, tối đa WAIT_TRIES lần."""
    if _asking(bot, pos):
        return "already"
    bot.tap(*pos, delay=0)
    attack = _menu_item(bot, boss_scan.ATTACK_ICON)
    if attack is None:
        bot.log(f"{NAME}: Attack button not found after tapping {pos}")
        return "failed"
    bot.tap(*attack, delay=0)
    button = _wait(bot, c.ASK_FOR_HELP)
    if button is None:
        bot.log(f"{NAME}: Ask for Help button not found")
        return "failed"
    bot.tap(*button, delay=0)
    if _wait(bot, c.ASK_DIALOG) is None:
        bot.log(f"{NAME}: Ask for Help dialog did not show")
        return "failed"
    confirm = bot.find(c.POPUP_CONFIRM, region=c.POPUP_REGION)
    if confirm is None:
        bot.log(f"{NAME}: Ask for Help dialog without Confirm button")
        return "failed"
    bot.tap(*confirm, delay=0)
    return "asked" if _wait(bot, c.ASK_DIALOG, gone=True) is not None else "failed"


def _share_boss(bot, pos) -> str:
    """Gửi boss vào chat liên minh như một tin nhắn: bấm boss, chờ menu nhanh, bấm Share, chọn liên minh, Confirm (boss_scan.share_to_alliance
    tự chờ từng hộp, 1 giây tối đa 5 lần). Không kiểm tra liên minh, không đọc / ghi nhớ toạ độ, không dọn màn hình. "shared" hoặc "failed"."""
    bot.tap(*pos, delay=0)
    found = _menu_item(bot, boss_scan.SHARE_ICON)
    if found is None:
        bot.log(f"{NAME}: Share button not found after tapping {pos}")
        return "failed"
    bot.tap(*found, delay=0)
    return "shared" if boss_scan.share_to_alliance(bot) else "failed"


# ---- Cửa sổ sự kiện và luật của việc (bảng bot/worker/priority.py: "run": JOB) ----------------------------------------
def in_window(now: datetime, server_time: str) -> bool:
    """Từ giờ reset thứ 2 tới giờ reset thứ 5 (3 ngày) của tuần chứa `now`."""
    hour, minute = map(int, reset_clock(server_time).split(":"))
    monday = (now - timedelta(days=now.weekday())).replace(hour=hour, minute=minute, second=0, microsecond=0)
    if monday > now:
        monday -= timedelta(days=7)
    return monday <= now < monday + timedelta(days=c.WINDOW_DAYS)


def summon_enabled(settings: dict) -> bool:
    """Nhiệm vụ Viking chạy khi đã chọn Join Monster War (tab này), tích đánh boss Viking trong danh sách boss, và tích Summon."""
    settings = settings or {}
    viking_selected = any(boss.get("name") == c.VIKING_NAME for boss in settings.get("selected_bosses") or [])
    return bool(settings.get(ENABLED_KEY, False)) and viking_selected


def _due(ctx, settings: dict) -> bool:
    """Đã bật (summon_enabled), đang trong cửa sổ sự kiện và qua INTERVAL_MINUTES phút từ lần thử trước."""
    if not summon_enabled(settings) or not in_window(datetime.now(), ctx.server_time()):
        return False
    try:
        since = datetime.now() - getattr(ctx, c.TRIED_ATTR)
    except (TypeError, AttributeError):
        return True   # chưa kiểm tra lần nào trong lượt chạy này (mới Start)
    return since >= timedelta(minutes=c.INTERVAL_MINUTES)


@save_errors(c.ERROR_KEY)   # lỗi thì lưu `viking_summon_error` vào DB
def _run_viking(ctx, settings: dict):
    ctx.log(f"Viking Summon: level {viking_level(settings)}")
    run(ctx, settings)
    setattr(ctx, c.TRIED_ATTR, datetime.now())   # giờ kiểm tra xong: _due đếm INTERVAL_MINUTES từ đây (không lưu DB)


JOB = {"run": _run_viking, "enabled": summon_enabled, "done": lambda ctx, settings: False, "due": _due}
