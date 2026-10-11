"""
gifts.py — nhận quà cuối ngày (gift claims) sau khi Daily Activities xong: phía worker quyết định quà nào đến hạn (chưa nhận
hôm nay), nhóm Valuable Event / Super Value Return, ghi "đã xử lý hôm nay" cho từng quà. Các bước làm trong game (mở sảnh,
từng quà, các nhóm quà) nằm ở bot/activities/gift_claims/.
"""
from ...activities import gift_claims
from ...activities.gift_claims import event_center, lobby, super_value_return, valuable_event
from ...activities.gift_claims.common import return_home
from ...activities.gift_claims.screens import GiftScreen


def run_gift_claims(ctx):
    """Run every due claim independently and remember each result for today."""
    tasks = gift_claims.TASKS
    task_keys = {task.key for task in tasks}
    group_keys = (valuable_event.KEYS | super_value_return.KEYS) & task_keys
    due_valuable = {key for key in valuable_event.KEYS & task_keys
                    if not ctx.is_daily_done(key)}
    due_super_value = {key for key in super_value_return.KEYS & task_keys
                       if not ctx.is_daily_done(key)}
    group_results = {key: "no_dot" for key in due_valuable | due_super_value}
    parent_clean = {
        GiftScreen.VALUABLE_EVENT: None,
        GiftScreen.SUPER_VALUE_RETURN: None,
    }

    # Lobby icons are intentionally unnamed and may change artwork. Open each
    # fixed slot, identify the fixed inner title, then dispatch that flow.
    opened_groups = set()
    # Finish every red dot in boundary 1 before moving to the potentially
    # longer right-hand boundary 2. Artwork and icon positions are irrelevant;
    # the opened fixed inner title decides which parent flow handles it.
    for boundary in lobby.BOUNDARIES:
        attempted = []
        for _ in range(lobby.MAX_OPENS_PER_BOUNDARY):
            screen_name = lobby.open_next(ctx, boundary, attempted)
            if screen_name is None:
                break
            if (screen_name == GiftScreen.VALUABLE_EVENT
                    and due_valuable
                    and screen_name not in opened_groups):
                states, clean = valuable_event.run_opened(ctx, due_valuable)
                group_results.update(states)
                parent_clean[screen_name] = clean
                if not clean:
                    ctx.log("Gift Claims: Valuable Event chưa được đánh dấu DONE")
                opened_groups.add(screen_name)
            elif (screen_name == GiftScreen.SUPER_VALUE_RETURN
                    and due_super_value
                    and screen_name not in opened_groups):
                states, clean = super_value_return.run_opened(ctx, due_super_value)
                group_results.update(states)
                parent_clean[screen_name] = clean
                if not clean:
                    ctx.log("Gift Claims: Super Value Return chưa được đánh dấu DONE")
                opened_groups.add(screen_name)
            elif (screen_name == GiftScreen.EVENT_CENTER
                  and not ctx.is_daily_done(event_center.KEY)):
                processed = event_center.run_opened(ctx)
                ctx.mark_daily_done(event_center.KEY)
                ctx.record("Gift Claims: Event Center Limited - "
                           + ("đã xử lý" if processed else "không có quà"))
            else:
                return_home(ctx)

    for task in tasks:
        if ctx.is_daily_done(task.key):
            continue
        if task.key in group_keys:
            parent = (GiftScreen.VALUABLE_EVENT
                      if task.key in valuable_event.KEYS
                      else GiftScreen.SUPER_VALUE_RETURN)
            if parent_clean[parent] is False:
                ctx.record(f"Gift Claims: {task.label} - giữ pending vì "
                           f"{parent.value} vẫn còn dấu đỏ")
                continue
            ctx.mark_daily_done(task.key)
            state = group_results.get(task.key, "no_dot")
            result = {
                "cleared": "đã xử lý và hết dấu đỏ",
                "remaining": "đã mở nhưng dấu đỏ vẫn còn",
                "claimed_remaining": "đã nhận, nhưng dấu đỏ vẫn còn",
                "processed": "đã kiểm tra/nhận quà ngày",
                "no_dot": "không có dấu đỏ",
            }[state]
            ctx.record(f"Gift Claims: {task.label} - {result}")
            continue
        ctx.check()
        ctx.record(f"Gift Claims: bắt đầu {task.label}")
        claimed = task.run(ctx)
        # A complete scan with no available/red-dot event is still today's result.
        ctx.mark_daily_done(task.key)
        result = "đã xử lý" if claimed else "không có quà"
        ctx.record(f"Gift Claims: {task.label} - {result}")
