from aiogram import Router,F
from aiogram.filters import CommandStart
from aiogram.types import Message,CallbackQuery
from app.db import ensure_user
from app.economy import referral
from app.keyboards import main
from app.ui import visual
r=Router()
@r.message(CommandStart())
async def start(m:Message):
    a=m.text.split(maxsplit=1)[1] if len(m.text.split())>1 else ""
    ref=int(a[3:]) if a.startswith("ref") and a[3:].isdigit() else None
    _,created=await ensure_user(m.from_user,ref)
    if created: await referral(m.from_user.id)
    await m.answer_photo(visual("FENIX COIN","🔥 Игровая платформа\\n🎮 Games • ⚔️ PvP • 🤖 PvE\\n💰 Fenix Coin • 🎯 Missions • 👥 Referrals","🔥"),
                          caption="<b>FENIX COIN</b>",reply_markup=main())
@r.callback_query(F.data=="home")
async def home(c:CallbackQuery):
    await c.answer();await c.message.delete()
    await c.message.answer_photo(visual("FENIX COIN","Главное меню.","🔥"),reply_markup=main())
