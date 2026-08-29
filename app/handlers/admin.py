from aiogram import Router,F
from aiogram.filters import Command
from aiogram.types import Message
from app.config import settings
from app.db import pool,balance
r=Router()
def admin(uid): return uid in settings.admin_ids
@r.message(Command("admin"))
async def panel(m):
    if not admin(m.from_user.id): return
    s=await pool.fetchrow("SELECT COUNT(*) users,COALESCE(SUM(balance),0) coins,COALESCE(SUM(games),0) games FROM users")
    await m.answer(f"🛡️ FENIX ADMIN\\n\\n👥 {s['users']} users\\n🔥 {s['coins']} coins\\n🎮 {s['games']} games\\n\\n/give ID AMOUNT\\n/take ID AMOUNT\\n/ban ID\\n/mission TITLE | REWARD | KIND | TARGET")
@r.message(Command("give"))
async def give(m):
    if not admin(m.from_user.id): return
    p=m.text.split()
    if len(p)==3:
        try: await balance(int(p[1]),int(p[2]),"admin_give");await m.answer("✅ Выдано")
        except Exception as e: await m.answer("❌ "+str(e))
@r.message(Command("take"))
async def take(m):
    if not admin(m.from_user.id): return
    p=m.text.split()
    if len(p)==3:
        try: await balance(int(p[1]),-int(p[2]),"admin_take");await m.answer("✅ Списано")
        except Exception as e: await m.answer("❌ "+str(e))
@r.message(Command("ban"))
async def ban(m):
    if admin(m.from_user.id) and len(m.text.split())==2:
        await pool.execute("UPDATE users SET banned=TRUE WHERE id=$1",int(m.text.split()[1]));await m.answer("🚫 Banned")
@r.message(F.chat.type=="channel")
async def channel(m):
    if m.text and m.text.startswith("/mission add") and (settings.admin_channel_id is None or m.chat.id==settings.admin_channel_id):
        p=[x.strip() for x in m.text.split("|")]
        if len(p)>=5:
            try:
                row=await pool.fetchrow("INSERT INTO missions(title,reward,kind,target) VALUES($1,$2,$3,$4) RETURNING id",p[1],int(p[2]),p[3],p[4])
                await m.reply(f"✅ Mission #{row['id']} created")
            except Exception as e: await m.reply("❌ "+str(e))
