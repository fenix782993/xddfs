MINES_GAMES = {}
CRASH_GAMES = {}


def get_mines(user_id: int):
    return MINES_GAMES.get(user_id)


def set_mines(
    user_id: int,
    game: dict,
):
    MINES_GAMES[user_id] = game


def delete_mines(
    user_id: int,
):
    MINES_GAMES.pop(
        user_id,
        None
    )


def get_crash(user_id: int):
    return CRASH_GAMES.get(user_id)


def set_crash(
    user_id: int,
    game: dict,
):
    CRASH_GAMES[user_id] = game


def delete_crash(
    user_id: int,
):
    CRASH_GAMES.pop(
        user_id,
        None
    )