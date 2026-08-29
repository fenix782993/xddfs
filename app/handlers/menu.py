from aiogram import Router, F
from aiogram.types import CallbackQuery

from app.db import get_user
from app.keyboards import (
    main_menu,
    games_menu,
    pvp_menu,
    back,
)
from app.config import settings


r = Router()


@r.callback_query(F.data == "games")
async def games(callback: CallbackQuery):

    await callback.message.edit_text(
        (
            "🎮 <b>FENIX GAMES</b>\n\n"
            "Выбери игру:"
        ),
        reply_markup=games_menu(),
    )

    await callback.answer()


@r.callback_query(F.data == "profile")
async def profile(callback: CallbackQuery):

    user = await get_user(
        callback.from_user.id
    )

    if not user:
        await callback.answer(
            "Сначала нажми /start",
            show_alert=True,
        )
        return

    await callback.message.edit_text(
        (
            "👤 <b>ТВОЙ ПРОФИЛЬ</b>\n\n"
            f"🆔 ID: <code>{user['id']}</code>\n"
            f"👤 Имя: {user['first_name'] or '-'}\n"
            f"💰 Баланс: <b>{user['balance']} 🔥</b>\n"
            f"⭐ XP: <b>{user['xp']}</b>\n"
            f"🏅 Уровень: <b>{user['level']}</b>\n\n"
            f"🎮 Игр: {user['games']}\n"
            f"🏆 Побед: {user['wins']}\n"
            f"💀 Поражений: {user['losses']}\n"
            f"👥 Рефералов: {user['referrals']}"
        ),
        reply_markup=back(),
    )

    await callback.answer()


@r.callback_query(F.data == "referrals")
async def referrals(callback: CallbackQuery):

    username = settings.bot_username

    if username:

        link = (
            f"https://t.me/{username}"
            f"?start=ref_{callback.from_user.id}"
        )

    else:

        link = "BOT_USERNAME не настроен"

    user = await get_user(
        callback.from_user.id
    )

    referrals_count = (
        user["referrals"]
        if user
        else 0
    )

    await callback.message.edit_text(
        (
            "👥 <b>РЕФЕРАЛЬНАЯ СИСТЕМА</b>\n\n"
            f"💰 За каждого реферала: "
            f"<b>{settings.ref_reward} 🔥</b>\n\n"
            f"👥 Приглашено: <b>{referrals_count}</b>\n\n"
            "🔗 Твоя ссылка:\n"
            f"<code>{link}</code>"
        ),
        reply_markup=back(),
    )

    await callback.answer()


@r.callback_query(F.data == "leaderboard")
async def leaderboard(callback: CallbackQuery):

    from app.db import pool

    rows = await pool.fetch(
        """
        SELECT
            username,
            first_name,
            balance
        FROM users
        WHERE banned = FALSE
        ORDER BY balance DESC
        LIMIT 10
        """
    )

    text = "🏆 <b>ТОП FENIX COIN</b>\n\n"

    for index, row in enumerate(rows, 1):

        name = (
            row["username"]
            or row["first_name"]
            or "Игрок"
        )

        text += (
            f"<b>{index}.</b> "
            f"{name} — "
            f"<b>{row['balance']} 🔥</b>\n"
        )

    await callback.message.edit_text(
        text,
        reply_markup=back(),
    )

    await callback.answer()


@r.callback_query(F.data == "pvp")
async def pvp(callback: CallbackQuery):

    await callback.message.edit_text(
        (
            "⚔️ <b>PVP ARENA</b>\n\n"
            "Играй против реальных игроков.\n\n"
            "💰 Ставка блокируется при создании боя.\n"
            "🏆 Победитель получает банк.\n"
            "⚡ Матч создаётся в реальном времени."
        ),
        reply_markup=pvp_menu(),
    )

    await callback.answer()


@r.callback_query(F.data == "pve")
async def pve(callback: CallbackQuery):

    await callback.message.edit_text(
        (
            "🤖 <b>PVE ARENA</b>\n\n"
            "Сражайся против противников AI.\n\n"
            "🟢 Easy\n"
            "🟡 Normal\n"
            "🔴 Hard\n"
            "🔥 Boss"
        ),
        reply_markup=back(),
    )

    await callback.answer()


@r.callback_query(F.data == "missions")
async def missions(callback: CallbackQuery):

    from app.db import pool

    rows = await pool.fetch(
        """
        SELECT
            id,
            title,
            reward,
            kind,
            target
        FROM missions
        WHERE active = TRUE
        ORDER BY id DESC
        """
    )

    text = "🎯 <b>МИССИИ</b>\n\n"

    if not rows:

        text += "Пока активных миссий нет."

    else:

        for row in rows:

            text += (
                f"🔥 <b>{row['title']}</b>\n"
                f"💰 Награда: {row['reward']} 🔥\n"
                f"📌 Тип: {row['kind']}\n\n"
            )

    await callback.message.edit_text(
        text,
        reply_markup=back(),
    )

    await callback.answer()


@r.callback_query(F.data == "bonus")
async def bonus(callback: CallbackQuery):

    await callback.answer(
        "🎁 Система бонусов будет доступна после настройки ежедневного бонуса.",
        show_alert=True,
    )