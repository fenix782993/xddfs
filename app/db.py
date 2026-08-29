import asyncpg
import json
from datetime import datetime, timezone
from typing import Optional, Any

from app.config import settings


pool: Optional[asyncpg.Pool] = None


# ============================================================
# DATABASE SCHEMA
# ============================================================

SCHEMA = r"""

-- ==========================================================
-- USERS
-- ==========================================================

CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY,

    username TEXT,
    first_name TEXT,
    last_name TEXT,

    balance BIGINT NOT NULL DEFAULT 1000,

    xp BIGINT NOT NULL DEFAULT 0,
    level INTEGER NOT NULL DEFAULT 1,

    games BIGINT NOT NULL DEFAULT 0,
    wins BIGINT NOT NULL DEFAULT 0,
    losses BIGINT NOT NULL DEFAULT 0,

    referrals INTEGER NOT NULL DEFAULT 0,
    referred_by BIGINT,

    referral_rewarded BOOLEAN NOT NULL DEFAULT FALSE,

    banned BOOLEAN NOT NULL DEFAULT FALSE,

    admin BOOLEAN NOT NULL DEFAULT FALSE,

    streak INTEGER NOT NULL DEFAULT 0,

    daily_claimed_at TIMESTAMPTZ,

    last_activity_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE INDEX IF NOT EXISTS idx_users_balance
ON users(balance DESC);


CREATE INDEX IF NOT EXISTS idx_users_referrer
ON users(referred_by);


CREATE INDEX IF NOT EXISTS idx_users_created
ON users(created_at);


-- ==========================================================
-- TRANSACTIONS
-- ==========================================================

CREATE TABLE IF NOT EXISTS transactions (
    id BIGSERIAL PRIMARY KEY,

    user_id BIGINT NOT NULL
        REFERENCES users(id)
        ON DELETE CASCADE,

    amount BIGINT NOT NULL,

    balance_before BIGINT,

    balance_after BIGINT,

    reason TEXT NOT NULL,

    meta JSONB NOT NULL DEFAULT '{}',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE INDEX IF NOT EXISTS idx_transactions_user
ON transactions(user_id, created_at DESC);


-- ==========================================================
-- GAMES
-- ==========================================================

CREATE TABLE IF NOT EXISTS games (
    id SERIAL PRIMARY KEY,

    code TEXT UNIQUE NOT NULL,

    title TEXT NOT NULL,

    description TEXT,

    emoji TEXT,

    enabled BOOLEAN NOT NULL DEFAULT TRUE,

    min_bet BIGINT NOT NULL DEFAULT 10,

    max_bet BIGINT NOT NULL DEFAULT 100000,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ==========================================================
-- GAME HISTORY
-- ==========================================================

CREATE TABLE IF NOT EXISTS game_history (
    id BIGSERIAL PRIMARY KEY,

    user_id BIGINT NOT NULL
        REFERENCES users(id)
        ON DELETE CASCADE,

    game_code TEXT NOT NULL,

    bet BIGINT NOT NULL DEFAULT 0,

    win BIGINT NOT NULL DEFAULT 0,

    profit BIGINT NOT NULL DEFAULT 0,

    multiplier NUMERIC(12,4),

    result JSONB NOT NULL DEFAULT '{}',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE INDEX IF NOT EXISTS idx_game_history_user
ON game_history(user_id, created_at DESC);


CREATE INDEX IF NOT EXISTS idx_game_history_game
ON game_history(game_code);


-- ==========================================================
-- PVP MATCHES
-- ==========================================================

CREATE TABLE IF NOT EXISTS pvp_matches (
    id BIGSERIAL PRIMARY KEY,

    creator_id BIGINT NOT NULL
        REFERENCES users(id)
        ON DELETE CASCADE,

    opponent_id BIGINT
        REFERENCES users(id)
        ON DELETE SET NULL,

    game_code TEXT NOT NULL DEFAULT 'dice',

    stake BIGINT NOT NULL,

    prize BIGINT NOT NULL DEFAULT 0,

    status TEXT NOT NULL DEFAULT 'open',

    creator_score INTEGER,
    opponent_score INTEGER,

    winner_id BIGINT
        REFERENCES users(id)
        ON DELETE SET NULL,

    loser_id BIGINT
        REFERENCES users(id)
        ON DELETE SET NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    started_at TIMESTAMPTZ,

    finished_at TIMESTAMPTZ
);


CREATE INDEX IF NOT EXISTS idx_pvp_status
ON pvp_matches(status);


CREATE INDEX IF NOT EXISTS idx_pvp_creator
ON pvp_matches(creator_id);


CREATE INDEX IF NOT EXISTS idx_pvp_opponent
ON pvp_matches(opponent_id);


-- ==========================================================
-- PVE BATTLES
-- ==========================================================

CREATE TABLE IF NOT EXISTS pve_battles (
    id BIGSERIAL PRIMARY KEY,

    user_id BIGINT NOT NULL
        REFERENCES users(id)
        ON DELETE CASCADE,

    difficulty TEXT NOT NULL DEFAULT 'easy',

    entry_fee BIGINT NOT NULL DEFAULT 0,

    reward BIGINT NOT NULL DEFAULT 0,

    player_score INTEGER,

    enemy_score INTEGER,

    result TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    finished_at TIMESTAMPTZ
);


CREATE INDEX IF NOT EXISTS idx_pve_user
ON pve_battles(user_id, created_at DESC);


-- ==========================================================
-- MISSIONS
-- ==========================================================

CREATE TABLE IF NOT EXISTS missions (
    id SERIAL PRIMARY KEY,

    title TEXT NOT NULL,

    description TEXT,

    kind TEXT NOT NULL,

    target TEXT,

    target_value BIGINT NOT NULL DEFAULT 1,

    reward BIGINT NOT NULL DEFAULT 0,

    active BOOLEAN NOT NULL DEFAULT TRUE,

    created_by BIGINT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE INDEX IF NOT EXISTS idx_missions_active
ON missions(active);


-- ==========================================================
-- USER MISSION PROGRESS
-- ==========================================================

CREATE TABLE IF NOT EXISTS mission_progress (
    user_id BIGINT NOT NULL
        REFERENCES users(id)
        ON DELETE CASCADE,

    mission_id INTEGER NOT NULL
        REFERENCES missions(id)
        ON DELETE CASCADE,

    progress BIGINT NOT NULL DEFAULT 0,

    completed BOOLEAN NOT NULL DEFAULT FALSE,

    claimed BOOLEAN NOT NULL DEFAULT FALSE,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY(user_id, mission_id)
);


-- ==========================================================
-- REFERRALS
-- ==========================================================

CREATE TABLE IF NOT EXISTS referrals (
    id BIGSERIAL PRIMARY KEY,

    referrer_id BIGINT NOT NULL
        REFERENCES users(id)
        ON DELETE CASCADE,

    referred_id BIGINT UNIQUE NOT NULL
        REFERENCES users(id)
        ON DELETE CASCADE,

    reward BIGINT NOT NULL DEFAULT 600,

    rewarded BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    rewarded_at TIMESTAMPTZ
);


CREATE INDEX IF NOT EXISTS idx_referrals_referrer
ON referrals(referrer_id);


-- ==========================================================
-- DAILY BONUSES
-- ==========================================================

CREATE TABLE IF NOT EXISTS daily_bonus_claims (
    id BIGSERIAL PRIMARY KEY,

    user_id BIGINT NOT NULL
        REFERENCES users(id)
        ON DELETE CASCADE,

    day DATE NOT NULL,

    reward BIGINT NOT NULL,

    streak INTEGER NOT NULL DEFAULT 1,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(user_id, day)
);


-- ==========================================================
-- ACHIEVEMENTS
-- ==========================================================

CREATE TABLE IF NOT EXISTS achievements (
    id SERIAL PRIMARY KEY,

    code TEXT UNIQUE NOT NULL,

    title TEXT NOT NULL,

    description TEXT,

    reward BIGINT NOT NULL DEFAULT 0
);


CREATE TABLE IF NOT EXISTS user_achievements (
    user_id BIGINT NOT NULL
        REFERENCES users(id)
        ON DELETE CASCADE,

    achievement_id INTEGER NOT NULL
        REFERENCES achievements(id)
        ON DELETE CASCADE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY(user_id, achievement_id)
);


-- ==========================================================
-- PROMO CODES
-- ==========================================================

CREATE TABLE IF NOT EXISTS promo_codes (
    code TEXT PRIMARY KEY,

    reward BIGINT NOT NULL,

    max_uses INTEGER NOT NULL DEFAULT 1,

    uses INTEGER NOT NULL DEFAULT 0,

    active BOOLEAN NOT NULL DEFAULT TRUE,

    expires_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE TABLE IF NOT EXISTS promo_claims (
    code TEXT NOT NULL
        REFERENCES promo_codes(code)
        ON DELETE CASCADE,

    user_id BIGINT NOT NULL
        REFERENCES users(id)
        ON DELETE CASCADE,

    reward BIGINT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY(code, user_id)
);


-- ==========================================================
-- SHOP
-- ==========================================================

CREATE TABLE IF NOT EXISTS shop_items (
    id SERIAL PRIMARY KEY,

    code TEXT UNIQUE NOT NULL,

    title TEXT NOT NULL,

    description TEXT,

    price BIGINT NOT NULL,

    kind TEXT NOT NULL,

    data JSONB NOT NULL DEFAULT '{}',

    active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ==========================================================
-- INVENTORY
-- ==========================================================

CREATE TABLE IF NOT EXISTS inventory (
    user_id BIGINT NOT NULL
        REFERENCES users(id)
        ON DELETE CASCADE,

    item_id INTEGER NOT NULL
        REFERENCES shop_items(id)
        ON DELETE CASCADE,

    quantity INTEGER NOT NULL DEFAULT 1,

    acquired_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY(user_id, item_id)
);


-- ==========================================================
-- CLANS
-- ==========================================================

CREATE TABLE IF NOT EXISTS clans (
    id SERIAL PRIMARY KEY,

    name TEXT UNIQUE NOT NULL,

    tag TEXT UNIQUE,

    description TEXT,

    owner_id BIGINT
        REFERENCES users(id)
        ON DELETE SET NULL,

    treasury BIGINT NOT NULL DEFAULT 0,

    level INTEGER NOT NULL DEFAULT 1,

    xp BIGINT NOT NULL DEFAULT 0,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE TABLE IF NOT EXISTS clan_members (
    clan_id INTEGER NOT NULL
        REFERENCES clans(id)
        ON DELETE CASCADE,

    user_id BIGINT NOT NULL
        REFERENCES users(id)
        ON DELETE CASCADE,

    role TEXT NOT NULL DEFAULT 'member',

    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY(clan_id, user_id)
);


-- ==========================================================
-- TOURNAMENTS
-- ==========================================================

CREATE TABLE IF NOT EXISTS tournaments (
    id SERIAL PRIMARY KEY,

    title TEXT NOT NULL,

    description TEXT,

    game_code TEXT NOT NULL,

    entry_fee BIGINT NOT NULL DEFAULT 0,

    prize_pool BIGINT NOT NULL DEFAULT 0,

    max_players INTEGER NOT NULL DEFAULT 32,

    status TEXT NOT NULL DEFAULT 'open',

    starts_at TIMESTAMPTZ,

    ends_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE TABLE IF NOT EXISTS tournament_players (
    tournament_id INTEGER NOT NULL
        REFERENCES tournaments(id)
        ON DELETE CASCADE,

    user_id BIGINT NOT NULL
        REFERENCES users(id)
        ON DELETE CASCADE,

    score INTEGER NOT NULL DEFAULT 0,

    position INTEGER,

    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY(tournament_id, user_id)
);


-- ==========================================================
-- ADMIN ACTION LOG
-- ==========================================================

CREATE TABLE IF NOT EXISTS admin_logs (
    id BIGSERIAL PRIMARY KEY,

    admin_id BIGINT NOT NULL,

    action TEXT NOT NULL,

    target_user_id BIGINT,

    amount BIGINT,

    data JSONB NOT NULL DEFAULT '{}',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ==========================================================
-- NOTIFICATIONS
-- ==========================================================

CREATE TABLE IF NOT EXISTS notifications (
    id BIGSERIAL PRIMARY KEY,

    user_id BIGINT NOT NULL
        REFERENCES users(id)
        ON DELETE CASCADE,

    title TEXT,

    message TEXT NOT NULL,

    read BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ==========================================================
-- SETTINGS
-- ==========================================================

CREATE TABLE IF NOT EXISTS system_settings (
    key TEXT PRIMARY KEY,

    value TEXT NOT NULL,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


"""


# ============================================================
# DEFAULT DATA
# ============================================================

DEFAULT_GAMES = [

    (
        "dice",
        "🎲 Dice",
        "Классическая игра в кости",
        "🎲",
    ),

    (
        "darts",
        "🎯 Darts",
        "Попади как можно ближе к центру",
        "🎯",
    ),

    (
        "football",
        "⚽ Football",
        "Telegram Football",
        "⚽",
    ),

    (
        "basketball",
        "🏀 Basketball",
        "Telegram Basketball",
        "🏀",
    ),

    (
        "bowling",
        "🎳 Bowling",
        "Telegram Bowling",
        "🎳",
    ),

    (
        "slots",
        "🎰 Slots",
        "Игровые слоты",
        "🎰",
    ),

    (
        "mines",
        "💣 Mines",
        "Поле 5×5 с минами",
        "💣",
    ),

    (
        "crash",
        "📈 Crash",
        "Забери выигрыш до краша",
        "📈",
    ),

    (
        "roulette",
        "🎡 Roulette",
        "Рулетка Fenix Coin",
        "🎡",
    ),
]


# ============================================================
# INIT
# ============================================================

async def init_db():

    global pool

    if not settings.database_url:
        raise RuntimeError(
            "DATABASE_URL is not configured"
        )

    pool = await asyncpg.create_pool(
        dsn=settings.database_url,
        min_size=1,
        max_size=10,
        command_timeout=30,
    )

    async with pool.acquire() as conn:

        await conn.execute(SCHEMA)

        # ----------------------------------------------------
        # Default games
        # ----------------------------------------------------

        for code, title, description, emoji in DEFAULT_GAMES:

            await conn.execute(
                """
                INSERT INTO games (
                    code,
                    title,
                    description,
                    emoji,
                    min_bet,
                    max_bet
                )

                VALUES (
                    $1,
                    $2,
                    $3,
                    $4,
                    $5,
                    $6
                )

                ON CONFLICT (code)

                DO UPDATE SET
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    emoji = EXCLUDED.emoji
                """,

                code,
                title,
                description,
                emoji,
                settings.min_bet,
                settings.max_bet,
            )

        # ----------------------------------------------------
        # System settings
        # ----------------------------------------------------

        defaults = {

            "ref_reward":
                str(settings.ref_reward),

            "start_balance":
                str(settings.start_balance),

            "min_bet":
                str(settings.min_bet),

            "max_bet":
                str(settings.max_bet),

            "house_edge":
                str(settings.house_edge),

        }

        for key, value in defaults.items():

            await conn.execute(
                """
                INSERT INTO system_settings (
                    key,
                    value
                )

                VALUES ($1, $2)

                ON CONFLICT (key)
                DO NOTHING
                """,

                key,
                value,
            )

    print("======================================")
    print("🔥 FENIX COIN DATABASE READY")
    print("======================================")


# ============================================================
# CLOSE
# ============================================================

async def close_db():

    global pool

    if pool:

        await pool.close()

        pool = None


# ============================================================
# CHECK
# ============================================================

def check_pool():

    if pool is None:
        raise RuntimeError(
            "Database pool is not initialized"
        )

    return pool


# ============================================================
# USER
# ============================================================

async def get_user(user_id: int):

    db = check_pool()

    return await db.fetchrow(
        """
        SELECT *
        FROM users
        WHERE id = $1
        """,
        user_id,
    )


async def ensure_user(
    user,
    ref: Optional[int] = None,
):

    db = check_pool()

    async with db.acquire() as conn:

        async with conn.transaction():

            existing = await conn.fetchrow(
                """
                SELECT *
                FROM users
                WHERE id = $1
                FOR UPDATE
                """,
                user.id,
            )

            if existing:

                await conn.execute(
                    """
                    UPDATE users

                    SET
                        username = $2,
                        first_name = $3,
                        last_name = $4,
                        last_activity_at = NOW(),
                        updated_at = NOW()

                    WHERE id = $1
                    """,

                    user.id,
                    user.username,
                    user.first_name,
                    user.last_name,
                )

                return existing, False

            # нельзя пригласить самого себя
            if ref == user.id:
                ref = None

            row = await conn.fetchrow(
                """
                INSERT INTO users (
                    id,
                    username,
                    first_name,
                    last_name,
                    balance,
                    referred_by,
                    last_activity_at
                )

                VALUES (
                    $1,
                    $2,
                    $3,
                    $4,
                    $5,
                    $6,
                    NOW()
                )

                RETURNING *
                """,

                user.id,
                user.username,
                user.first_name,
                user.last_name,
                settings.start_balance,
                ref,
            )

            # стартовые монеты
            await conn.execute(
                """
                INSERT INTO transactions (
                    user_id,
                    amount,
                    balance_before,
                    balance_after,
                    reason
                )

                VALUES (
                    $1,
                    $2,
                    0,
                    $2,
                    'start_balance'
                )
                """,

                user.id,
                settings.start_balance,
            )

            # ------------------------------------------------
            # REFERRAL
            # ------------------------------------------------

            if ref:

                # проверяем существование пригласившего
                referrer = await conn.fetchrow(
                    """
                    SELECT id
                    FROM users
                    WHERE id = $1
                    FOR UPDATE
                    """,

                    ref,
                )

                if referrer:

                    reward = settings.ref_reward

                    current_balance = await conn.fetchval(
                        """
                        SELECT balance
                        FROM users
                        WHERE id = $1
                        """,

                        ref,
                    )

                    new_balance = (
                        current_balance + reward
                    )

                    await conn.execute(
                        """
                        UPDATE users

                        SET
                            balance = $2,
                            referrals = referrals + 1

                        WHERE id = $1
                        """,

                        ref,
                        new_balance,
                    )

                    await conn.execute(
                        """
                        INSERT INTO referrals (
                            referrer_id,
                            referred_id,
                            reward,
                            rewarded,
                            rewarded_at
                        )

                        VALUES (
                            $1,
                            $2,
                            $3,
                            TRUE,
                            NOW()
                        )

                        ON CONFLICT (referred_id)
                        DO NOTHING
                        """,

                        ref,
                        user.id,
                        reward,
                    )

                    await conn.execute(
                        """
                        INSERT INTO transactions (
                            user_id,
                            amount,
                            balance_before,
                            balance_after,
                            reason,
                            meta
                        )

                        VALUES (
                            $1,
                            $2,
                            $3,
                            $4,
                            'referral',
                            $5::jsonb
                        )
                        """,

                        ref,
                        reward,
                        current_balance,
                        new_balance,
                        json.dumps({
                            "referred_user": user.id
                        }),
                    )

            return row, True


# ============================================================
# BALANCE
# ============================================================

async def change_balance(
    user_id: int,
    amount: int,
    reason: str,
    meta: Optional[dict] = None,
):

    db = check_pool()

    async with db.acquire() as conn:

        async with conn.transaction():

            row = await conn.fetchrow(
                """
                SELECT
                    balance,
                    banned

                FROM users

                WHERE id = $1

                FOR UPDATE
                """,

                user_id,
            )

            if not row:
                raise ValueError(
                    "user_not_found"
                )

            if row["banned"]:
                raise ValueError(
                    "user_banned"
                )

            before = row["balance"]

            after = before + amount

            if after < 0:
                raise ValueError(
                    "insufficient_funds"
                )

            await conn.execute(
                """
                UPDATE users

                SET
                    balance = $2,
                    updated_at = NOW()

                WHERE id = $1
                """,

                user_id,
                after,
            )

            await conn.execute(
                """
                INSERT INTO transactions (
                    user_id,
                    amount,
                    balance_before,
                    balance_after,
                    reason,
                    meta
                )

                VALUES (
                    $1,
                    $2,
                    $3,
                    $4,
                    $5,
                    $6::jsonb
                )
                """,

                user_id,
                amount,
                before,
                after,
                reason,
                json.dumps(
                    meta or {}
                ),
            )

            return after


async def balance(
    user_id: int,
    delta: int,
    reason: str,
    meta: Optional[dict] = None,
):

    return await change_balance(
        user_id,
        delta,
        reason,
        meta,
    )


# ============================================================
# XP / LEVEL
# ============================================================

async def add_xp(
    user_id: int,
    amount: int,
):

    db = check_pool()

    async with db.acquire() as conn:

        row = await conn.fetchrow(
            """
            SELECT xp, level
            FROM users
            WHERE id = $1
            FOR UPDATE
            """,

            user_id,
        )

        if not row:
            raise ValueError(
                "user_not_found"
            )

        new_xp = row["xp"] + amount

        new_level = (
            new_xp // 100
        ) + 1

        await conn.execute(
            """
            UPDATE users

            SET
                xp = $2,
                level = $3,
                updated_at = NOW()

            WHERE id = $1
            """,

            user_id,
            new_xp,
            new_level,
        )

        return new_xp, new_level


async def xp(
    user_id: int,
    amount: int,
):

    return await add_xp(
        user_id,
        amount,
    )


# ============================================================
# GAME RESULT
# ============================================================

async def record_game(
    user_id: int,
    game_code: str,
    bet: int,
    win: int,
    multiplier: Optional[float] = None,
    result_data: Optional[dict] = None,
):

    profit = win - bet

    db = check_pool()

    async with db.acquire() as conn:

        async with conn.transaction():

            await conn.execute(
                """
                UPDATE users

                SET
                    games = games + 1,
                    wins = wins + $2,
                    losses = losses + $3,
                    updated_at = NOW()

                WHERE id = $1
                """,

                user_id,
                1 if profit > 0 else 0,
                1 if profit <= 0 else 0,
            )

            await conn.execute(
                """
                INSERT INTO game_history (
                    user_id,
                    game_code,
                    bet,
                    win,
                    profit,
                    multiplier,
                    result
                )

                VALUES (
                    $1,
                    $2,
                    $3,
                    $4,
                    $5,
                    $6,
                    $7::jsonb
                )
                """,

                user_id,
                game_code,
                bet,
                win,
                profit,
                multiplier,
                json.dumps(
                    result_data or {}
                ),
            )


async def result(
    user_id: int,
    win: bool,
):

    db = check_pool()

    await db.execute(
        """
        UPDATE users

        SET
            games = games + 1,
            wins = wins + $2,
            losses = losses + $3,
            updated_at = NOW()

        WHERE id = $1
        """,

        user_id,
        1 if win else 0,
        0 if win else 1,
    )


# ============================================================
# GAME HISTORY
# ============================================================

async def get_game_history(
    user_id: int,
    limit: int = 20,
):

    db = check_pool()

    return await db.fetch(
        """
        SELECT *
        FROM game_history
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT $2
        """,

        user_id,
        limit,
    )


# ============================================================
# TRANSACTIONS
# ============================================================

async def get_transactions(
    user_id: int,
    limit: int = 30,
):

    db = check_pool()

    return await db.fetch(
        """
        SELECT *
        FROM transactions
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT $2
        """,

        user_id,
        limit,
    )


# ============================================================
# REFERRALS
# ============================================================

async def get_referrals(
    user_id: int,
):

    db = check_pool()

    return await db.fetch(
        """
        SELECT
            r.*,
            u.username,
            u.first_name

        FROM referrals r

        JOIN users u
            ON u.id = r.referred_id

        WHERE r.referrer_id = $1

        ORDER BY r.created_at DESC
        """,

        user_id,
    )


async def referral_count(
    user_id: int,
):

    db = check_pool()

    return await db.fetchval(
        """
        SELECT COUNT(*)
        FROM referrals
        WHERE referrer_id = $1
        """,

        user_id,
    )


# ============================================================
# MISSIONS
# ============================================================

async def create_mission(
    title: str,
    description: str,
    kind: str,
    target: str,
    target_value: int,
    reward: int,
    created_by: Optional[int] = None,
):

    db = check_pool()

    return await db.fetchrow(
        """
        INSERT INTO missions (
            title,
            description,
            kind,
            target,
            target_value,
            reward,
            created_by
        )

        VALUES (
            $1,
            $2,
            $3,
            $4,
            $5,
            $6,
            $7
        )

        RETURNING *
        """,

        title,
        description,
        kind,
        target,
        target_value,
        reward,
        created_by,
    )


async def get_active_missions():

    db = check_pool()

    return await db.fetch(
        """
        SELECT *
        FROM missions
        WHERE active = TRUE
        ORDER BY id DESC
        """
    )


async def update_mission_progress(
    user_id: int,
    mission_id: int,
    amount: int = 1,
):

    db = check_pool()

    async with db.acquire() as conn:

        async with conn.transaction():

            mission = await conn.fetchrow(
                """
                SELECT *
                FROM missions
                WHERE id = $1
                  AND active = TRUE
                """,

                mission_id,
            )

            if not mission:
                return None

            await conn.execute(
                """
                INSERT INTO mission_progress (
                    user_id,
                    mission_id,
                    progress
                )

                VALUES (
                    $1,
                    $2,
                    $3
                )

                ON CONFLICT (
                    user_id,
                    mission_id
                )

                DO UPDATE SET
                    progress =
                        mission_progress.progress
                        + EXCLUDED.progress,

                    updated_at = NOW()
                """,

                user_id,
                mission_id,
                amount,
            )

            progress = await conn.fetchrow(
                """
                SELECT *
                FROM mission_progress
                WHERE user_id = $1
                  AND mission_id = $2
                """,

                user_id,
                mission_id,
            )

            if (
                progress["progress"]
                >= mission["target_value"]
            ):

                await conn.execute(
                    """
                    UPDATE mission_progress

                    SET completed = TRUE

                    WHERE user_id = $1
                      AND mission_id = $2
                    """,

                    user_id,
                    mission_id,
                )

            return progress


async def claim_mission(
    user_id: int,
    mission_id: int,
):

    db = check_pool()

    async with db.acquire() as conn:

        async with conn.transaction():

            row = await conn.fetchrow(
                """
                SELECT
                    mp.*,
                    m.reward

                FROM mission_progress mp

                JOIN missions m
                    ON m.id = mp.mission_id

                WHERE mp.user_id = $1
                  AND mp.mission_id = $2

                FOR UPDATE
                """,

                user_id,
                mission_id,
            )

            if not row:
                raise ValueError(
                    "mission_not_started"
                )

            if not row["completed"]:
                raise ValueError(
                    "mission_not_completed"
                )

            if row["claimed"]:
                raise ValueError(
                    "mission_already_claimed"
                )

            await conn.execute(
                """
                UPDATE mission_progress

                SET claimed = TRUE

                WHERE user_id = $1
                  AND mission_id = $2
                """,

                user_id,
                mission_id,
            )

            reward = row["reward"]

            await conn.execute(
                """
                UPDATE users

                SET balance = balance + $2

                WHERE id = $1
                """,

                user_id,
                reward,
            )

            await conn.execute(
                """
                INSERT INTO transactions (
                    user_id,
                    amount,
                    reason
                )

                VALUES (
                    $1,
                    $2,
                    'mission_reward'
                )
                """,

                user_id,
                reward,
            )

            return reward


# ============================================================
# DAILY BONUS
# ============================================================

async def claim_daily_bonus(
    user_id: int,
    reward: int,
):

    db = check_pool()

    async with db.acquire() as conn:

        async with conn.transaction():

            today = datetime.now(
                timezone.utc
            ).date()

            existing = await conn.fetchrow(
                """
                SELECT *
                FROM daily_bonus_claims

                WHERE user_id = $1
                  AND day = $2

                FOR UPDATE
                """,

                user_id,
                today,
            )

            if existing:

                raise ValueError(
                    "already_claimed"
                )

            previous = await conn.fetchrow(
                """
                SELECT *
                FROM daily_bonus_claims

                WHERE user_id = $1

                ORDER BY day DESC

                LIMIT 1
                """,

                user_id,
            )

            streak = 1

            if previous:

                diff = (
                    today
                    - previous["day"]
                ).days

                if diff == 1:
                    streak = (
                        previous["streak"] + 1
                    )

            await conn.execute(
                """
                INSERT INTO daily_bonus_claims (
                    user_id,
                    day,
                    reward,
                    streak
                )

                VALUES (
                    $1,
                    $2,
                    $3,
                    $4
                )
                """,

                user_id,
                today,
                reward,
                streak,
            )

            await conn.execute(
                """
                UPDATE users

                SET
                    balance = balance + $2,
                    streak = $3,
                    daily_claimed_at = NOW()

                WHERE id = $1
                """,

                user_id,
                reward,
                streak,
            )

            await conn.execute(
                """
                INSERT INTO transactions (
                    user_id,
                    amount,
                    reason
                )

                VALUES (
                    $1,
                    $2,
                    'daily_bonus'
                )
                """,

                user_id,
                reward,
            )

            return reward, streak


# ============================================================
# PVP
# ============================================================

async def create_pvp(
    creator_id: int,
    stake: int,
    game_code: str = "dice",
):

    # блокируем деньги
    await change_balance(
        creator_id,
        -stake,
        "pvp_lock",
        {
            "game": game_code
        },
    )

    db = check_pool()

    return await db.fetchrow(
        """
        INSERT INTO pvp_matches (
            creator_id,
            game_code,
            stake,
            prize,
            status
        )

        VALUES (
            $1,
            $2,
            $3,
            $4,
            'open'
        )

        RETURNING *
        """,

        creator_id,
        game_code,
        stake,
        stake,
    )


async def join_pvp(
    match_id: int,
    opponent_id: int,
):

    db = check_pool()

    async with db.acquire() as conn:

        async with conn.transaction():

            match = await conn.fetchrow(
                """
                SELECT *
                FROM pvp_matches

                WHERE id = $1
                  AND status = 'open'

                FOR UPDATE
                """,

                match_id,
            )

            if not match:
                raise ValueError(
                    "match_not_found"
                )

            if (
                match["creator_id"]
                == opponent_id
            ):
                raise ValueError(
                    "self_join"
                )

            stake = match["stake"]

            # сначала списываем деньги
            await change_balance(
                opponent_id,
                -stake,
                "pvp_lock",
                {
                    "match": match_id
                },
            )

            prize = stake * 2

            await conn.execute(
                """
                UPDATE pvp_matches

                SET
                    opponent_id = $2,
                    prize = $3,
                    status = 'active',
                    started_at = NOW()

                WHERE id = $1
                """,

                match_id,
                opponent_id,
                prize,
            )

            return await conn.fetchrow(
                """
                SELECT *
                FROM pvp_matches
                WHERE id = $1
                """,

                match_id,
            )


async def finish_pvp(
    match_id: int,
    winner_id: int,
    loser_id: int,
    creator_score: int,
    opponent_score: int,
):

    db = check_pool()

    async with db.acquire() as conn:

        async with conn.transaction():

            match = await conn.fetchrow(
                """
                SELECT *
                FROM pvp_matches

                WHERE id = $1
                  AND status = 'active'

                FOR UPDATE
                """,

                match_id,
            )

            if not match:
                raise ValueError(
                    "match_not_active"
                )

            prize = match["prize"]

            await conn.execute(
                """
                UPDATE pvp_matches

                SET
                    creator_score = $2,
                    opponent_score = $3,
                    winner_id = $4,
                    loser_id = $5,
                    status = 'finished',
                    finished_at = NOW()

                WHERE id = $1
                """,

                match_id,
                creator_score,
                opponent_score,
                winner_id,
                loser_id,
            )

            await conn.execute(
                """
                UPDATE users

                SET
                    balance = balance + $2,
                    wins = wins + 1

                WHERE id = $1
                """,

                winner_id,
                prize,
            )

            await conn.execute(
                """
                UPDATE users

                SET
                    losses = losses + 1

                WHERE id = $1
                """,

                loser_id,
            )

            await conn.execute(
                """
                INSERT INTO transactions (
                    user_id,
                    amount,
                    reason,
                    meta
                )

                VALUES (
                    $1,
                    $2,
                    'pvp_win',
                    $3::jsonb
                )
                """,

                winner_id,
                prize,
                json.dumps({
                    "match_id": match_id
                }),
            )

            return prize


# ============================================================
# LEADERBOARD
# ============================================================

async def leaderboard(
    limit: int = 50,
):

    db = check_pool()

    return await db.fetch(
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

        WHERE banned = FALSE

        ORDER BY balance DESC

        LIMIT $1
        """,

        limit,
    )


# ============================================================
# PROMO
# ============================================================

async def create_promo(
    code: str,
    reward: int,
    max_uses: int = 1,
    expires_at=None,
):

    db = check_pool()

    return await db.fetchrow(
        """
        INSERT INTO promo_codes (
            code,
            reward,
            max_uses,
            expires_at
        )

        VALUES (
            $1,
            $2,
            $3,
            $4
        )

        RETURNING *
        """,

        code.upper(),
        reward,
        max_uses,
        expires_at,
    )


async def claim_promo(
    user_id: int,
    code: str,
):

    db = check_pool()

    async with db.acquire() as conn:

        async with conn.transaction():

            promo = await conn.fetchrow(
                """
                SELECT *
                FROM promo_codes

                WHERE code = $1
                  AND active = TRUE

                FOR UPDATE
                """,

                code.upper(),
            )

            if not promo:
                raise ValueError(
                    "promo_not_found"
                )

            if promo["expires_at"]:

                now = datetime.now(
                    timezone.utc
                )

                if promo["expires_at"] < now:
                    raise ValueError(
                        "promo_expired"
                    )

            if promo["uses"] >= promo["max_uses"]:

                raise ValueError(
                    "promo_limit"
                )

            already = await conn.fetchrow(
                """
                SELECT *
                FROM promo_claims

                WHERE code = $1
                  AND user_id = $2
                """,

                code.upper(),
                user_id,
            )

            if already:
                raise ValueError(
                    "promo_already_used"
                )

            reward = promo["reward"]

            await conn.execute(
                """
                INSERT INTO promo_claims (
                    code,
                    user_id,
                    reward
                )

                VALUES (
                    $1,
                    $2,
                    $3
                )
                """,

                code.upper(),
                user_id,
                reward,
            )

            await conn.execute(
                """
                UPDATE promo_codes

                SET uses = uses + 1

                WHERE code = $1
                """,

                code.upper(),
            )

            await conn.execute(
                """
                UPDATE users

                SET balance = balance + $2

                WHERE id = $1
                """,

                user_id,
                reward,
            )

            await conn.execute(
                """
                INSERT INTO transactions (
                    user_id,
                    amount,
                    reason
                )

                VALUES (
                    $1,
                    $2,
                    'promo'
                )
                """,

                user_id,
                reward,
            )

            return reward


# ============================================================
# ADMIN
# ============================================================

async def admin_give(
    admin_id: int,
    user_id: int,
    amount: int,
):

    new_balance = await change_balance(
        user_id,
        amount,
        "admin_give",
        {
            "admin_id": admin_id
        },
    )

    db = check_pool()

    await db.execute(
        """
        INSERT INTO admin_logs (
            admin_id,
            action,
            target_user_id,
            amount
        )

        VALUES (
            $1,
            'give',
            $2,
            $3
        )
        """,

        admin_id,
        user_id,
        amount,
    )

    return new_balance


async def admin_take(
    admin_id: int,
    user_id: int,
    amount: int,
):

    new_balance = await change_balance(
        user_id,
        -amount,
        "admin_take",
        {
            "admin_id": admin_id
        },
    )

    db = check_pool()

    await db.execute(
        """
        INSERT INTO admin_logs (
            admin_id,
            action,
            target_user_id,
            amount
        )

        VALUES (
            $1,
            'take',
            $2,
            $3
        )
        """,

        admin_id,
        user_id,
        amount,
    )

    return new_balance


async def set_ban(
    admin_id: int,
    user_id: int,
    banned: bool,
):

    db = check_pool()

    await db.execute(
        """
        UPDATE users

        SET
            banned = $2,
            updated_at = NOW()

        WHERE id = $1
        """,

        user_id,
        banned,
    )

    await db.execute(
        """
        INSERT INTO admin_logs (
            admin_id,
            action,
            target_user_id,
            data
        )

        VALUES (
            $1,
            $2,
            $3,
            $4::jsonb
        )
        """,

        admin_id,
        "ban" if banned else "unban",
        user_id,
        json.dumps({
            "banned": banned
        }),
    )


# ============================================================
# SHOP
# ============================================================

async def get_shop():

    db = check_pool()

    return await db.fetch(
        """
        SELECT *
        FROM shop_items

        WHERE active = TRUE

        ORDER BY price ASC
        """
    )


async def buy_item(
    user_id: int,
    item_id: int,
):

    db = check_pool()

    async with db.acquire() as conn:

        async with conn.transaction():

            item = await conn.fetchrow(
                """
                SELECT *
                FROM shop_items

                WHERE id = $1
                  AND active = TRUE

                FOR UPDATE
                """,

                item_id,
            )

            if not item:
                raise ValueError(
                    "item_not_found"
                )

            user = await conn.fetchrow(
                """
                SELECT balance
                FROM users
                WHERE id = $1
                FOR UPDATE
                """,

                user_id,
            )

            if not user:
                raise ValueError(
                    "user_not_found"
                )

            if user["balance"] < item["price"]:
                raise ValueError(
                    "insufficient_funds"
                )

            await conn.execute(
                """
                UPDATE users

                SET balance =
                    balance - $2

                WHERE id = $1
                """,

                user_id,
                item["price"],
            )

            await conn.execute(
                """
                INSERT INTO inventory (
                    user_id,
                    item_id,
                    quantity
                )

                VALUES (
                    $1,
                    $2,
                    1
                )

                ON CONFLICT (
                    user_id,
                    item_id
                )

                DO UPDATE SET
                    quantity =
                        inventory.quantity + 1
                """,

                user_id,
                item_id,
            )

            await conn.execute(
                """
                INSERT INTO transactions (
                    user_id,
                    amount,
                    reason,
                    meta
                )

                VALUES (
                    $1,
                    $2,
                    'shop_purchase',
                    $3::jsonb
                )
                """,

                user_id,
                -item["price"],
                json.dumps({
                    "item_id": item_id
                }),
            )

            return item


# ============================================================
# INVENTORY
# ============================================================

async def get_inventory(
    user_id: int,
):

    db = check_pool()

    return await db.fetch(
        """
        SELECT
            i.*,
            s.code,
            s.title,
            s.description,
            s.kind,
            s.data

        FROM inventory i

        JOIN shop_items s
            ON s.id = i.item_id

        WHERE i.user_id = $1

        ORDER BY i.acquired_at DESC
        """,

        user_id,
    )


# ============================================================
# STATS
# ============================================================

async def get_stats():

    db = check_pool()

    users = await db.fetchval(
        """
        SELECT COUNT(*)
        FROM users
        """
    )

    active_users = await db.fetchval(
        """
        SELECT COUNT(*)
        FROM users
        WHERE banned = FALSE
        """
    )

    total_coins = await db.fetchval(
        """
        SELECT COALESCE(
            SUM(balance),
            0
        )
        FROM users
        """
    )

    games = await db.fetchval(
        """
        SELECT COUNT(*)
        FROM game_history
        """
    )

    pvp = await db.fetchval(
        """
        SELECT COUNT(*)
        FROM pvp_matches
        """
    )

    referrals = await db.fetchval(
        """
        SELECT COUNT(*)
        FROM referrals
        """
    )

    return {
        "users": users,
        "active_users": active_users,
        "total_coins": total_coins,
        "games": games,
        "pvp_matches": pvp,
        "referrals": referrals,
    }