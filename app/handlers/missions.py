from aiogram import Router,F
from aiogram.types import CallbackQuery
from app.missions import list_active
from app.keyboards import back
from app.ui import visual
r=Router()
@r.callback_query(F.data=="missions")
async def missions(c):
    rows=await list_active()
    t="\\n".join(f"#{x['id']} • {x['title']} — +{x['reward']} 🔥" for x in rows) or "Активных миссий нет."
    await c.answer();await c.message.delete();await c.message.answer_photo(visual("MISSIONS",t,"🎯"),reply_markup=back())
