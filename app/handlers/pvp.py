from aiogram import Router,F
from aiogram.types import Message
import secrets
from app.db import pool,balance,result,xp
r=Router()
@r.message(F.text.regexp(r"^/duel\s+\d+$"))
async def duel(m):
    uid=int(m.text.split()[1])
    if uid==m.from_user.id:return await m.answer("❌ Нельзя вызвать себя")
    row=await pool.fetchrow("INSERT INTO pvp_matches(creator_id,opponent_id,stake) VALUES($1,$2,250) RETURNING id",m.from_user.id,uid)
    await m.answer(f"⚔️ Дуэль #{row['id']} создана. Игрок {uid}: /accept {row['id']}")
@r.message(F.text.regexp(r"^/accept\s+\d+$"))
async def accept(m):
    mid=int(m.text.split()[1]);x=await pool.fetchrow("SELECT * FROM pvp_matches WHERE id=$1 AND status='open'",mid)
    if not x or x["opponent_id"]!=m.from_user.id:return await m.answer("❌ Дуэль не найдена")
    try:
        await balance(x["creator_id"],-x["stake"],f"pvp:{mid}:bet");await balance(m.from_user.id,-x["stake"],f"pvp:{mid}:bet")
    except:return await m.answer("❌ Недостаточно Coin")
    a,b=secrets.randbelow(100),secrets.randbelow(100);winner=x["creator_id"] if a>=b else m.from_user.id
    prize=int(x["stake"]*2*.95);await balance(winner,prize,f"pvp:{mid}:prize")
    await pool.execute("UPDATE pvp_matches SET status='finished',creator_score=$2,opponent_score=$3,winner_id=$4 WHERE id=$1",mid,a,b,winner)
    loser=m.from_user.id if winner==x["creator_id"] else x["creator_id"]
    await result(winner,True);await result(loser,False);await xp(winner,40)
    await m.answer(f"⚔️ #{mid}\\n{a} : {b}\\n🏆 Winner: {winner}\\n💰 {prize} 🔥")
