import random


RED = {
    1, 3, 5, 7, 9,
    12, 14, 16, 18,
    19, 21, 23, 25,
    27, 30, 32, 34, 36,
}

BLACK = {
    2, 4, 6, 8, 10,
    11, 13, 15, 17,
    20, 22, 24, 26,
    28, 29, 31, 33,
    35,
}


async def spin(
    bet: int,
    choice: str,
):

    number = random.randint(0, 36)

    if number == 0:
        color = "green"
    elif number in RED:
        color = "red"
    else:
        color = "black"

    if choice == str(number):
        multiplier = 35.0
    elif choice == color:
        multiplier = 2.0
    else:
        multiplier = 0.0

    win = multiplier > 0

    if win:
        profit = int(
            bet * multiplier
        ) - bet
    else:
        profit = -bet

    return {
        "game": "roulette",
        "number": number,
        "color": color,
        "choice": choice,
        "win": win,
        "multiplier": multiplier,
        "profit": profit,
    }