from aiogram import Router,F
from aiogram.types import CallbackQuery
from app.db import get_user,pool,balance
from app.keyboards import back
from app.ui import visual
r=Router()
@r.callback_query(F.data=="profile")
async def profile(c):
    u=await get_user(c.from_user.id);await c.answer()
    t=f"👤 <b>{u['first_name'] or 'Игрок'}</b>\\n\\n🔥 {u['balance']} Coin\\n⭐ Level {u['level']}\\n✨ XP {u['xp']}\\n🎮 Games {u['games']}\\n🏆 Wins {u['wins']}\\n👥 Referrals {u['referrals']}"
    await c.message.delete();await c.message.answer_photo(visual("PROFILE",t,"👤"),reply_markup=back())
@r.callback_query(F.data=="top")
async def top(c):
    rows=await pool.fetch("SELECT username,balance FROM users WHERE banned=FALSE ORDER BY balance DESC LIMIT 10")
    t="\\n".join(f"{i}. @{x['username'] or 'player'} — {x['balance']} 🔥" for i,x in enumerate(rows,1)) or "Пока пусто"
    await c.answer();await c.message.delete();await c.message.answer_photo(visual("TOP PLAYERS",t,"🏆"),reply_markup=back())
@r.callback_query(F.data=="refs")
async def refs(c):
    from app.config import settings
    link=f"https://t.me/{settings.bot_username}?start=ref{c.from_user.id}"
    await c.answer();await c.message.answer_photo(visual("REFERRALS",f"600 🔥 за подтверждённого реферала.\\n\\n{link}","👥"),reply_markup=back())
@r.callback_query(F.data=="rules")
async def rules(c):
    await c.answer();await c.message.answer_photo(visual("RULES","• PostgreSQL economy\\n• Bet is deducted before round\\n• Result is server/Telegram based\\n• Transactions protect balance\\n• Fenix Coin is virtual currency","📜"),reply_markup=back())
@r.callback_query(F.data=="bonus")
async def bonus(c):
    from datetime import datetime,timezone,timedelta
    u=await get_user(c.from_user.id);now=datetime.now(timezone.utc)
    if u["daily_claimed_at"] and now-u["daily_claimed_at"]<timedelta(hours=24): return await c.answer("Бонус уже получен",show_alert=True)
    await pool.execute("UPDATE users SET daily_claimed_at=$2,streak=streak+1 WHERE id=$1",c.from_user.id,now)
    await balance(c.from_user.id,300,"daily_bonus");await c.answer("🎁 +300 🔥")
@r.callback_query(F.data=="shop")
async def shop(c):
    rows=await pool.fetch("SELECT * FROM shop_items WHERE active=TRUE ORDER BY price")
    t="\\n".join(f"🛍️ {x['title']} — {x['price']} 🔥" for x in rows) or "Магазин готов к наполнению."
    await c.answer();await c.message.answer_photo(visual("SHOP",t,"🛍️"),reply_markup=back())
