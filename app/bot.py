import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from app.config import settings
from app.db import init_db, close_db, ensure_user, get_user, get_games, claim_daily_bonus, leaderboard

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
log=logging.getLogger('fenix-bot')

if not settings.bot_token:
    raise RuntimeError('BOT_TOKEN is not configured in Render Environment Variables')
bot=Bot(settings.bot_token)
dp=Dispatcher()

def menu():
    rows=[]
    if settings.webapp_url and settings.webapp_url.startswith('https://'):
        rows.append([InlineKeyboardButton(text='🔥 Открыть Fenix Coin', web_app=WebAppInfo(url=settings.webapp_url))])
    else:
        rows.append([InlineKeyboardButton(text='⚠️ Mini App URL не настроен', callback_data='webapp_missing')])
    rows += [[InlineKeyboardButton(text='🎮 Игры',callback_data='games'),InlineKeyboardButton(text='👤 Профиль',callback_data='profile')],
             [InlineKeyboardButton(text='🎁 Бонус',callback_data='bonus'),InlineKeyboardButton(text='🏆 Рейтинг',callback_data='rating')],
             [InlineKeyboardButton(text='🔄 Обновить',callback_data='home')]]
    return InlineKeyboardMarkup(inline_keyboard=rows)

def home_text(u):
    return (f'🔥 <b>FENIX COIN ULTRA</b>\n\n💰 Баланс: <b>{int(u["balance"]):,}</b> FC\n'
            f'⭐ Уровень: <b>{u["level"]}</b>\n🎮 Игр: <b>{u["games"]}</b>\n🏆 Побед: <b>{u["wins"]}</b>\n\n'
            'Открой Mini App для всех игр, PvP, Mines, Crash и остальных механик.')

@dp.message(CommandStart())
async def start(message:Message):
    ref=None; parts=(message.text or '').split(maxsplit=1)
    if len(parts)>1 and parts[1].startswith('ref_'):
        try: ref=int(parts[1][4:])
        except ValueError: pass
    u,_=await ensure_user(message.from_user,ref)
    await message.answer(home_text(u),reply_markup=menu(),parse_mode='HTML')

@dp.message(Command('menu'))
async def cmd_menu(message:Message):
    u=await ensure_user(message.from_user,None); u=u[0] if isinstance(u,tuple) else u
    await message.answer(home_text(u),reply_markup=menu(),parse_mode='HTML')

@dp.message(Command('bonus'))
async def cmd_bonus(message:Message):
    await ensure_user(message.from_user,None)
    try:
        reward,streak=await claim_daily_bonus(message.from_user.id,100+50)
        await message.answer(f'🎁 <b>Бонус получен!</b>\n+{reward} FC\n🔥 Streak: {streak}',parse_mode='HTML',reply_markup=menu())
    except ValueError as e: await message.answer(f'⏳ {e}',reply_markup=menu())


@dp.message(Command('games'))
async def cmd_games(message:Message):
    rows=await get_games()
    text='🎮 <b>ИГРЫ FENIX COIN</b>\n\n'+'\n'.join(f'{g["emoji"]} {g["title"]} — {g["min_bet"]}–{g["max_bet"]} FC' for g in rows)
    await message.answer(text,parse_mode='HTML',reply_markup=menu())

@dp.message(Command('balance'))
async def cmd_balance(message:Message):
    u=await get_user(message.from_user.id)
    if not u: u,_=await ensure_user(message.from_user,None)
    await message.answer(f'💰 Баланс: <b>{int(u["balance"]):,} FC</b>',parse_mode='HTML',reply_markup=menu())

@dp.callback_query(F.data=='home')
async def home(call):
    u=await get_user(call.from_user.id)
    if not u: u,_=await ensure_user(call.from_user,None)
    await call.message.edit_text(home_text(u),reply_markup=menu(),parse_mode='HTML'); await call.answer()

@dp.callback_query(F.data=='webapp_missing')
async def web_missing(call): await call.answer('На Render нужно добавить WEBAPP_URL=https://твой-web.onrender.com',show_alert=True)

@dp.callback_query(F.data=='games')
async def games(call):
    rows=await get_games(); text='🎮 <b>ВСЕ ИГРЫ</b>\n\n'+'\n'.join(f'{g["emoji"]} <b>{g["title"]}</b> — {g["min_bet"]}–{g["max_bet"]} FC' for g in rows)
    await call.message.edit_text(text,reply_markup=menu(),parse_mode='HTML'); await call.answer()

@dp.callback_query(F.data=='profile')
async def profile(call):
    u=await get_user(call.from_user.id)
    if not u: await call.answer('Нажми /start',show_alert=True); return
    text=(f'👤 <b>ПРОФИЛЬ</b>\n\nID: <code>{u["id"]}</code>\n💰 {int(u["balance"]):,} FC\n'
          f'⭐ Level {u["level"]}\n🎮 Игр: {u["games"]}\n🏆 Побед: {u["wins"]}\n💀 Поражений: {u["losses"]}\n👥 Рефералов: {u["referrals"]}')
    await call.message.edit_text(text,reply_markup=menu(),parse_mode='HTML'); await call.answer()

@dp.callback_query(F.data=='bonus')
async def bonus(call):
    try:
        await ensure_user(call.from_user,None); reward,streak=await claim_daily_bonus(call.from_user.id,150)
        await call.answer(f'🎁 +{reward} FC · streak {streak}',show_alert=True)
        u=await get_user(call.from_user.id); await call.message.edit_text(home_text(u),reply_markup=menu(),parse_mode='HTML')
    except ValueError as e: await call.answer(str(e),show_alert=True)

@dp.callback_query(F.data=='rating')
async def rating_cb(call):
    rows=await leaderboard(10)
    text='🏆 <b>ТОП-10</b>\n\n'+('\n'.join(f'{i}. {r["first_name"] or r["username"] or "Игрок"} — {int(r["balance"]):,} FC' for i,r in enumerate(rows,1)) or 'Пока пусто')
    await call.message.edit_text(text,reply_markup=menu(),parse_mode='HTML'); await call.answer()

async def main():
    await init_db()
    try:
        # Removes a stale webhook / another webhook mode so polling can start reliably.
        await bot.delete_webhook(drop_pending_updates=False)
        log.info('Fenix bot polling started')
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await close_db(); await bot.session.close()

if __name__=='__main__': asyncio.run(main())
