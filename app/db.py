import asyncpg

from app.config import settings


pool = None


# =========================================================
# DATABASE SCHEMA
# =========================================================

SCHEMA = """

CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY,

    username TEXT,
    first_name TEXT,

    balance BIGINT NOT NULL DEFAULT 1000,

    xp BIGINT NOT NULL DEFAULT 0,
    level INTEGER NOT NULL DEFAULT 1,

    games INTEGER NOT NULL DEFAULT 0,
    wins INTEGER NOT NULL DEFAULT 0,
    losses INTEGER NOT NULL DEFAULT 0,

    referrals INTEGER NOT NULL DEFAULT 0,

    referred_by BIGINT,

    referral_rewarded BOOLEAN NOT NULL DEFAULT FALSE,

    banned BOOLEAN NOT NULL DEFAULT FALSE,

    streak INTEGER NOT NULL DEFAULT 0,

    daily_claimed_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE TABLE IF NOT EXISTS transactions (

    id BIGSERIAL PRIMARY KEY,

    user_id BIGINT NOT NULL
        REFERENCES users(id)
        ON DELETE CASCADE,

    amount BIGINT NOT NULL,

    reason TEXT NOT NULL,

    meta JSONB NOT NULL DEFAULT '{}',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE TABLE IF NOT EXISTS games (

    id SERIAL PRIMARY KEY,

    code TEXT UNIQUE NOT NULL,

    title TEXT NOT NULL,

    enabled BOOLEAN NOT NULL DEFAULT TRUE,

    min_bet BIGINT NOT NULL DEFAULT 10,

    max_bet BIGINT NOT NULL DEFAULT 100000
);


CREATE TABLE IF NOT EXISTS missions (

    id SERIAL PRIMARY KEY,

    title TEXT NOT NULL,

    reward BIGINT NOT NULL,

    kind TEXT NOT NULL,

    target TEXT,

    active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE TABLE IF NOT EXISTS mission_claims (

    mission_id INTEGER NOT NULL
        REFERENCES missions(id)
        ON DELETE CASCADE,

    user_id BIGINT NOT NULL
        REFERENCES users(id)
        ON DELETE CASCADE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (
        mission_id,
        user_id
    )
);


CREATE TABLE IF NOT EXISTS achievements (

    id SERIAL PRIMARY KEY,

    code TEXT UNIQUE NOT NULL,

    title TEXT NOT NULL,

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

    PRIMARY KEY (
        user_id,
        achievement_id
    )
);


CREATE TABLE IF NOT EXISTS promo_codes (

    code TEXT PRIMARY KEY,

    reward BIGINT NOT NULL,

    max_uses INTEGER NOT NULL DEFAULT 1,

    uses INTEGER NOT NULL DEFAULT 0,

    active BOOLEAN NOT NULL DEFAULT TRUE
);


CREATE TABLE IF NOT EXISTS promo_claims (

    code TEXT NOT NULL
        REFERENCES promo_codes(code)
        ON DELETE CASCADE,

    user_id BIGINT NOT NULL
        REFERENCES users(id)
        ON DELETE CASCADE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (
        code,
        user_id
    )
);


CREATE TABLE IF NOT EXISTS clans (

    id SERIAL PRIMARY KEY,

    name TEXT UNIQUE NOT NULL,

    owner_id BIGINT
        REFERENCES users(id)
        ON DELETE SET NULL,

    treasury BIGINT NOT NULL DEFAULT 0,

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

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (
        clan_id,
        user_id
    )
);


CREATE TABLE IF NOT EXISTS tournaments (

    id SERIAL PRIMARY KEY,

    title TEXT NOT NULL,

    entry_fee BIGINT NOT NULL DEFAULT 0,

    prize BIGINT NOT NULL DEFAULT 0,

    status TEXT NOT NULL DEFAULT 'open',

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

    PRIMARY KEY (
        tournament_id,
        user_id
    )
);


CREATE TABLE IF NOT EXISTS pvp_matches (

    id BIGSERIAL PRIMARY KEY,

    creator_id BIGINT NOT NULL
        REFERENCES users(id)
        ON DELETE CASCADE,

    opponent_id BIGINT
        REFERENCES users(id)
        ON DELETE SET NULL,

    stake BIGINT NOT NULL,

    status TEXT NOT NULL DEFAULT 'open',

    creator_score INTEGER,

    opponent_score INTEGER,

    winner_id BIGINT
        REFERENCES users(id)
        ON DELETE SET NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE TABLE IF NOT EXISTS inventory (

    user_id BIGINT NOT NULL
        REFERENCES users(id)
        ON DELETE CASCADE,

    item_code TEXT NOT NULL,

    quantity INTEGER NOT NULL DEFAULT 1,

    PRIMARY KEY (
        user_id,
        item_code
    )
);


CREATE TABLE IF NOT EXISTS shop_items (

    code TEXT PRIMARY KEY,

    title TEXT NOT NULL,

    price BIGINT NOT NULL,

    kind TEXT NOT NULL,

    active BOOLEAN NOT NULL DEFAULT TRUE
);

"""


# =========================================================
# DEFAULT GAMES
# =========================================================

GAMES = [

    ("dice", "🎲 Dice"),

    ("darts", "🎯 Darts"),

    ("football", "⚽ Football"),

    ("basketball", "🏀 Basketball"),

    ("bowling", "🎳 Bowling"),

    ("slots", "🎰 Slots"),

    ("mines", "💣 Mines 5×5"),

    ("crash", "📈 Crash"),

    ("roulette", "🎡 Roulette"),

]


# =========================================================
# INIT DATABASE
# =========================================================

async def init_db():

    global pool

    if not settings.database_url:

        raise RuntimeError(
            "DATABASE_URL is not configured"
        )

    pool = await asyncpg.create_pool(
        settings.database_url,
        min_size=1,
        max_size=8,
    )

    async with pool.acquire() as connection:

        await connection.execute(
            SCHEMA
        )

        for code, title in GAMES:

            await connection.execute(
                """
                INSERT INTO games (
                    code,
                    title,
                    min_bet,
                    max_bet
                )

                VALUES (
                    $1,
                    $2,
                    $3,
                    $4
                )

                ON CONFLICT (code)
                DO UPDATE SET
                    title = EXCLUDED.title
                """,

                code,
                title,
                settings.min_bet,
                settings.max_bet,
            )

    print("✅ DATABASE INITIALIZED")


# =========================================================
# CLOSE
# =========================================================

async def close_db():

    global pool

    if pool:

        await pool.close()

        pool = None


# =========================================================
# USER
# =========================================================

async def ensure_user(
    user,
    ref=None,
):

    async with pool.acquire() as connection:

        existing = await connection.fetchrow(
            """
            SELECT *
            FROM users
            WHERE id = $1
            """,
            user.id,
        )

        if existing:

            await connection.execute(
                """
                UPDATE users

                SET
                    username = $2,
                    first_name = $3

                WHERE id = $1
                """,

                user.id,
                user.username,
                user.first_name,
            )

            return existing, False

        if ref == user.id:

            ref = None

        row = await connection.fetchrow(
            """
            INSERT INTO users (
                id,
                username,
                first_name,
                balance,
                referred_by
            )

            VALUES (
                $1,
                $2,
                $3,
                $4,
                $5
            )

            RETURNING *
            """,

            user.id,
            user.username,
            user.first_name,
            settings.start_balance,
            ref,
        )

        await connection.execute(
            """
            INSERT INTO transactions (
                user_id,
                amount,
                reason
            )

            VALUES (
                $1,
                $2,
                'start'
            )
            """,

            user.id,
            settings.start_balance,
        )

        return row, True


# =========================================================
# GET USER
# =========================================================

async def get_user(uid):

    return await pool.fetchrow(
        """
        SELECT *
        FROM users
        WHERE id = $1
        """,
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

    async with pool.acquire() as connection:

        async with connection.transaction():

            user = await connection.fetchrow(
                """
                SELECT
                    balance,
                    banned

                FROM users

                WHERE id = $1

                FOR UPDATE
                """,

                uid,
            )

            if not user:

                raise ValueError(
                    "user_not_found"
                )

            if user["banned"]:

                raise ValueError(
                    "banned"
                )

            new_balance = (
                user["balance"] + delta
            )

            if new_balance < 0:

                raise ValueError(
                    "insufficient_funds"
                )

            await connection.execute(
                """
                UPDATE users

                SET balance = $2

                WHERE id = $1
                """,

                uid,
                new_balance,
            )

            await connection.execute(
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
                    $3,
                    $4
                )
                """,

                uid,
                delta,
                reason,
                meta or {},
            )

            return new_balance


# =========================================================
# XP
# =========================================================

async def xp(
    uid,
    amount,
):

    await pool.execute(
        """
        UPDATE users

        SET
            xp = xp + $2,
            level = 1 + ((xp + $2) / 100)

        WHERE id = $1
        """,

        uid,
        amount,
    )


# =========================================================
# GAME RESULT
# =========================================================

async def result(
    uid,
    win,
):

    await pool.execute(
        """
        UPDATE users

        SET
            games = games + 1,

            wins = wins + $2,

            losses = losses + $3

        WHERE id = $1
        """,

        uid,

        1 if win else 0,

        0 if win else 1,
    )