import random


SIZE = 5
CELLS = SIZE * SIZE


def create_board(
    mines: int = 5,
):

    positions = random.sample(
        range(CELLS),
        mines
    )

    return {
        "mines": positions,
        "opened": [],
        "safe": [],
        "alive": True,
    }


def open_cell(
    board: dict,
    cell: int,
):

    if not board["alive"]:
        return {
            "status": "finished"
        }

    if cell < 0 or cell >= CELLS:
        return {
            "status": "invalid"
        }

    if cell in board["opened"]:
        return {
            "status": "already_open"
        }

    if cell in board["mines"]:

        board["alive"] = False

        return {
            "status": "mine",
            "cell": cell,
            "multiplier": 0,
        }

    board["opened"].append(cell)
    board["safe"].append(cell)

    opened = len(
        board["safe"]
    )

    multiplier = round(
        1.0 + opened * 0.35,
        2
    )

    return {
        "status": "safe",
        "cell": cell,
        "opened": opened,
        "multiplier": multiplier,
    }


def cashout(
    board: dict,
    bet: int,
):

    if not board["alive"]:
        return {
            "win": False,
            "profit": -bet,
        }

    opened = len(
        board["safe"]
    )

    if opened == 0:
        return {
            "win": False,
            "profit": -bet,
        }

    multiplier = round(
        1.0 + opened * 0.35,
        2
    )

    payout = int(
        bet * multiplier
    )

    board["alive"] = False

    return {
        "win": True,
        "payout": payout,
        "profit": payout - bet,
        "multiplier": multiplier,
    }