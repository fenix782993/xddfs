import os
from typing import Any, Optional

import asyncpg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

_pool: Optional[asyncpg.Pool] = None


# =========================================================
# CONNECTION
# =========================================================

async def get_pool() -> asyncpg.Pool:
    global _pool

    if _pool is None:
        if not DATABASE_URL:
            raise RuntimeError(
                "DATABASE_URL не задан в Environment Variables"
            )

        _pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=1,
            max_size=10,
            command_timeout=30,
        )

    return _pool


async def close_db():
    global _pool

    if _pool:
        await _pool.close()
        _pool = None


# =========================================================
# DATABASE INIT
# =========================================================

async def init_db():
    pool = await get_pool()

    async with pool.acquire() as conn:

        # =================================================
        # USERS
        # =================================================

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id BIGSERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                username TEXT DEFAULT '',
                first_name TEXT DEFAULT '',
                last_name TEXT DEFAULT '',
                balance BIGINT NOT NULL DEFAULT 1000,
                xp BIGINT NOT NULL DEFAULT 0,
                level INTEGER NOT NULL DEFAULT 1,
                games_played BIGINT NOT NULL DEFAULT 0,
                games_won BIGINT NOT NULL DEFAULT 0,
                games_lost BIGINT NOT NULL DEFAULT 0,
                referrals BIGINT NOT NULL DEFAULT 0,
                referral_earned BIGINT NOT NULL DEFAULT 0,
                referrer_id BIGINT,
                is_admin BOOLEAN NOT NULL DEFAULT FALSE,
                is_banned BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)

        # =================================================
        # USERS MIGRATIONS
        # =================================================

        user_columns = {
            "username": "TEXT DEFAULT ''",
            "first_name": "TEXT DEFAULT ''",
            "last_name": "TEXT DEFAULT ''",
            "balance": "BIGINT NOT NULL DEFAULT 1000",
            "xp": "BIGINT NOT NULL DEFAULT 0",
            "level": "INTEGER NOT NULL DEFAULT 1",
            "games_played": "BIGINT NOT NULL DEFAULT 0",
            "games_won": "BIGINT NOT NULL DEFAULT 0",
            "games_lost": "BIGINT NOT NULL DEFAULT 0",
            "referrals": "BIGINT NOT NULL DEFAULT 0",
            "referral_earned": "BIGINT NOT NULL DEFAULT 0",
            "referrer_id": "BIGINT",
            "is_admin": "BOOLEAN NOT NULL DEFAULT FALSE",
            "is_banned": "BOOLEAN NOT NULL DEFAULT FALSE",
            "created_at": "TIMESTAMPTZ NOT NULL DEFAULT NOW()",
            "updated_at": "TIMESTAMPTZ NOT NULL DEFAULT NOW()",
        }

        for column, definition in user_columns.items():
            await conn.execute(
                f"""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS {column} {definition}
                """
            )

        # =================================================
        # GAMES
        # =================================================

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS games (
                id SERIAL PRIMARY KEY,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                emoji TEXT DEFAULT '🎮',
                enabled BOOLEAN NOT NULL DEFAULT TRUE,
                min_bet BIGINT NOT NULL DEFAULT 100,
                max_bet BIGINT NOT NULL DEFAULT 1000000,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)

        game_columns = {
            "description": "TEXT DEFAULT ''",
            "emoji": "TEXT DEFAULT '🎮'",
            "enabled": "BOOLEAN NOT NULL DEFAULT TRUE",
            "min_bet": "BIGINT NOT NULL DEFAULT 100",
            "max_bet": "BIGINT NOT NULL DEFAULT 1000000",
            "created_at": "TIMESTAMPTZ NOT NULL DEFAULT NOW()",
        }

        for column, definition in game_columns.items():
            await conn.execute(
                f"""
                ALTER TABLE games
                ADD COLUMN IF NOT EXISTS {column} {definition}
                """
            )

        # =================================================
        # GAME RESULTS
        # =================================================

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS game_results (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                game_code TEXT NOT NULL,
                bet BIGINT NOT NULL DEFAULT 0,
                win BOOLEAN NOT NULL DEFAULT FALSE,
                profit BIGINT NOT NULL DEFAULT 0,
                multiplier DOUBLE PRECISION NOT NULL DEFAULT 0,
                data JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)

        # =================================================
        # TRANSACTIONS
        # =================================================

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                amount BIGINT NOT NULL,
                balance_after BIGINT NOT NULL DEFAULT 0,
                type TEXT NOT NULL,
                description TEXT DEFAULT '',
                metadata JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)

        # =================================================
        # REFERRALS
        # =================================================

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS referrals (
                id BIGSERIAL PRIMARY KEY,
                referrer_id BIGINT NOT NULL,
                referred_id BIGINT UNIQUE NOT NULL,
                reward BIGINT NOT NULL DEFAULT 600,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)

        # =================================================
        # MISSIONS
        # =================================================

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS missions (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                mission_type TEXT NOT NULL DEFAULT 'custom',
                target BIGINT NOT NULL DEFAULT 1,
                reward BIGINT NOT NULL DEFAULT 0,
                channel_id TEXT,
                channel_url TEXT,
                enabled BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)

        # =================================================
        # USER MISSIONS
        # =================================================

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_missions (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                mission_id INTEGER NOT NULL,
                progress BIGINT NOT NULL DEFAULT 0,
                completed BOOLEAN NOT NULL DEFAULT FALSE,
                claimed BOOLEAN NOT NULL DEFAULT FALSE,
                completed_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                UNIQUE(user_id, mission_id)
            )
        """)

        # =================================================
        # PVP ROOMS
        # =================================================

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS pvp_rooms (
                id BIGSERIAL PRIMARY KEY,
                room_code TEXT UNIQUE NOT NULL,
                creator_id BIGINT NOT NULL,
                opponent_id BIGINT,
                game_code TEXT NOT NULL,
                bet BIGINT NOT NULL,
                status TEXT NOT NULL DEFAULT 'waiting',
                winner_id BIGINT,
                loser_id BIGINT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                finished_at TIMESTAMPTZ
            )
        """)

        # =================================================
        # PVP MOVES
        # =================================================

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS pvp_moves (
                id BIGSERIAL PRIMARY KEY,
                room_id BIGINT NOT NULL,
                user_id BIGINT NOT NULL,
                move TEXT NOT NULL,
                value BIGINT DEFAULT 0,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)

        # =================================================
        # PVE SESSIONS
        # =================================================

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS pve_sessions (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                game_code TEXT NOT NULL,
                difficulty TEXT NOT NULL DEFAULT 'normal',
                bet BIGINT NOT NULL DEFAULT 0,
                state JSONB DEFAULT '{}'::jsonb,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                finished_at TIMESTAMPTZ
            )
        """)

        # =================================================
        # DAILY BONUSES
        # =================================================

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_bonuses (
                user_id BIGINT PRIMARY KEY,
                streak INTEGER NOT NULL DEFAULT 0,
                last_claim TIMESTAMPTZ,
                total_claims BIGINT NOT NULL DEFAULT 0
            )
        """)

        # =================================================
        # ACHIEVEMENTS
        # =================================================

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS achievements (
                id SERIAL PRIMARY KEY,
                code TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                reward BIGINT NOT NULL DEFAULT 0,
                xp_reward BIGINT NOT NULL DEFAULT 0,
                enabled BOOLEAN NOT NULL DEFAULT TRUE
            )
        """)

        # =================================================
        # USER ACHIEVEMENTS
        # =================================================

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_achievements (
                user_id BIGINT NOT NULL,
                achievement_id INTEGER NOT NULL,
                unlocked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY(user_id, achievement_id)
            )
        """)

        # =================================================
        # ADMIN LOGS
        # =================================================

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS admin_logs (
                id BIGSERIAL PRIMARY KEY,
                admin_id BIGINT NOT NULL,
                action TEXT NOT NULL,
                target_user BIGINT,
                amount BIGINT,
                data JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)

        # =================================================
        # SETTINGS
        # =================================================

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL DEFAULT '',
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)

        # =================================================
        # INDEXES
        # =================================================

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_balance
            ON users(balance DESC)
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_xp
            ON users(xp DESC)
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_game_results_user
            ON game_results(user_id)
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_user
            ON transactions(user_id)
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_pvp_status
            ON pvp_rooms(status)
        """)

        # =================================================
        # DEFAULT GAMES
        # =================================================

        await conn.execute("""
            INSERT INTO games
                (code, name, description, emoji, min_bet, max_bet)
            VALUES
                (
                    'dice',
                    'Dice',
                    'Кости Telegram',
                    '🎲',
                    100,
                    1000000
                ),
                (
                    'slots',
                    'Slots',
                    'Игровой автомат',
                    '🎰',
                    100,
                    1000000
                ),
                (
                    'mines',
                    'Mines',
                    'Мины 5×5',
                    '💣',
                    100,
                    1000000
                ),
                (
                    'crash',
                    'Crash',
                    'Забери выигрыш до краша',
                    '📈',
                    100,
                    1000000
                ),
                (
                    'roulette',
                    'Roulette',
                    'Рулетка',
                    '🎡',
                    100,
                    1000000
                ),
                (
                    'football',
                    'Football',
                    'Футбольная игра',
                    '⚽',
                    100,
                    1000000
                ),
                (
                    'basketball',
                    'Basketball',
                    'Баскетбол',
                    '🏀',
                    100,
                    1000000
                ),
                (
                    'darts',
                    'Darts',
                    'Дартс',
                    '🎯',
                    100,
                    1000000
                ),
                (
                    'bowling',
                    'Bowling',
                    'Боулинг',
                    '🎳',
                    100,
                    1000000
                )
            ON CONFLICT (code) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                emoji = EXCLUDED.emoji,
                min_bet = EXCLUDED.min_bet,
                max_bet = EXCLUDED.max_bet
        """)

        # =================================================
        # DEFAULT SETTINGS
        # =================================================

        defaults = {
            "referral_reward": "600",
            "starting_balance": "1000",
            "currency_name": "Fenix Coin",
            "currency_symbol": "🔥",
            "pvp_commission": "5",
            "maintenance": "false",
        }

        for key, value in defaults.items():
            await conn.execute(
                """
                INSERT INTO settings(key, value)
                VALUES($1, $2)
                ON CONFLICT(key) DO NOTHING
                """,
                key,
                value,
            )

        print("✅ Fenix Coin database initialized")


# =========================================================
# USER
# =========================================================

async def get_user(
    telegram_id: int,
):
    pool = await get_pool()

    async with pool.acquire() as conn:
        return await conn.fetchrow(
            """
            SELECT *
            FROM users
            WHERE telegram_id = $1
            """,
            telegram_id,
        )


async def create_user(
    telegram_id: int,
    username: str = "",
    first_name: str = "",
    last_name: str = "",
    referrer_id: Optional[int] = None,
):

    pool = await get_pool()

    async with pool.acquire() as conn:

        async with conn.transaction():

            user = await conn.fetchrow(
                """
                INSERT INTO users(
                    telegram_id,
                    username,
                    first_name,
                    last_name
                )
                VALUES($1, $2, $3, $4)
                ON CONFLICT(telegram_id)
                DO UPDATE SET
                    username = EXCLUDED.username,
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    updated_at = NOW()
                RETURNING *
                """,
                telegram_id,
                username or "",
                first_name or "",
                last_name or "",
            )

            if (
                referrer_id
                and referrer_id != telegram_id
            ):
                referrer = await conn.fetchrow(
                    """
                    SELECT *
                    FROM users
                    WHERE telegram_id = $1
                    """,
                    referrer_id,
                )

                if referrer:

                    existing = await conn.fetchval(
                        """
                        SELECT id
                        FROM referrals
                        WHERE referred_id = $1
                        """,
                        telegram_id,
                    )

                    if not existing:

                        reward = await get_setting_int_conn(
                            conn,
                            "referral_reward",
                            600,
                        )

                        await conn.execute(
                            """
                            UPDATE users
                            SET
                                balance = balance + $1,
                                referrals = referrals + 1,
                                referral_earned =
                                    referral_earned + $1,
                                updated_at = NOW()
                            WHERE telegram_id = $2
                            """,
                            reward,
                            referrer_id,
                        )

                        await conn.execute(
                            """
                            INSERT INTO referrals(
                                referrer_id,
                                referred_id,
                                reward
                            )
                            VALUES($1, $2, $3)
                            ON CONFLICT(referred_id)
                            DO NOTHING
                            """,
                            referrer_id,
                            telegram_id,
                            reward,
                        )

                        await conn.execute(
                            """
                            UPDATE users
                            SET referrer_id = $1
                            WHERE telegram_id = $2
                            AND referrer_id IS NULL
                            """,
                            referrer_id,
                            telegram_id,
                        )

                        ref_balance = await conn.fetchval(
                            """
                            SELECT balance
                            FROM users
                            WHERE telegram_id = $1
                            """,
                            referrer_id,
                        )

                        await conn.execute(
                            """
                            INSERT INTO transactions(
                                user_id,
                                amount,
                                balance_after,
                                type,
                                description
                            )
                            VALUES(
                                $1,
                                $2,
                                $3,
                                'referral',
                                'Реферальная награда'
                            )
                            """,
                            referrer_id,
                            reward,
                            ref_balance,
                        )

            return user


# =========================================================
# BALANCE
# =========================================================

async def change_balance(
    telegram_id: int,
    amount: int,
    transaction_type: str = "system",
    metadata: Optional[dict] = None,
):

    pool = await get_pool()

    async with pool.acquire() as conn:

        async with conn.transaction():

            user = await conn.fetchrow(
                """
                SELECT *
                FROM users
                WHERE telegram_id = $1
                FOR UPDATE
                """,
                telegram_id,
            )

            if not user:
                raise ValueError(
                    "Пользователь не найден"
                )

            new_balance = (
                user["balance"] + amount
            )

            if new_balance < 0:
                raise ValueError(
                    "Недостаточно Fenix Coin"
                )

            await conn.execute(
                """
                UPDATE users
                SET
                    balance = $1,
                    updated_at = NOW()
                WHERE telegram_id = $2
                """,
                new_balance,
                telegram_id,
            )

            await conn.execute(
                """
                INSERT INTO transactions(
                    user_id,
                    amount,
                    balance_after,
                    type,
                    metadata
                )
                VALUES(
                    $1,
                    $2,
                    $3,
                    $4,
                    $5::jsonb
                )
                """,
                telegram_id,
                amount,
                new_balance,
                transaction_type,
                __import__("json").dumps(
                    metadata or {}
                ),
            )

            return new_balance


# =========================================================
# XP / LEVEL
# =========================================================

async def add_xp(
    telegram_id: int,
    amount: int,
):

    pool = await get_pool()

    async with pool.acquire() as conn:

        user = await conn.fetchrow(
            """
            SELECT xp, level
            FROM users
            WHERE telegram_id = $1
            FOR UPDATE
            """,
            telegram_id,
        )

        if not user:
            return None

        xp = user["xp"] + amount

        level = max(
            1,
            int(xp // 1000) + 1,
        )

        await conn.execute(
            """
            UPDATE users
            SET
                xp = $1,
                level = $2,
                updated_at = NOW()
            WHERE telegram_id = $3
            """,
            xp,
            level,
            telegram_id,
        )

        return {
            "xp": xp,
            "level": level,
        }


# =========================================================
# GAME RESULT
# =========================================================

async def add_game_result(
    user_id: int,
    game_code: str,
    bet: int,
    win: bool,
    profit: int,
    multiplier: float = 0,
    data: Optional[dict] = None,
):

    pool = await get_pool()

    async with pool.acquire() as conn:

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
            VALUES(
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
            __import__("json").dumps(
                data or {}
            ),
        )

        await conn.execute(
            """
            UPDATE users
            SET
                games_played =
                    games_played + 1,
                games_won =
                    games_won + CASE
                        WHEN $2 THEN 1
                        ELSE 0
                    END,
                games_lost =
                    games_lost + CASE
                        WHEN NOT $2 THEN 1
                        ELSE 0
                    END,
                updated_at = NOW()
            WHERE telegram_id = $1
            """,
            user_id,
            win,
        )

    return True


# =========================================================
# LEADERBOARD
# =========================================================

async def get_top_users(
    limit: int = 10,
):

    pool = await get_pool()

    async with pool.acquire() as conn:
        return await conn.fetch(
            """
            SELECT
                telegram_id,
                username,
                first_name,
                balance,
                xp,
                level,
                games_won
            FROM users
            WHERE is_banned = FALSE
            ORDER BY balance DESC
            LIMIT $1
            """,
            limit,
        )


# =========================================================
# REFERRALS
# =========================================================

async def get_referrals(
    telegram_id: int,
):

    pool = await get_pool()

    async with pool.acquire() as conn:

        return await conn.fetch(
            """
            SELECT
                r.*,
                u.username,
                u.first_name
            FROM referrals r
            LEFT JOIN users u
                ON u.telegram_id = r.referred_id
            WHERE r.referrer_id = $1
            ORDER BY r.created_at DESC
            """,
            telegram_id,
        )


# =========================================================
# MISSIONS
# =========================================================

async def get_active_missions():

    pool = await get_pool()

    async with pool.acquire() as conn:

        return await conn.fetch(
            """
            SELECT *
            FROM missions
            WHERE enabled = TRUE
            ORDER BY id DESC
            """
        )


async def create_mission(
    title: str,
    description: str,
    mission_type: str,
    target: int,
    reward: int,
    channel_id: Optional[str] = None,
    channel_url: Optional[str] = None,
):

    pool = await get_pool()

    async with pool.acquire() as conn:

        return await conn.fetchrow(
            """
            INSERT INTO missions(
                title,
                description,
                mission_type,
                target,
                reward,
                channel_id,
                channel_url
            )
            VALUES(
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
            mission_type,
            target,
            reward,
            channel_id,
            channel_url,
        )


# =========================================================
# SETTINGS
# =========================================================

async def get_setting(
    key: str,
    default: str = "",
):

    pool = await get_pool()

    async with pool.acquire() as conn:
        value = await conn.fetchval(
            """
            SELECT value
            FROM settings
            WHERE key = $1
            """,
            key,
        )

        return (
            value
            if value is not None
            else default
        )


async def get_setting_int(
    key: str,
    default: int = 0,
):

    value = await get_setting(
        key,
        str(default),
    )

    try:
        return int(value)
    except (
        TypeError,
        ValueError,
    ):
        return default


async def get_setting_int_conn(
    conn,
    key: str,
    default: int = 0,
):

    value = await conn.fetchval(
        """
        SELECT value
        FROM settings
        WHERE key = $1
        """,
        key,
    )

    try:
        return int(value)
    except (
        TypeError,
        ValueError,
    ):
        return default


async def set_setting(
    key: str,
    value: str,
):

    pool = await get_pool()

    async with pool.acquire() as conn:

        await conn.execute(
            """
            INSERT INTO settings(
                key,
                value,
                updated_at
            )
            VALUES(
                $1,
                $2,
                NOW()
            )
            ON CONFLICT(key)
            DO UPDATE SET
                value = EXCLUDED.value,
                updated_at = NOW()
            """,
            key,
            str(value),
        )


# =========================================================
# ADMIN
# =========================================================

async def is_admin(
    telegram_id: int,
):

    pool = await get_pool()

    async with pool.acquire() as conn:

        result = await conn.fetchval(
            """
            SELECT is_admin
            FROM users
            WHERE telegram_id = $1
            """,
            telegram_id,
        )

        return bool(result)


async def set_admin(
    telegram_id: int,
    value: bool = True,
):

    pool = await get_pool()

    async with pool.acquire() as conn:

        await conn.execute(
            """
            UPDATE users
            SET is_admin = $1
            WHERE telegram_id = $2
            """,
            value,
            telegram_id,
        )


async def ban_user(
    telegram_id: int,
    value: bool = True,
):

    pool = await get_pool()

    async with pool.acquire() as conn:

        await conn.execute(
            """
            UPDATE users
            SET is_banned = $1
            WHERE telegram_id = $2
            """,
            value,
            telegram_id,
        )


async def admin_adjust_balance(
    admin_id: int,
    target_user: int,
    amount: int,
    reason: str = "admin",
):

    new_balance = await change_balance(
        target_user,
        amount,
        "admin",
        {
            "admin_id": admin_id,
            "reason": reason,
        },
    )

    pool = await get_pool()

    async with pool.acquire() as conn:

        await conn.execute(
            """
            INSERT INTO admin_logs(
                admin_id,
                action,
                target_user,
                amount,
                data
            )
            VALUES(
                $1,
                'balance_change',
                $2,
                $3,
                $4::jsonb
            )
            """,
            admin_id,
            target_user,
            amount,
            __import__("json").dumps({
                "reason": reason
            }),
        )

    return new_balance


# =========================================================
# STATS
# =========================================================

async def get_stats():

    pool = await get_pool()

    async with pool.acquire() as conn:

        users = await conn.fetchval(
            "SELECT COUNT(*) FROM users"
        )

        balance = await conn.fetchval(
            "SELECT COALESCE(SUM(balance), 0) FROM users"
        )

        games = await conn.fetchval(
            "SELECT COUNT(*) FROM game_results"
        )

        pvp = await conn.fetchval(
            "SELECT COUNT(*) FROM pvp_rooms"
        )

        return {
            "users": users or 0,
            "balance": balance or 0,
            "games": games or 0,
            "pvp": pvp or 0,
        }
# =========================================================
# COMPATIBILITY FUNCTIONS FOR WEB.PY
# =========================================================

async def leaderboard(limit: int = 10):
    return await get_top_users(limit)


async def get_leaderboard(limit: int = 10):
    return await get_top_users(limit)


async def get_user_by_id(telegram_id: int):
    return await get_user(telegram_id)


async def ensure_user(
    telegram_id: int,
    username: str = "",
    first_name: str = "",
    last_name: str = "",
):
    user = await get_user(telegram_id)

    if user:
        return user

    return await create_user(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
    )


async def add_coins(
    telegram_id: int,
    amount: int,
    reason: str = "system",
):
    return await change_balance(
        telegram_id,
        amount,
        reason,
    )


async def remove_coins(
    telegram_id: int,
    amount: int,
    reason: str = "game",
):
    return await change_balance(
        telegram_id,
        -abs(amount),
        reason,
    )


async def get_balance(
    telegram_id: int,
):
    user = await get_user(telegram_id)

    if not user:
        return 0

    return user["balance"]


async def update_user(
    telegram_id: int,
    **fields: Any,
):

    allowed = {
        "username",
        "first_name",
        "last_name",
        "balance",
        "xp",
        "level",
        "games_played",
        "games_won",
        "games_lost",
        "referrals",
        "referral_earned",
        "referrer_id",
        "is_admin",
        "is_banned",
    }

    fields = {
        key: value
        for key, value in fields.items()
        if key in allowed
    }

    if not fields:
        return await get_user(telegram_id)

    pool = await get_pool()

    set_parts = []
    values = []

    index = 1

    for key, value in fields.items():
        set_parts.append(
            f"{key} = ${index}"
        )
        values.append(value)
        index += 1

    values.append(telegram_id)

    query = f"""
        UPDATE users
        SET
            {", ".join(set_parts)},
            updated_at = NOW()
        WHERE telegram_id = ${index}
        RETURNING *
    """

    async with pool.acquire() as conn:
        return await conn.fetchrow(
            query,
            *values,
        )


async def get_all_users(
    limit: int = 1000,
    offset: int = 0,
):
    pool = await get_pool()

    async with pool.acquire() as conn:
        return await conn.fetch(
            """
            SELECT *
            FROM users
            ORDER BY id DESC
            LIMIT $1
            OFFSET $2
            """,
            limit,
            offset,
        )


async def count_users():
    pool = await get_pool()

    async with pool.acquire() as conn:
        return await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM users
            """
        )


async def get_game(
    code: str,
):
    pool = await get_pool()

    async with pool.acquire() as conn:
        return await conn.fetchrow(
            """
            SELECT *
            FROM games
            WHERE code = $1
            """,
            code,
        )


async def get_games():
    pool = await get_pool()

    async with pool.acquire() as conn:
        return await conn.fetch(
            """
            SELECT *
            FROM games
            WHERE enabled = TRUE
            ORDER BY id
            """
        )


async def get_all_games():
    pool = await get_pool()

    async with pool.acquire() as conn:
        return await conn.fetch(
            """
            SELECT *
            FROM games
            ORDER BY id
            """
        )


async def set_game_enabled(
    code: str,
    enabled: bool,
):
    pool = await get_pool()

    async with pool.acquire() as conn:
        return await conn.fetchrow(
            """
            UPDATE games
            SET enabled = $1
            WHERE code = $2
            RETURNING *
            """,
            enabled,
            code,
        )


async def get_user_stats(
    telegram_id: int,
):
    pool = await get_pool()

    async with pool.acquire() as conn:

        user = await conn.fetchrow(
            """
            SELECT *
            FROM users
            WHERE telegram_id = $1
            """,
            telegram_id,
        )

        if not user:
            return None

        games = await conn.fetchrow(
            """
            SELECT
                COUNT(*) AS total,
                COUNT(*) FILTER (
                    WHERE win = TRUE
                ) AS wins,
                COUNT(*) FILTER (
                    WHERE win = FALSE
                ) AS losses,
                COALESCE(
                    SUM(profit),
                    0
                ) AS profit
            FROM game_results
            WHERE user_id = $1
            """,
            telegram_id,
        )

        return {
            "user": user,
            "games": games,
        }


async def get_transactions(
    telegram_id: int,
    limit: int = 50,
):
    pool = await get_pool()

    async with pool.acquire() as conn:
        return await conn.fetch(
            """
            SELECT *
            FROM transactions
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            telegram_id,
            limit,
        )


async def create_pvp_room(
    room_code: str,
    creator_id: int,
    game_code: str,
    bet: int,
):
    pool = await get_pool()

    async with pool.acquire() as conn:
        return await conn.fetchrow(
            """
            INSERT INTO pvp_rooms(
                room_code,
                creator_id,
                game_code,
                bet
            )
            VALUES(
                $1,
                $2,
                $3,
                $4
            )
            RETURNING *
            """,
            room_code,
            creator_id,
            game_code,
            bet,
        )


async def get_pvp_room(
    room_code: str,
):
    pool = await get_pool()

    async with pool.acquire() as conn:
        return await conn.fetchrow(
            """
            SELECT *
            FROM pvp_rooms
            WHERE room_code = $1
            """,
            room_code,
        )


async def join_pvp_room(
    room_code: str,
    opponent_id: int,
):
    pool = await get_pool()

    async with pool.acquire() as conn:
        return await conn.fetchrow(
            """
            UPDATE pvp_rooms
            SET
                opponent_id = $1,
                status = 'active'
            WHERE room_code = $2
            AND status = 'waiting'
            RETURNING *
            """,
            opponent_id,
            room_code,
        )


async def finish_pvp_room(
    room_code: str,
    winner_id: int,
    loser_id: int,
):
    pool = await get_pool()

    async with pool.acquire() as conn:
        return await conn.fetchrow(
            """
            UPDATE pvp_rooms
            SET
                winner_id = $1,
                loser_id = $2,
                status = 'finished',
                finished_at = NOW()
            WHERE room_code = $3
            RETURNING *
            """,
            winner_id,
            loser_id,
            room_code,
        )
