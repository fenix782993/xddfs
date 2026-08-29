import random


SYMBOLS = [
    "🍒",
    "🍋",
    "🍊",
    "🍇",
    "💎",
    "7️⃣",
]


async def play(user_id: int, bet: int):

    result = [
        random.choice(SYMBOLS)
        for _ in range(3)
    ]

    if len(set(result)) == 1:

        if result[0] == "7️⃣":
            multiplier = 10.0
        elif result[0] == "💎":
            multiplier = 7.0
        else:
            multiplier = 5.0

    elif len(set(result)) == 2:
        multiplier = 1.5

    else:
        multiplier = 0.0

    win = multiplier > 0

    if win:
        profit = int(bet * multiplier) - bet
    else:
        profit = -bet

    return {
        "game": "slots",
        "symbols": result,
        "win": win,
        "multiplier": multiplier,
        "profit": profit,
    }