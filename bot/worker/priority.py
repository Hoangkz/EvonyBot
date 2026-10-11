"""priority.py — bảng nhiệm vụ của worker (dữ liệu tĩnh): độ ưu tiên và luật chạy của từng nhiệm vụ.

DATA: {nhóm (tên activity): [{key, label, priority, note?, must_finish?, policy?, ...}]}. `policy` chọn luật chạy ở
policies.py (BUILDERS); registry.py dựng TaskDef từ mọi dòng có `policy`. Tham số khác của dòng: `event` (policy event /
event_claim: event nào), `run` (policy plain: hàm nào ở policies.PLAIN), `group` (nhóm chọn nhiệm vụ, nếu khác nhóm chứa
dòng), `once`, `repeat`. Dòng không có `policy` (Bubble, Join Monster War, gift_*, việc chưa làm) không vào bộ chọn. `_doc` giữ
ghi chú luật riêng (Bubble, Join Boss, gift_*). Số lớn hơn làm trước. Trước đây là file
.json cùng tên; đổi sang .py để Nuitka compile cùng code, không cần ship file riêng lúc
build.
"""
DATA ={
    "_doc": "Độ ưu tiên của từng nhiệm vụ cho bộ chọn nhiệm vụ của worker (chưa dùng). Nhóm = activity (nút Select Activity / tab UI). key = key nhiệm vụ trong settings / daily_done. Ưu tiên cao hơn làm trước; cùng ưu tiên thì xoay vòng. Mặc định 1. Bubble và Join Boss cũng là nhiệm vụ nhưng có luật riêng (bot/worker/TODO.md mục 1): bubble luôn cao nhất, Join Boss chạy giữa mỗi 2 nhiệm vụ thường. Các key gift_* có ưu tiên -100 thấp nhất và hiện được Daily Activities gọi sau khi mọi nhiệm vụ đã chọn cùng Activity Rewards hoàn tất. Thêm \"must_finish\": true vào nhiệm vụ cần làm tới xong: đã bắt đầu thì không bị Bubble / Join Boss / giới hạn 120 giây ngắt (chỉ Stop), xong rồi mới tới Bubble và Join Boss; khi cả activity còn chạy nguyên khối thì mọi nhiệm vụ của nhóm phải có cờ này.",
    "Bubble": [
        { "key": "bubble", "label": "Bubble (giữ khiên)", "priority": 99999, "note": "Luật riêng: luôn cao nhất, tới hạn khi còn <= 2 giờ, ngắt được mọi nhiệm vụ kể cả Join Boss" }
    ],
    "Join Monster War": [
        { "key": "join_monster_war", "label": "Join Monster War", "priority": 9999 }
    ],
    "Crazy Eggs": [
        { "key": "crazy_eggs", "label": "Crazy Eggs", "priority": 999, "policy": "crazy_eggs", "group": "Daily Activities", "repeat": True }
    ],
    "Open Gift Box": [
        { "key": "open_gift_box", "label": "Open Gift Box", "priority": 888, "policy": "open_gift_box" }
    ],
    "Alliance Capacity": [
        { "key": "alliance_capacity", "label": "Alliance Capacity: donate Alliance Science", "priority": 777, "policy": "plain", "run": "alliance_capacity" }
    ],
    "Event": [
        { "key": "gather_troops_cultivate_generals", "label": "Gather Troops: Cultivate Generals", "priority": 600, "policy": "event", "event": "gather_troops" },
        { "key": "gather_troops_ground_troop", "label": "Gather Troops: Ground Troop", "priority": 552, "policy": "event", "event": "gather_troops" },
        { "key": "gather_troops_mounted_troop", "label": "Gather Troops: Mounted Troop", "priority": 551, "policy": "event", "event": "gather_troops" },
        { "key": "gather_troops_ranged_troop", "label": "Gather Troops: Ranged Troop", "priority": 550, "policy": "event", "event": "gather_troops" },
        { "key": "gather_troops_siege_machine", "label": "Gather Troops: Siege Machine", "priority": 549, "policy": "event", "event": "gather_troops" },
        { "key": "gather_troops_defense_force", "label": "Gather Troops: Defense Force", "priority": 548, "policy": "event", "event": "gather_troops" },
        { "key": "kings_path_wheel", "label": "King's Path: Wheel", "priority": 559, "policy": "event", "event": "kings_path" },
        { "key": "kings_path_black_market", "label": "King's Path: Black Market", "priority": 558, "policy": "event", "event": "kings_path" },
        { "key": "kings_path_patrol", "label": "King's Path: Patrol", "priority": 557, "note": "Yêu cầu phải cao hơn King's Path: Donate", "policy": "event", "event": "kings_path" },
        { "key": "kings_path_donate", "label": "King's Path: Donate", "priority": 556, "policy": "event", "event": "kings_path" },
        { "key": "kings_path_city_tax", "label": "King's Path: City Tax", "priority": 554, "policy": "event", "event": "kings_path" },
        { "key": "kings_path_train_troop", "label": "King's Path: Train Troop", "priority": 553, "policy": "event", "event": "kings_path" },
        { "key": "kings_path_heal", "label": "King's Path: Heal", "priority": 547, "policy": "event", "event": "kings_path" },
        { "key": "kings_path_refine", "label": "King's Path: Refine Equipment", "priority": 546, "policy": "event", "event": "kings_path" },
        { "key": "gather_troops_claim", "label": "Gather Troops: nhận thưởng (chấm đỏ + rương mốc)", "priority": 500, "policy": "event_claim", "event": "gather_troops" },
        { "key": "kings_path_claim", "label": "King's Path: nhận thưởng (chấm đỏ)", "priority": 499, "policy": "event_claim", "event": "kings_path" },
        { "key": "three_day_event", "label": "Event 3 ngày (Event Center)", "priority": 498, "policy": "three_day" }
    ],
    "Daily Activities": [
        { "key": "daily_buy_general", "label": "General: Buy Stamina + Hammers", "priority": 668, "policy": "buy_general" },
        { "key": "daily_offering", "label": "Offering", "priority": 666, "policy": "daily" },
        { "key": "daily_resource_gathering", "label": "Resource Gathering", "priority": 665, "note": "Phải chạy ngay sau Offering (bàn tay nổi trong thành)", "policy": "daily" },
        { "key": "daily_resource_tax", "label": "Resource Tax", "priority": 399, "policy": "daily" },
        { "key": "daily_gold_levy", "label": "Gold Levy", "priority": 398, "policy": "daily" },
        { "key": "daily_troop_training", "label": "Troop Training", "priority": 397, "policy": "daily" },
        { "key": "daily_troop_heading", "label": "Troop Heading", "priority": 396, "policy": "daily" },
        { "key": "daily_trap_buiding", "label": "Trap Buiding", "priority": 395, "policy": "daily" },
        { "key": "daily_alliance_donation", "label": "Alliance Donation", "priority": 394, "note": "Chạy cuối Daily theo giờ (ô chọn 0-4h); chưa xong thì Daily Activities hẹn chạy lại (ctx.again_after, AGAIN_PRIORITY thấp nhất)", "policy": "hourly" },
        { "key": "daily_alliance_help", "label": "Alliance Help", "priority": 393, "note": "Như Alliance Donation (theo giờ, ô chọn 0-4h, mặc định 4h), chạy ngay sau Alliance Donation", "policy": "hourly" },
        { "key": "daily_alliance_science", "label": "Alliance Science", "priority": 393 },
        { "key": "daily_alliance_research", "label": "Alliance Research", "priority": 392 },
        { "key": "daily_alliance_technology", "label": "Alliance Technology", "priority": 391 },
        { "key": "daily_black_market", "label": "Black Market", "priority": 390, "policy": "daily" },
        { "key": "daily_general_enhancing", "label": "General Enhancing", "priority": 389, "note": "Cần làm thêm", "policy": "daily" },
        { "key": "daily_wheel_of_fortune", "label": "Wheel of Fortune", "priority": 388, "policy": "daily" },
        { "key": "daily_patrol", "label": "Patrol", "priority": 387, "must_finish": True, "policy": "daily" },
        { "key": "daily_material_composing", "label": "Material Composing", "priority": 386, "policy": "daily" },
        { "key": "daily_greet_champion", "label": "Greet Champion", "priority": 385, "must_finish": True },
        { "key": "daily_monster_killing", "label": "Monster Killing", "priority": 384, "policy": "daily" },
        { "key": "daily_resource_collecting", "label": "Resource Collecting", "priority": 383, "policy": "daily" },
        { "key": "daily_rewards", "label": "Activity Rewards (nhận thưởng cuối)", "priority": 300, "policy": "rewards" },
        { "key": "gift_dragon_battle", "label": "Nhận quà: Dragon Battle", "priority": -100 },
        { "key": "gift_grace_of_star_trail", "label": "Nhận quà: Grace of Star Trail", "priority": -100 },
        { "key": "gift_limited_offer", "label": "Nhận quà: Limited Offer", "priority": -100 },
        { "key": "gift_speedup_sprint", "label": "Nhận quà: Speedup Sprint", "priority": -100 },
        { "key": "gift_super_blazon_sale", "label": "Nhận quà: Super Blazon Sale", "priority": -100 },
        { "key": "gift_sulis_wishing", "label": "Nhận quà: Sulis Wishing Pool", "priority": -100 },
        { "key": "gift_super_value_weekly_card", "label": "Nhận quà: Super Value Weekly Card", "priority": -100 },
        { "key": "gift_successive_purchase_benefits", "label": "Nhận quà: Successive Purchase Benefits", "priority": -100 },
        { "key": "gift_login_gifts", "label": "Nhận quà: Login Gifts", "priority": -100 },
        { "key": "gift_empire_depot", "label": "Nhận quà: Empire Depot", "priority": -100 },
        { "key": "gift_lucky_raffle", "label": "Nhận quà: Lucky Raffle", "priority": -100 },
        { "key": "gift_city_growth_plan", "label": "Nhận quà: City Growth Plan Stage 1", "priority": -100 },
        { "key": "gift_event_center_limited", "label": "Nhận quà: Event Center Limited (bỏ Invite Friends/Facebook và Activities)", "priority": -100 }
    ],
    "Black Market": [
        { "key": "black_market_market", "label": "Black Market: mua ở Market", "priority": 0, "policy": "plain", "run": "black_market", "once": True }
    ],
    "Battlefield Shop": [
        { "key": "battlefield_shop", "label": "Battlefield Shop", "priority": -1, "policy": "plain", "run": "battlefield_shop" }
    ]
}