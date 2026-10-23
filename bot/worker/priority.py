"""priority.py — bảng nhiệm vụ của worker: mỗi dòng có độ ưu tiên và `run` là việc thực hiện nhiệm vụ đó, import thẳng từ
bot/activities: một hàm trơn `run(ctx, cấu hình tab)`, hoặc một dict {run, enabled, done, every} do code của nhiệm vụ dựng sẵn. Dòng không có `run` (Bubble, Join Monster War, việc chưa làm) không vào danh sách nhiệm vụ."""
from ..activities.daily_activities.offering import TASK as daily_offering
from ..activities.daily_activities.offering.run import after_go as offering_after_go
from ..activities.daily_activities.resource_tax import TASK as daily_resource_tax
from ..activities.daily_activities.resource_tax.run import after_go as resource_tax_after_go
from ..activities.daily_activities.gold_levy import TASK as daily_gold_levy
from ..activities.daily_activities.gold_levy.run import after_go as gold_levy_after_go
from ..activities.daily_activities.troop_training import TASK as daily_troop_training
from ..activities.daily_activities.troop_healing import TASK as daily_troop_heading
from ..activities.daily_activities.troop_healing.run import after_go as troop_healing_after_go
from ..activities.daily_activities.troop_training.run import after_go as troop_training_after_go
from ..activities.daily_activities.trap_building import TASK as daily_trap_buiding
from ..activities.daily_activities.trap_building.run import after_go as trap_building_after_go
from ..activities.daily_activities.black_market import TASK as daily_black_market
from ..activities.daily_activities.black_market.run import after_go as black_market_after_go
from ..activities.daily_activities.general_enhancing import TASK as daily_general_enhancing
from ..activities.daily_activities.general_enhancing.run import after_go as general_enhancing_after_go
from ..activities.daily_activities.wheel_of_fortune import TASK as daily_wheel_of_fortune
from ..activities.daily_activities.wheel_of_fortune.run import after_go as wheel_of_fortune_after_go
from ..activities.daily_activities.patrol import TASK as daily_patrol
from ..activities.daily_activities.patrol.run import MORE_JOB as daily_patrol_more_job
from ..activities.daily_activities.patrol.run import after_go as patrol_after_go
from ..activities.daily_activities.material_composing import TASK as daily_material_composing
from ..activities.daily_activities.material_composing import after_go as material_composing_after_go
from ..activities.daily_activities.alliance_research import TASK as daily_alliance_research
from ..activities.daily_activities.alliance_research.run import after_go as alliance_research_after_go
from ..activities.daily_activities.greet_champion import TASK as daily_greet_champion
from ..activities.daily_activities.greet_champion.run import MORE_JOB as daily_greet_champion_more_job
from ..activities.daily_activities.greet_champion.run import after_go as greet_champion_after_go
from ..activities.daily_activities.ranger_knight import TASK as daily_ranger_knight
from ..activities.daily_activities.ranger_knight.run import after_go as ranger_knight_after_go
from ..activities.daily_activities.trade_carriage import TASK as daily_trade_carriage
from ..activities.daily_activities.trade_carriage.run import after_go as trade_carriage_after_go
from ..activities.event.gather_troops.cultivate_generals.run import run as gather_troops_cultivate_generals
from ..activities.event.gather_troops.ground_troop.run import run as gather_troops_ground_troop
from ..activities.event.gather_troops.mounted_troop.run import run as gather_troops_mounted_troop
from ..activities.event.gather_troops.ranged_troop.run import run as gather_troops_ranged_troop
from ..activities.event.gather_troops.siege_machine.run import run as gather_troops_siege_machine
from ..activities.event.gather_troops.trap_factory.run import run as gather_troops_trap_factory
from ..activities.event.kings_path.city_tax.run import run as kings_path_city_tax
from ..activities.event.kings_path.patrol.run import run as kings_path_patrol
from ..activities.event.kings_path.donate.run import run as kings_path_donate
from ..activities.event.kings_path.train_troop.run import run as kings_path_train_troop
from ..activities.event.kings_path.heal.run import run as kings_path_heal
from ..activities.event.kings_path.wheel.run import run as kings_path_wheel
from ..activities.event.kings_path.refine.run import run as kings_path_refine
from ..activities.event.kings_path.black_market.run import run as kings_path_black_market
from ..activities.alliance_capacity.run import run as alliance_capacity
from ..activities.black_market.run import run as black_market_market
from ..activities.daily_activities.alliance_donation import TASK as alliance_donation_task
from ..activities.daily_activities.alliance_donation.run import donate_free
from ..activities.daily_activities.alliance_help import TASK as alliance_help_task
from ..activities.daily_activities.alliance_help.run import help_all
from ..activities.daily_activities.buy_daily.run import JOB as daily_buy_general
from ..activities.daily_activities.alliance_vip import JOB as daily_alliance_vip
from ..activities.daily_activities.city_vip import JOB as daily_city_vip
from ..activities.daily_activities.alliance_donation import constants as alliance_donation_constants
from ..activities.daily_activities.alliance_help import constants as alliance_help_constants
from ..activities.daily_activities.common import REWARDS_JOB as daily_rewards
from ..activities.daily_activities.common import daily_job, hourly_job
from ..activities.event.run import claim_job, event_job
from ..activities.event_center.crazy_eggs.run import JOB as crazy_eggs
from ..activities.event_center.three_day.run import JOB as three_day_event
from ..activities.open_gift_box.run import run as open_gift_box
from ..activities.find_boss import JOB as find_boss_job
from ..activities.craft import JOB as craft_job
from ..activities.gather_resources import JOB as gather_resources_job
from ..activities import gift_claims, join_monster_war

DATA ={
    "_doc": "Độ ưu tiên của từng nhiệm vụ cho bộ chọn nhiệm vụ của worker.",
    "Bubble": [
        {
            "key": "bubble", 
            "label": "Bubble (giữ khiên)", 
            "priority": 99999,
            "note": "Luật riêng: luôn cao nhất, tới hạn khi còn <= 2 giờ, ngắt được mọi nhiệm vụ kể cả Join Boss" 
        }
    ],
    "Join Monster War": [
        { 
            "key": "join_monster_war",
            "handler": join_monster_war.run,
            "label": "Join Monster War",
            "priority": 9999,
}
    ],
    "Crazy Eggs": [
        { 
            "key": "crazy_eggs",
            "run": crazy_eggs,
            "label": "Crazy Eggs",
            "priority": 999,
            "group": "Daily Activities"
}
    ],
    "Open Gift Box": [
        { 
            "key": "open_gift_box",
            "run": open_gift_box,
            "saves": True,
            "label": "Open Gift Box",
            "priority": 888,
        }
    ],
    "Alliance Capacity": [
        { 
            "key": "alliance_capacity",
            "needs_alliance": True,
            "run": alliance_capacity,
            "label": "Alliance Capacity: donate Alliance Science",
            "priority": 777,
            "once": True,   # chỉ làm 1 lần (mỗi lần Start): xong thì không lưu gì vào DB, không làm lại khi sang ngày mới
    }
    ],
    "Event": [
        { 
            "key": "gather_troops_cultivate_generals",
            "run": event_job("gather_troops", gather_troops_cultivate_generals),
            "label": "Gather Troops: Cultivate Generals",
            "priority": 600,
        },
        { 
            "key": "gather_troops_ground_troop",
            "run": event_job("gather_troops", gather_troops_ground_troop),
            "label": "Gather Troops: Ground Troop",
            "priority": 552,
        },
        { 
            "key": "gather_troops_mounted_troop",
            "run": event_job("gather_troops", gather_troops_mounted_troop),
            "label": "Gather Troops: Mounted Troop",
            "priority": 551,
        },
        { 
            "key": "gather_troops_ranged_troop",
            "run": event_job("gather_troops", gather_troops_ranged_troop),
            "label": "Gather Troops: Ranged Troop",
            "priority": 550,
        },
        { 
            "key": "gather_troops_siege_machine",
            "run": event_job("gather_troops", gather_troops_siege_machine),
            "label": "Gather Troops: Siege Machine",
            "priority": 549,
        },
        { 
            "key": "gather_troops_trap_factory",
            "run": event_job("gather_troops", gather_troops_trap_factory),
            "label": "Gather Troops: Trap Factory",
            "priority": 548, 
        },
        { 
            "key": "kings_path_wheel",
            "run": event_job("kings_path", kings_path_wheel),
            "label": "King's Path: Wheel",
            "priority": 559,
        },
        { 
            "key": "kings_path_black_market",
            "run": event_job("kings_path", kings_path_black_market),
            "label": "King's Path: Black Market",
            "priority": 558,
        },
        { 
            "key": "kings_path_patrol",
            "run": event_job("kings_path", kings_path_patrol),
            "label": "King's Path: Patrol",
            "priority": 557, "note": "Yêu cầu phải cao hơn King's Path: Donate",
        },
        { 
            "key": "kings_path_donate",
            "run": event_job("kings_path", kings_path_donate),
            "label": "King's Path: Donate",
            "priority": 556,
        },
        { 
            "key": "kings_path_city_tax",
            "run": event_job("kings_path", kings_path_city_tax),
            "label": "King's Path: City Tax",
            "priority": 554,
        },
        { 
            "key": "kings_path_train_troop",
            "run": event_job("kings_path", kings_path_train_troop),
            "label": "King's Path: Train Troop",
            "priority": 553,
        },
        { 
            "key": "kings_path_heal",
            "run": event_job("kings_path", kings_path_heal),
            "label": "King's Path: Heal",
            "priority": 547,
        },
        { 
            "key": "kings_path_refine",
            "run": event_job("kings_path", kings_path_refine),
            "label": "King's Path: Refine Equipment",
            "priority": 546,
        },
        { 
            "key": "gather_troops_claim",
            "run": claim_job("gather_troops"),
            "label": "Gather Troops: nhận thưởng (chấm đỏ + rương mốc)",
            "priority": 500,
        },
        { 
            "key": "kings_path_claim",
            "run": claim_job("kings_path"),
            "label": "King's Path: nhận thưởng (chấm đỏ)",
            "priority": 499,
        },
        { 
            "key": "three_day_event",
            "run": three_day_event,
            "label": "Event 3 ngày (Event Center)",
            "priority": 498,
        }
    ],
    "Daily Activities": [
        { 
            "key": "daily_buy_general",
            "run": daily_buy_general,
            "label": "General: Buy Stamina + Hammers",
            "priority": 668,
        },
        { 
            "key": "daily_offering",
            "run": daily_job(daily_offering, target="Offer Gems", after_go=offering_after_go),
            "label": "Offering",
            "priority": 398,
        },
        { 
            "key": "daily_resource_tax",
            "run": daily_job(daily_resource_tax, after_go=resource_tax_after_go),
            "must_finish": True,
            "label": "Resource Tax",
            "priority": 397,
        },
        { 
            "key": "daily_gold_levy",
            "run": daily_job(daily_gold_levy, after_go=gold_levy_after_go),
            "label": "Gold Levy",
            "priority": 396,
        },
        { 
            "key": "daily_troop_training",
            "run": daily_job(daily_troop_training, after_go=troop_training_after_go),
            "label": "Troop Training",
            "priority": 395,
        },
        { 
            "key": "daily_troop_heading",
            "run": daily_job(daily_troop_heading, after_go=troop_healing_after_go),
            "label": "Troop Heading",
            "priority": 394,
        },
        { 
            "key": "daily_trap_buiding",
            "run": daily_job(daily_trap_buiding, after_go=trap_building_after_go),
            "label": "Trap Buiding",
            "priority": 393,
        },
        { 
            "key": "daily_alliance_donation",
            "needs_alliance": True,
            "run": hourly_job(alliance_donation_task, donate_free, alliance_donation_constants),
            "must_finish": True,
            "label": "Alliance Donation",
            "priority": 391, 
            "note": "Theo giờ (ô chọn 0-4h); đứng sau Alliance Help như thứ tự game; tới giờ thì worker đẩy lên đầu danh sách",
        },
        { 
            "key": "daily_alliance_help",
            "needs_alliance": True,
            "run": hourly_job(alliance_help_task, help_all, alliance_help_constants),
            "must_finish": True,
            "label": "Alliance Help",
            "priority": 392, 
            "note": "Như Alliance Donation (theo giờ, ô chọn 0-4h, mặc định 4h), đứng ngay trước Alliance Donation như thứ tự game",
        },
        { 
            "key": "daily_alliance_research",
            "run": daily_job(daily_alliance_research, after_go=alliance_research_after_go),
            "label": "Research",
            "priority": 399,
            "note": "Học viện: nghiên cứu 1 công nghệ xanh bất kỳ, tốn thời gian thì Speed Up bằng vật phẩm",
        },
        { 
            "key": "daily_city_vip",
            "run": daily_city_vip,
            "label": "City VIP",
            "priority": 650,   # cao nhất trong Event (cao nhất 600) và Daily Activities
            "note": "Nhận VIP ở thành: không có ô tích, chỉ 0h-1h giờ máy tính và khi đã có route công trình trong DB (flow nhận chưa viết)",
        },
        { 
            "key": "daily_alliance_vip",
            "needs_alliance": True,
            "run": daily_alliance_vip,
            "label": "Alliance VIP",
            "priority": 390,
            "note": "Alliance Shop: mua VIP Monthly rồi Daily (nút xám = coi như đã mua)",
        },
        { 
            "key": "daily_black_market",
            "run": daily_job(daily_black_market, after_go=black_market_after_go),
            "label": "Black Market",
            "priority": 389,
        },
        { 
            "key": "daily_general_enhancing",
            "run": daily_job(daily_general_enhancing, after_go=general_enhancing_after_go),
            "label": "General Enhancing",
            "priority": 388, 
            "note": "Cần làm thêm",
        },
        { 
            "key": "daily_wheel_of_fortune",
            "run": daily_job(daily_wheel_of_fortune, after_go=wheel_of_fortune_after_go),
            "label": "Wheel of Fortune",
            "priority": 387,
        },
        { 
            "key": "daily_patrol",
            "run": daily_job(daily_patrol, after_go=patrol_after_go),
            "label": "Patrol",
            "priority": 386, 
        },
        {
            "key": "daily_patrol_more",
            "run": daily_patrol_more_job,
            "label": "Patrol (more rounds)",
            "priority": 386,
            "note": "Sau khi Daily Patrol xong (đủ 1 lượt): tìm thành -> Tường thành -> patrol tiếp tới đủ 10 lượt, không đi qua Go",
        },
        { 
            "key": "daily_material_composing",
            "run": daily_job(daily_material_composing, after_go=material_composing_after_go),
            "label": "Material Composing",
            "priority": 385,
        },
        { 
            "key": "daily_greet_champion",
            "run": daily_job(daily_greet_champion, after_go=greet_champion_after_go),
            "label": "Greet Champion",
            "priority": 384, 
            "note": "Về thành: bấm trái tim trên Keep (hoặc Keep -> Champion), chào 2 lần",
        },
        {
            "key": "daily_greet_champion_more",
            "run": daily_greet_champion_more_job,
            "label": "Greet Champion (more)",
            "priority": 384,
            "note": "Sau khi Daily Greet xong (đủ 2 lần): tìm thành -> trái tim / Keep -> Champion, chào tiếp tới 10/10, không đi qua Go",
        },
        {
            "key": "daily_ranger_knight",
            "run": daily_job(daily_ranger_knight, after_go=ranger_knight_after_go),
            "label": "Ranger Knight",
            "priority": 383,
            "must_finish": True,
        },
        {
            "key": "daily_trade_carriage",
            "run": daily_job(daily_trade_carriage, after_go=trade_carriage_after_go),
            "must_finish": True,
            "label": "Trade Carriage",
            "priority": 301,
            "note": "Nhiệm vụ cuối cùng trước nhận thưởng Activity",
        },
        {
            "key": "daily_rewards",
            "run": daily_rewards,
            "label": "Activity Rewards (nhận thưởng cuối)",
            "priority": 300,
            "tail": True,
        },
    ],
    "Find Boss": [
        {
            "key": "find_boss",
            "run": find_boss_job,
            "label": "Find Boss: quét bản đồ thế giới tìm boss",
            "priority": 700,
            "idle_only": True,   # chỉ làm khi không còn nhiệm vụ nào khác
            "note": "CHỈ khi rảnh (hết mọi nhiệm vụ khác): quét xong thì về toạ độ của mình rồi quét tiếp; chia sẻ boss đang tích vào liên minh",
        }
    ],
    "Craft": [
        {
            "key": "craft",
            "run": craft_job,
            "label": "Craft: chế tạo trang bị",
            "priority": 669,   # cao hơn mọi nhiệm vụ Daily Activities (cao nhất 668): Craft làm trước Daily
            "once": True,    # chỉ làm 1 lần (mỗi lần Start): xong thì không làm lại khi sang ngày mới
            "note": "Chế tạo các trang bị đã tích ở tab Craft; một lần duy nhất, ưu tiên cao hơn Daily Activities",
            "needs_city_map": True,   # nhiệm vụ cần route: chỉ vào danh sách khi máy đã có bản đồ thành (worker quét lúc Join Boss rảnh)
        }
    ],
    "Gather Resources": [
        {
            "key": "gather_resources",
            "run": gather_resources_job,
            "label": "Gather Resources: gửi đội đi thu thập",
            "priority": 701,     # trong các việc `idle_only`: trước Find Boss (700), chỉ khi có đội đã về
            "idle_only": True,   # cuối cùng: chỉ làm khi hết mọi nhiệm vụ khác
            "note": "Cuối cùng (chỉ khi rảnh), theo giờ: tới lượt khi có đội đã về (giờ đội về lưu trong DB, đọc từ màn March); hết lính thì chờ 30 phút",
        }
    ],
    "Black Market": [
        {
            "key": "black_market_market",
            "run": black_market_market,
            "label": "Black Market: mua ở Market",
            "priority": 10,
            "once": True,
            "needs_city_map": True,   # nhiệm vụ cần route: chỉ vào danh sách khi máy đã có bản đồ thành (worker quét lúc Join Boss rảnh)
        }
    ],
    # Nhận quà event: chạy sau các Daily Activities; Event Center luôn đứng
    # trước hai khu quà ngoài thành. Thuộc nhóm Daily Activities: ô tích
    # "Claim Event Gifts" ở tab đó (settings["General"]["gift_claims"]).
    "Gift Claims": [
        {
            "key": gift_claims.valuable_event.KEY,
            "group": "Daily Activities",
            "run": gift_claims.job(gift_claims.valuable_event),
            "label": "Gift Claims: Valuable Event",
            "priority": 2,
            "tail": True,
        },
        {
            "key": gift_claims.super_value_return.KEY,
            "group": "Daily Activities",
            "run": gift_claims.job(gift_claims.super_value_return),
            "label": "Gift Claims: Super Value Return",
            "priority": 1,
            "tail": True,
        },
        {
            "key": gift_claims.event_center.KEY,
            "group": "Daily Activities",
            "run": gift_claims.job(gift_claims.event_center),
            "label": "Gift Claims: Event Center",
            "priority": 3,
            "tail": True,
        },
    ],
}
