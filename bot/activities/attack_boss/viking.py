"""
viking.py — luồng Viking TỰ GỌI của Attack Boss: gọi boss ở màn Viking Challenge, Ask for Help rồi TẤN CÔNG luôn boss đó (không chia sẻ liên minh).

Luồng riêng, KHÔNG sửa event_center/viking_summon (luồng của Join Monster War vẫn gọi -> nhờ giúp -> chia sẻ như cũ). Chỉ dùng lại (đọc, không sửa) hằng số / ảnh
của nó và vài bước nhỏ: chọn độ khó, chờ về bản đồ, tìm boss, Ask for Help.

Lịch (KHÔNG kiểm tra định kỳ 8 phút như Viking Summon): chỉ trong cửa sổ sự kiện (giờ reset thứ 2 tới giờ reset thứ 5); chạy MỘT lần khi bắt đầu, rồi mỗi khi game
hiện popup "boss Viking đã bị hạ" (có chữ Summon; ensure_world ghi nhớ nếu lỡ đóng nó bằng Back) thì gọi boss mới và tấn công tiếp. Boss còn sống (nút Go thay cho Summon) thì bấm Go rồi tấn công.
"""
from datetime import datetime

from ..event_center.common import HANDLED, run_task_with_retry
from ..event_center.constants import ACTIVITIES
from ..event_center.viking_summon import constants as c
from ..event_center.viking_summon.run import (_answer_level_popup, _ask_for_help, _choose_level, _find_viking, _wait_map, in_window,
                                              viking_level)
from ..result import NOT_DONE, clear, take
from .constants import DEFEATED_ATTR, VIKING_SUMMON_KEY

NAME = "Attack Boss: Viking"
STARTED_ATTR = "attack_viking_started"      # trên bot: đã chạy luồng này một lần kể từ lúc bắt đầu


def summon_due(bot, settings: dict, screen) -> bool:
    """Tới lượt Viking tự gọi: đã tích Summon, đang trong cửa sổ sự kiện, và (chưa chạy lần nào từ lúc bắt đầu, hoặc popup "boss Viking đã bị hạ" đang hiện
    trên `screen`)."""
    if not settings.get(VIKING_SUMMON_KEY) or not in_window(datetime.now(), bot.server_time()):
        return False
    return (not getattr(bot, STARTED_ATTR, False) or getattr(bot, DEFEATED_ATTR, False)
            or bot.find(c.DEFEATED_TEXT, screen=screen) is not None)


def run(bot, settings: dict, attack):
    """Một lượt: tới màn Viking Challenge (Event Center), gọi boss (hoặc Go tới boss còn sống), Ask for Help, rồi `attack(bot)` tấn công boss đang ở giữa
    màn hình. `settings` là cấu hình tab Attack Boss (`viking_level`)."""
    clear(bot)
    setattr(bot, DEFEATED_ATTR, False)
    level = viking_level(settings)
    state = {"select_tries": 0, "congrats_tapped": False}

    def handle(action, pos, screen):
        if action == c.ON_DEFEATED:     # popup boss bị hạ hiện ở bất cứ màn nào: bấm Summon gọi boss mới
            return c.DONE if _defeated(bot, screen, attack) else HANDLED
        if action != c.ON_VIKING:
            return None
        return c.DONE if _viking(bot, level, state, attack) else HANDLED

    run_task_with_retry(bot, NAME, ACTIVITIES, c.ICON, handle, targets=[(c.DEFEATED_TEXT, c.ON_DEFEATED), (c.TITLE, c.ON_VIKING)],
                        regions={c.TITLE: c.TITLE_REGION}, icon_threshold=c.ICON_THRESHOLD)
    setattr(bot, STARTED_ATTR, True)
    return take(bot) or NOT_DONE


def _viking(bot, level: str, state: dict, attack) -> bool:
    """Màn Viking Challenge. True khi xong lượt (đã gọi / tấn công, hoặc bỏ cuộc); False nếu rời màn để run_task xử lý rồi quay lại."""
    for _ in range(c.MAX_STEPS):
        screen = bot.screenshot()
        if bot.find(c.TITLE, screen=screen, region=c.TITLE_REGION) is None:
            return False
        if bot.find(c.CONGRATULATIONS, screen=screen) is not None:
            if state["congrats_tapped"]:    # bấm vào popup mà vẫn còn: đóng bằng BACK
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
            bot.log(f"{NAME}: Viking boss is still alive, Go to it")
            bot.tap(*bot.find(c.GO, screen=screen, region=c.SUMMON_REGION), delay=0)
            return _to_boss_and_attack(bot, attack, "Go")
        elif bot.find(c.SUMMON_COST, screen=screen) is not None:
            pos = bot.find(c.SUMMON, screen=screen, region=c.SUMMON_REGION)
            if pos is None:
                bot.record(f"{NAME}: Summon button not found")
                return True
            bot.record(f"{NAME}: Summon ({level})")
            bot.tap(*pos, delay=0)
            return _to_boss_and_attack(bot, attack, "Summon")
        else:
            bot.log(f"{NAME}: unknown Viking screen, wait")
            bot.sleep(c.WAIT_SECONDS)
    bot.record(f"{NAME}: stopped after {c.MAX_STEPS} steps")
    return True


def _defeated(bot, screen, attack) -> bool:
    """Popup "boss Viking đã bị hạ, tốn thể lực Summon cấp N?": bấm Summon rồi như Summon ở màn Viking."""
    pos = bot.find(c.DEFEATED_SUMMON, screen=screen)
    if pos is None:
        bot.log(f"{NAME}: defeated popup without Summon button, back")
        bot.back(delay=1)
        return False
    bot.record(f"{NAME}: Viking defeated popup, Summon")
    bot.tap(*pos, delay=0)
    return _to_boss_and_attack(bot, attack, "Summon")


def _to_boss_and_attack(bot, attack, how: str) -> bool:
    """Sau Summon / Go: chờ về bản đồ thế giới (boss ở giữa màn hình), Ask for Help (bỏ qua nếu đã nhờ), rồi tấn công luôn. True khi xong lượt."""
    if not _wait_map(bot):
        bot.record(f"{NAME}: world map not shown after {how}")
        return True
    pos = _find_viking(bot)       # nhãn "Viking" ngay sau Summon; đã nhờ giúp rồi thì nhãn đổi, _ask_for_help thấy "(Asking for help)" nên bỏ qua
    bot.record(f"{NAME}: ask for help: {_ask_for_help(bot, pos)}")
    result = attack(bot)
    bot.record(f"{NAME}: attack own Viking: {result}")
    return True
