import asyncio
import logging
from html import escape
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from app.config import settings
from app.db import (
    init_db, close_db, ensure_user, get_user, get_games, leaderboard,
    claim_daily_bonus, is_admin, admin_users, admin_give, admin_take, set_ban,
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
log=logging.getLogger('fenix')
bot=Bot(settings.bot_token) if settings.bot_token else None
dp=Dispatcher()

def kb(rows): return InlineKeyboardMarkup(inline_keyboard=rows)
def menu(uid):
    rows=[]
    if settings.webapp_url.startswith('https://'):
        rows.append([InlineKeyboardButton(text='🔥 ОТКРЫТЬ FENIX COIN',web_app=WebAppInfo(url=settings.webapp_url))])
    rows += [[InlineKeyboardButton(text='💰 Баланс',callback_data='balance'),InlineKeyboardButton(text='👤 Профиль',callback_data='profile')],
             [InlineKeyboardButton(text='🎮 Игры',callback_data='games'),InlineKeyboardButton(text='🏆 Рейтинг',callback_data='rating')],
             [InlineKeyboardButton(text='🎁 Бонус',callback_data='bonus'),InlineKeyboardButton(text='⚔️ PvP / Mini App',callback_data='open')]]
    if uid in settings.admin_ids: rows.append([InlineKeyboardButton(text='⚙️ ADMIN PANEL',callback_data='admin')])
    return kb(rows)

def home(u):
    return f"🔥 <b>FENIX COIN ULTRA</b>\n\n💰 <b>{int(u['balance']):,} FC</b>\n⭐ Level <b>{u['level']}</b>\n🎮 Игр: <b>{u['games']}</b>\n🏆 Побед: <b>{u['wins']}</b>\n\nОткрывай Mini App — там все игры и PvP."

@dp.message(CommandStart())
async def start(m:Message):
    ref=None; p=(m.text or '').split(maxsplit=1)
    if len(p)>1 and p[1].startswith('ref_'):
        try: ref=int(p[1][4:])
        except: pass
    u,_=await ensure_user(m.from_user,ref)
    await m.answer(home(u),reply_markup=menu(m.from_user.id),parse_mode='HTML')

@dp.message(Command('menu'))
async def cmd_menu(m:Message):
    u,_=await ensure_user(m.from_user,None); await m.answer(home(u),reply_markup=menu(m.from_user.id),parse_mode='HTML')

@dp.message(Command('games'))
async def games(m:Message):
    await ensure_user(m.from_user,None); gs=await get_games()
    text='🎮 <b>ВСЕ ИГРЫ</b>\n\n'+'\n'.join(f"{g['emoji']} <b>{escape(g['title'])}</b> — {g['min_bet']}–{g['max_bet']} FC" for g in gs)
    await m.answer(text,reply_markup=menu(m.from_user.id),parse_mode='HTML')

@dp.message(Command('balance'))
async def balance_cmd(m:Message):
    u,_=await ensure_user(m.from_user,None); await m.answer(f"💰 <b>{int(u['balance']):,} FC</b>",reply_markup=menu(m.from_user.id),parse_mode='HTML')

@dp.message(Command('bonus'))
async def bonus_cmd(m:Message):
    await ensure_user(m.from_user,None)
    try:
        reward,streak=await claim_daily_bonus(m.from_user.id,150)
        await m.answer(f'🎁 <b>+{reward} FC</b>\n🔥 Streak: {streak}',reply_markup=menu(m.from_user.id),parse_mode='HTML')
    except ValueError as e: await m.answer('⏳ '+escape(str(e)),reply_markup=menu(m.from_user.id),parse_mode='HTML')

@dp.callback_query(F.data=='open')
async def open_app(c:CallbackQuery):
    if not settings.webapp_url.startswith('https://'): await c.answer('WEBAPP_URL на Render не настроен',show_alert=True); return
    await c.message.answer('🔥 Нажми кнопку ниже:',reply_markup=kb([[InlineKeyboardButton(text='ОТКРЫТЬ MINI APP',web_app=WebAppInfo(url=settings.webapp_url))]])); await c.answer()

@dp.callback_query(F.data=='balance')
async def cb_balance(c:CallbackQuery):
    u=await get_user(c.from_user.id); await c.message.edit_text(f"💰 <b>{int(u['balance']):,} FC</b>",reply_markup=menu(c.from_user.id),parse_mode='HTML'); await c.answer()
@dp.callback_query(F.data=='profile')
async def cb_profile(c:CallbackQuery):
    u=await get_user(c.from_user.id); await c.message.edit_text(f"👤 <b>ПРОФИЛЬ</b>\n\nID: <code>{u['id']}</code>\n💰 {int(u['balance']):,} FC\n⭐ LVL {u['level']}\n🎮 {u['games']} игр\n🏆 {u['wins']} побед\n💀 {u['losses']} поражений\n👥 {u['referrals']} рефералов",reply_markup=menu(c.from_user.id),parse_mode='HTML'); await c.answer()
@dp.callback_query(F.data=='games')
async def cb_games(c:CallbackQuery):
    gs=await get_games(); text='🎮 <b>ИГРЫ</b>\n\n'+'\n'.join(f"{g['emoji']} {g['title']}" for g in gs); await c.message.edit_text(text,reply_markup=menu(c.from_user.id),parse_mode='HTML'); await c.answer()
@dp.callback_query(F.data=='rating')
async def cb_rating(c:CallbackQuery):
    rs=await leaderboard(10); text='🏆 <b>ТОП-10</b>\n\n'+('\n'.join(f"{i}. {r['first_name'] or r['username'] or 'Игрок'} — {int(r['balance']):,} FC" for i,r in enumerate(rs,1)) or 'Пусто'); await c.message.edit_text(text,reply_markup=menu(c.from_user.id),parse_mode='HTML'); await c.answer()
@dp.callback_query(F.data=='bonus')
async def cb_bonus(c:CallbackQuery):
    try:
        await ensure_user(c.from_user,None); reward,streak=await claim_daily_bonus(c.from_user.id,150); await c.answer(f'🎁 +{reward} FC · streak {streak}',show_alert=True)
    except ValueError as e: await c.answer(str(e),show_alert=True)

@dp.callback_query(F.data=='admin')
async def cb_admin(c:CallbackQuery):
    if not await is_admin(c.from_user.id): await c.answer('Нет доступа',show_alert=True); return
    s=await __import__('app.db',fromlist=['get_stats']).get_stats();
    text=f"⚙️ <b>ADMIN PANEL</b>\n\n👥 Игроков: {s['users']}\n🎮 Игр: {s['games']}\n⚔️ PvP: {s['pvp_matches']}\n💰 Всего FC: {s['total_coins']}"
    await c.message.edit_text(text,reply_markup=kb([[InlineKeyboardButton(text='📋 Игроки',callback_data='admin_users')],[InlineKeyboardButton(text='⬅️ Назад',callback_data='home')]]),parse_mode='HTML'); await c.answer()
@dp.callback_query(F.data=='admin_users')
async def cb_admin_users(c:CallbackQuery):
    if not await is_admin(c.from_user.id): return
    us=await admin_users(20); text='📋 <b>ИГРОКИ</b>\n\n'+'\n'.join(f"{u['id']} · {escape(u['first_name'] or u['username'] or 'Игрок')} · {int(u['balance']):,} FC" for u in us)
    await c.message.edit_text(text,reply_markup=kb([[InlineKeyboardButton(text='⬅️ Admin',callback_data='admin')]]),parse_mode='HTML'); await c.answer()
@dp.callback_query(F.data=='home')
async def cb_home(c:CallbackQuery):
    u=await get_user(c.from_user.id); await c.message.edit_text(home(u),reply_markup=menu(c.from_user.id),parse_mode='HTML'); await c.answer()

async def main():
    if not settings.bot_token:
        raise RuntimeError('BOT_TOKEN не задан. Render Worker → Environment → BOT_TOKEN')
    if not settings.database_url:
        raise RuntimeError('DATABASE_URL не задан. Render Worker → Environment → DATABASE_URL')
    await init_db()
    try:
        me=await bot.get_me(); log.info('Telegram bot: @%s (%s)',me.username,me.id)
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot,allowed_updates=dp.resolve_used_update_types())
    finally:
        await close_db(); await bot.session.close()

if __name__=='__main__': asyncio.run(main())
