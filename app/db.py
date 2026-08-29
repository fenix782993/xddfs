# ============================================================
# FENIX COIN ULTRA
# app/db.py
# PostgreSQL / asyncpg
# ============================================================

import json
from datetime import datetime, timezone, date
from typing import Optional, Any

import asyncpg

from app.config import settings


# ============================================================
# GLOBAL POOL
# ============================================================

pool: Optional[asyncpg.Pool] = None


# ============================================================
# HELPERS
# ============================================================

def check_pool() -> asyncpg.Pool:
    if pool is None:
        raise RuntimeError("Database pool is not initialized")
    return pool


def json_dump(value: Any) -> str:
    return json.dumps(
        value if value is not None else {},
        ensure_ascii=False,
        default=str,
    )


# ============================================================
# DATABASE SCHEMA
# ============================================================

SCHEMA = r"""
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


CREATE TABLE IF NOT EXISTS games (
    id SERIAL PRIMARY KEY,

    code TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,

    description TEXT DEFAULT '',
    emoji TEXT DEFAULT '🎮',

    enabled BOOLEAN NOT NULL DEFAULT TRUE,

    min_bet BIGINT NOT NULL DEFAULT 10,
    max_bet BIGINT NOT NULL DEFAULT 100000,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


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


CREATE TABLE IF NOT EXISTS pvp_matches (
    id BIGSERIAL PRIMARY KEY,

    creator_id BIGINT NOT NULL
        REFERENCES users(id)
        ON DELETE CASCADE,

    opponent_id BIGINT
        REFERENCES users(id)
        ON DELETE SET NULL,

    game_code TEXT NOT NULL DEFAULT 'dice',

    stake BIGINT NOT NULL DEFAULT 0,
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


CREATE TABLE IF NOT EXISTS missions (
    id SERIAL PRIMARY KEY,

    title TEXT NOT NULL,
    description TEXT DEFAULT '',

    kind TEXT NOT NULL,
    target TEXT DEFAULT '',

    target_value BIGINT NOT NULL DEFAULT 1,
    reward BIGINT NOT NULL DEFAULT 0,

    active BOOLEAN NOT NULL DEFAULT TRUE,

    created_by BIGINT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


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


CREATE TABLE IF NOT EXISTS achievements (
    id SERIAL PRIMARY KEY,

    code TEXT UNIQUE NOT NULL,

    title TEXT NOT NULL,
    description TEXT DEFAULT '',

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


CREATE TABLE IF NOT EXISTS shop_items (
    id SERIAL PRIMARY KEY,

    code TEXT UNIQUE NOT NULL,

    title TEXT NOT NULL,
    description TEXT DEFAULT '',

    price BIGINT NOT NULL,

    kind TEXT NOT NULL,

    data JSONB NOT NULL DEFAULT '{}',

    active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


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


CREATE TABLE IF NOT EXISTS clans (
    id SERIAL PRIMARY KEY,

    name TEXT UNIQUE NOT NULL,
    tag TEXT UNIQUE,

    description TEXT DEFAULT '',

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


CREATE TABLE IF NOT EXISTS tournaments (
    id SERIAL PRIMARY KEY,

    title TEXT NOT NULL,
    description TEXT DEFAULT '',

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


CREATE TABLE IF NOT EXISTS admin_logs (
    id BIGSERIAL PRIMARY KEY,

    admin_id BIGINT NOT NULL,

    action TEXT NOT NULL,

    target_user_id BIGINT,

    amount BIGINT,

    data JSONB NOT NULL DEFAULT '{}',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


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


CREATE TABLE IF NOT EXISTS system_settings (
    key TEXT PRIMARY KEY,

    value TEXT NOT NULL,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


# ============================================================
# DEFAULT GAMES
# ============================================================

DEFAULT_GAMES = [
    ("dice", "🎲 Dice", "Классическая игра в кости", "🎲"),
    ("darts", "🎯 Darts", "Попади как можно ближе к центру", "🎯"),
    ("football", "⚽ Football", "Футбольная игра Telegram", "⚽"),
    ("basketball", "🏀 Basketball", "Баскетбольная игра Telegram", "🏀"),
    ("bowling", "🎳 Bowling", "Боулинг", "🎳"),
    ("slots", "🎰 Slots", "Игровые слоты", "🎰"),
    ("mines", "💣 Mines", "Поле 5×5 с минами", "💣"),
    ("crash", "📈 Crash", "Забери выигрыш до краша", "📈"),
    ("roulette", "🎡 Roulette", "Рулетка Fenix Coin", "🎡"),
    ("coinflip", "🪙 Coin Flip", "Орёл или решка", "🪙"),
    ("blackjack", "🃏 Blackjack", "Карточная игра", "🃏"),
    ("reaction", "⚡ Reaction", "Проверь скорость реакции", "⚡"),
    ("race", "🏁 Race", "Гоночная игра", "🏁"),
]


# ============================================================
# DEFAULT SHOP
# ============================================================

DEFAULT_SHOP = [
    (
        "vip",
        "👑 VIP",
        "VIP-статус игрока",
        50000,
        "vip",
        {"days": 30},
    ),
    (
        "profile_red",
        "🔴 Red Profile",
        "Красное оформление профиля",
        10000,
        "profile_theme",
        {"theme": "red"},
    ),
    (
        "profile_gold",
        "🟡 Gold Profile",
        "Золотое оформление профиля",
        25000,
        "profile_theme",
        {"theme": "gold"},
    ),
    (
        "title_pro",
        "⚡ PRO",
        "Титул PRO",
        15000,
        "title",
        {"title": "PRO"},
    ),
]


# ============================================================
# DEFAULT ACHIEVEMENTS
# ============================================================

DEFAULT_ACHIEVEMENTS = [
    (
        "first_game",
        "🎮 Первая игра",
        "Сыграть первую игру",
        100,
    ),
    (
        "ten_games",
        "🔥 10 игр",
        "Сыграть 10 игр",
        500,
    ),
    (
        "hundred_games",
        "💎 100 игр",
        "Сыграть 100 игр",
        2500,
    ),
    (
        "first_win",
        "🏆 Первая победа",
        "Выиграть первую игру",
        250,
    ),
    (
        "referral",
        "👥 Рефер",
        "Пригласить первого игрока",
        500,
    ),
]


# ============================================================
# INIT DATABASE
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

        # Основная схема
        await conn.execute(SCHEMA)

        # ====================================================
        # SAFE MIGRATIONS
        # ====================================================

        migrations = [
            # USERS
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS username TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS balance BIGINT NOT NULL DEFAULT 1000",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS xp BIGINT NOT NULL DEFAULT 0",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS level INTEGER NOT NULL DEFAULT 1",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS games BIGINT NOT NULL DEFAULT 0",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS wins BIGINT NOT NULL DEFAULT 0",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS losses BIGINT NOT NULL DEFAULT 0",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS referrals INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS referred_by BIGINT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS referral_rewarded BOOLEAN NOT NULL DEFAULT FALSE",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS banned BOOLEAN NOT NULL DEFAULT FALSE",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS admin BOOLEAN NOT NULL DEFAULT FALSE",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS streak INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS daily_claimed_at TIMESTAMPTZ",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_activity_at TIMESTAMPTZ",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()",

            # GAMES
            "ALTER TABLE games ADD COLUMN IF NOT EXISTS code TEXT",
            "ALTER TABLE games ADD COLUMN IF NOT EXISTS title TEXT",
            "ALTER TABLE games ADD COLUMN IF NOT EXISTS description TEXT DEFAULT ''",
            "ALTER TABLE games ADD COLUMN IF NOT EXISTS emoji TEXT DEFAULT '🎮'",
            "ALTER TABLE games ADD COLUMN IF NOT EXISTS enabled BOOLEAN NOT NULL DEFAULT TRUE",
            "ALTER TABLE games ADD COLUMN IF NOT EXISTS min_bet BIGINT NOT NULL DEFAULT 10",
            "ALTER TABLE games ADD COLUMN IF NOT EXISTS max_bet BIGINT NOT NULL DEFAULT 100000",
            "ALTER TABLE games ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()",

            # HISTORY
            "ALTER TABLE game_history ADD COLUMN IF NOT EXISTS game_code TEXT",
            "ALTER TABLE game_history ADD COLUMN IF NOT EXISTS bet BIGINT NOT NULL DEFAULT 0",
            "ALTER TABLE game_history ADD COLUMN IF NOT EXISTS win BIGINT NOT NULL DEFAULT 0",
            "ALTER TABLE game_history ADD COLUMN IF NOT EXISTS profit BIGINT NOT NULL DEFAULT 0",
            "ALTER TABLE game_history ADD COLUMN IF NOT EXISTS multiplier NUMERIC(12,4)",
            "ALTER TABLE game_history ADD COLUMN IF NOT EXISTS result JSONB NOT NULL DEFAULT '{}'",
            "ALTER TABLE game_history ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()",

            # TRANSACTIONS
            "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS amount BIGINT NOT NULL DEFAULT 0",
            "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS balance_before BIGINT",
            "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS balance_after BIGINT",
            "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS reason TEXT NOT NULL DEFAULT 'unknown'",
            "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS meta JSONB NOT NULL DEFAULT '{}'",
            "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()",
        ]

        for query in migrations:
            try:
                await conn.execute(query)
            except Exception as exc:
                print(f"[DB MIGRATION WARNING] {exc}")

        # ====================================================
        # DEFAULT GAMES
        # ====================================================

        for code, title, description, emoji in DEFAULT_GAMES:

            await conn.execute(
                """
                INSERT INTO games
                (
                    code,
                    title,
                    description,
                    emoji,
                    enabled,
                    min_bet,
                    max_bet
                )
                VALUES
                (
                    $1,
                    $2,
                    $3,
                    $4,
                    TRUE,
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
                int(getattr(settings, "min_bet", 10)),
                int(getattr(settings, "max_bet", 100000)),
            )

        # ====================================================
        # SHOP
        # ====================================================

        for (
            code,
            title,
            description,
            price,
            kind,
            data,
        ) in DEFAULT_SHOP:

            await conn.execute(
                """
                INSERT INTO shop_items
                (
                    code,
                    title,
                    description,
                    price,
                    kind,
                    data,
                    active
                )
                VALUES
                (
                    $1,
                    $2,
                    $3,
                    $4,
                    $5,
                    $6::jsonb,
                    TRUE
                )
                ON CONFLICT (code)
                DO NOTHING
                """,
                code,
                title,
                description,
                price,
                kind,
                json_dump(data),
            )

        # ====================================================
        # ACHIEVEMENTS
        # ====================================================

        for (
            code,
            title,
            description,
            reward,
        ) in DEFAULT_ACHIEVEMENTS:

            await conn.execute(
                """
                INSERT INTO achievements
                (
                    code,
                    title,
                    description,
                    reward
                )
                VALUES
                (
                    $1,
                    $2,
                    $3,
                    $4
                )
                ON CONFLICT (code)
                DO NOTHING
                """,
                code,
                title,
                description,
                reward,
            )

        # ====================================================
        # SYSTEM SETTINGS
        # ====================================================

        defaults = {
            "ref_reward": str(
                getattr(settings, "ref_reward", 600)
            ),
            "start_balance": str(
                getattr(settings, "start_balance", 1000)
            ),
            "min_bet": str(
                getattr(settings, "min_bet", 10)
            ),
            "max_bet": str(
                getattr(settings, "max_bet", 100000)
            ),
            "house_edge": str(
                getattr(settings, "house_edge", 0.05)
            ),
        }

        for key, value in defaults.items():

            await conn.execute(
                """
                INSERT INTO system_settings
                (
                    key,
                    value
                )
                VALUES
                (
                    $1,
                    $2
                )
                ON CONFLICT (key)
                DO NOTHING
                """,
                key,
                value,
            )

    print("==========================================")
    print("🔥 FENIX COIN ULTRA DATABASE READY")
    print("🎮 GAMES: READY")
    print("💰 ECONOMY: READY")
    print("👥 REFERRALS: READY")
    print("⚔️ PVP: READY")
    print("🤖 PVE: READY")
    print("📋 MISSIONS: READY")
    print("🛒 SHOP: READY")
    print("🏆 ACHIEVEMENTS: READY")
    print("==========================================")


# ============================================================
# CLOSE
# ============================================================

async def close_db():
    global pool

    if pool is not None:
        await pool.close()
        pool = None


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
        int(user_id),
    )


async def ensure_user(
    user,
    ref: Optional[int] = None,
):
    db = check_pool()

    user_id = int(user.id)

    username = getattr(user, "username", None)
    first_name = getattr(user, "first_name", "") or ""
    last_name = getattr(user, "last_name", None)

    async with db.acquire() as conn:

        async with conn.transaction():

            existing = await conn.fetchrow(
                """
                SELECT *
                FROM users
                WHERE id = $1
                FOR UPDATE
                """,
                user_id,
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
                    user_id,
                    username,
                    first_name,
                    last_name,
                )

                return existing, False

            if ref == user_id:
                ref = None

            start_balance = int(
                getattr(settings, "start_balance", 1000)
            )

            row = await conn.fetchrow(
                """
                INSERT INTO users
                (
                    id,
                    username,
                    first_name,
                    last_name,
                    balance,
                    referred_by,
                    last_activity_at
                )
                VALUES
                (
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
                user_id,
                username,
                first_name,
                last_name,
                start_balance,
                ref,
            )

            await conn.execute(
                """
                INSERT INTO transactions
                (
                    user_id,
                    amount,
                    balance_before,
                    balance_after,
                    reason
                )
                VALUES
                (
                    $1,
                    $2,
                    0,
                    $2,
                    'start_balance'
                )
                """,
                user_id,
                start_balance,
            )

            # ==================================================
            # REFERRAL
            # ==================================================

            if ref:

                referrer = await conn.fetchrow(
                    """
                    SELECT id, balance
                    FROM users
                    WHERE id = $1
                    FOR UPDATE
                    """,
                    int(ref),
                )

                if referrer:

                    reward = int(
                        getattr(settings, "ref_reward", 600)
                    )

                    before = int(referrer["balance"])
                    after = before + reward

                    await conn.execute(
                        """
                        UPDATE users
                        SET
                            balance = $2,
                            referrals = referrals + 1,
                            updated_at = NOW()
                        WHERE id = $1
                        """,
                        int(ref),
                        after,
                    )

                    await conn.execute(
                        """
                        INSERT INTO referrals
                        (
                            referrer_id,
                            referred_id,
                            reward,
                            rewarded,
                            rewarded_at
                        )
                        VALUES
                        (
                            $1,
                            $2,
                            $3,
                            TRUE,
                            NOW()
                        )
                        ON CONFLICT (referred_id)
                        DO NOTHING
                        """,
                        int(ref),
                        user_id,
                        reward,
                    )

                    await conn.execute(
                        """
                        INSERT INTO transactions
                        (
                            user_id,
                            amount,
                            balance_before,
                            balance_after,
                            reason,
                            meta
                        )
                        VALUES
                        (
                            $1,
                            $2,
                            $3,
                            $4,
                            'referral',
                            $5::jsonb
                        )
                        """,
                        int(ref),
                        reward,
                        before,
                        after,
                        json_dump({
                            "referred_user": user_id
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

    amount = int(amount)

    async with db.acquire() as conn:

        async with conn.transaction():

            user = await conn.fetchrow(
                """
                SELECT
                    id,
                    balance,
                    banned
                FROM users
                WHERE id = $1
                FOR UPDATE
                """,
                int(user_id),
            )

            if not user:
                raise ValueError("user_not_found")

            if user["banned"]:
                raise ValueError("user_banned")

            before = int(user["balance"])
            after = before + amount

            if after < 0:
                raise ValueError("insufficient_funds")

            await conn.execute(
                """
                UPDATE users
                SET
                    balance = $2,
                    updated_at = NOW()
                WHERE id = $1
                """,
                int(user_id),
                after,
            )

            await conn.execute(
                """
                INSERT INTO transactions
                (
                    user_id,
                    amount,
                    balance_before,
                    balance_after,
                    reason,
                    meta
                )
                VALUES
                (
                    $1,
                    $2,
                    $3,
                    $4,
                    $5,
                    $6::jsonb
                )
                """,
                int(user_id),
                amount,
                before,
                after,
                str(reason),
                json_dump(meta),
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
# XP
# ============================================================

async def add_xp(
    user_id: int,
    amount: int,
):

    db = check_pool()

    async with db.acquire() as conn:

        async with conn.transaction():

            row = await conn.fetchrow(
                """
                SELECT xp, level
                FROM users
                WHERE id = $1
                FOR UPDATE
                """,
                int(user_id),
            )

            if not row:
                raise ValueError("user_not_found")

            new_xp = max(
                0,
                int(row["xp"]) + int(amount),
            )

            new_level = (new_xp // 100) + 1

            await conn.execute(
                """
                UPDATE users
                SET
                    xp = $2,
                    level = $3,
                    updated_at = NOW()
                WHERE id = $1
                """,
                int(user_id),
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

    db = check_pool()

    bet = int(bet)
    win = int(win)

    profit = win - bet

    async with db.acquire() as conn:

        async with conn.transaction():

            await conn.execute(
                """
                UPDATE users
                SET
                    games = games + 1,
                    wins = wins + $2,
                    losses = losses + $3,
                    last_activity_at = NOW(),
                    updated_at = NOW()
                WHERE id = $1
                """,
                int(user_id),
                1 if profit > 0 else 0,
                1 if profit <= 0 else 0,
            )

            await conn.execute(
                """
                INSERT INTO game_history
                (
                    user_id,
                    game_code,
                    bet,
                    win,
                    profit,
                    multiplier,
                    result
                )
                VALUES
                (
                    $1,
                    $2,
                    $3,
                    $4,
                    $5,
                    $6,
                    $7::jsonb
                )
                """,
                int(user_id),
                str(game_code),
                bet,
                win,
                profit,
                multiplier,
                json_dump(result_data),
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
        int(user_id),
        1 if win else 0,
        0 if win else 1,
    )


# ============================================================
# PLAY GAME
# ============================================================

async def play_game(
    user_id: int,
    game_code: str,
    bet: int,
    win: int,
    multiplier: Optional[float] = None,
    result_data: Optional[dict] = None,
):

    bet = int(bet)
    win = int(win)

    if bet <= 0:
        raise ValueError("Ставка должна быть больше 0")

    if win < 0:
        raise ValueError("Некорректный результат")

    db = check_pool()

    async with db.acquire() as conn:

        async with conn.transaction():

            user = await conn.fetchrow(
                """
                SELECT
                    id,
                    balance,
                    banned
                FROM users
                WHERE id = $1
                FOR UPDATE
                """,
                int(user_id),
            )

            if not user:
                raise ValueError("Пользователь не найден")

            if user["banned"]:
                raise ValueError("Пользователь заблокирован")

            before = int(user["balance"])

            if before < bet:
                raise ValueError(
                    "Недостаточно Fenix Coin"
                )

            profit = win - bet

            after = before + profit

            await conn.execute(
                """
                UPDATE users
                SET
                    balance = $2,
                    games = games + 1,
                    wins = wins + $3,
                    losses = losses + $4,
                    last_activity_at = NOW(),
                    updated_at = NOW()
                WHERE id = $1
                """,
                int(user_id),
                after,
                1 if profit > 0 else 0,
                1 if profit <= 0 else 0,
            )

            await conn.execute(
                """
                INSERT INTO game_history
                (
                    user_id,
                    game_code,
                    bet,
                    win,
                    profit,
                    multiplier,
                    result
                )
                VALUES
                (
                    $1,
                    $2,
                    $3,
                    $4,
                    $5,
                    $6,
                    $7::jsonb
                )
                """,
                int(user_id),
                str(game_code),
                bet,
                win,
                profit,
                multiplier,
                json_dump(result_data),
            )

            await conn.execute(
                """
                INSERT INTO transactions
                (
                    user_id,
                    amount,
                    balance_before,
                    balance_after,
                    reason,
                    meta
                )
                VALUES
                (
                    $1,
                    $2,
                    $3,
                    $4,
                    $5,
                    $6::jsonb
                )
                """,
                int(user_id),
                profit,
                before,
                after,
                f"game:{game_code}",
                json_dump({
                    "game": game_code,
                    "bet": bet,
                    "win": win,
                    "multiplier": multiplier,
                }),
            )

            # XP
            xp_gain = max(
                1,
                min(50, bet // 10),
            )

            await conn.execute(
                """
                UPDATE users
                SET
                    xp = xp + $2,
                    level = ((xp + $2) / 100) + 1
                WHERE id = $1
                """,
                int(user_id),
                xp_gain,
            )

            return {
                "win": profit > 0,
                "bet": bet,
                "win_amount": win,
                "profit": profit,
                "multiplier": multiplier,
                "balance": after,
                "game": str(game_code),
            }


# ============================================================
# GAME HISTORY
# ============================================================

async def get_game_history(
    user_id: int,
    limit: int = 20,
):

    db = check_pool()

    limit = max(
        1,
        min(int(limit), 200),
    )

    return await db.fetch(
        """
        SELECT *
        FROM game_history
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT $2
        """,
        int(user_id),
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

    limit = max(
        1,
        min(int(limit), 200),
    )

    return await db.fetch(
        """
        SELECT *
        FROM transactions
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT $2
        """,
        int(user_id),
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
        LEFT JOIN users u
            ON u.id = r.referred_id
        WHERE r.referrer_id = $1
        ORDER BY r.created_at DESC
        """,
        int(user_id),
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
        int(user_id),
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
        INSERT INTO missions
        (
            title,
            description,
            kind,
            target,
            target_value,
            reward,
            created_by
        )
        VALUES
        (
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
        int(target_value),
        int(reward),
        created_by,
    )


async def get_active_missions():

    db = check_pool()

    return await db.fetch(
        """
        SELECT
            m.*,
            COALESCE(
                mp.progress,
                0
            ) AS progress,
            COALESCE(
                mp.completed,
                FALSE
            ) AS completed,
            COALESCE(
                mp.claimed,
                FALSE
            ) AS claimed
        FROM missions m
        LEFT JOIN mission_progress mp
            ON mp.mission_id = m.id
        WHERE m.active = TRUE
        ORDER BY m.id DESC
        """
    )


async def get_user_missions(
    user_id: int,
):

    db = check_pool()

    return await db.fetch(
        """
        SELECT
            m.*,
            COALESCE(mp.progress, 0) AS progress,
            COALESCE(mp.completed, FALSE) AS completed,
            COALESCE(mp.claimed, FALSE) AS claimed
        FROM missions m
        LEFT JOIN mission_progress mp
            ON mp.mission_id = m.id
            AND mp.user_id = $1
        WHERE m.active = TRUE
        ORDER BY m.id DESC
        """,
        int(user_id),
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
                int(mission_id),
            )

            if not mission:
                return None

            row = await conn.fetchrow(
                """
                INSERT INTO mission_progress
                (
                    user_id,
                    mission_id,
                    progress
                )
                VALUES
                (
                    $1,
                    $2,
                    $3
                )
                ON CONFLICT
                (
                    user_id,
                    mission_id
                )
                DO UPDATE SET
                    progress =
                        mission_progress.progress
                        + EXCLUDED.progress,
                    updated_at = NOW()
                RETURNING *
                """,
                int(user_id),
                int(mission_id),
                int(amount),
            )

            completed = (
                int(row["progress"])
                >= int(mission["target_value"])
            )

            if completed:

                await conn.execute(
                    """
                    UPDATE mission_progress
                    SET completed = TRUE,
                        updated_at = NOW()
                    WHERE user_id = $1
                      AND mission_id = $2
                    """,
                    int(user_id),
                    int(mission_id),
                )

            return await conn.fetchrow(
                """
                SELECT *
                FROM mission_progress
                WHERE user_id = $1
                  AND mission_id = $2
                """,
                int(user_id),
                int(mission_id),
            )


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
                int(user_id),
                int(mission_id),
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

            reward = int(row["reward"])

            user = await conn.fetchrow(
                """
                SELECT balance
                FROM users
                WHERE id = $1
                FOR UPDATE
                """,
                int(user_id),
            )

            before = int(user["balance"])
            after = before + reward

            await conn.execute(
                """
                UPDATE mission_progress
                SET claimed = TRUE
                WHERE user_id = $1
                  AND mission_id = $2
                """,
                int(user_id),
                int(mission_id),
            )

            await conn.execute(
                """
                UPDATE users
                SET
                    balance = $2,
                    updated_at = NOW()
                WHERE id = $1
                """,
                int(user_id),
                after,
            )

            await conn.execute(
                """
                INSERT INTO transactions
                (
                    user_id,
                    amount,
                    balance_before,
                    balance_after,
                    reason
                )
                VALUES
                (
                    $1,
                    $2,
                    $3,
                    $4,
                    'mission_reward'
                )
                """,
                int(user_id),
                reward,
                before,
                after,
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

    reward = int(reward)

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
                int(user_id),
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
                int(user_id),
            )

            streak = 1

            if previous:

                diff = (
                    today - previous["day"]
                ).days

                if diff == 1:
                    streak = (
                        int(previous["streak"]) + 1
                    )

            user = await conn.fetchrow(
                """
                SELECT balance
                FROM users
                WHERE id = $1
                FOR UPDATE
                """,
                int(user_id),
            )

            if not user:
                raise ValueError(
                    "user_not_found"
                )

            before = int(user["balance"])
            after = before + reward

            await conn.execute(
                """
                INSERT INTO daily_bonus_claims
                (
                    user_id,
                    day,
                    reward,
                    streak
                )
                VALUES
                (
                    $1,
                    $2,
                    $3,
                    $4
                )
                """,
                int(user_id),
                today,
                reward,
                streak,
            )

            await conn.execute(
                """
                UPDATE users
                SET
                    balance = $2,
                    streak = $3,
                    daily_claimed_at = NOW(),
                    updated_at = NOW()
                WHERE id = $1
                """,
                int(user_id),
                after,
                streak,
            )

            await conn.execute(
                """
                INSERT INTO transactions
                (
                    user_id,
                    amount,
                    balance_before,
                    balance_after,
                    reason
                )
                VALUES
                (
                    $1,
                    $2,
                    $3,
                    $4,
                    'daily_bonus'
                )
                """,
                int(user_id),
                reward,
                before,
                after,
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

    stake = int(stake)

    if stake <= 0:
        raise ValueError("invalid_stake")

    db = check_pool()

    async with db.acquire() as conn:

        async with conn.transaction():

            user = await conn.fetchrow(
                """
                SELECT balance, banned
                FROM users
                WHERE id = $1
                FOR UPDATE
                """,
                int(creator_id),
            )

            if not user:
                raise ValueError(
                    "user_not_found"
                )

            if user["banned"]:
                raise ValueError(
                    "user_banned"
                )

            if int(user["balance"]) < stake:
                raise ValueError(
                    "insufficient_funds"
                )

            before = int(user["balance"])
            after = before - stake

            await conn.execute(
                """
                UPDATE users
                SET balance = $2
                WHERE id = $1
                """,
                int(creator_id),
                after,
            )

            await conn.execute(
                """
                INSERT INTO transactions
                (
                    user_id,
                    amount,
                    balance_before,
                    balance_after,
                    reason,
                    meta
                )
                VALUES
                (
                    $1,
                    $2,
                    $3,
                    $4,
                    'pvp_lock',
                    $5::jsonb
                )
                """,
                int(creator_id),
                -stake,
                before,
                after,
                json_dump({
                    "game": game_code
                }),
            )

            return await conn.fetchrow(
                """
                INSERT INTO pvp_matches
                (
                    creator_id,
                    game_code,
                    stake,
                    prize,
                    status
                )
                VALUES
                (
                    $1,
                    $2,
                    $3,
                    $3,
                    'open'
                )
                RETURNING *
                """,
                int(creator_id),
                str(game_code),
                stake,
            )


async def get_open_pvp(
    game_code: Optional[str] = None,
):

    db = check_pool()

    if game_code:

        return await db.fetch(
            """
            SELECT *
            FROM pvp_matches
            WHERE status = 'open'
              AND game_code = $1
            ORDER BY created_at DESC
            """,
            str(game_code),
        )

    return await db.fetch(
        """
        SELECT *
        FROM pvp_matches
        WHERE status = 'open'
        ORDER BY created_at DESC
        """
    )


async def get_pvp(
    match_id: int,
):

    db = check_pool()

    return await db.fetchrow(
        """
        SELECT *
        FROM pvp_matches
        WHERE id = $1
        """,
        int(match_id),
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
                int(match_id),
            )

            if not match:
                raise ValueError(
                    "match_not_found"
                )

            if int(match["creator_id"]) == int(opponent_id):
                raise ValueError(
                    "self_join"
                )

            stake = int(match["stake"])

            opponent = await conn.fetchrow(
                """
                SELECT balance, banned
                FROM users
                WHERE id = $1
                FOR UPDATE
                """,
                int(opponent_id),
            )

            if not opponent:
                raise ValueError(
                    "opponent_not_found"
                )

            if opponent["banned"]:
                raise ValueError(
                    "user_banned"
                )

            if int(opponent["balance"]) < stake:
                raise ValueError(
                    "insufficient_funds"
                )

            before = int(opponent["balance"])
            after = before - stake

            await conn.execute(
                """
                UPDATE users
                SET balance = $2
                WHERE id = $1
                """,
                int(opponent_id),
                after,
            )

            await conn.execute(
                """
                INSERT INTO transactions
                (
                    user_id,
                    amount,
                    balance_before,
                    balance_after,
                    reason
                )
                VALUES
                (
                    $1,
                    $2,
                    $3,
                    $4,
                    'pvp_lock'
                )
                """,
                int(opponent_id),
                -stake,
                before,
                after,
            )

            prize = stake * 2

            return await conn.fetchrow(
                """
                UPDATE pvp_matches
                SET
                    opponent_id = $2,
                    prize = $3,
                    status = 'active',
                    started_at = NOW()
                WHERE id = $1
                RETURNING *
                """,
                int(match_id),
                int(opponent_id),
                prize,
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
                int(match_id),
            )

            if not match:
                raise ValueError(
                    "match_not_active"
                )

            prize = int(match["prize"])

            winner = await conn.fetchrow(
                """
                SELECT balance
                FROM users
                WHERE id = $1
                FOR UPDATE
                """,
                int(winner_id),
            )

            if not winner:
                raise ValueError(
                    "winner_not_found"
                )

            before = int(winner["balance"])
            after = before + prize

            await conn.execute(
                """
                UPDATE users
                SET
                    balance = $2,
                    games = games + 1,
                    wins = wins + 1,
                    updated_at = NOW()
                WHERE id = $1
                """,
                int(winner_id),
                after,
            )

            await conn.execute(
                """
                UPDATE users
                SET
                    games = games + 1,
                    losses = losses + 1,
                    updated_at = NOW()
                WHERE id = $1
                """,
                int(loser_id),
            )

            await conn.execute(
                """
                INSERT INTO transactions
                (
                    user_id,
                    amount,
                    balance_before,
                    balance_after,
                    reason,
                    meta
                )
                VALUES
                (
                    $1,
                    $2,
                    $3,
                    $4,
                    'pvp_win',
                    $5::jsonb
                )
                """,
                int(winner_id),
                prize,
                before,
                after,
                json_dump({
                    "match_id": match_id
                }),
            )

            await conn.execute(
                """
                UPDATE pvp_matches
                SET
                    status = 'finished',
                    winner_id = $2,
                    loser_id = $3,
                    creator_score = $4,
                    opponent_score = $5,
                    finished_at = NOW()
                WHERE id = $1
                """,
                int(match_id),
                int(winner_id),
                int(loser_id),
                int(creator_score),
                int(opponent_score),
            )

            return await conn.fetchrow(
                """
                SELECT *
                FROM pvp_matches
                WHERE id = $1
                """,
                int(match_id),
            )


# ============================================================
# LEADERBOARD
# ============================================================

async def leaderboard(
    limit: int = 50,
):

    db = check_pool()

    limit = max(
        1,
        min(int(limit), 100),
    )

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
        INSERT INTO promo_codes
        (
            code,
            reward,
            max_uses,
            expires_at
        )
        VALUES
        (
            $1,
            $2,
            $3,
            $4
        )
        RETURNING *
        """,
        str(code).upper(),
        int(reward),
        int(max_uses),
        expires_at,
    )


async def claim_promo(
    user_id: int,
    code: str,
):

    db = check_pool()

    code = str(code).upper()

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
                code,
            )

            if not promo:
                raise ValueError(
                    "promo_not_found"
                )

            if (
                promo["expires_at"]
                and promo["expires_at"] < datetime.now(timezone.utc)
            ):
                raise ValueError(
                    "promo_expired"
                )

            if int(promo["uses"]) >= int(promo["max_uses"]):
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
                code,
                int(user_id),
            )

            if already:
                raise ValueError(
                    "promo_already_claimed"
                )

            user = await conn.fetchrow(
                """
                SELECT balance
                FROM users
                WHERE id = $1
                FOR UPDATE
                """,
                int(user_id),
            )

            if not user:
                raise ValueError(
                    "user_not_found"
                )

            reward = int(promo["reward"])

            before = int(user["balance"])
            after = before + reward

            await conn.execute(
                """
                INSERT INTO promo_claims
                (
                    code,
                    user_id,
                    reward
                )
                VALUES
                (
                    $1,
                    $2,
                    $3
                )
                """,
                code,
                int(user_id),
                reward,
            )

            await conn.execute(
                """
                UPDATE promo_codes
                SET uses = uses + 1
                WHERE code = $1
                """,
                code,
            )

            await conn.execute(
                """
                UPDATE users
                SET balance = $2
                WHERE id = $1
                """,
                int(user_id),
                after,
            )

            await conn.execute(
                """
                INSERT INTO transactions
                (
                    user_id,
                    amount,
                    balance_before,
                    balance_after,
                    reason,
                    meta
                )
                VALUES
                (
                    $1,
                    $2,
                    $3,
                    $4,
                    'promo',
                    $5::jsonb
                )
                """,
                int(user_id),
                reward,
                before,
                after,
                json_dump({
                    "code": code
                }),
            )

            return reward


# ============================================================
# ADMIN
# ============================================================

async def is_admin(
    user_id: int,
):

    db = check_pool()

    return bool(
        await db.fetchval(
            """
            SELECT admin
            FROM users
            WHERE id = $1
            """,
            int(user_id),
        )
    )


async def admin_give(
    admin_id: int,
    user_id: int,
    amount: int,
):

    if not await is_admin(admin_id):
        raise ValueError(
            "admin_required"
        )

    new_balance = await change_balance(
        user_id,
        int(amount),
        "admin_give",
        {
            "admin_id": int(admin_id)
        },
    )

    db = check_pool()

    await db.execute(
        """
        INSERT INTO admin_logs
        (
            admin_id,
            action,
            target_user_id,
            amount
        )
        VALUES
        (
            $1,
            'give',
            $2,
            $3
        )
        """,
        int(admin_id),
        int(user_id),
        int(amount),
    )

    return new_balance


async def admin_take(
    admin_id: int,
    user_id: int,
    amount: int,
):

    if not await is_admin(admin_id):
        raise ValueError(
            "admin_required"
        )

    new_balance = await change_balance(
        user_id,
        -abs(int(amount)),
        "admin_take",
        {
            "admin_id": int(admin_id)
        },
    )

    db = check_pool()

    await db.execute(
        """
        INSERT INTO admin_logs
        (
            admin_id,
            action,
            target_user_id,
            amount
        )
        VALUES
        (
            $1,
            'take',
            $2,
            $3
        )
        """,
        int(admin_id),
        int(user_id),
        int(amount),
    )

    return new_balance


async def set_ban(
    admin_id: int,
    user_id: int,
    banned: bool,
):

    if not await is_admin(admin_id):
        raise ValueError(
            "admin_required"
        )

    db = check_pool()

    await db.execute(
        """
        UPDATE users
        SET
            banned = $2,
            updated_at = NOW()
        WHERE id = $1
        """,
        int(user_id),
        bool(banned),
    )

    await db.execute(
        """
        INSERT INTO admin_logs
        (
            admin_id,
            action,
            target_user_id,
            data
        )
        VALUES
        (
            $1,
            $2,
            $3,
            $4::jsonb
        )
        """,
        int(admin_id),
        "ban" if banned else "unban",
        int(user_id),
        json_dump({
            "banned": bool(banned)
        }),
    )

    return True


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
    item_id,
):

    db = check_pool()

    async with db.acquire() as conn:

        async with conn.transaction():

            # Поддерживаем и ID, и code.
            if isinstance(item_id, int) or str(item_id).isdigit():

                item = await conn.fetchrow(
                    """
                    SELECT *
                    FROM shop_items
                    WHERE id = $1
                      AND active = TRUE
                    FOR UPDATE
                    """,
                    int(item_id),
                )

            else:

                item = await conn.fetchrow(
                    """
                    SELECT *
                    FROM shop_items
                    WHERE code = $1
                      AND active = TRUE
                    FOR UPDATE
                    """,
                    str(item_id),
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
                int(user_id),
            )

            if not user:
                raise ValueError(
                    "user_not_found"
                )

            price = int(item["price"])
            before = int(user["balance"])

            if before < price:
                raise ValueError(
                    "insufficient_funds"
                )

            after = before - price

            await conn.execute(
                """
                UPDATE users
                SET balance = $2
                WHERE id = $1
                """,
                int(user_id),
                after,
            )

            await conn.execute(
                """
                INSERT INTO inventory
                (
                    user_id,
                    item_id,
                    quantity
                )
                VALUES
                (
                    $1,
                    $2,
                    1
                )
                ON CONFLICT
                (
                    user_id,
                    item_id
                )
                DO UPDATE SET
                    quantity =
                        inventory.quantity + 1
                """,
                int(user_id),
                int(item["id"]),
            )

            await conn.execute(
                """
                INSERT INTO transactions
                (
                    user_id,
                    amount,
                    balance_before,
                    balance_after,
                    reason,
                    meta
                )
                VALUES
                (
                    $1,
                    $2,
                    $3,
                    $4,
                    'shop_purchase',
                    $5::jsonb
                )
                """,
                int(user_id),
                -price,
                before,
                after,
                json_dump({
                    "item_id": item["id"],
                    "code": item["code"],
                }),
            )

            return True, {
                "item": dict(item),
                "balance": after,
            }


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
            s.price,
            s.data
        FROM inventory i
        JOIN shop_items s
            ON s.id = i.item_id
        WHERE i.user_id = $1
        ORDER BY i.acquired_at DESC
        """,
        int(user_id),
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

    missions = await db.fetchval(
        """
        SELECT COUNT(*)
        FROM missions
        WHERE active = TRUE
        """
    )

    return {
        "users": int(users or 0),
        "active_users": int(active_users or 0),
        "total_coins": int(total_coins or 0),
        "games": int(games or 0),
        "pvp_matches": int(pvp or 0),
        "referrals": int(referrals or 0),
        "missions": int(missions or 0),
    }


# ============================================================
# GAMES API
# ============================================================

async def get_games():

    db = check_pool()

    return await db.fetch(
        """
        SELECT
            id,
            code,
            title,
            description,
            emoji,
            enabled,
            min_bet,
            max_bet,
            created_at
        FROM games
        WHERE enabled = TRUE
        ORDER BY id ASC
        """
    )


async def get_game(
    game_code,
):

    db = check_pool()

    return await db.fetchrow(
        """
        SELECT
            id,
            code,
            title,
            description,
            emoji,
            enabled,
            min_bet,
            max_bet,
            created_at
        FROM games
        WHERE code = $1
        LIMIT 1
        """,
        str(game_code),
    )


# ============================================================
# PLAYER STATS
# ============================================================

async def get_player_stats(
    user_id: int,
):

    db = check_pool()

    row = await db.fetchrow(
        """
        SELECT
            id,
            username,
            first_name,
            last_name,
            balance,
            xp,
            level,
            games,
            wins,
            losses,
            referrals,
            streak,
            created_at,
            last_activity_at
        FROM users
        WHERE id = $1
        """,
        int(user_id),
    )

    if not row:
        return None

    return row


# ============================================================
# NOTIFICATIONS
# ============================================================

async def create_notification(
    user_id: int,
    message: str,
    title: str = "",
):

    db = check_pool()

    return await db.fetchrow(
        """
        INSERT INTO notifications
        (
            user_id,
            title,
            message
        )
        VALUES
        (
            $1,
            $2,
            $3
        )
        RETURNING *
        """,
        int(user_id),
        title,
        message,
    )


async def get_notifications(
    user_id: int,
    limit: int = 30,
):

    db = check_pool()

    return await db.fetch(
        """
        SELECT *
        FROM notifications
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT $2
        """,
        int(user_id),
        max(1, min(int(limit), 100)),
    )


async def mark_notifications_read(
    user_id: int,
):

    db = check_pool()

    await db.execute(
        """
        UPDATE notifications
        SET read = TRUE
        WHERE user_id = $1
        """,
        int(user_id),
    )


# ============================================================
# ACHIEVEMENTS
# ============================================================

async def get_achievements():

    db = check_pool()

    return await db.fetch(
        """
        SELECT *
        FROM achievements
        ORDER BY id ASC
        """
    )


async def get_user_achievements(
    user_id: int,
):

    db = check_pool()

    return await db.fetch(
        """
        SELECT
            a.*,
            ua.created_at AS unlocked_at
        FROM user_achievements ua
        JOIN achievements a
            ON a.id = ua.achievement_id
        WHERE ua.user_id = $1
        ORDER BY ua.created_at DESC
        """,
        int(user_id),
    )


async def unlock_achievement(
    user_id: int,
    code: str,
):

    db = check_pool()

    async with db.acquire() as conn:

        async with conn.transaction():

            achievement = await conn.fetchrow(
                """
                SELECT *
                FROM achievements
                WHERE code = $1
                """,
                str(code),
            )

            if not achievement:
                return False

            inserted = await conn.fetchrow(
                """
                INSERT INTO user_achievements
                (
                    user_id,
                    achievement_id
                )
                VALUES
                (
                    $1,
                    $2
                )
                ON CONFLICT DO NOTHING
                RETURNING *
                """,
                int(user_id),
                int(achievement["id"]),
            )

            if not inserted:
                return False

            reward = int(
                achievement["reward"]
            )

            if reward > 0:

                user = await conn.fetchrow(
                    """
                    SELECT balance
                    FROM users
                    WHERE id = $1
                    FOR UPDATE
                    """,
                    int(user_id),
                )

                before = int(user["balance"])
                after = before + reward

                await conn.execute(
                    """
                    UPDATE users
                    SET balance = $2
                    WHERE id = $1
                    """,
                    int(user_id),
                    after,
                )

                await conn.execute(
                    """
                    INSERT INTO transactions
                    (
                        user_id,
                        amount,
                        balance_before,
                        balance_after,
                        reason,
                        meta
                    )
                    VALUES
                    (
                        $1,
                        $2,
                        $3,
                        $4,
                        'achievement',
                        $5::jsonb
                    )
                    """,
                    int(user_id),
                    reward,
                    before,
                    after,
                    json_dump({
                        "achievement": code
                    }),
                )

            return True