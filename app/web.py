import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.db import init_db, close_db, pool, get_user


BASE_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = BASE_DIR / "web"
STATIC_DIR = WEB_DIR / "static"


# =========================================================
# TELEGRAM BOT
# =========================================================

async def run_telegram_bot():
    from aiogram import Bot, Dispatcher

    from app.handlers import (
        start,
        menu,
        games,
        missions,
        admin,
        pvp,
    )

    if not settings.bot_token:
        print("WARNING: BOT_TOKEN is not configured.")
        return

    bot = Bot(token=settings.bot_token)

    dp = Dispatcher()

    dp.include_router(start.r)
    dp.include_router(menu.r)
    dp.include_router(games.r)
    dp.include_router(missions.r)
    dp.include_router(admin.r)
    dp.include_router(pvp.r)

    print("======================================")
    print("🔥 FENIX COIN TELEGRAM BOT STARTING")
    print("======================================")

    try:
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
        )
    finally:
        await bot.session.close()


# =========================================================
# FASTAPI LIFESPAN
# =========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    print("======================================")
    print("🔥 FENIX COIN ULTRA STARTING")
    print("======================================")

    # PostgreSQL
    await init_db()

    print("✅ PostgreSQL connected")

    # Telegram bot
    bot_task = asyncio.create_task(
        run_telegram_bot()
    )

    app.state.bot_task = bot_task

    print("✅ Telegram bot task started")
    print("✅ Mini App started")
    print("======================================")

    try:
        yield

    finally:

        print("Stopping Fenix Coin...")

        bot_task.cancel()

        try:
            await bot_task
        except asyncio.CancelledError:
            pass

        await close_db()


# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(
    title="Fenix Coin Ultra",
    version="ULTRA FULL",
    lifespan=lifespan,
)


# =========================================================
# STATIC
# =========================================================

if STATIC_DIR.exists():

    app.mount(
        "/static",
        StaticFiles(
            directory=str(STATIC_DIR)
        ),
        name="static",
    )


# =========================================================
# HOME / MINI APP
# =========================================================

@app.get(
    "/",
    include_in_schema=False,
)
async def home():

    index = WEB_DIR / "index.html"

    if index.exists():

        return FileResponse(
            str(index),
            media_type="text/html",
        )

    return {
        "ok": True,
        "service": "Fenix Coin Ultra",
        "version": "ULTRA FULL",
    }


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
async def health():

    return {
        "status": "healthy",
        "service": "fenix-coin-ultra",
        "version": "ultra-full",
    }


# =========================================================
# PROFILE
# =========================================================

@app.get("/api/profile/{uid}")
async def profile(uid: int):

    user = await get_user(uid)

    if not user:

        raise HTTPException(
            status_code=404,
            detail="user_not_found",
        )

    return dict(user)


# =========================================================
# GAMES
# =========================================================

@app.get("/api/games")
async def games_api():

    rows = await pool.fetch(
        """
        SELECT
            id,
            code,
            title,
            enabled,
            min_bet,
            max_bet
        FROM games
        WHERE enabled = TRUE
        ORDER BY id
        """
    )

    return [
        dict(row)
        for row in rows
    ]


# =========================================================
# MISSIONS
# =========================================================

@app.get("/api/missions")
async def missions_api():

    rows = await pool.fetch(
        """
        SELECT
            id,
            title,
            reward,
            kind,
            target,
            active
        FROM missions
        WHERE active = TRUE
        ORDER BY id DESC
        """
    )

    return [
        dict(row)
        for row in rows
    ]


# =========================================================
# LEADERBOARD
# =========================================================

@app.get("/api/leaderboard")
async def leaderboard():

    rows = await pool.fetch(
        """
        SELECT
            id,
            username,
            first_name,
            balance,
            xp,
            level,
            wins,
            losses,
            games
        FROM users
        WHERE banned = FALSE
        ORDER BY balance DESC
        LIMIT 50
        """
    )

    return [
        dict(row)
        for row in rows
    ]


# =========================================================
# STATS
# =========================================================

@app.get("/api/stats")
async def stats():

    users = await pool.fetchval(
        "SELECT COUNT(*) FROM users"
    )

    games = await pool.fetchval(
        "SELECT COALESCE(SUM(games), 0) FROM users"
    )

    coins = await pool.fetchval(
        "SELECT COALESCE(SUM(balance), 0) FROM users"
    )

    return {
        "users": users,
        "games": games,
        "coins": coins,
    }