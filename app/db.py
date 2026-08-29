import asyncpg
from app.config import settings

pool = None


GAMES = [
    ("dice", "🎲 Dice"),
    ("darts", "🎯 Darts"),
    ("football", "⚽ Football"),
    ("basketball", "🏀 Basketball"),
    ("bowling", "🎳 Bowling"),
    ("slots", "🎰 Slots"),
    ("mines", "💣 Mines 5x5"),
    ("crash", "📈 Crash"),
    ("roulette", "🎡 Roulette"),
]


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY,
    username TEXT DEFAULT '',
    first_name TEXT DEFAULT '',
    balance BIGINT NOT NULL DEFAULT 1000,
    xp BIGINT NOT NULL DEFAULT 0,
    level INT NOT NULL DEFAULT 1,
    games INT NOT NULL DEFAULT 0,
    wins INT NOT NULL DEFAULT 0,
    losses INT NOT NULL DEFAULT 0,
    referrals INT NOT NULL DEFAULT 0,
    referred_by BIGINT,
    referral_rewarded BOOLEAN NOT NULL DEFAULT FALSE,
    banned BOOLEAN NOT NULL DEFAULT FALSE,
    streak INT NOT NULL DEFAULT 0,
    daily_claimed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS transactions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    amount BIGINT NOT NULL,
    balance_before BIGINT NOT NULL DEFAULT 0,
    balance_after BIGINT NOT NULL DEFAULT 0,
    reason TEXT NOT NULL DEFAULT '',
    meta JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS games (
    id SERIAL PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    emoji TEXT DEFAULT '🎮',
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    min_bet BIGINT NOT NULL DEFAULT 10,
    max_bet BIGINT NOT NULL DEFAULT 100000
);

CREATE TABLE IF NOT EXISTS game_results (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    game_code TEXT NOT NULL,
    bet BIGINT NOT NULL DEFAULT 0,
    win BOOLEAN NOT NULL DEFAULT FALSE,
    profit BIGINT NOT NULL DEFAULT 0,
    multiplier DOUBLE PRECISION,
    data JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS missions (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    reward BIGINT NOT NULL DEFAULT 0,
    kind TEXT NOT NULL DEFAULT 'custom',
    target TEXT DEFAULT '',
    target_value TEXT DEFAULT '',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS mission_claims (
    mission_id INT REFERENCES missions(id) ON DELETE CASCADE,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY(mission_id, user_id)
);

CREATE TABLE IF NOT EXISTS achievements (
    id SERIAL PRIMARY KEY,
    code TEXT UNIQUE,
    title TEXT,
    description TEXT DEFAULT '',
    reward BIGINT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS user_achievements (
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    achievement_id INT REFERENCES achievements(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY(user_id, achievement_id)
);

CREATE TABLE IF NOT EXISTS promo_codes (
    code TEXT PRIMARY KEY,
    reward BIGINT NOT NULL,
    max_uses INT NOT NULL DEFAULT 1,
    uses INT NOT NULL DEFAULT 0,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS promo_claims (
    code TEXT REFERENCES promo_codes(code) ON DELETE CASCADE,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    PRIMARY KEY(code, user_id)
);

CREATE TABLE IF NOT EXISTS clans (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    owner_id BIGINT REFERENCES users(id),
    treasury BIGINT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS clan_members (
    clan_id INT REFERENCES clans(id) ON DELETE CASCADE,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    role TEXT DEFAULT 'member',
    PRIMARY KEY(clan_id, user_id)
);

CREATE TABLE IF NOT EXISTS tournaments (
    id SERIAL PRIMARY KEY,
    title TEXT,
    entry_fee BIGINT DEFAULT 0,
    prize BIGINT DEFAULT 0,
    status TEXT DEFAULT 'open',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tournament_players (
    tournament_id INT REFERENCES tournaments(id) ON DELETE CASCADE,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    score INT DEFAULT 0,
    PRIMARY KEY(tournament_id, user_id)
);

CREATE TABLE IF NOT EXISTS pvp_matches (
    id BIGSERIAL PRIMARY KEY,
    creator_id BIGINT REFERENCES users(id),
    opponent_id BIGINT,
    stake BIGINT NOT NULL DEFAULT 250,
    status TEXT NOT NULL DEFAULT 'open',
    creator_score INT,
    opponent_score INT,
    winner_id BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS inventory (
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    item_code TEXT,
    quantity INT NOT NULL DEFAULT 1,
    PRIMARY KEY(user_id, item_code)
);

CREATE TABLE IF NOT EXISTS shop_items (
    code TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    price BIGINT NOT NULL DEFAULT 0,
    kind TEXT DEFAULT 'item',
    data JSONB NOT NULL DEFAULT '{}'::jsonb,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS referrals (
    id BIGSERIAL PRIMARY KEY,
    referrer_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    referred_id BIGINT UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    reward BIGINT NOT NULL DEFAULT 600,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


async def init_db():
    global pool

    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is not configured")

    pool = await asyncpg.create_pool(
        settings.database_url,
        min_size=1,
        max_size=8,
        command_timeout=30,
    )

    async with pool.acquire() as c:
        await c.execute(SCHEMA)

        # -------------------------------------------------
        # MIGRATIONS
        # -------------------------------------------------

        migrations = [
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS username TEXT DEFAULT ''",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name TEXT DEFAULT ''",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS balance BIGINT NOT NULL DEFAULT 1000",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS xp BIGINT NOT NULL DEFAULT 0",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS level INT NOT NULL DEFAULT 1",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS games INT NOT NULL DEFAULT 0",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS wins INT NOT NULL DEFAULT 0",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS losses INT NOT NULL DEFAULT 0",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS referrals INT NOT NULL DEFAULT 0",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS referred_by BIGINT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS referral_rewarded BOOLEAN NOT NULL DEFAULT FALSE",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS banned BOOLEAN NOT NULL DEFAULT FALSE",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS streak INT NOT NULL DEFAULT 0",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS daily_claimed_at TIMESTAMPTZ",

            "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS balance_before BIGINT NOT NULL DEFAULT 0",
            "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS balance_after BIGINT NOT NULL DEFAULT 0",
            "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS reason TEXT NOT NULL DEFAULT ''",
            "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS meta JSONB NOT NULL DEFAULT '{}'::jsonb",

            "ALTER TABLE games ADD COLUMN IF NOT EXISTS description TEXT DEFAULT ''",
            "ALTER TABLE games ADD COLUMN IF NOT EXISTS emoji TEXT DEFAULT '🎮'",
            "ALTER TABLE games ADD COLUMN IF NOT EXISTS enabled BOOLEAN NOT NULL DEFAULT TRUE",
            "ALTER TABLE games ADD COLUMN IF NOT EXISTS min_bet BIGINT NOT NULL DEFAULT 10",
            "ALTER TABLE games ADD COLUMN IF NOT EXISTS max_bet BIGINT NOT NULL DEFAULT 100000",

            "ALTER TABLE missions ADD COLUMN IF NOT EXISTS description TEXT DEFAULT ''",
            "ALTER TABLE missions ADD COLUMN IF NOT EXISTS target_value TEXT DEFAULT ''",

            "ALTER TABLE shop_items ADD COLUMN IF NOT EXISTS description TEXT DEFAULT ''",
            "ALTER TABLE shop_items ADD COLUMN IF NOT EXISTS data JSONB NOT NULL DEFAULT '{}'::jsonb",
        ]

        for sql in migrations:
            try:
                await c.execute(sql)
            except Exception as e:
                print("Migration warning:", e)

        # -------------------------------------------------
        # GAMES
        # -------------------------------------------------

        for code, title in GAMES:
            emoji = title.split()[0]

            await c.execute(
                """
                INSERT INTO games(
                    code,
                    title,
                    description,
                    emoji,
                    enabled,
                    min_bet,
                    max_bet
                )
                VALUES($1,$2,$3,$4,TRUE,$5,$6)
                ON CONFLICT(code)
                DO UPDATE SET
                    title = EXCLUDED.title,
                    emoji = EXCLUDED.emoji
                """,
                code,
                title,
                f"{title} — Fenix Coin game",
                emoji,
                settings.min_bet,
                settings.max_bet,
            )

        # -------------------------------------------------
        # SHOP
        # -------------------------------------------------

        shop_defaults = [
            (
                "vip",
                "💎 VIP",
                "VIP статус игрока",
                5000,
                "vip",
            ),
            (
                "profile_red",
                "🔴 Red Profile",
                "Красивое оформление профиля",
                2500,
                "profile",
            ),
            (
                "title_pro",
                "👑 PRO Title",
                "Эксклюзивный титул",
                10000,
                "title",
            ),
        ]

        for code, title, description, price, kind in shop_defaults:
            await c.execute(
                """
                INSERT INTO shop_items(
                    code,
                    title,
                    description,
                    price,
                    kind
                )
                VALUES($1,$2,$3,$4,$5)
                ON CONFLICT(code) DO NOTHING
                """,
                code,
                title,
                description,
                price,
                kind,
            )

    print("✅ Fenix Coin PostgreSQL initialized")


async def close_db():
    global pool

    if pool is not None:
        await pool.close()
        pool = None


# =========================================================
# USERS
# =========================================================

async def ensure_user(u, ref=None):
    async with pool.acquire() as c:

        row = await c.fetchrow(
            "SELECT * FROM users WHERE id=$1",
            u.id,
        )

        if row:
            await c.execute(
                """
                UPDATE users
                SET
                    username=$2,
                    first_name=$3
                WHERE id=$1
                """,
                u.id,
                u.username or "",
                u.first_name or "",
            )

            return row, False

        if ref == u.id:
            ref = None

        row = await c.fetchrow(
            """
            INSERT INTO users(
                id,
                username,
                first_name,
                balance,
                referred_by
            )
            VALUES($1,$2,$3,$4,$5)
            RETURNING *
            """,
            u.id,
            u.username or "",
            u.first_name or "",
            settings.start_balance,
            ref,
        )

        await c.execute(
            """
            INSERT INTO transactions(
                user_id,
                amount,
                balance_before,
                balance_after,
                reason
            )
            VALUES($1,$2,0,$2,'start')
            """,
            u.id,
            settings.start_balance,
        )

        # Реальный реферальный бонус
        if ref and ref != u.id:
            ref_exists = await c.fetchval(
                "SELECT id FROM users WHERE id=$1",
                ref,
            )

            if ref_exists:
                already = await c.fetchval(
                    """
                    SELECT 1
                    FROM referrals
                    WHERE referred_id=$1
                    """,
                    u.id,
                )

                if not already:
                    reward = settings.ref_reward

                    await c.execute(
                        """
                        UPDATE users
                        SET
                            balance=balance+$1,
                            referrals=referrals+1
                        WHERE id=$2
                        """,
                        reward,
                        ref,
                    )

                    await c.execute(
                        """
                        INSERT INTO referrals(
                            referrer_id,
                            referred_id,
                            reward
                        )
                        VALUES($1,$2,$3)
                        ON CONFLICT(referred_id)
                        DO NOTHING
                        """,
                        ref,
                        u.id,
                        reward,
                    )

                    ref_balance = await c.fetchval(
                        """
                        SELECT balance
                        FROM users
                        WHERE id=$1
                        """,
                        ref,
                    )

                    await c.execute(
                        """
                        INSERT INTO transactions(
                            user_id,
                            amount,
                            balance_before,
                            balance_after,
                            reason,
                            meta
                        )
                        VALUES(
                            $1,
                            $2,
                            $3-$2,
                            $3,
                            'referral_reward',
                            '{"reward":600}'::jsonb
                        )
                        """,
                        ref,
                        reward,
                        ref_balance,
                    )

                    await c.execute(
                        """
                        UPDATE users
                        SET referral_rewarded=TRUE
                        WHERE id=$1
                        """,
                        u.id,
                    )

        return row, True


async def get_user(uid):
    if pool is None:
        return None

    return await pool.fetchrow(
        "SELECT * FROM users WHERE id=$1",
        uid,
    )


# =========================================================
# BALANCE
# =========================================================

async def balance(
    uid,
    delta,
    reason,
    meta=None,
):
    async with pool.acquire() as c:

        async with c.transaction():

            row = await c.fetchrow(
                """
                SELECT balance,banned
                FROM users
                WHERE id=$1
                FOR UPDATE
                """,
                uid,
            )

            if not row:
                raise ValueError("user_not_found")

            if row["banned"]:
                raise ValueError("banned")

            before = row["balance"]
            after = before + delta

            if after < 0:
                raise ValueError("insufficient_funds")

            await c.execute(
                """
                UPDATE users
                SET balance=$2
                WHERE id=$1
                """,
                uid,
                after,
            )

            await c.execute(
                """
                INSERT INTO transactions(
                    user_id,
                    amount,
                    balance_before,
                    balance_after,
                    reason,
                    meta
                )
                VALUES(
                    $1,
                    $2,
                    $3,
                    $4,
                    $5,
                    $6
                )
                """,
                uid,
                delta,
                before,
                after,
                reason,
                meta or {},
            )

            return after


# =========================================================
# XP
# =========================================================

async def xp(uid, n):
    await pool.execute(
        """
        UPDATE users
        SET
            xp=xp+$2,
            level=1+((xp+$2)/100)
        WHERE id=$1
        """,
        uid,
        n,
    )


# =========================================================
# GAME RESULT
# =========================================================

async def result(uid, win):
    await pool.execute(
        """
        UPDATE users
        SET
            games=games+1,
            wins=wins+$2,
            losses=losses+$3
        WHERE id=$1
        """,
        uid,
        1 if win else 0,
        0 if win else 1,
    )


# =========================================================
# GAME HISTORY
# =========================================================

async def get_game_history(
    uid,
    limit=50,
):
    return await pool.fetch(
        """
        SELECT
            id,
            user_id,
            game_code,
            bet,
            win,
            profit,
            multiplier,
            data,
            created_at
        FROM game_results
        WHERE user_id=$1
        ORDER BY created_at DESC
        LIMIT $2
        """,
        uid,
        limit,
    )


async def add_game_history(
    uid,
    game_code,
    bet,
    win,
    profit,
    multiplier=None,
    data=None,
):
    return await pool.fetchrow(
        """
        INSERT INTO game_results(
            user_id,
            game_code,
            bet,
            win,
            profit,
            multiplier,
            data
        )
        VALUES($1,$2,$3,$4,$5,$6,$7)
        RETURNING *
        """,
        uid,
        game_code,
        bet,
        win,
        profit,
        multiplier,
        data or {},
    )


# =========================================================
# TRANSACTIONS
# =========================================================

async def get_transactions(
    uid,
    limit=50,
):
    return await pool.fetch(
        """
        SELECT
            id,
            user_id,
            amount,
            balance_before,
            balance_after,
            reason,
            meta,
            created_at
        FROM transactions
        WHERE user_id=$1
        ORDER BY created_at DESC
        LIMIT $2
        """,
        uid,
        limit,
    )


# =========================================================
# LEADERBOARD
# =========================================================

async def leaderboard(
    limit=100,
):
    return await pool.fetch(
        """
        SELECT
            id,
            username,
            first_name,
            balance,
            xp,
            level,
            games,
            wins,
            losses,
            referrals
        FROM users
        WHERE banned=FALSE
        ORDER BY balance DESC
        LIMIT $1
        """,
        limit,
    )


async def get_leaderboard(limit=100):
    return await leaderboard(limit)


# =========================================================
# REFERRALS
# =========================================================

async def get_referrals(uid):
    return await pool.fetch(
        """
        SELECT
            r.id,
            r.referrer_id,
            r.referred_id,
            r.reward,
            r.created_at,
            u.username,
            u.first_name
        FROM referrals r
        LEFT JOIN users u
            ON u.id=r.referred_id
        WHERE r.referrer_id=$1
        ORDER BY r.created_at DESC
        """,
        uid,
    )


# =========================================================
# MISSIONS
# =========================================================

async def get_active_missions():
    return await pool.fetch(
        """
        SELECT
            id,
            title,
            description,
            reward,
            kind,
            target,
            target_value,
            active
        FROM missions
        WHERE active=TRUE
        ORDER BY id DESC
        """
    )


async def create_mission(
    title,
    reward,
    kind,
    target,
    description="",
    target_value="",
):
    return await pool.fetchrow(
        """
        INSERT INTO missions(
            title,
            description,
            reward,
            kind,
            target,
            target_value
        )
        VALUES($1,$2,$3,$4,$5,$6)
        RETURNING *
        """,
        title,
        description,
        reward,
        kind,
        target,
        target_value,
    )


async def claim_mission(uid, mission_id):
    async with pool.acquire() as c:

        async with c.transaction():

            mission = await c.fetchrow(
                """
                SELECT *
                FROM missions
                WHERE id=$1
                AND active=TRUE
                """,
                mission_id,
            )

            if not mission:
                return False, "mission_not_found"

            claimed = await c.fetchval(
                """
                SELECT 1
                FROM mission_claims
                WHERE mission_id=$1
                AND user_id=$2
                """,
                mission_id,
                uid,
            )

            if claimed:
                return False, "already_claimed"

            row = await c.fetchrow(
                """
                SELECT balance
                FROM users
                WHERE id=$1
                FOR UPDATE
                """,
                uid,
            )

            if not row:
                return False, "user_not_found"

            before = row["balance"]
            after = before + mission["reward"]

            await c.execute(
                """
                UPDATE users
                SET balance=$2
                WHERE id=$1
                """,
                uid,
                after,
            )

            await c.execute(
                """
                INSERT INTO mission_claims(
                    mission_id,
                    user_id
                )
                VALUES($1,$2)
                """,
                mission_id,
                uid,
            )

            await c.execute(
                """
                INSERT INTO transactions(
                    user_id,
                    amount,
                    balance_before,
                    balance_after,
                    reason
                )
                VALUES(
                    $1,
                    $2,
                    $3,
                    $4,
                    'mission_reward'
                )
                """,
                uid,
                mission["reward"],
                before,
                after,
            )

            return True, mission["reward"]


# =========================================================
# SHOP
# =========================================================

async def get_shop():
    return await pool.fetch(
        """
        SELECT
            id,
            code,
            title,
            description,
            price,
            kind,
            data
        FROM shop_items
        WHERE active=TRUE
        ORDER BY price ASC
        """
    )


async def get_inventory(uid):
    return await pool.fetch(
        """
        SELECT
            i.item_code AS code,
            i.item_code,
            i.quantity,
            s.code AS shop_code,
            s.title,
            s.description,
            s.kind,
            s.data
        FROM inventory i
        LEFT JOIN shop_items s
            ON s.code=i.item_code
        WHERE i.user_id=$1
        ORDER BY s.price ASC
        """,
        uid,
    )


async def buy_item(uid, code):
    async with pool.acquire() as c:

        async with c.transaction():

            item = await c.fetchrow(
                """
                SELECT *
                FROM shop_items
                WHERE code=$1
                AND active=TRUE
                FOR UPDATE
                """,
                code,
            )

            if not item:
                return False, "item_not_found"

            user = await c.fetchrow(
                """
                SELECT balance,banned
                FROM users
                WHERE id=$1
                FOR UPDATE
                """,
                uid,
            )

            if not user:
                return False, "user_not_found"

            if user["banned"]:
                return False, "banned"

            if user["balance"] < item["price"]:
                return False, "insufficient_funds"

            before = user["balance"]
            after = before - item["price"]

            await c.execute(
                """
                UPDATE users
                SET balance=$2
                WHERE id=$1
                """,
                uid,
                after,
            )

            await c.execute(
                """
                INSERT INTO inventory(
                    user_id,
                    item_code,
                    quantity
                )
                VALUES($1,$2,1)
                ON CONFLICT(user_id,item_code)
                DO UPDATE SET
                    quantity=inventory.quantity+1
                """,
                uid,
                code,
            )

            await c.execute(
                """
                INSERT INTO transactions(
                    user_id,
                    amount,
                    balance_before,
                    balance_after,
                    reason,
                    meta
                )
                VALUES(
                    $1,
                    $2,
                    $3,
                    $4,
                    'shop_purchase',
                    $5
                )
                """,
                uid,
                -item["price"],
                before,
                after,
                {
                    "item": code
                },
            )

            return True, item


# =========================================================
# STATS
# =========================================================

async def get_stats():
    users = await pool.fetchval(
        "SELECT COUNT(*) FROM users"
    )

    coins = await pool.fetchval(
        """
        SELECT COALESCE(
            SUM(balance),
            0
        )
        FROM users
        """
    )

    games_count = await pool.fetchval(
        """
        SELECT COALESCE(
            SUM(games),
            0
        )
        FROM users
        """

    )

    pvp_count = await pool.fetchval(
        """
        SELECT COUNT(*)
        FROM pvp_matches
        """
    )

    referrals = await pool.fetchval(
        """
        SELECT COUNT(*)
        FROM referrals
        """
    )

    return {
        "users": int(users or 0),
        "coins": int(coins or 0),
        "games": int(games_count or 0),
        "pvp": int(pvp_count or 0),
        "referrals": int(referrals or 0),
    }


# =========================================================
# ADMIN
# =========================================================

async def admin_give(
    admin_id,
    target_id,
    amount,
):
    return await balance(
        target_id,
        abs(amount),
        "admin_give",
        {
            "admin_id": admin_id,
        },
    )


async def admin_take(
    admin_id,
    target_id,
    amount,
):
    return await balance(
        target_id,
        -abs(amount),
        "admin_take",
        {
            "admin_id": admin_id,
        },
    )


async def ban_user(uid):
    await pool.execute(
        """
        UPDATE users
        SET banned=TRUE
        WHERE id=$1
        """,
        uid,
    )


async def unban_user(uid):
    await pool.execute(
        """
        UPDATE users
        SET banned=FALSE
        WHERE id=$1
        """,
        uid,
    )


# =========================================================
# PVP
# =========================================================

async def create_pvp(
    creator_id,
    opponent_id,
    stake=250,
):
    return await pool.fetchrow(
        """
        INSERT INTO pvp_matches(
            creator_id,
            opponent_id,
            stake
        )
        VALUES($1,$2,$3)
        RETURNING *
        """,
        creator_id,
        opponent_id,
        stake,
    )


async def get_pvp(match_id):
    return await pool.fetchrow(
        """
        SELECT *
        FROM pvp_matches
        WHERE id=$1
        """,
        match_id,
    )


async def finish_pvp(
    match_id,
    creator_score,
    opponent_score,
    winner_id,
):
    return await pool.fetchrow(
        """
        UPDATE pvp_matches
        SET
            status='finished',
            creator_score=$2,
            opponent_score=$3,
            winner_id=$4
        WHERE id=$1
        RETURNING *
        """,
        match_id,
        creator_score,
        opponent_score,
        winner_id,
    )


# =========================================================
# COMPATIBILITY
# =========================================================

async def get_balance(uid):
    user = await get_user(uid)

    if not user:
        return 0

    return user["balance"]


async def add_coins(uid, amount, reason="system"):
    return await balance(
        uid,
        abs(amount),
        reason,
    )


async def remove_coins(uid, amount, reason="system"):
    return await balance(
        uid,
        -abs(amount),
        reason,
    )
# =========================================================
# UNIVERSAL GAME ENGINE
# =========================================================

async def play_game(
    uid: int,
    game_code: str,
    bet: int,
    win: bool,
    multiplier: float = 0.0,
    data: dict | None = None,
):
    if bet <= 0:
        raise ValueError("invalid_bet")

    user = await get_user(uid)

    if not user:
        raise ValueError("user_not_found")

    if user["banned"]:
        raise ValueError("banned")

    if user["balance"] < bet:
        raise ValueError("insufficient_funds")

    profit = 0

    if win:
        payout = int(bet * multiplier)
        profit = payout - bet
    else:
        payout = 0
        profit = -bet

    async with pool.acquire() as conn:
        async with conn.transaction():

            row = await conn.fetchrow(
                """
                SELECT balance
                FROM users
                WHERE id=$1
                FOR UPDATE
                """,
                uid,
            )

            if not row:
                raise ValueError("user_not_found")

            before = row["balance"]

            if before < bet:
                raise ValueError("insufficient_funds")

            after = before + profit

            await conn.execute(
                """
                UPDATE users
                SET
                    balance=$2,
                    games=games+1,
                    wins=wins+$3,
                    losses=losses+$4,
                    xp=xp+$5,
                    level=GREATEST(1, 1 + (($6)::bigint / 100))
                WHERE id=$1
                """,
                uid,
                after,
                1 if win else 0,
                0 if win else 1,
                max(1, bet // 10),
                after,
            )

            await conn.execute(
                """
                INSERT INTO game_results(
                    user_id,
                    game_code,
                    bet,
                    win,
                    profit,
                    multiplier,
                    data
                )
                VALUES($1,$2,$3,$4,$5,$6,$7)
                """,
                uid,
                game_code,
                bet,
                win,
                profit,
                multiplier,
                data or {},
            )

            await conn.execute(
                """
                INSERT INTO transactions(
                    user_id,
                    amount,
                    balance_before,
                    balance_after,
                    reason,
                    meta
                )
                VALUES(
                    $1,
                    $2,
                    $3,
                    $4,
                    $5,
                    $6
                )
                """,
                uid,
                profit,
                before,
                after,
                f"game:{game_code}",
                data or {},
            )

            return {
                "game": game_code,
                "bet": bet,
                "win": win,
                "multiplier": multiplier,
                "profit": profit,
                "balance_before": before,
                "balance_after": after,
            }


# =========================================================
# GAME LIST
# =========================================================

async def get_games():
    return await pool.fetch(
        """
        SELECT
            id,
            code,
            title,
            description,
            emoji,
            enabled,
            min_bet,
            max_bet
        FROM games
        WHERE enabled=TRUE
        ORDER BY id
        """
    )


async def get_game(code: str):
    return await pool.fetchrow(
        """
        SELECT *
        FROM games
        WHERE code=$1
        """,
        code,
    )


# =========================================================
# PLAYER STATS
# =========================================================

async def get_player_stats(uid: int):
    return await pool.fetchrow(
        """
        SELECT
            id,
            username,
            first_name,
            balance,
            xp,
            level,
            games,
            wins,
            losses,
            referrals,
            streak,
            created_at
        FROM users
        WHERE id=$1
        """,
        uid,
    )


async def get_player_game_stats(uid: int):
    return await pool.fetch(
        """
        SELECT
            game_code,
            COUNT(*) AS games,
            COUNT(*) FILTER (WHERE win=TRUE) AS wins,
            COUNT(*) FILTER (WHERE win=FALSE) AS losses,
            COALESCE(SUM(profit),0) AS profit,
            COALESCE(SUM(bet),0) AS turnover
        FROM game_results
        WHERE user_id=$1
        GROUP BY game_code
        ORDER BY profit DESC
        """,
        uid,
    )
