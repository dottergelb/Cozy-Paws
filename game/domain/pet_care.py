from game.models import Quest


ACTION_RULES = {
    "feed": {
        "label": "покормил",
        "energy": 0,
        "mood": 3,
        "hunger": 22,
        "experience": 8,
        "coins": 4,
        "quest": Quest.FEED,
        "requires": {},
    },
    "play": {
        "label": "поиграл с",
        "energy": -18,
        "mood": 20,
        "hunger": -7,
        "experience": 13,
        "coins": 7,
        "quest": Quest.PLAY,
        "requires": {"energy": 15},
    },
    "pet": {
        "label": "погладил",
        "energy": 0,
        "mood": 10,
        "hunger": -2,
        "experience": 5,
        "coins": 3,
        "quest": Quest.PET,
        "requires": {},
    },
    "walk": {
        "label": "вывел гулять",
        "energy": -25,
        "mood": 14,
        "hunger": -12,
        "experience": 18,
        "coins": 11,
        "quest": Quest.WALK,
        "requires": {"energy": 25},
    },
}


COOLDOWNS = {
    "pet_action": 8,
    "buy_item": 2,
    "claim_quest": 2,
    "train": 20,
    "show": 30,
    "chat": 10,
    "message": 10,
    "support": 60,
    "explore": 8,
    "assistant": 5,
    "club": 5,
    "adventure": 5,
    "competition": 5,
    "chest": 5,
    "gift": 5,
    "forum": 5,
    "memory": 5,
}
