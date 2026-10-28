"""
stamina.py — Attack Boss hết thể lực: dùng vật phẩm thể lực y như Join Monster War (`_Boss._use_stamina`), chỉ khi ô Use Stamina của tab được chọn
(ALL / 100 / 200 ... 500). Dùng lại các hàm của Join Monster War (nút Use của vật phẩm, thêm số lượng bằng nút +, chờ popup), chỉ khác phần sau cùng:
Join Boss bấm March bằng ảnh nút của nó, Attack Boss để `_march` (run.py) tự chọn đội và bấm March lại.
"""
from ...common import delay
from ..join_monster_war.constants import (REGIONS, STAMINA_ITEMS_OPEN_INTERVAL, STAMINA_ITEMS_OPEN_WAIT, STAMINA_REFILL_WAIT,
                                          STAMINA_SLIDER_END, STAMINA_USE)
from ..join_monster_war.run import (POLL_INTERVAL, STAMINA_CHOICES, STAMINA_CLOSE_ROUNDS, STAMINA_CLOSE_WAIT, STAMINA_MULTIPLES,
                                    _item_use_buttons)


OK, EMPTY, FAILED = "ok", "empty", "failed"      # kết quả của refill: đã dùng xong / hết vật phẩm thể lực / lỗi khác (màn không mở, popup không đóng)


def enabled(helper) -> bool:
    """Tab có chọn dùng vật phẩm thể lực (ALL / 100 / 200 ... 500); "No" hoặc giá trị lạ thì không."""
    return helper.use_stamina in STAMINA_CHOICES


def refill(bot, helper, confirm: tuple[int, int]) -> str:
    """Popup "You do not have enough Stamina. Get more now?" đang hiện (`confirm` = nút Confirm của nó): Confirm -> màn Use Item -> nút Use của vật phẩm đầu tiên
    -> popup số lượng (ALL: cuối thanh trượt; 200 ... 500: bấm + cho đủ) -> Use -> chờ game đóng popup -> Back. `helper` là `_Boss` của Join Monster War (dùng `use_stamina`,
    `_poll_screen`, `_add_stamina`). OK khi đã dùng xong và màn hình về lại màn March; EMPTY khi hết vật phẩm thể lực; FAILED khi màn không mở / popup không đóng (nơi gọi `ensure_map`)."""
    bot.tap(*confirm)
    _, buttons = helper._poll_screen("attack_stamina_items", lambda image: _item_use_buttons(bot, image),
                                     timeout=STAMINA_ITEMS_OPEN_WAIT, interval=STAMINA_ITEMS_OPEN_INTERVAL)
    if not buttons:
        bot.record("Attack Boss: hết vật phẩm thể lực")
        return EMPTY
    bot.tap(*buttons[0])

    shot, use = helper._poll_screen("attack_stamina_amount", lambda image: bot.find(STAMINA_USE, screen=image, region=REGIONS[STAMINA_USE]))
    if use is None:
        bot.back()
        return FAILED
    if helper.use_stamina == "ALL":
        bot.tap_percent(*STAMINA_SLIDER_END)
        delay(bot, POLL_INTERVAL)
    elif helper.use_stamina in STAMINA_MULTIPLES:
        helper._add_stamina(shot, int(helper.use_stamina))
    bot.tap(*use)
    bot.record(f"Attack Boss: dùng vật phẩm thể lực ({helper.use_stamina})")

    delay(bot, STAMINA_REFILL_WAIT)      # bấm Use xong game tự đóng popup
    bot.back()
    closed = False
    for round_ in range(STAMINA_CLOSE_ROUNDS):
        _, closed = helper._poll_screen(
            "attack_stamina_closed",
            lambda image: bot.find(STAMINA_USE, screen=image, region=REGIONS[STAMINA_USE]) is None and not _item_use_buttons(bot, image),
            timeout=STAMINA_CLOSE_WAIT, interval=1)
        if closed:
            break
        if round_ < STAMINA_CLOSE_ROUNDS - 1:
            bot.back()
    if not closed:
        bot.record("Attack Boss: màn dùng thể lực chưa đóng sau 20 s")
        return FAILED
    return OK
