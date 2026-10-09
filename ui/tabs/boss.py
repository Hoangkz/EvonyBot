"""boss.py — danh mục boss cho tab Join Monster War và nhận diện OCR (dữ liệu tĩnh).

DATA: `boss_categories` -> `list` boss: `name`, `active` (mặc định tích), `levels`
(level / tier / power). Trước đây là file .json cùng tên; đổi sang .py để Nuitka compile
cùng code, không cần ship file riêng lúc build.
"""
DATA ={
    "boss_categories": [
        {
            "category_key": "standard_bosses",
            "label": "Boss Standard",
            "list": [
                {
                    "levels": [ ],
                    "name": "Zombie",
                    "active": False
                },
                {
                    "levels": [ ],
                    "name": "Redcap",
                    "active": False
                },
                {
                    "levels": [ ],
                    "name": "Centaur",
                    "active": False
                },
                {
                    "levels": [ ],
                    "name": "Skeleton Dragon",
                    "active": False
                },
                {
                    "levels": [ ],
                    "name": "Werewolf",
                    "active": False
                },
                {
                    "levels": [ ],
                    "name": "Manticore",
                    "active": False
                },
                {
                    "levels": [ ],
                    "name": "Yasha",
                    "active": False
                },
                {
                    "levels": [ ],
                    "name": "Peryton",
                    "active": False
                },
                {
                    "levels": [ ],
                    "name": "Minotaur",
                    "active": False
                },
                {
                    "levels": [ ],
                    "name": "Griffin",
                    "active": False
                },
                {
                    "levels": [ ],
                    "name": "Ifrit",
                    "active": False
                },
                {
                    "levels": [ ],
                    "name": "Kamaitachi",
                    "active": False
                },
                {
                    "levels": [ ],
                    "name": "Fafnir",
                    "active": True
                },
                {
                    "levels": [ ],
                    "name": "Behemoth",
                    "active": True
                },
                {
                    "levels": [ ],
                    "name": "Phoenix",
                    "active": True
                },
                {
                    "levels": [ ],
                    "name": "Jormungandr",
                    "active": True
                },
                {
                    "levels": [ ],
                    "name": "Typhon",
                    "active": True
                },
                {
                    "levels": [ ],
                    "name": "Ammit",
                    "active": True
                },
                {
                    "levels": [ ],
                    "name": "Stymphalian Bird",
                    "active": True
                },
                {
                    "levels": [ ],
                    "name": "Lernean Hydra",
                    "active": True
                },
                {
                    "levels": [ ],
                    "name": "Azazel",
                    "active": True
                },
                {
                    "levels": [ ],
                    "name": "Leviathan",
                    "active": True
                },
                {
                    "levels": [ ],
                    "name": "Garmr",
                    "active": True
                }
            ]
        },
        {
            "category_key": "special_and_recurring_event_bosses",
            "label": "Boss Event",
            "list": [
                {
                    "name": "Cerberus",
                    "levels": [
                        {
                            "level": 1,
                            "tier": "Junior",
                            "power": "68.2M",
                            "active": False
                        },
                        {
                            "level": 2,
                            "tier": "Medium",
                            "power": "153.4M",
                            "active": False
                        },
                        {
                            "level": 3,
                            "tier": "Senior",
                            "power": "234.2M",
                            "active": False
                        },
                        {
                            "level": 4,
                            "tier": "Legendary",
                            "power": "694.9M",
                            "active": False
                        },
                        {
                            "level": 5,
                            "tier": "Epic",
                            "power": "1.5B",
                            "active": False
                        }
                    ]
                },
                {
                    "name": "Ymir",
                    "levels": [
                        {
                            "level": 1,
                            "power": "23.4M",
                            "active": False
                        },
                        {
                            "level": 2,
                            "power": "70.8M",
                            "active": False
                        },
                        {
                            "level": 3,
                            "power": "120.2M",
                            "active": True
                        },
                        {
                            "level": 4,
                            "power": "206.4M",
                            "active": True
                        },
                        {
                            "level": 5,
                            "power": "361.3M",
                            "active": True
                        },
                        {
                            "level": 6,
                            "power": "722.6M",
                            "active": True
                        },
                        {
                            "level": 7,
                            "power": "1.8B",
                            "active": True
                        }
                    ]
                },
                {
                    "name": "Sphinx",
                    "levels": [
                        {
                            "level": 1,
                            "power": "12.4M",
                            "active": False
                        },
                        {
                            "level": 2,
                            "power": "22.3M",
                            "active": False
                        },
                        {
                            "level": 3,
                            "power": "74.5M",
                            "active": True
                        },
                        {
                            "level": 4,
                            "power": "147.5M",
                            "active": True
                        },
                        {
                            "level": 5,
                            "power": "225.2M",
                            "active": True
                        },
                        {
                            "level": 6,
                            "power": "472.9M",
                            "active": True
                        },
                        {
                            "level": 7,
                            "power": "914.4M",
                            "active": True
                        },
                        {
                            "level": 8,
                            "power": "2B",
                            "active": True
                        }
                    ]
                },
                {
                    "name": "Knight Bayard",
                    "levels": [
                        {
                            "level": 1,
                            "tier": "Junior",
                            "power": "65.5M",
                            "active": False
                        },
                        {
                            "level": 2,
                            "tier": "Senior",
                            "power": "147.5M",
                            "active": False
                        },
                        {
                            "level": 3,
                            "tier": "Excellent",
                            "power": "225.2M",
                            "active": True
                        },
                        {
                            "level": 4,
                            "tier": "Legendary",
                            "power": "668.1M",
                            "active": True
                        },
                        {
                            "level": 5,
                            "tier": "Epic",
                            "power": "1.5B",
                            "active": True
                        }
                    ]
                },
                {
                    "name": "Warlord",
                    "levels": [
                        {
                            "level": 1,
                            "power": "13M",
                            "active": False
                        },
                        {
                            "level": 2,
                            "power": "24.6M",
                            "active": False
                        },
                        {
                            "level": 3,
                            "power": "85.6M",
                            "active": True
                        },
                        {
                            "level": 4,
                            "power": "154.8M",
                            "active": True
                        },
                        {
                            "level": 5,
                            "power": "225.2M",
                            "active": True
                        },
                        {
                            "level": 6,
                            "power": "668.1M",
                            "active": True
                        },
                        {
                            "level": 7,
                            "power": "1.5B",
                            "active": True
                        }
                    ]
                },
                {
                    "name": "Golem",
                    "levels": [
                        {
                            "level": 1,
                            "power": "12.4M",
                            "active": False
                        },
                        {
                            "level": 2,
                            "power": "22.3M",
                            "active": False
                        },
                        {
                            "level": 3,
                            "power": "74.5M",
                            "active": True
                        },
                        {
                            "level": 4,
                            "power": "147.5M",
                            "active": True
                        },
                        {
                            "level": 5,
                            "power": "225.2M",
                            "active": True
                        },
                        {
                            "level": 6,
                            "power": "668.1M",
                            "active": True
                        },
                        {
                            "level": 7,
                            "power": "1.5B",
                            "active": True
                        }
                    ]
                },
                {
                    "name": "Witch",
                    "levels": [
                        {
                            "level": 1,
                            "power": "13M",
                            "active": False
                        },
                        {
                            "level": 2,
                            "power": "24.6M",
                            "active": False
                        },
                        {
                            "level": 3,
                            "power": "85.6M",
                            "active": True
                        },
                        {
                            "level": 4,
                            "power": "154.8M",
                            "active": True
                        },
                        {
                            "level": 5,
                            "power": "225.2M",
                            "active": True
                        },
                        {
                            "level": 6,
                            "power": "668.1M",
                            "active": True
                        },
                        {
                            "level": 7,
                            "power": "1.5B",
                            "active": True
                        }
                    ]
                },
                {
                    "name": "Hydra",
                    "levels": [
                        {
                            "level": 1,
                            "tier": "Junior",
                            "power": "84.9M",
                            "active": False
                        },
                        {
                            "level": 2,
                            "tier": "Medium",
                            "power": "120.6M",
                            "active": False
                        },
                        {
                            "level": 3,
                            "tier": "Senior",
                            "power": "198.9M",
                            "active": True
                        },
                        {
                            "level": 4,
                            "tier": "Legendary",
                            "power": "328.4M",
                            "active": True
                        },
                        {
                            "level": 5,
                            "tier": "Epic",
                            "power": "678.8M",
                            "active": True
                        },
                        {
                            "level": 6,
                            "tier": "Mythical",
                            "power": "1.5B",
                            "active": True
                        }
                    ]
                },
                {
                    "name": "Lava Turtle",
                    "levels": [
                        {
                            "level": 1,
                            "power": "12.4M",
                            "active": False
                        },
                        {
                            "level": 2,
                            "power": "22.3M",
                            "active": False
                        },
                        {
                            "level": 3,
                            "power": "74.5M",
                            "active": True
                        },
                        {
                            "level": 4,
                            "power": "147.5M",
                            "active": True
                        },
                        {
                            "level": 5,
                            "power": "225.2M",
                            "active": True
                        },
                        {
                            "level": 6,
                            "power": "668.1M",
                            "active": True
                        },
                        {
                            "level": 7,
                            "power": "1.5B",
                            "active": True
                        }
                    ]
                },
                {
                    "name": "Pan",
                    "levels": [
                        {
                            "level": 1,
                            "power": "22.3M",
                            "active": False
                        },
                        {
                            "level": 2,
                            "power": "42.8M",
                            "active": False
                        },
                        {
                            "level": 3,
                            "power": "122.9M",
                            "active": True
                        },
                        {
                            "level": 4,
                            "power": "206.4M",
                            "active": True
                        },
                        {
                            "level": 5,
                            "power": "361.3M",
                            "active": True
                        },
                        {
                            "level": 6,
                            "power": "711.7M",
                            "active": True
                        },
                        {
                            "level": 7,
                            "power": "1.8B",
                            "active": True
                        }
                    ]
                },
                {
                    "name": "Pumpkin Monster",
                    "levels": [
                        {
                            "level": 1,
                            "power": "708.5K",
                            "active": False
                        },
                        {
                            "level": 2,
                            "power": "1.9M",
                            "active": False
                        },
                        {
                            "level": 3,
                            "power": "5.9M",
                            "active": True
                        },
                        {
                            "level": 4,
                            "power": "16.1M",
                            "active": True
                        },
                        {
                            "level": 5,
                            "power": "53.6M",
                            "active": True
                        },
                        {
                            "level": 6,
                            "power": "80.4M",
                            "active": True
                        },
                        {
                            "level": 7,
                            "power": "134.1M",
                            "active": True
                        },
                        {
                            "level": 8,
                            "power": "268.1M",
                            "active": True
                        }
                    ]
                },
                {
                    "name": "Nian",
                    "levels": [
                        {
                            "level": 1,
                            "tier": "Junior",
                            "power": "59.6M",
                            "active": False
                        },
                        {
                            "level": 2,
                            "tier": "Medium",
                            "power": "71.5M",
                            "active": False
                        },
                        {
                            "level": 3,
                            "tier": "Senior",
                            "power": "89.4M",
                            "active": True
                        },
                        {
                            "level": 4,
                            "tier": "Grand",
                            "power": "134.1M",
                            "active": True
                        },
                        {
                            "level": 5,
                            "tier": "Epic",
                            "power": "236.5M",
                            "active": True
                        },
                        {
                            "level": 6,
                            "tier": "Legendary",
                            "power": "472.9M",
                            "active": True
                        }
                    ]
                }
            ]
        },
        {
            "category_key": "mythical_and_elite_bosses",
            "label": "Boss Special",
            "list": [
                {
                    "name": "Viking",
                    "levels": [ ]
                },
                {
                    "name": "Aglaope",
                    "levels": [
                        {
                            "level": 1,
                            "active": True
                        }
                    ]
                },
                {
                    "name": "Garuda",
                    "levels": [
                        {
                            "level": 1,
                            "tier": "Junior",
                            "power": "1.3M",
                            "active": False
                        },
                        {
                            "level": 2,
                            "tier": "Senior",
                            "power": "1.7M",
                            "active": False
                        },
                        {
                            "level": 3,
                            "tier": "Master",
                            "power": "125M",
                            "active": True
                        }
                    ]
                },
                {
                    "name": "Savage Tiger Gladiator",
                    "levels": [
                        {
                            "level": 1,
                            "tier": "Junior",
                            "power": "85.6M",
                            "active": False
                        },
                        {
                            "level": 2,
                            "tier": "Medium",
                            "power": "154.8M",
                            "active": True
                        },
                        {
                            "level": 3,
                            "tier": "Senior",
                            "power": "225.2M",
                            "active": True
                        }
                    ]
                },
                {
                    "name": "Taotie",
                    "levels": [
                        {
                            "level": 1,
                            "power": "124.6M",
                            "active": False
                        },
                        {
                            "level": 2,
                            "power": "398.1M",
                            "active": True
                        },
                        {
                            "level": 3,
                            "power": "805.1M",
                            "active": True
                        }
                    ]
                },
                {
                    "name": "Arachne",
                    "levels": [
                        {
                            "level": 1,
                            "tier": "Junior",
                            "power": "85.6M",
                            "active": False
                        },
                        {
                            "level": 2,
                            "tier": "Senior",
                            "power": "154.8M",
                            "active": True
                        }
                    ]
                },
                {
                    "name": "Carcinus",
                    "levels": [
                        {
                            "level": 1,
                            "tier": "Junior",
                            "power": "85.6M",
                            "active": False
                        },
                        {
                            "level": 2,
                            "tier": "Senior",
                            "power": "154.8M",
                            "active": True
                        }
                    ]
                },
                {
                    "name": "Harpy",
                    "levels": [
                        {
                            "level": 1,
                            "tier": "Junior",
                            "power": "85.6M",
                            "active": False
                        },
                        {
                            "level": 2,
                            "tier": "Senior",
                            "power": "154.8M",
                            "active": True
                        }
                    ]
                },
                {
                    "name": "Serpopard",
                    "levels": [
                        {
                            "level": 1,
                            "tier": "Junior",
                            "power": "85.6M",
                            "active": False
                        },
                        {
                            "level": 2,
                            "tier": "Senior",
                            "power": "154.8M",
                            "active": True
                        }
                    ]
                },
                {
                    "name": "Gugler Knight",
                    "levels": [
                        {
                            "level": 1,
                            "tier": "Junior",
                            "power": "85.6M",
                            "active": False
                        },
                        {
                            "level": 2,
                            "tier": "Senior",
                            "power": "154.8M",
                            "active": True
                        }
                    ]
                },
                {
                    "name": "Nasu",
                    "levels": [
                        {
                            "level": 1,
                            "tier": "Junior",
                            "power": "85.6M",
                            "active": False
                        },
                        {
                            "level": 2,
                            "tier": "Senior",
                            "power": "154.8M",
                            "active": True
                        }
                    ]
                },
                {
                    "name": "Barbary Pirate",
                    "levels": [
                        {
                            "level": 1,
                            "tier": "Junior",
                            "power": "85.6M",
                            "active": False
                        },
                        {
                            "level": 2,
                            "tier": "Senior",
                            "power": "154.8M",
                            "active": True
                        }
                    ]
                },
                {
                    "name": "Outlander Elites",
                    "levels": [
                        {
                            "level": 1,
                            "tier": "Junior",
                            "power": "85.6M",
                            "active": False
                        },
                        {
                            "level": 2,
                            "tier": "Senior",
                            "power": "154.8M",
                            "active": True
                        }
                    ]
                },
                {
                    "name": "Temple Guard",
                    "levels": [
                        {
                            "level": 1,
                            "tier": "Junior",
                            "power": "85.6M",
                            "active": False
                        },
                        {
                            "level": 2,
                            "tier": "Senior",
                            "power": "154.8M",
                            "active": True
                        }
                    ]
                },
                {
                    "name": "Elite Temple Guard",
                    "levels": [
                        {
                            "level": 1,
                            "active": True
                        }
                    ]
                },
                {
                    "name": "Fenrir",
                    "levels": [
                        {
                            "level": 1,
                            "tier": "Weak",
                            "power": "27.4K",
                            "active": False
                        },
                        {
                            "level": 2,
                            "tier": "Common",
                            "power": "186.1K",
                            "active": False
                        },
                        {
                            "level": 3,
                            "tier": "Fierce",
                            "power": "492.7K",
                            "active": False
                        }
                    ]
                }
            ]
        }
    ]
}