from app.db import balance,pool
from app.config import settings
async def bet(uid,amount,reason):
    if amount<settings.min_bet or amount>settings.max_bet: raise ValueError("invalid_bet")
    return await balance(uid,-amount,"bet:"+reason)
async def payout(uid,amount,reason): return await balance(uid,amount,"win:"+reason)
async def referral(uid):
    row=await pool.fetchrow("SELECT referred_by,referral_rewarded FROM users WHERE id=$1 FOR UPDATE",uid)
    if not row or not row["referred_by"] or row["referral_rewarded"]: return None
    ref=row["referred_by"]
    async with pool.acquire() as c:
        async with c.transaction():
            await c.execute("UPDATE users SET referral_rewarded=TRUE WHERE id=$1",uid)
            await c.execute("UPDATE users SET referrals=referrals+1 WHERE id=$1",ref)
    await balance(ref,settings.ref_reward,"referral_reward")
    return ref
