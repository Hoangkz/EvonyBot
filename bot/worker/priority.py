"""priority.py — bảng nhiệm vụ của worker: mỗi dòng có độ ưu tiên và `run` là việc thực hiện nhiệm vụ đó, import thẳng từ
bot/activities: một hàm trơn `run(ctx, cấu hình tab)`, hoặc một dict {run, enabled, done, every} do code của nhiệm vụ dựng sẵn. Dòng không có `run` (Bubble, Join Monster War, việc chưa làm) không vào danh sách nhiệm vụ."""
from ..activities.daily_activities.monster_killing import TASK as daily_monster_killing
from ..activities.daily_activities.resource_collecting import TASK as daily_resource_collecting
from ..activities.daily_activities.offering import TASK as daily_offering
from ..activities.daily_activities.resource_gathering import TASK as daily_resource_gathering
from ..activities.daily_activities.resource_tax import TASK as daily_resource_tax
from ..activities.daily_activities.gold_levy import TASK as daily_gold_levy
from ..activities.daily_activities.troop_training import TASK as daily_troop_training
from ..activities.daily_activities.troop_healing import TASK as daily_troop_heading
from ..activities.daily_activities.troop_healing.run import after_go as troop_healing_after_go
from ..activities.daily_activities.troop_training.run import after_go as troop_training_after_go
from ..activities.daily_activities.trap_building import TASK as daily_trap_buiding
from ..activities.daily_activities.trap_building.run import after_go as trap_building_after_go
from ..activities.daily_activities.black_market import TASK as daily_black_market
from ..activities.daily_activities.general_enhancing import TASK as daily_general_enhancing
from ..activities.daily_activities.wheel_of_fortune import TASK as daily_wheel_of_fortune
from ..activities.daily_activities.patrol import TASK as daily_patrol
from ..activities.daily_activities.material_composing import TASK as daily_material_composing
from ..activities.daily_activities.research_technologies import TASK as daily_research_technologies
from ..activities.daily_activities.research_technologies.run import after_go as research_technologies_after_go
from ..activities.daily_activities.greet_champion import TASK as daily_greet_champion
from ..activities.daily_activities.greet_champion.run import after_go as greet_champion_after_go
from ..activities.daily_activities.trade_carriage import TASK as daily_trade_carriage
from ..activities.daily_activities.trade_carriage.run import after_go as trade_carriage_after_go
from ..activities.event.gather_troops.cultivate_generals.run import run as gather_troops_cultivate_generals
from ..activities.event.gather_troops.ground_troop.run import run as gather_troops_ground_troop
from ..activities.event.gather_troops.mounted_troop.run import run as gather_troops_mounted_troop
from ..activities.event.gather_troops.ranged_troop.run import run as gather_troops_ranged_troop
from ..activities.event.gather_troops.siege_machine.run import run as gather_troops_siege_machine
from ..activities.event.gather_troops.defense_force.run import run as gather_troops_defense_force
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
from ..activities.battlefield_shop.run import run as battlefield_shop
from ..activities.daily_activities.alliance_donation import TASK as alliance_donation_task
from ..activities.daily_activities.alliance_donation.run import donate_free
from ..activities.daily_activities.alliance_help import TASK as alliance_help_task
from ..activities.daily_activities.alliance_help.run import help_all
from ..activities.daily_activities.buy_daily.run import JOB as daily_buy_general
from ..activities.daily_activities.alliance_donation import constants as alliance_donation_constants
from ..activities.daily_activities.alliance_help import constants as alliance_help_constants
from ..activities.daily_activities.common import GIFTS_JOB as daily_gift_claims
from ..activities.daily_activities.common import REWARDS_JOB as daily_rewards
from ..activities.daily_activities.common import daily_job, hourly_job
from ..activities.event.run import claim_job, event_job
from ..activities.event_center.crazy_eggs.run import JOB as crazy_eggs
from ..activities.event_center.three_day.run import JOB as three_day_event
from ..activities.open_gift_box.run import run as open_gift_box
from ..activities import join_monster_war

DATA ={
    "_doc": "Độ ưu tiên của từng nhiệm vụ cho bộ chọn nhiệm vụ của worker (chưa dùng). Nhóm = activity (nút Select Activity / tab UI). key = key nhiệm vụ trong settings / daily_done. Ưu tiên cao hơn làm trước; cùng ưu tiên thì xoay vòng. Mặc định 1. Bubble và Join Boss cũng là nhiệm vụ nhưng có luật riêng (bot/worker/TODO.md mục 1): bubble luôn cao nhất, Join Boss chạy giữa mỗi 2 nhiệm vụ thường. Các key gift_* (bot/activities/gift_claims) không có dòng ở đây: Daily Activities gọi chúng sau khi mọi nhiệm vụ đã chọn cùng Activity Rewards hoàn tất. Mọi nhiệm vụ của nhóm Daily Activities (có run) đều must_finish: làm tới xong rồi mới tới nhiệm vụ khác, không giới hạn 120 giây, không bị Bubble / Auto Times Out / Join Boss ngắt. Thêm \"must_finish\": true vào nhiệm vụ cần làm tới xong: đã bắt đầu thì không bị Bubble / Join Boss / giới hạn 120 giây ngắt (chỉ Stop), xong rồi mới tới Bubble và Join Boss; khi cả activity còn chạy nguyên khối thì mọi nhiệm vụ của nhóm phải có cờ này.",
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
            "key": "gather_troops_defense_force",
            "run": event_job("gather_troops", gather_troops_defense_force),
            "label": "Gather Troops: Defense Force",
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
            "must_finish": True,
            "label": "General: Buy Stamina + Hammers",
            "priority": 668,
},
        { 
            "key": "daily_offering",
            "run": daily_job(daily_offering, target="Offer Gems"),
            "must_finish": True,   # xong khi số lần đã offer trong DB >= số ở ô "Offer Gems" của tab
            "label": "Offering",
            "priority": 666,

        },
        { 
            "key": "daily_resource_gathering",
            "run": daily_job(daily_resource_gathering),
            "must_finish": True,
            "label": "Resource Gathering",
            "priority": 665, "note": "Phải chạy ngay sau Offering (bàn tay nổi trong thành)",

        },
        { 
            "key": "daily_resource_tax",
            "run": daily_job(daily_resource_tax),
            "must_finish": True,
            "label": "Resource Tax",
            "priority": 399,

        },
        { 
            "key": "daily_gold_levy",
            "run": daily_job(daily_gold_levy),
            "must_finish": True,
            "label": "Gold Levy",
            "priority": 398,

        },
        { 
            "key": "daily_troop_training",
            "run": daily_job(daily_troop_training, after_go=troop_training_after_go),
            "must_finish": True,
            "label": "Troop Training",
            "priority": 397,

        },
        { 
            "key": "daily_troop_heading",
            "run": daily_job(daily_troop_heading, after_go=troop_healing_after_go),
            "must_finish": True,
            "label": "Troop Heading",
            "priority": 396,

        },
        { 
            "key": "daily_trap_buiding",
            "run": daily_job(daily_trap_buiding, after_go=trap_building_after_go),
            "must_finish": True,
            "label": "Trap Buiding",
            "priority": 395,

        },
        { 
            "key": "daily_alliance_donation",
            "run": hourly_job(alliance_donation_task, donate_free, alliance_donation_constants),
            "must_finish": True,
            "label": "Alliance Donation",
            "priority": 394, 
            "note": "Chạy cuối Daily theo giờ (ô chọn 0-4h); tới giờ thì worker đẩy lên đầu danh sách",

        },
        { 
            "key": "daily_alliance_help",
            "run": hourly_job(alliance_help_task, help_all, alliance_help_constants),
            "must_finish": True,
            "label": "Alliance Help",
            "priority": 393, 
            "note": "Như Alliance Donation (theo giờ, ô chọn 0-4h, mặc định 4h), chạy ngay sau Alliance Donation",

        },
        { 
            "key": "daily_alliance_research",
            "label": "Alliance Research",
            "priority": -392 
        },
        { 
            "key": "daily_alliance_technology",
            "label": "Alliance Technology",
            "priority": -391 
        },
        { 
            "key": "daily_black_market",
            "run": daily_job(daily_black_market),
            "must_finish": True,
            "label": "Black Market",
            "priority": 390,

        },
        { 
            "key": "daily_general_enhancing",
            "run": daily_job(daily_general_enhancing),
            "must_finish": True,
            "label": "General Enhancing",
            "priority": 389, 
            "note": "Cần làm thêm",

        },
        { 
            "key": "daily_wheel_of_fortune",
            "run": daily_job(daily_wheel_of_fortune),
            "must_finish": True,
            "label": "Wheel of Fortune",
            "priority": 388,

        },
        { 
            "key": "daily_patrol",
            "run": daily_job(daily_patrol),
            "label": "Patrol",
            "priority": 387, 
            "must_finish": True,

        },
        { 
            "key": "daily_material_composing",
            "run": daily_job(daily_material_composing),
            "must_finish": True,
            "label": "Material Composing",
            "priority": 386,

        },
        { 
            "key": "daily_greet_champion",
            "run": daily_job(daily_greet_champion, after_go=greet_champion_after_go),
            "label": "Greet Champion",
            "priority": 385, 
            "must_finish": True,
            "note": "Về thành: bấm trái tim trên Keep (hoặc Keep -> Champion), chào 2 lần",
        },
        { 
            "key": "daily_monster_killing",
            "run": daily_job(daily_monster_killing),
            "must_finish": True,
            "label": "Monster Killing",
            "priority": -384,

        },
        { 
            "key": "daily_resource_collecting",
            "run": daily_job(daily_resource_collecting),
            "must_finish": True,
            "label": "Resource Collecting",
            "priority": 383,

        },
        { 
            "key": "daily_research_technologies",
            "run": daily_job(daily_research_technologies, after_go=research_technologies_after_go),
            "must_finish": True,
            "label": "Research",
            "priority": 382,
            "note": "Học viện: nghiên cứu 1 công nghệ xanh bất kỳ, tốn thời gian thì Speed Up bằng vật phẩm",

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
            "must_finish": True,
            "label": "Activity Rewards (nhận thưởng cuối)",
            "priority": 300,

        },
        {
            "key": "daily_gift_claims",
            "run": daily_gift_claims,
            "label": "Nhận quà cuối ngày (sau khi Daily và thưởng Activity xong)",
            "priority": 200,
        }
    ],
    "Black Market": [
        { 
            "key": "black_market_market",
            "run": black_market_market,
            "label": "Black Market: mua ở Market",
            "priority": 0,
            "once": True 
        }
    ],
    "Battlefield Shop": [
        { 
            "key": "battlefield_shop",
            "run": battlefield_shop,
            "label": "Battlefield Shop",
            "priority": -1,
        }
    ]
}
