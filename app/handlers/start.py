from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from app.db import ensure_user
from app.keyboards import main_menu
from app.config import settings


r = Router()


@r.message(CommandStart())
async def start(message: Message):

    ref = None

    args = message.text.split(maxsplit=1)

    if len(args) == 2:

        value = args[1]

        if value.startswith("ref_"):

            raw = value.replace(
                "ref_",
                "",
                1,
            )

            if raw.isdigit():
                ref = int(raw)

    user, created = await ensure_user(
        message.from_user,
        ref,
    )

    if created and ref:

        if ref != message.from_user.id:

            try:
                await message.bot.send_message(
                    ref,
                    (
                        "🔥 <b>Новый реферал!</b>\n\n"
                        f"Ты получил <b>{settings.ref_reward} 🔥</b> "
                        "Fenix Coin."
                    ),
                )
            except Exception:
                pass

    await message.answer(
        (
            "🔥 <b>FENIX COIN</b>\n\n"
            "Добро пожаловать в игровую систему.\n\n"
            f"💰 Баланс: <b>{user['balance']} 🔥</b>\n"
            f"⭐ Уровень: <b>{user['level']}</b>\n\n"
            "Выбирай раздел:"
        ),
        reply_markup=main_menu(),
    )


@r.callback_query(F.data == "home")
async def home(callback: CallbackQuery):

    user, _ = await ensure_user(
        callback.from_user
    )

    await callback.message.edit_text(
        (
            "🔥 <b>FENIX COIN</b>\n\n"
            f"💰 Баланс: <b>{user['balance']} 🔥</b>\n"
            f"⭐ Уровень: <b>{user['level']}</b>\n\n"
            "Главное меню:"
        ),
        reply_markup=main_menu(),
    )

    await callback.answer()