# ============================================================
# FENIX COIN ULTRA
# GAME ENGINE
# ============================================================

from __future__ import annotations

import random
import secrets
from typing import Any, Dict, List, Optional

from app.db import play_game, get_game


# ============================================================
# HELPERS
# ============================================================

def _safe_bet(bet: int) -> int:
    bet = int(bet)

    if bet <= 0:
        raise ValueError("Ставка должна быть больше 0")

    return bet


def _money(value: Any) -> int:
    return int(value or 0)


def _result(
    game: str,
    bet: int,
    win: int,
    multiplier: Optional[float],
    data: Dict[str, Any],
) -> Dict[str, Any]:

    return {
        "game": game,
        "bet": bet,
        "win_amount": win,
        "multiplier": multiplier,
        "result": data,
    }


# ============================================================
# DICE
# Telegram dice style: 1..6
# ============================================================

async def play_dice(user_id: int, bet: int) -> Dict[str, Any]:

    bet = _safe_bet(bet)

    value = random.randint(1, 6)

    multipliers = {
        1: 0.0,
        2: 0.0,
        3: 0.0,
        4: 1.5,
        5: 2.0,
        6: 3.0,
    }

    multiplier = multipliers[value]
    win = int(bet * multiplier)

    result = await play_game(
        user_id=user_id,
        game_code="dice",
        bet=bet,
        win=win,
        multiplier=multiplier,
        result_data={
            "value": value,
            "type": "dice",
        },
    )

    return {
        **result,
        "value": value,
        "multiplier": multiplier,
    }


# ============================================================
# DARTS
# Telegram darts style: 1..6
# ============================================================

async def play_darts(user_id: int, bet: int) -> Dict[str, Any]:

    bet = _safe_bet(bet)

    value = random.randint(1, 6)

    multipliers = {
        1: 0.0,
        2: 0.0,
        3: 1.5,
        4: 2.0,
        5: 3.0,
        6: 5.0,
    }

    multiplier = multipliers[value]
    win = int(bet * multiplier)

    result = await play_game(
        user_id,
        "darts",
        bet,
        win,
        multiplier,
        {
            "value": value,
            "type": "darts",
        },
    )

    return {
        **result,
        "value": value,
        "multiplier": multiplier,
    }


# ============================================================
# FOOTBALL
# Telegram football style
# ============================================================

async def play_football(user_id: int, bet: int) -> Dict[str, Any]:

    bet = _safe_bet(bet)

    value = random.randint(1, 5)

    multipliers = {
        1: 0.0,
        2: 0.0,
        3: 1.5,
        4: 2.5,
        5: 4.0,
    }

    multiplier = multipliers[value]
    win = int(bet * multiplier)

    result = await play_game(
        user_id,
        "football",
        bet,
        win,
        multiplier,
        {
            "value": value,
            "type": "football",
        },
    )

    return {
        **result,
        "value": value,
        "multiplier": multiplier,
    }


# ============================================================
# BASKETBALL
# ============================================================

async def play_basketball(user_id: int, bet: int) -> Dict[str, Any]:

    bet = _safe_bet(bet)

    value = random.randint(1, 5)

    multipliers = {
        1: 0.0,
        2: 0.0,
        3: 1.5,
        4: 2.5,
        5: 4.0,
    }

    multiplier = multipliers[value]
    win = int(bet * multiplier)

    result = await play_game(
        user_id,
        "basketball",
        bet,
        win,
        multiplier,
        {
            "value": value,
            "type": "basketball",
        },
    )

    return {
        **result,
        "value": value,
        "multiplier": multiplier,
    }


# ============================================================
# BOWLING
# ============================================================

async def play_bowling(user_id: int, bet: int) -> Dict[str, Any]:

    bet = _safe_bet(bet)

    value = random.randint(1, 6)

    multipliers = {
        1: 0.0,
        2: 0.0,
        3: 1.25,
        4: 1.75,
        5: 2.5,
        6: 5.0,
    }

    multiplier = multipliers[value]
    win = int(bet * multiplier)

    result = await play_game(
        user_id,
        "bowling",
        bet,
        win,
        multiplier,
        {
            "value": value,
            "type": "bowling",
        },
    )

    return {
        **result,
        "value": value,
        "multiplier": multiplier,
    }


# ============================================================
# SLOTS
# ============================================================

SLOT_SYMBOLS = [
    "🍒",
    "🍋",
    "🍊",
    "🍇",
    "🔔",
    "⭐",
    "💎",
    "🔥",
]


def _slots_spin() -> List[str]:

    return [
        random.choice(SLOT_SYMBOLS),
        random.choice(SLOT_SYMBOLS),
        random.choice(SLOT_SYMBOLS),
    ]


def _slots_multiplier(symbols: List[str]) -> float:

    a, b, c = symbols

    if a == b == c == "💎":
        return 20.0

    if a == b == c == "🔥":
        return 15.0

    if a == b == c == "⭐":
        return 10.0

    if a == b == c:
        return 8.0

    if a == b or a == c or b == c:
        return 2.0

    return 0.0


async def play_slots(user_id: int, bet: int) -> Dict[str, Any]:

    bet = _safe_bet(bet)

    symbols = _slots_spin()

    multiplier = _slots_multiplier(symbols)

    win = int(bet * multiplier)

    result = await play_game(
        user_id,
        "slots",
        bet,
        win,
        multiplier,
        {
            "symbols": symbols,
            "type": "slots",
        },
    )

    return {
        **result,
        "symbols": symbols,
        "multiplier": multiplier,
    }


# ============================================================
# ROULETTE
# ============================================================

ROULETTE_RED = {
    1, 3, 5, 7, 9,
    12, 14, 16, 18,
    19, 21, 23, 25,
    27, 30, 32, 34, 36,
}


async def play_roulette(
    user_id: int,
    bet: int,
    choice: str,
) -> Dict[str, Any]:

    bet = _safe_bet(bet)

    choice = str(choice).lower().strip()

    if choice not in {
        "red",
        "black",
        "green",
        "odd",
        "even",
    }:
        raise ValueError("Неверная ставка рулетки")

    number = random.randint(0, 36)

    if number == 0:
        color = "green"
    elif number in ROULETTE_RED:
        color = "red"
    else:
        color = "black"

    win = 0
    multiplier = 0.0

    if choice == color:

        if choice == "green":
            multiplier = 14.0
        else:
            multiplier = 2.0

    elif choice == "odd" and number != 0 and number % 2 == 1:
        multiplier = 2.0

    elif choice == "even" and number != 0 and number % 2 == 0:
        multiplier = 2.0

    win = int(bet * multiplier)

    result = await play_game(
        user_id,
        "roulette",
        bet,
        win,
        multiplier,
        {
            "number": number,
            "color": color,
            "choice": choice,
        },
    )

    return {
        **result,
        "number": number,
        "color": color,
        "choice": choice,
        "multiplier": multiplier,
    }


# ============================================================
# CRASH
# ============================================================

def _crash_multiplier() -> float:

    # house edge ~5%
    value = random.random()

    if value < 0.03:
        return 1.0

    multiplier = 1.0 / max(0.01, (1.0 - value))

    multiplier *= 0.95

    return max(
        1.0,
        round(min(multiplier, 100.0), 2),
    )


async def play_crash(
    user_id: int,
    bet: int,
    cashout: Optional[float] = None,
) -> Dict[str, Any]:

    bet = _safe_bet(bet)

    crash_at = _crash_multiplier()

    if cashout is None:
        cashout = crash_at

    cashout = float(cashout)

    if cashout < 1.0:
        raise ValueError("Cashout должен быть >= 1.0")

    if cashout <= crash_at:

        multiplier = cashout
        win = int(bet * multiplier)

        status = "cashed_out"

    else:

        multiplier = 0.0
        win = 0

        status = "crashed"

    result = await play_game(
        user_id,
        "crash",
        bet,
        win,
        multiplier,
        {
            "crash_at": crash_at,
            "cashout": cashout,
            "status": status,
        },
    )

    return {
        **result,
        "crash_at": crash_at,
        "cashout": cashout,
        "status": status,
    }


# ============================================================
# MINES 5x5
# ============================================================

MINES_SIZE = 5
MINES_CELLS = 25


def _mine_positions(count: int) -> List[int]:

    if count < 1:
        count = 1

    if count > 24:
        count = 24

    return secrets.SystemRandom().sample(
        range(MINES_CELLS),
        count,
    )


def create_mines_board(
    mines: int = 5,
) -> Dict[str, Any]:

    positions = _mine_positions(mines)

    return {
        "size": 5,
        "mines": mines,
        "mine_positions": positions,
        "opened": [],
    }


def mines_multiplier(
    opened: int,
    mines: int,
) -> float:

    safe_cells = MINES_CELLS - mines

    if opened <= 0:
        return 1.0

    if opened >= safe_cells:
        return 24.0

    multiplier = 1.0

    for i in range(opened):
        multiplier *= (
            MINES_CELLS - mines - i
        ) / (
            MINES_CELLS - i
        )

    if multiplier <= 0:
        return 1.0

    return round(
        0.96 / multiplier,
        2,
    )


async def play_mines(
    user_id: int,
    bet: int,
    mines: int = 5,
    opened: Optional[List[int]] = None,
) -> Dict[str, Any]:

    bet = _safe_bet(bet)

    mines = int(mines)

    if mines < 1 or mines > 24:
        raise ValueError(
            "Количество мин должно быть от 1 до 24"
        )

    opened = opened or []

    for cell in opened:

        if int(cell) < 0 or int(cell) >= 25:
            raise ValueError(
                "Клетка должна быть от 0 до 24"
            )

    board = create_mines_board(mines)

    mine_positions = set(
        board["mine_positions"]
    )

    opened_set = set(
        int(x) for x in opened
    )

    hit_mine = bool(
        opened_set & mine_positions
    )

    if hit_mine:

        multiplier = 0.0
        win = 0

    else:

        multiplier = mines_multiplier(
            len(opened_set),
            mines,
        )

        win = int(
            bet * multiplier
        )

    result = await play_game(
        user_id,
        "mines",
        bet,
        win,
        multiplier,
        {
            "mines": mines,
            "opened": list(opened_set),
            "mine_positions": list(
                mine_positions
            ),
            "hit_mine": hit_mine,
        },
    )

    return {
        **result,
        "mines": mines,
        "opened": list(opened_set),
        "mine_positions": list(
            mine_positions
        ),
        "hit_mine": hit_mine,
    }


# ============================================================
# HIGH / LOW
# ============================================================

async def play_high_low(
    user_id: int,
    bet: int,
    choice: str,
) -> Dict[str, Any]:

    bet = _safe_bet(bet)

    choice = choice.lower().strip()

    if choice not in {
        "high",
        "low",
    }:
        raise ValueError(
            "choice должен быть high или low"
        )

    value = random.randint(1, 100)

    if choice == "high":
        success = value >= 51
    else:
        success = value <= 50

    multiplier = 1.9 if success else 0.0

    win = int(
        bet * multiplier
    )

    result = await play_game(
        user_id,
        "high_low",
        bet,
        win,
        multiplier,
        {
            "value": value,
            "choice": choice,
        },
    )

    return {
        **result,
        "value": value,
        "choice": choice,
    }


# ============================================================
# COIN FLIP
# ============================================================

async def play_coinflip(
    user_id: int,
    bet: int,
    choice: str,
) -> Dict[str, Any]:

    bet = _safe_bet(bet)

    choice = choice.lower().strip()

    if choice not in {
        "heads",
        "tails",
    }:
        raise ValueError(
            "choice должен быть heads или tails"
        )

    result_value = random.choice(
        ["heads", "tails"]
    )

    success = result_value == choice

    multiplier = 1.9 if success else 0.0

    win = int(
        bet * multiplier
    )

    result = await play_game(
        user_id,
        "coinflip",
        bet,
        win,
        multiplier,
        {
            "choice": choice,
            "result": result_value,
        },
    )

    return {
        **result,
        "choice": choice,
        "result_value": result_value,
    }


# ============================================================
# ROCK PAPER SCISSORS
# ============================================================

RPS = {
    "rock",
    "paper",
    "scissors",
}


def _rps_winner(
    player: str,
    enemy: str,
) -> str:

    if player == enemy:
        return "draw"

    wins = {
        ("rock", "scissors"),
        ("scissors", "paper"),
        ("paper", "rock"),
    }

    if (player, enemy) in wins:
        return "player"

    return "enemy"


async def play_rps(
    user_id: int,
    bet: int,
    choice: str,
) -> Dict[str, Any]:

    bet = _safe_bet(bet)

    choice = choice.lower().strip()

    if choice not in RPS:
        raise ValueError(
            "Неверный вариант"
        )

    enemy = random.choice(
        list(RPS)
    )

    winner = _rps_winner(
        choice,
        enemy,
    )

    if winner == "player":
        multiplier = 1.9
        win = int(
            bet * multiplier
        )

    elif winner == "draw":
        multiplier = 1.0
        win = bet

    else:
        multiplier = 0.0
        win = 0

    result = await play_game(
        user_id,
        "rps",
        bet,
        win,
        multiplier,
        {
            "player": choice,
            "enemy": enemy,
            "winner": winner,
        },
    )

    return {
        **result,
        "player": choice,
        "enemy": enemy,
        "winner": winner,
    }


# ============================================================
# COLOR
# ============================================================

COLORS = [
    "red",
    "black",
    "blue",
    "green",
    "yellow",
]


async def play_color(
    user_id: int,
    bet: int,
    choice: str,
) -> Dict[str, Any]:

    bet = _safe_bet(bet)

    choice = choice.lower().strip()

    if choice not in COLORS:
        raise ValueError(
            "Неверный цвет"
        )

    result_color = random.choice(
        COLORS
    )

    if result_color == choice:

        multiplier = 4.0

        win = int(
            bet * multiplier
        )

    else:

        multiplier = 0.0

        win = 0

    result = await play_game(
        user_id,
        "color",
        bet,
        win,
        multiplier,
        {
            "choice": choice,
            "result": result_color,
        },
    )

    return {
        **result,
        "choice": choice,
        "result_color": result_color,
    }


# ============================================================
# GAME ROUTER
# ============================================================

GAME_HANDLERS = {
    "dice": play_dice,
    "darts": play_darts,
    "football": play_football,
    "basketball": play_basketball,
    "bowling": play_bowling,
    "slots": play_slots,
    "crash": play_crash,
    "mines": play_mines,
    "roulette": play_roulette,
    "high_low": play_high_low,
    "coinflip": play_coinflip,
    "rps": play_rps,
    "color": play_color,
}


async def play(
    user_id: int,
    game_code: str,
    bet: int,
    **kwargs,
) -> Dict[str, Any]:

    game_code = str(
        game_code
    ).lower().strip()

    handler = GAME_HANDLERS.get(
        game_code
    )

    if handler is None:
        raise ValueError(
            f"Игра '{game_code}' не найдена"
        )

    game = await get_game(
        game_code
    )

    if not game:
        raise ValueError(
            f"Игра '{game_code}' не зарегистрирована в БД"
        )

    if not game["enabled"]:
        raise ValueError(
            "Игра временно отключена"
        )

    bet = _safe_bet(bet)

    if bet < int(game["min_bet"]):
        raise ValueError(
            f"Минимальная ставка: {game['min_bet']}"
        )

    if bet > int(game["max_bet"]):
        raise ValueError(
            f"Максимальная ставка: {game['max_bet']}"
        )

    return await handler(
        user_id,
        bet,
        **kwargs,
    )


# ============================================================
# GAME LIST
# ============================================================

async def available_games() -> List[Dict[str, Any]]:

    from app.db import get_games

    rows = await get_games()

    return [
        dict(row)
        for row in rows
    ]


# ============================================================
# GAME INFO
# ============================================================

GAME_RULES = {

    "dice": {
        "title": "🎲 Dice",
        "rules": "Бросок кости 1–6. Чем выше результат, тем выше множитель.",
    },

    "darts": {
        "title": "🎯 Darts",
        "rules": "Бросок дротика. Попадание в более высокий сектор увеличивает множитель.",
    },

    "football": {
        "title": "⚽ Football",
        "rules": "Удар по воротам. Удачный удар приносит множитель ставки.",
    },

    "basketball": {
        "title": "🏀 Basketball",
        "rules": "Бросок в кольцо. Чем лучше результат, тем выше награда.",
    },

    "bowling": {
        "title": "🎳 Bowling",
        "rules": "Бросок шара. Максимальный результат даёт максимальный множитель.",
    },

    "slots": {
        "title": "🎰 Slots",
        "rules": "Собери одинаковые символы. Три одинаковых символа дают большой множитель.",
    },

    "mines": {
        "title": "💣 Mines",
        "rules": "Открывай клетки 5×5 и избегай мин. Чем больше безопасных клеток открыл — тем выше множитель.",
    },

    "crash": {
        "title": "📈 Crash",
        "rules": "Множитель растёт. Забери выигрыш до того, как произойдёт crash.",
    },

    "roulette": {
        "title": "🎡 Roulette",
        "rules": "Выбирай цвет или чётность числа. Выплата зависит от выбранного исхода.",
    },

    "high_low": {
        "title": "⬆️ High / Low",
        "rules": "Выбери высокий или низкий результат.",
    },

    "coinflip": {
        "title": "🪙 Coin Flip",
        "rules": "Выбери орёл или решку.",
    },

    "rps": {
        "title": "✊ RPS",
        "rules": "Камень, ножницы, бумага против бота.",
    },

    "color": {
        "title": "🌈 Color",
        "rules": "Выбери цвет. Совпадение приносит выигрыш.",
    },
}


def get_game_rules(
    game_code: str,
) -> Dict[str, Any]:

    return GAME_RULES.get(
        game_code,
        {
            "title": game_code,
            "rules": "Правила игры отсутствуют.",
        },
    )