import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from app.config import settings
from app.db import init_db, close_db, ensure_user, get_user, get_games, claim_daily_bonus

logging.basicConfig(level=logging.INFO)

bot = Bot(settings.bot_token)
dp = Dispatcher()

def menu():
    rows=[]
    if settings.webapp_url:
        rows.append([InlineKeyboardButton(text="🔥 Открыть Fenix Coin", web_app=WebAppInfo(url=settings.webapp_url))])
    rows += [
        [InlineKeyboardButton(text="🎮 Игры", callback_data="games"), InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="🎁 Бонус", callback_data="bonus"), InlineKeyboardButton(text="🏆 Рейтинг", callback_data="rating")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

@dp.message(CommandStart())
async def start(message: Message):
    ref=None
    parts=(message.text or "").split(maxsplit=1)
    if len(parts)>1 and parts[1].startswith("ref_"):
        try: ref=int(parts[1][4:])
        except ValueError: pass
    user,_=await ensure_user(message.from_user,ref)
    await message.answer(f"🔥 <b>FENIX COIN ULTRA</b>\n\n💰 Баланс: <b>{user['balance']:,}</b> FC\n⭐ Уровень: <b>{user['level']}</b>\n🎮 Игр: <b>{user['games']}</b>\n🏆 Побед: <b>{user['wins']}</b>\n\nНажми кнопку и открывай игру.",reply_markup=menu(),parse_mode="HTML")

@dp.callback_query(F.data=="games")
async def games(call):
    games=await get_games()
    text="🎮 <b>ИГРЫ</b>\n\n"+"\n".join(f"{g['emoji']} {g['title']} — {g['min_bet']}–{g['max_bet']} FC" for g in games)
    await call.message.edit_text(text,reply_markup=menu(),parse_mode="HTML"); await call.answer()

@dp.callback_query(F.data=="profile")
async def profile(call):
    u=await get_user(call.from_user.id)
    if not u: await call.answer("Сначала /start",show_alert=True); return
    await call.message.edit_text(f"👤 <b>ПРОФИЛЬ</b>\n\nID: <code>{u['id']}</code>\n💰 {u['balance']:,} FC\n⭐ Level {u['level']}\n🎮 Игр: {u['games']}\n🏆 Побед: {u['wins']}\n💀 Поражений: {u['losses']}\n👥 Рефералов: {u['referrals']}",reply_markup=menu(),parse_mode="HTML"); await call.answer()

@dp.callback_query(F.data=="bonus")
async def bonus(call):
    try:
        reward,streak=await claim_daily_bonus(call.from_user.id,100+50)
        await call.answer(f"🎁 +{reward} FC · streak {streak}",show_alert=True)
    except ValueError as e: await call.answer(str(e),show_alert=True)

@dp.callback_query(F.data=="rating")
async def rating(call):
    from app.db import leaderboard
    rows=await leaderboard(10)
    text="🏆 <b>ТОП-10</b>\n\n"+"\n".join(f"{i}. {r['first_name'] or r['username'] or 'Игрок'} — {r['balance']:,} FC" for i,r in enumerate(rows,1))
    await call.message.edit_text(text or "Пока пусто",reply_markup=menu(),parse_mode="HTML"); await call.answer()

async def main():
    if not settings.bot_token: raise RuntimeError("BOT_TOKEN is not configured")
    await init_db()
    try: await dp.start_polling(bot)
    finally: await close_db()

if __name__=="__main__": asyncio.run(main())
