"""Claim General Vault Daily Free (luật nhận riêng: claim_daily_free, xem FLOW.md)."""
from ...common import GiftTask, close_congratulations
from ...screens import GiftScreen
from ..named_flow import ExactFlow, STEP_DELAY, run_carousel_exact
from ..named_flow.run import find_any

KEY = "gift_general_vault"
BUTTONS = ("ValuableEvent/GeneralVault/button_daily_free_current",
           "ValuableEvent/GeneralVault/button_daily_free")
BUTTON_REGION = (0, 18, 100, 50)   # % màn: chỉ tìm nút Daily Free ở y 18-50%
BUTTON_THRESHOLD = 0.72
CONGRATS_WAITS = 5                 # sau khi bấm: chờ 1s rồi tìm Congratulations, tối đa chừng này lần
TAP_ROUNDS = 2                     # số lần bấm nút (bước 3) tối đa


def claim_daily_free(bot) -> bool:
    """Tìm nút Daily Free ở y 18-50%: không thấy = đã nhận, DONE. Thấy thì bấm vào giữa nút, cứ 1s tìm Congratulations, tối đa
    CONGRATS_WAITS lần; thấy thì đóng (Back), DONE. Không ra thì làm lại từ bước tìm nút, tối đa TAP_ROUNDS lần bấm; hết mà
    vẫn chưa có Congratulations thì PENDING (False)."""
    for attempt in range(1, TAP_ROUNDS + 1):
        bot.check()
        hit = find_any(bot, BUTTONS, region=BUTTON_REGION, threshold=BUTTON_THRESHOLD)
        if hit is None:
            bot.record("Gift Claims: General Vault không còn nút Daily Free; DONE")
            return True
        name, pos = hit
        bot.record(f"Gift Claims: General Vault bấm {name} tại {pos} (lần {attempt}/{TAP_ROUNDS})")
        bot.tap(*pos)
        for _ in range(CONGRATS_WAITS):
            bot.sleep(STEP_DELAY)
            if close_congratulations(bot, attempts=1):
                bot.record("Gift Claims: General Vault -> Congratulations; DONE")
                return True
        bot.record(f"Gift Claims: General Vault chưa thấy Congratulations sau {CONGRATS_WAITS}s "
                   f"(lần {attempt}/{TAP_ROUNDS})")
    return False


FLOW = ExactFlow(claims=BUTTONS, handler=claim_daily_free)


def run(bot):
    return run_carousel_exact(bot, GiftScreen.VALUABLE_EVENT,
                              "ValuableEvent/title", "ValuableEvent/GeneralVault/tab_icon", FLOW)


TASK = GiftTask(KEY, "General Vault", run)
