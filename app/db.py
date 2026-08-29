import asyncpg
from app.config import settings
pool = None

SCHEMA = r"""
CREATE TABLE IF NOT EXISTS users(
 id BIGINT PRIMARY KEY, username TEXT, first_name TEXT,
 balance BIGINT NOT NULL DEFAULT 1000, xp BIGINT NOT NULL DEFAULT 0,
 level INT NOT NULL DEFAULT 1, games INT DEFAULT 0, wins INT DEFAULT 0,
 losses INT DEFAULT 0, referrals INT DEFAULT 0, referred_by BIGINT,
 referral_rewarded BOOLEAN DEFAULT FALSE, banned BOOLEAN DEFAULT FALSE,
 streak INT DEFAULT 0, daily_claimed_at TIMESTAMPTZ, created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS transactions(
 id BIGSERIAL PRIMARY KEY,user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
 amount BIGINT NOT NULL,reason TEXT NOT NULL,meta JSONB DEFAULT '{}',created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS games(
 id SERIAL PRIMARY KEY,code TEXT UNIQUE NOT NULL,title TEXT NOT NULL,
 enabled BOOLEAN DEFAULT TRUE,min_bet BIGINT DEFAULT 10,max_bet BIGINT DEFAULT 100000
);
CREATE TABLE IF NOT EXISTS missions(
 id SERIAL PRIMARY KEY,title TEXT NOT NULL,reward BIGINT NOT NULL,kind TEXT NOT NULL,
 target TEXT,active BOOLEAN DEFAULT TRUE,created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS mission_claims(
 mission_id INT REFERENCES missions(id) ON DELETE CASCADE,
 user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
 created_at TIMESTAMPTZ DEFAULT NOW(),PRIMARY KEY(mission_id,user_id)
);
CREATE TABLE IF NOT EXISTS achievements(
 id SERIAL PRIMARY KEY,code TEXT UNIQUE,title TEXT,reward BIGINT DEFAULT 0
);
CREATE TABLE IF NOT EXISTS user_achievements(
 user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
 achievement_id INT REFERENCES achievements(id) ON DELETE CASCADE,
 created_at TIMESTAMPTZ DEFAULT NOW(),PRIMARY KEY(user_id,achievement_id)
);
CREATE TABLE IF NOT EXISTS promo_codes(
 code TEXT PRIMARY KEY,reward BIGINT NOT NULL,max_uses INT DEFAULT 1,uses INT DEFAULT 0,active BOOLEAN DEFAULT TRUE
);
CREATE TABLE IF NOT EXISTS promo_claims(
 code TEXT REFERENCES promo_codes(code) ON DELETE CASCADE,
 user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,PRIMARY KEY(code,user_id)
);
CREATE TABLE IF NOT EXISTS clans(
 id SERIAL PRIMARY KEY,name TEXT UNIQUE NOT NULL,owner_id BIGINT REFERENCES users(id),
 treasury BIGINT DEFAULT 0,created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS clan_members(
 clan_id INT REFERENCES clans(id) ON DELETE CASCADE,user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
 role TEXT DEFAULT 'member',PRIMARY KEY(clan_id,user_id)
);
CREATE TABLE IF NOT EXISTS tournaments(
 id SERIAL PRIMARY KEY,title TEXT,entry_fee BIGINT DEFAULT 0,prize BIGINT DEFAULT 0,
 status TEXT DEFAULT 'open',created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS tournament_players(
 tournament_id INT REFERENCES tournaments(id) ON DELETE CASCADE,
 user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,score INT DEFAULT 0,
 PRIMARY KEY(tournament_id,user_id)
);
CREATE TABLE IF NOT EXISTS pvp_matches(
 id BIGSERIAL PRIMARY KEY,creator_id BIGINT REFERENCES users(id),opponent_id BIGINT,
 stake BIGINT,status TEXT DEFAULT 'open',creator_score INT,opponent_score INT,winner_id BIGINT,
 created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS inventory(
 user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,item_code TEXT,quantity INT DEFAULT 1,
 PRIMARY KEY(user_id,item_code)
);
CREATE TABLE IF NOT EXISTS shop_items(
 code TEXT PRIMARY KEY,title TEXT,price BIGINT,kind TEXT,active BOOLEAN DEFAULT TRUE
);
"""
GAMES=[("dice","🎲 Dice"),("darts","🎯 Darts"),("football","⚽ Football"),
("basketball","🏀 Basketball"),("bowling","🎳 Bowling"),("slots","🎰 Slots"),
("mines","💣 Mines 5x5"),("crash","📈 Crash"),("roulette","🎡 Roulette")]

async def init_db():
    global pool
    pool=await asyncpg.create_pool(settings.database_url,min_size=1,max_size=8)
    async with pool.acquire() as c:
        await c.execute(SCHEMA)
        for code,title in GAMES:
            await c.execute("INSERT INTO games(code,title,min_bet,max_bet) VALUES($1,$2,$3,$4) ON CONFLICT(code) DO NOTHING",
                            code,title,settings.min_bet,settings.max_bet)

async def close_db():
    if pool: await pool.close()

async def ensure_user(u,ref=None):
    async with pool.acquire() as c:
        row=await c.fetchrow("SELECT * FROM users WHERE id=$1",u.id)
        if row:
            await c.execute("UPDATE users SET username=$2,first_name=$3 WHERE id=$1",u.id,u.username,u.first_name)
            return row,False
        if ref==u.id: ref=None
        row=await c.fetchrow("""INSERT INTO users(id,username,first_name,balance,referred_by)
                                VALUES($1,$2,$3,$4,$5) RETURNING *""",
                             u.id,u.username,u.first_name,settings.start_balance,ref)
        await c.execute("INSERT INTO transactions(user_id,amount,reason) VALUES($1,$2,'start')",
                        u.id,settings.start_balance)
        return row,True

async def get_user(uid):
    return await pool.fetchrow("SELECT * FROM users WHERE id=$1",uid)

async def balance(uid,delta,reason,meta=None):
    async with pool.acquire() as c:
        async with c.transaction():
            r=await c.fetchrow("SELECT balance,banned FROM users WHERE id=$1 FOR UPDATE",uid)
            if not r: raise ValueError("user_not_found")
            if r["banned"]: raise ValueError("banned")
            new=r["balance"]+delta
            if new<0: raise ValueError("insufficient_funds")
            await c.execute("UPDATE users SET balance=$2 WHERE id=$1",uid,new)
            await c.execute("INSERT INTO transactions(user_id,amount,reason,meta) VALUES($1,$2,$3,$4)",
                            uid,delta,reason,meta or {})
            return new

async def xp(uid,n):
    await pool.execute("UPDATE users SET xp=xp+$2,level=1+(xp+$2)/100 WHERE id=$1",uid,n)

async def result(uid,win):
    await pool.execute("UPDATE users SET games=games+1,wins=wins+$2,losses=losses+$3 WHERE id=$1",
                       uid,1 if win else 0,0 if win else 1)
