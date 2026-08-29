import random


async def play(user_id: int, bet: int):

    value = random.random()

    if value < 0.02:
        multiplier = 1.0
    else:
        multiplier = round(
            1.0 + random.random() * 9.0,
            2
        )

    return {
        "game": "crash",
        "crash": multiplier,
        "bet": bet,
    }


async def cashout(
    bet: int,
    multiplier: float,
):

    if multiplier < 1:
        return {
            "win": False,
            "profit": -bet,
        }

    payout = int(
        bet * multiplier
    )

    return {
        "win": True,
        "payout": payout,
        "profit": payout - bet,
        "multiplier": multiplier,
    }