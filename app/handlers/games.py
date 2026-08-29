import random

from aiogram import Router, F
from aiogram.types import CallbackQuery

from app.db import balance, result
from app.keyboards import games_menu, back


r = Router()


GAME_EMOJI = {
    "dice": "🎲",
    "darts": "🎯",
    "football": "⚽",
    "basketball": "🏀",
    "bowling": "🎳",
    "slots": "🎰",
}


async def play_game(
    callback: CallbackQuery,
    game: str,
):

    emoji = GAME_EMOJI[game]

    await callback.message.edit_text(
        (
            f"{emoji} <b>{game.upper()}</b>\n\n"
            "Введите ставку командой:\n\n"
            f"<code>/bet {game} 100</code>"
        ),
        reply_markup=games_menu(),
    )

    await callback.answer()


@r.callback_query(F.data.startswith("game_"))
async def game(callback: CallbackQuery):

    game_name = callback.data.replace(
        "game_",
        "",
        1,
    )

    if game_name not in GAME_EMOJI:

        await callback.answer(
            "Игра ещё не подключена.",
            show_alert=True,
        )

        return

    await play_game(
        callback,
        game_name,
    )


@r.message(F.text.startswith("/bet "))
async def bet(message):

    parts = message.text.split()

    if len(parts) != 3:

        await message.answer(
            "Использование:\n"
            "<code>/bet dice 100</code>"
        )

        return

    game = parts[1].lower()

    try:
        amount = int(parts[2])
    except ValueError:

        await message.answer(
            "Ставка должна быть числом."
        )

        return

    if game not in GAME_EMOJI:

        await message.answer(
            "Неизвестная игра."
        )

        return

    if amount <= 0:

        await message.answer(
            "Ставка должна быть больше 0."
        )

        return

    # списываем ставку
    try:

        await balance(
            message.from_user.id,
            -amount,
            f"bet:{game}",
        )

    except ValueError as error:

        if str(error) == "insufficient_funds":

            await message.answer(
                "❌ Недостаточно Fenix Coin."
            )

        else:

            await message.answer(
                "❌ Не удалось сделать ставку."
            )

        return

    # Telegram animation
    dice = await message.answer_dice(
        emoji=GAME_EMOJI[game]
    )

    value = dice.dice.value

    # базовая механика
    win = value >= 4

    if win:

        multiplier = 1.8

        reward = int(
            amount * multiplier
        )

        await balance(
            message.from_user.id,
            reward,
            f"win:{game}",
        )

        await result(
            message.from_user.id,
            True,
        )

        await message.answer(
            (
                "🔥 <b>ПОБЕДА!</b>\n\n"
                f"{GAME_EMOJI[game]} "
                f"Результат: <b>{value}</b>\n"
                f"💰 Выигрыш: <b>+{reward} 🔥</b>"
            )
        )

    else:

        await result(
            message.from_user.id,
            False,
        )

        await message.answer(
            (
                "💀 <b>ПРОИГРЫШ</b>\n\n"
                f"{GAME_EMOJI[game]} "
                f"Результат: <b>{value}</b>\n"
                f"💸 Потеряно: <b>{amount} 🔥</b>"
            )
        )