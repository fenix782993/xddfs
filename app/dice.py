import random


async def play(user_id: int, bet: int):
    roll = random.randint(1, 6)

    win = roll >= 5

    if win:
        multiplier = 2.0
        profit = int(bet * multiplier) - bet
    else:
        multiplier = 0.0
        profit = -bet

    return {
        "game": "dice",
        "roll": roll,
        "win": win,
        "multiplier": multiplier,
        "profit": profit,
    }