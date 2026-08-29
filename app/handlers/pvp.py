from aiogram import Router, F
from aiogram.types import CallbackQuery, Message

from app.db import pool, balance
from app.keyboards import pvp_menu, back


r = Router()


@r.callback_query(F.data == "pvp_create")
async def pvp_create(callback: CallbackQuery):

    await callback.message.edit_text(
        (
            "⚔️ <b>СОЗДАНИЕ PVP БОЯ</b>\n\n"
            "Создай комнату командой:\n\n"
            "<code>/pvp 500</code>\n\n"
            "После этого другой игрок сможет "
            "присоединиться к бою."
        ),
        reply_markup=pvp_menu(),
    )

    await callback.answer()


@r.message(F.text.startswith("/pvp "))
async def create_match(message: Message):

    parts = message.text.split()

    if len(parts) != 2:

        await message.answer(
            "Пример:\n<code>/pvp 500</code>"
        )

        return

    try:
        stake = int(parts[1])
    except ValueError:

        await message.answer(
            "Ставка должна быть числом."
        )

        return

    if stake <= 0:

        await message.answer(
            "Ставка должна быть больше 0."
        )

        return

    try:

        await balance(
            message.from_user.id,
            -stake,
            "pvp_lock",
        )

    except ValueError:

        await message.answer(
            "❌ Недостаточно Fenix Coin."
        )

        return

    match = await pool.fetchrow(
        """
        INSERT INTO pvp_matches (
            creator_id,
            stake,
            status
        )

        VALUES (
            $1,
            $2,
            'open'
        )

        RETURNING id
        """,

        message.from_user.id,
        stake,
    )

    await message.answer(
        (
            "⚔️ <b>PVP БОЙ СОЗДАН</b>\n\n"
            f"🆔 Бой: <code>#{match['id']}</code>\n"
            f"💰 Ставка: <b>{stake} 🔥</b>\n\n"
            "Другой игрок может присоединиться:\n"
            f"<code>/join {match['id']}</code>"
        )
    )


@r.callback_query(F.data == "pvp_find")
async def pvp_find(callback: CallbackQuery):

    match = await pool.fetchrow(
        """
        SELECT
            p.id,
            p.stake,
            p.creator_id,
            u.username,
            u.first_name

        FROM pvp_matches p

        LEFT JOIN users u
            ON u.id = p.creator_id

        WHERE p.status = 'open'
          AND p.creator_id != $1

        ORDER BY p.created_at ASC

        LIMIT 1
        """,

        callback.from_user.id,
    )

    if not match:

        await callback.message.edit_text(
            (
                "🔎 <b>ПОИСК БОЯ</b>\n\n"
                "Свободных PvP комнат сейчас нет.\n\n"
                "Создай свою:"
            ),
            reply_markup=pvp_menu(),
        )

        await callback.answer()

        return

    await callback.message.edit_text(
        (
            "⚔️ <b>НАЙДЕН БОЙ</b>\n\n"
            f"🆔 #{match['id']}\n"
            f"💰 Ставка: <b>{match['stake']} 🔥</b>\n"
            f"👤 Создатель: "
            f"{match['username'] or match['first_name'] or 'Игрок'}\n\n"
            f"Чтобы войти:\n"
            f"<code>/join {match['id']}</code>"
        ),
        reply_markup=back(),
    )

    await callback.answer()


@r.message(F.text.startswith("/join "))
async def join_match(message: Message):

    parts = message.text.split()

    if len(parts) != 2:

        return

    try:
        match_id = int(parts[1])
    except ValueError:

        return

    match = await pool.fetchrow(
        """
        SELECT *
        FROM pvp_matches
        WHERE id = $1
          AND status = 'open'
        FOR UPDATE
        """,
        match_id,
    )

    if not match:

        await message.answer(
            "❌ Бой не найден или уже занят."
        )

        return

    if match["creator_id"] == message.from_user.id:

        await message.answer(
            "❌ Нельзя присоединиться к своему бою."
        )

        return

    stake = match["stake"]

    try:

        await balance(
            message.from_user.id,
            -stake,
            "pvp_lock",
        )

    except ValueError:

        await message.answer(
            "❌ Недостаточно Fenix Coin."
        )

        return

    await pool.execute(
        """
        UPDATE pvp_matches

        SET
            opponent_id = $2,
            status = 'active'

        WHERE id = $1
        """,

        match_id,
        message.from_user.id,
    )

    await message.answer(
        (
            "⚔️ <b>ТЫ ВОШЁЛ В БОЙ!</b>\n\n"
            f"Бой: <b>#{match_id}</b>\n"
            f"Банк: <b>{stake * 2} 🔥</b>\n\n"
            "🔥 PvP матч активирован."
        )
    )

    try:

        await message.bot.send_message(
            match["creator_id"],
            (
                "⚔️ <b>СОПЕРНИК НАЙДЕН!</b>\n\n"
                f"Бой #{match_id} начался.\n"
                f"Банк: <b>{stake * 2} 🔥</b>"
            ),
        )

    except Exception:
        pass


@r.callback_query(F.data == "pvp_my")
async def my_matches(callback: CallbackQuery):

    rows = await pool.fetch(
        """
        SELECT
            id,
            stake,
            status,
            created_at

        FROM pvp_matches

        WHERE creator_id = $1
           OR opponent_id = $1

        ORDER BY id DESC

        LIMIT 10
        """,

        callback.from_user.id,
    )

    text = "⚔️ <b>МОИ БОИ</b>\n\n"

    if not rows:

        text += "Боёв пока нет."

    else:

        for row in rows:

            text += (
                f"#{row['id']} — "
                f"{row['stake']} 🔥 — "
                f"<b>{row['status']}</b>\n"
            )

    await callback.message.edit_text(
        text,
        reply_markup=pvp_menu(),
    )

    await callback.answer()