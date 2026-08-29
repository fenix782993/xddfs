import random
from typing import Any


def dice():
    value = random.randint(1, 6)

    return {
        "value": value,
        "emoji": f"🎲 {value}",
    }


def darts():
    value = random.randint(1, 6)

    return {
        "value": value,
        "emoji": f"🎯 {value}",
    }


def football():
    value = random.randint(1, 6)

    if value >= 5:
        return {
            "value": value,
            "goal": True,
            "emoji": "⚽ GOAL!",
        }

    return {
        "value": value,
        "goal": False,
        "emoji": "⚽ MISS",
    }


def basketball():
    value = random.randint(1, 6)

    if value >= 5:
        return {
            "value": value,
            "score": True,
            "emoji": "🏀 SCORE!",
        }

    return {
        "value": value,
        "score": False,
        "emoji": "🏀 MISS",
    }


def bowling():
    value = random.randint(1, 6)

    return {
        "value": value,
        "pins": value,
        "emoji": f"🎳 {value} pins",
    }


def slots():
    symbols = [
        "🍒",
        "🍋",
        "🍊",
        "🔔",
        "⭐",
        "💎",
        "7️⃣",
    ]

    result = [
        random.choice(symbols),
        random.choice(symbols),
        random.choice(symbols),
    ]

    if result[0] == result[1] == result[2]:
        multiplier = 10.0
        win = True

    elif result[0] == result[1] or result[1] == result[2]:
        multiplier = 2.0
        win = True

    else:
        multiplier = 0.0
        win = False

    return {
        "symbols": result,
        "display": " | ".join(result),
        "win": win,
        "multiplier": multiplier,
    }


def mines():
    mines_count = 5

    mine_positions = random.sample(
        range(25),
        mines_count,
    )

    safe_positions = [
        x for x in range(25)
        if x not in mine_positions
    ]

    return {
        "size": 5,
        "mines": mine_positions,
        "safe": safe_positions,
    }


def crash():
    value = random.random()

    if value < 0.03:
        multiplier = 1.0
    else:
        multiplier = round(
            1.0 + random.random() * 9.0,
            2,
        )

    return {
        "multiplier": multiplier,
        "crashed": multiplier <= 1.0,
    }


def roulette():
    number = random.randint(0, 36)

    if number == 0:
        color = "green"
    elif number % 2:
        color = "red"
    else:
        color = "black"

    return {
        "number": number,
        "color": color,
    }


def play(
    game_code: str,
) -> dict[str, Any]:

    games = {
        "dice": dice,
        "darts": darts,
        "football": football,
        "basketball": basketball,
        "bowling": bowling,
        "slots": slots,
        "mines": mines,
        "crash": crash,
        "roulette": roulette,
    }

    game = games.get(game_code)

    if not game:
        raise ValueError("unknown_game")

    return game()