from app.db import pool,balance
async def list_active(): return await pool.fetch("SELECT * FROM missions WHERE active=TRUE ORDER BY id DESC")
async def claim(uid,mid):
    async with pool.acquire() as c:
        async with c.transaction():
            m=await c.fetchrow("SELECT * FROM missions WHERE id=$1 AND active=TRUE",mid)
            if not m:return False,"Миссия не найдена"
            old=await c.fetchval("SELECT 1 FROM mission_claims WHERE mission_id=$1 AND user_id=$2",mid,uid)
            if old:return False,"Уже получено"
            await c.execute("INSERT INTO mission_claims VALUES($1,$2)",mid,uid)
    await balance(uid,m["reward"],f"mission:{mid}")
    return True,f"+{m['reward']} 🔥"
