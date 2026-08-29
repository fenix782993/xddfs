from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from app.config import settings
from app.db import pool, balance


r = Router()


def is_admin(user_id: int):

    return settings.is_admin(
        user_id
    )


@r.message(F.text == "/admin")
async def admin(message: Message):

    if not is_admin(
        message.from_user.id
    ):

        await message.answer(
            "⛔ Доступ запрещён."
        )

        return

    users = await pool.fetchval(
        "SELECT COUNT(*) FROM users"
    )

    coins = await pool.fetchval(
        "SELECT COALESCE(SUM(balance), 0) FROM users"
    )

    await message.answer(
        (
            "🛡️ <b>FENIX ADMIN PANEL</b>\n\n"
            f"👥 Пользователей: <b>{users}</b>\n"
            f"🔥 В обороте: <b>{coins}</b>\n\n"
            "<b>Команды:</b>\n\n"
            "/stats\n"
            "/give USER_ID AMOUNT\n"
            "/take USER_ID AMOUNT\n"
            "/ban USER_ID\n"
            "/unban USER_ID\n"
            "/mission TITLE REWARD\n"
        )
    )


@r.message(F.text == "/stats")
async def stats(message: Message):

    if not is_admin(
        message.from_user.id
    ):
        return

    users = await pool.fetchval(
        "SELECT COUNT(*) FROM users"
    )

    games = await pool.fetchval(
        "SELECT COALESCE(SUM(games), 0) FROM users"
    )

    await message.answer(
        (
            "📊 <b>СТАТИСТИКА</b>\n\n"
            f"👥 Users: {users}\n"
            f"🎮 Games: {games}"
        )
    )


@r.message(F.text.startswith("/give "))
async def give(message: Message):

    if not is_admin(
        message.from_user.id
    ):
        return

    parts = message.text.split()

    if len(parts) != 3:
        await message.answer(
            "/give USER_ID AMOUNT"
        )
        return

    uid = int(parts[1])
    amount = int(parts[2])

    new_balance = await balance(
        uid,
        amount,
        "admin_give",
    )

    await message.answer(
        f"✅ Баланс: <b>{new_balance} 🔥</b>"
    )


@r.message(F.text.startswith("/take "))
async def take(message: Message):

    if not is_admin(
        message.from_user.id
    ):
        return

    parts = message.text.split()

    if len(parts) != 3:
        await message.answer(
            "/take USER_ID AMOUNT"
        )
        return

    uid = int(parts[1])
    amount = int(parts[2])

    try:

        new_balance = await balance(
            uid,
            -amount,
            "admin_take",
        )

    except ValueError:

        await message.answer(
            "❌ Недостаточно средств."
        )

        return

    await message.answer(
        f"✅ Баланс: <b>{new_balance} 🔥</b>"
    )


@r.message(F.text.startswith("/ban "))
async def ban(message: Message):

    if not is_admin(
        message.from_user.id
    ):
        return

    uid = int(
        message.text.split()[1]
    )

    await pool.execute(
        """
        UPDATE users
        SET banned = TRUE
        WHERE id = $1
        """,
        uid,
    )

    await message.answer(
        "🔨 Пользователь заблокирован."
    )


@r.message(F.text.startswith("/unban "))
async def unban(message: Message):

    if not is_admin(
        message.from_user.id
    ):
        return

    uid = int(
        message.text.split()[1]
    )

    await pool.execute(
        """
        UPDATE users
        SET banned = FALSE
        WHERE id = $1
        """,
        uid,
    )

    await message.answer(
        "✅ Пользователь разблокирован."
    )