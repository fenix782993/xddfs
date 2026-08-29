import asyncio
import logging

from aiogram import (
    Bot,
    Dispatcher,
    F,
)

from aiogram.filters import CommandStart

from aiogram.types import (
    Message,
    CallbackQuery,
)

from app.config import settings
from app.db import (
    init_db,
    close_db,
    ensure_user,
    get_user,
)

from app.keyboards.main import (
    main_menu,
    back_menu,
)

from app.keyboards.games import (
    games_menu,
    bet_menu,
)


logging.basicConfig(
    level=logging.INFO
)

bot = Bot(
    token=settings.bot_token
)

dp = Dispatcher()


# ============================================================
# START
# ============================================================

@dp.message(CommandStart())
async def start(
    message: Message,
):

    ref = None

    args = (
        message.text or ""
    ).split(maxsplit=1)

    if len(args) > 1:

        payload = args[1]

        if payload.startswith(
            "ref_"
        ):

            try:
                ref = int(
                    payload[4:]
                )
            except ValueError:
                ref = None

    user, created = await ensure_user(
        message.from_user,
        ref,
    )

    text = (
        "🔥 <b>FENIX COIN ULTRA</b>\n\n"

        "Добро пожаловать в игровую "
        "экономику Fenix Coin.\n\n"

        f"💰 Баланс: "
        f"<b>{user['balance']:,}</b> 🔥\n"

        f"⭐ Уровень: "
        f"<b>{user['level']}</b>\n"

        f"🏆 Побед: "
        f"<b>{user['wins']}</b>\n"

        f"👥 Рефералов: "
        f"<b>{user['referrals']}</b>\n\n"

        "Выбирай раздел ниже:"
    )

    await message.answer(
        text,
        reply_markup=main_menu(
            settings.webapp_url
        ),
        parse_mode="HTML",
    )


# ============================================================
# HOME
# ============================================================

@dp.callback_query(
    F.data == "home"
)
async def home(
    callback: CallbackQuery,
):

    user = await get_user(
        callback.from_user.id
    )

    if not user:
        await callback.answer(
            "Открой /start",
            show_alert=True,
        )
        return

    await callback.message.edit_text(
        (
            "🔥 <b>FENIX COIN</b>\n\n"
            f"💰 Баланс: <b>{user['balance']:,}</b> 🔥\n"
            f"⭐ Уровень: <b>{user['level']}</b>\n\n"
            "Выбирай действие:"
        ),
        reply_markup=main_menu(
            settings.webapp_url
        ),
        parse_mode="HTML",
    )

    await callback.answer()


# ============================================================
# PROFILE
# ============================================================

@dp.callback_query(
    F.data == "profile"
)
async def profile(
    callback: CallbackQuery,
):

    user = await get_user(
        callback.from_user.id
    )

    if not user:
        await callback.answer(
            "Пользователь не найден",
            show_alert=True,
        )
        return

    text = (
        "👤 <b>ТВОЙ ПРОФИЛЬ</b>\n\n"

        f"🆔 ID: <code>{user['id']}</code>\n"

        f"👤 Username: "
        f"@{user['username'] or 'нет'}\n\n"

        f"💰 Баланс: "
        f"<b>{user['balance']:,}</b> 🔥\n"

        f"⭐ XP: "
        f"<b>{user['xp']:,}</b>\n"

        f"🏅 Уровень: "
        f"<b>{user['level']}</b>\n\n"

        f"🎮 Игр: "
        f"<b>{user['games']}</b>\n"

        f"🏆 Побед: "
        f"<b>{user['wins']}</b>\n"

        f"💀 Поражений: "
        f"<b>{user['losses']}</b>\n\n"

        f"👥 Рефералов: "
        f"<b>{user['referrals']}</b>"
    )

    await callback.message.edit_text(
        text,
        reply_markup=back_menu(),
        parse_mode="HTML",
    )

    await callback.answer()


# ============================================================
# GAMES
# ============================================================

@dp.callback_query(
    F.data == "games"
)
async def games(
    callback: CallbackQuery,
):

    await callback.message.edit_text(
        (
            "🎮 <b>FENIX GAMES</b>\n\n"
            "Выбирай игру.\n\n"
            "💰 Все ставки проходят "
            "через Fenix Coin."
        ),
        reply_markup=games_menu(),
        parse_mode="HTML",
    )

    await callback.answer()


# ============================================================
# GAME
# ============================================================

@dp.callback_query(
    F.data.startswith("game:")
)
async def game(
    callback: CallbackQuery,
):

    game_code = (
        callback.data.split(":")[1]
    )

    names = {
        "dice": "🎲 DICE",
        "slots": "🎰 SLOTS",
        "mines": "💣 MINES",
        "crash": "📈 CRASH",
        "roulette": "🎡 ROULETTE",
        "football": "⚽ FOOTBALL",
        "basketball": "🏀 BASKETBALL",
        "darts": "🎯 DARTS",
        "bowling": "🎳 BOWLING",
    }

    title = names.get(
        game_code,
        "🎮 GAME"
    )

    await callback.message.edit_text(
        (
            f"<b>{title}</b>\n\n"

            "💰 Выбери размер ставки:\n\n"

            "⚠️ Правила:\n"
            "• ставка списывается перед игрой\n"
            "• результат определяется сервером\n"
            "• выигрыш возвращается автоматически\n"
            "• история сохраняется в базе"
        ),
        reply_markup=bet_menu(
            game_code
        ),
        parse_mode="HTML",
    )

    await callback.answer()


# ============================================================
# BET
# ============================================================

@dp.callback_query(
    F.data.startswith("bet:")
)
async def bet(
    callback: CallbackQuery,
):

    _, game_code, amount = (
        callback.data.split(":")
    )

    amount = int(amount)

    user = await get_user(
        callback.from_user.id
    )

    if not user:
        await callback.answer(
            "Пользователь не найден",
            show_alert=True,
        )
        return

    if amount > user["balance"]:

        await callback.answer(
            "❌ Недостаточно Fenix Coin",
            show_alert=True,
        )

        return

    await callback.answer(
        "🎮 Игра будет подключена следующим модулем.",
        show_alert=True,
    )


# ============================================================
# RUN
# ============================================================

async def start_bot():

    if not settings.bot_token:

        raise RuntimeError(
            "BOT_TOKEN is not configured"
        )

    await init_db()

    try:

        await dp.start_polling(
            bot
        )

    finally:

        await close_db()

        await bot.session.close()


if __name__ == "__main__":

    asyncio.run(
        start_bot()
    )
@dp.callback_query(
    F.data.startswith("bet:")
)
async def play_bet(
    callback: CallbackQuery,
):

    _, game_code, amount = (
        callback.data.split(":")
    )

    amount = int(amount)
    user_id = callback.from_user.id

    user = await get_user(
        user_id
    )

    if not user:
        await callback.answer(
            "❌ Пользователь не найден",
            show_alert=True,
        )
        return

    if amount <= 0:
        await callback.answer(
            "❌ Неверная ставка",
            show_alert=True,
        )
        return

    if amount > user["balance"]:
        await callback.answer(
            "❌ Недостаточно Fenix Coin",
            show_alert=True,
        )
        return

    # MINES запускается отдельно
    if game_code == "mines":

        await change_balance(
            user_id,
            -amount,
            "mines_bet",
            {"bet": amount},
        )

        board = mines.create_board(
            mines=5
        )

        board["bet"] = amount

        set_mines(
            user_id,
            board,
        )

        await callback.message.edit_text(
            (
                "💣 <b>MINES 5×5</b>\n\n"
                f"💰 Ставка: <b>{amount:,}</b> 🔥\n"
                "💎 Открывай безопасные клетки.\n"
                "💣 Мина уничтожит ставку.\n\n"
                "Чем больше открыл — тем выше множитель."
            ),
            reply_markup=mines_board(),
            parse_mode="HTML",
        )

        await callback.answer()
        return

    # DICE
    if game_code == "dice":

        await change_balance(
            user_id,
            -amount,
            "dice_bet",
            {"bet": amount},
        )

        result = await dice.play(
            user_id,
            amount,
        )

        if result["win"]:

            payout = int(
                amount *
                result["multiplier"]
            )

            await change_balance(
                user_id,
                payout,
                "dice_win",
                {
                    "bet": amount,
                    "roll": result["roll"],
                },
            )

        await add_game_result(
            user_id=user_id,
            game_code="dice",
            bet=amount,
            win=result["win"],
            profit=result["profit"],
            multiplier=result["multiplier"],
            data=result,
        )

        icon = (
            "🎉"
            if result["win"]
            else "💀"
        )

        await callback.message.edit_text(
            (
                f"{icon} <b>DICE</b>\n\n"
                f"🎲 Выпало: "
                f"<b>{result['roll']}</b>\n\n"
                f"💰 Ставка: "
                f"<b>{amount:,}</b> 🔥\n"
                f"📈 Множитель: "
                f"<b>{result['multiplier']}x</b>\n\n"
                f"{'🏆 Победа!' if result['win'] else '💀 Проигрыш'}"
            ),
            reply_markup=bet_menu("dice"),
            parse_mode="HTML",
        )

        await callback.answer()
        return

    # SLOTS
    if game_code == "slots":

        await change_balance(
            user_id,
            -amount,
            "slots_bet",
            {"bet": amount},
        )

        result = await slots.play(
            user_id,
            amount,
        )

        if result["win"]:

            payout = int(
                amount *
                result["multiplier"]
            )

            await change_balance(
                user_id,
                payout,
                "slots_win",
                {
                    "bet": amount,
                    "symbols": result["symbols"],
                },
            )

        await add_game_result(
            user_id=user_id,
            game_code="slots",
            bet=amount,
            win=result["win"],
            profit=result["profit"],
            multiplier=result["multiplier"],
            data=result,
        )

        await callback.message.edit_text(
            (
                "🎰 <b>SLOTS</b>\n\n"
                f"{' | '.join(result['symbols'])}\n\n"
                f"💰 Ставка: "
                f"<b>{amount:,}</b> 🔥\n"
                f"📈 Множитель: "
                f"<b>{result['multiplier']}x</b>\n\n"
                f"{'🎉 ПОБЕДА' if result['win'] else '💀 ПРОИГРЫШ'}"
            ),
            reply_markup=bet_menu("slots"),
            parse_mode="HTML",
        )

        await callback.answer()
        return

    await callback.answer(
        "🎮 Эта игра подключается следующим модулем.",
        show_alert=True,
    )