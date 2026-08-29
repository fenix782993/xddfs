from aiogram import Router, F
from aiogram.types import CallbackQuery

from app.db import pool, balance
from app.keyboards import back


r = Router()


@r.callback_query(F.data == "missions")
async def missions(callback: CallbackQuery):

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

    text = "🎯 <b>АКТИВНЫЕ МИССИИ</b>\n\n"

    if not rows:

        text += "Миссий пока нет."

    else:

        for row in rows:

            text += (
                f"🔥 <b>{row['title']}</b>\n"
                f"💰 +{row['reward']} 🔥\n"
                f"📌 {row['kind']}\n\n"
            )

    await callback.message.edit_text(
        text,
        reply_markup=back(),
    )

    await callback.answer()