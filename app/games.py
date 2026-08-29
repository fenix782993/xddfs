from __future__ import annotations

import random
from typing import Any, Dict, List, Optional


# ============================================================
# COMMON
# ============================================================

def _result(
    game: str,
    win: bool,
    bet: int,
    multiplier: float,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:

    win_amount = int(bet * multiplier) if win else 0

    data = {
        "game": game,
        "win": bool(win),
        "bet": int(bet),
        "multiplier": float(multiplier),
        "win_amount": win_amount,
        "profit": win_amount - int(bet),
    }

    if extra:
        data.update(extra)

    return data


def _validate_bet(bet: int) -> int:
    bet = int(bet)

    if bet <= 0:
        raise ValueError("Ставка должна быть больше 0")

    return bet


# ============================================================
# DICE
# ============================================================

def dice(
    bet: int,
    prediction: Optional[int] = None,
) -> Dict[str, Any]:

    bet = _validate_bet(bet)

    roll = random.randint(1, 6)

    if prediction is not None:

        prediction = int(prediction)

        if prediction < 1 or prediction > 6:
            raise ValueError("Число должно быть от 1 до 6")

        win = roll == prediction
        multiplier = 5.5

    else:

        win = roll >= 4
        multiplier = 1.8

    return _result(
        "dice",
        win,
        bet,
        multiplier,
        {
            "roll": roll,
            "prediction": prediction,
        },
    )


# ============================================================
# DARTS
# ============================================================

def darts(
    bet: int,
    target: Optional[int] = None,
) -> Dict[str, Any]:

    bet = _validate_bet(bet)

    score = random.randint(1, 60)

    if target is not None:
        target = int(target)

        if target < 1 or target > 60:
            raise ValueError("target должен быть от 1 до 60")

        distance = abs(score - target)

        if distance == 0:
            multiplier = 8.0
            win = True
        elif distance <= 3:
            multiplier = 3.5
            win = True
        elif distance <= 7:
            multiplier = 1.8
            win = True
        else:
            multiplier = 0.0
            win = False

    else:

        if score >= 55:
            multiplier = 4.0
            win = True
        elif score >= 40:
            multiplier = 2.0
            win = True
        elif score >= 25:
            multiplier = 1.2
            win = True
        else:
            multiplier = 0.0
            win = False

    return _result(
        "darts",
        win,
        bet,
        multiplier,
        {
            "score": score,
            "target": target,
        },
    )


# ============================================================
# BOWLING
# ============================================================

def bowling(
    bet: int,
) -> Dict[str, Any]:

    bet = _validate_bet(bet)

    pins = random.randint(0, 10)

    if pins == 10:
        multiplier = 4.0
        win = True
    elif pins >= 8:
        multiplier = 2.5
        win = True
    elif pins >= 5:
        multiplier = 1.5
        win = True
    else:
        multiplier = 0.0
        win = False

    return _result(
        "bowling",
        win,
        bet,
        multiplier,
        {
            "pins": pins,
            "max_pins": 10,
            "strike": pins == 10,
        },
    )


# ============================================================
# COIN FLIP
# ============================================================

def coinflip(
    bet: int,
    choice: Optional[str] = None,
) -> Dict[str, Any]:

    bet = _validate_bet(bet)

    result = random.choice(["heads", "tails"])

    if choice:

        choice = str(choice).lower().strip()

        if choice not in ("heads", "tails"):
            raise ValueError(
                "choice должен быть heads или tails"
            )

        win = result == choice

    else:

        win = result == "heads"

    return _result(
        "coinflip",
        win,
        bet,
        1.9,
        {
            "result": result,
            "choice": choice,
        },
    )


# ============================================================
# ROULETTE
# ============================================================

def roulette(
    bet: int,
    choice: Optional[str] = None,
) -> Dict[str, Any]:

    bet = _validate_bet(bet)

    number = random.randint(0, 36)

    red_numbers = {
        1, 3, 5, 7, 9,
        12, 14, 16, 18,
        19, 21, 23, 25,
        27, 30, 32, 34, 36,
    }

    if number == 0:
        color = "green"

    elif number in red_numbers:
        color = "red"

    else:
        color = "black"

    choice = str(choice or "red").lower()

    if choice in ("red", "black", "green"):

        win = color == choice

        multiplier = (
            14.0
            if choice == "green"
            else 1.9
        )

    elif choice == "even":

        win = number != 0 and number % 2 == 0
        multiplier = 1.9

    elif choice == "odd":

        win = number % 2 == 1
        multiplier = 1.9

    elif choice == "low":

        win = 1 <= number <= 18
        multiplier = 1.9

    elif choice == "high":

        win = 19 <= number <= 36
        multiplier = 1.9

    else:

        raise ValueError(
            "Неизвестная ставка рулетки"
        )

    return _result(
        "roulette",
        win,
        bet,
        multiplier,
        {
            "number": number,
            "color": color,
            "choice": choice,
        },
    )


# ============================================================
# SLOTS
# ============================================================

SLOT_SYMBOLS = [
    "🍒",
    "🍋",
    "🔔",
    "⭐",
    "💎",
    "7️⃣",
]


def slots(
    bet: int,
) -> Dict[str, Any]:

    bet = _validate_bet(bet)

    reels = [
        random.choice(SLOT_SYMBOLS),
        random.choice(SLOT_SYMBOLS),
        random.choice(SLOT_SYMBOLS),
    ]

    if reels[0] == reels[1] == reels[2]:

        if reels[0] == "7️⃣":
            multiplier = 15.0

        elif reels[0] == "💎":
            multiplier = 10.0

        else:
            multiplier = 7.0

        win = True

    elif (
        reels[0] == reels[1]
        or reels[1] == reels[2]
        or reels[0] == reels[2]
    ):

        multiplier = 2.0
        win = True

    else:

        multiplier = 0.0
        win = False

    return _result(
        "slots",
        win,
        bet,
        multiplier,
        {
            "reels": reels,
        },
    )


# ============================================================
# HIGH / LOW
# ============================================================

def highlow(
    bet: int,
    choice: str = "high",
) -> Dict[str, Any]:

    bet = _validate_bet(bet)

    choice = str(choice).lower()

    if choice not in ("high", "low"):
        raise ValueError(
            "choice должен быть high или low"
        )

    number = random.randint(1, 100)

    if choice == "high":
        win = number > 50
    else:
        win = number < 50

    return _result(
        "highlow",
        win,
        bet,
        1.9,
        {
            "number": number,
            "choice": choice,
        },
    )


# ============================================================
# ROCK PAPER SCISSORS
# ============================================================

RPS = [
    "rock",
    "paper",
    "scissors",
]


def rps(
    bet: int,
    choice: str,
) -> Dict[str, Any]:

    bet = _validate_bet(bet)

    choice = str(choice).lower()

    if choice not in RPS:
        raise ValueError(
            "choice должен быть rock, paper или scissors"
        )

    enemy = random.choice(RPS)

    if choice == enemy:

        win = False
        multiplier = 1.0

    elif (
        (choice == "rock" and enemy == "scissors")
        or
        (choice == "paper" and enemy == "rock")
        or
        (choice == "scissors" and enemy == "paper")
    ):

        win = True
        multiplier = 1.9

    else:

        win = False
        multiplier = 0.0

    return _result(
        "rps",
        win,
        bet,
        multiplier,
        {
            "player": choice,
            "enemy": enemy,
        },
    )


# ============================================================
# MINES
# ============================================================

def mines(
    bet: int,
    mines_count: int = 5,
    size: int = 5,
    opened: Optional[List[int]] = None,
) -> Dict[str, Any]:

    bet = _validate_bet(bet)

    mines_count = int(mines_count)
    size = int(size)

    if size < 2 or size > 10:
        raise ValueError(
            "Размер поля должен быть от 2 до 10"
        )

    total = size * size

    if mines_count < 1 or mines_count >= total:
        raise ValueError(
            "Некорректное количество мин"
        )

    mine_positions = set(
        random.sample(
            range(total),
            mines_count,
        )
    )

    opened = opened or []

    opened = [
        int(x)
        for x in opened
    ]

    hit_mine = any(
        cell in mine_positions
        for cell in opened
    )

    safe_opened = sum(
        1
        for cell in opened
        if cell not in mine_positions
    )

    if hit_mine:

        multiplier = 0.0
        win = False

    elif safe_opened == 0:

        multiplier = 1.0
        win = False

    else:

        multiplier = round(
            1.0 + safe_opened * 0.35,
            2,
        )

        win = True

    return _result(
        "mines",
        win,
        bet,
        multiplier,
        {
            "size": size,
            "mines_count": mines_count,
            "mine_positions": list(
                mine_positions
            ),
            "opened": opened,
            "safe_opened": safe_opened,
            "hit_mine": hit_mine,
        },
    )


# ============================================================
# CRASH
# ============================================================

def crash(
    bet: int,
) -> Dict[str, Any]:

    bet = _validate_bet(bet)

    value = random.random()

    if value < 0.03:

        multiplier = 1.0

    else:

        multiplier = max(
            1.0,
            round(
                1 /
                max(
                    random.random(),
                    0.01,
                ),
                2,
            ),
        )

    multiplier = min(
        multiplier,
        100.0,
    )

    cashout = round(
        random.uniform(
            1.0,
            multiplier,
        ),
        2,
    )

    win = cashout < multiplier

    return _result(
        "crash",
        win,
        bet,
        cashout if win else 0.0,
        {
            "crash_at": multiplier,
            "cashout": cashout,
        },
    )


# ============================================================
# RACE
# ============================================================

def race(
    bet: int,
) -> Dict[str, Any]:

    bet = _validate_bet(bet)

    racers = [
        {
            "id": i,
            "position": random.randint(
                1,
                100,
            ),
        }
        for i in range(1, 5)
    ]

    racers.sort(
        key=lambda x: x["position"],
        reverse=True,
    )

    winner = racers[0]

    player_won = (
        winner["id"] == 1
    )

    return _result(
        "race",
        player_won,
        bet,
        3.5,
        {
            "racers": racers,
            "winner": winner["id"],
        },
    )


# ============================================================
# FOOTBALL
# ============================================================

def football(
    bet: int,
    prediction: str = "home",
) -> Dict[str, Any]:

    bet = _validate_bet(bet)

    prediction = str(
        prediction
    ).lower()

    if prediction not in (
        "home",
        "draw",
        "away",
    ):
        raise ValueError(
            "prediction должен быть home, draw или away"
        )

    home = random.randint(0, 5)
    away = random.randint(0, 5)

    if home > away:
        result = "home"

    elif home < away:
        result = "away"

    else:
        result = "draw"

    multiplier_map = {
        "home": 1.8,
        "draw": 3.2,
        "away": 2.3,
    }

    win = result == prediction

    return _result(
        "football",
        win,
        bet,
        multiplier_map[result],
        {
            "home": home,
            "away": away,
            "prediction": prediction,
            "result": result,
        },
    )


# ============================================================
# BASKETBALL
# ============================================================

def basketball(
    bet: int,
    prediction: str = "home",
) -> Dict[str, Any]:

    bet = _validate_bet(bet)

    prediction = str(
        prediction
    ).lower()

    if prediction not in (
        "home",
        "away",
    ):
        raise ValueError(
            "prediction должен быть home или away"
        )

    home = random.randint(
        70,
        130,
    )

    away = random.randint(
        70,
        130,
    )

    result = (
        "home"
        if home > away
        else "away"
    )

    win = result == prediction

    return _result(
        "basketball",
        win,
        bet,
        1.9,
        {
            "home": home,
            "away": away,
            "prediction": prediction,
            "result": result,
        },
    )


# ============================================================
# PLINKO
# ============================================================

def plinko(
    bet: int,
    rows: int = 8,
) -> Dict[str, Any]:

    bet = _validate_bet(bet)

    rows = int(rows)

    if rows < 4 or rows > 16:
        raise ValueError(
            "rows должен быть от 4 до 16"
        )

    position = 0
    path = []

    for _ in range(rows):

        direction = random.choice(
            [-1, 1]
        )

        position += direction
        path.append(direction)

    distance = abs(position)

    multipliers = [
        0.2,
        0.5,
        0.8,
        1.2,
        1.8,
        2.5,
        5.0,
    ]

    index = min(
        distance,
        len(multipliers) - 1,
    )

    multiplier = multipliers[index]

    win = multiplier > 1.0

    return _result(
        "plinko",
        win,
        bet,
        multiplier,
        {
            "rows": rows,
            "path": path,
            "position": position,
        },
    )


# ============================================================
# BLACKJACK
# ============================================================

def blackjack(
    bet: int,
) -> Dict[str, Any]:

    bet = _validate_bet(bet)

    player = random.randint(
        16,
        21,
    )

    dealer = random.randint(
        15,
        21,
    )

    if player > dealer:

        win = True
        multiplier = 2.0

    elif player == dealer:

        win = False
        multiplier = 1.0

    else:

        win = False
        multiplier = 0.0

    return _result(
        "blackjack",
        win,
        bet,
        multiplier,
        {
            "player": player,
            "dealer": dealer,
        },
    )


# ============================================================
# GAME REGISTRY
# ============================================================

GAMES = {

    "dice": dice,

    "darts": darts,

    "bowling": bowling,

    "coinflip": coinflip,

    "roulette": roulette,

    "slots": slots,

    "highlow": highlow,

    "rps": rps,

    "mines": mines,

    "crash": crash,

    "race": race,

    "football": football,

    "basketball": basketball,

    "plinko": plinko,

    "blackjack": blackjack,

}


# ============================================================
# GAME HELPERS
# ============================================================

def get_game(
    game_code: str,
):
    return GAMES.get(
        str(game_code).lower().strip()
    )


def get_games() -> List[str]:
    return list(
        GAMES.keys()
    )


def play(
    game_code: str,
    bet: int,
    **kwargs,
) -> Dict[str, Any]:

    game = get_game(
        game_code
    )

    if game is None:
        raise ValueError(
            f"Игра '{game_code}' не найдена"
        )

    return game(
        bet,
        **kwargs,
    )


# Алиас, если старый web.py
# вызывает play_game вместо play.
def play_game(
    game_code: str,
    bet: int,
    **kwargs,
) -> Dict[str, Any]:

    return play(
        game_code,
        bet,
        **kwargs,
    )


# ============================================================
# EXPORTS
# ============================================================

__all__ = [

    "dice",

    "darts",

    "bowling",

    "coinflip",

    "roulette",

    "slots",

    "highlow",

    "rps",

    "mines",

    "crash",

    "race",

    "football",

    "basketball",

    "plinko",

    "blackjack",

    "get_game",

    "get_games",

    "play",

    "play_game",

    "GAMES",

]