import os
from contextlib import asynccontextmanager

from fastapi import (
    FastAPI,
    HTTPException,
    Header,
)

from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import (
    init_db,
    close_db,
    get_user,
    leaderboard,
    get_active_missions,
    get_game_history,
    get_transactions,
    get_referrals,
    get_shop,
    get_inventory,
    get_stats,
)


@asynccontextmanager
async def lifespan(app: FastAPI):

    await init_db()

    yield

    await close_db()


app = FastAPI(
    title="Fenix Coin Ultra",
    version="ULTRA",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# HEALTH
# ============================================================

@app.get("/")
async def root():

    return {
        "ok": True,
        "service": "Fenix Coin Ultra",
        "version": "ULTRA",
        "status": "online",
    }


@app.get("/health")
async def health():

    return {
        "ok": True,
        "database": "connected",
        "service": "Fenix Coin Ultra",
    }


# ============================================================
# USER
# ============================================================

@app.get("/api/user/{user_id}")
async def api_user(
    user_id: int,
):

    user = await get_user(user_id)

    if not user:
        raise HTTPException(
            404,
            "User not found"
        )

    return {
        "id": user["id"],
        "username": user["username"],
        "first_name": user["first_name"],
        "last_name": user["last_name"],

        "balance": user["balance"],

        "xp": user["xp"],
        "level": user["level"],

        "games": user["games"],
        "wins": user["wins"],
        "losses": user["losses"],

        "referrals": user["referrals"],
        "streak": user["streak"],

        "banned": user["banned"],
    }


# ============================================================
# PROFILE
# ============================================================

@app.get("/api/profile/{user_id}")
async def profile(
    user_id: int,
):

    user = await get_user(user_id)

    if not user:
        raise HTTPException(
            404,
            "User not found"
        )

    history = await get_game_history(
        user_id,
        10
    )

    return {
        "user": {
            "id": user["id"],
            "username": user["username"],
            "first_name": user["first_name"],
            "balance": user["balance"],
            "xp": user["xp"],
            "level": user["level"],
            "games": user["games"],
            "wins": user["wins"],
            "losses": user["losses"],
            "referrals": user["referrals"],
            "streak": user["streak"],
        },

        "history": [
            {
                "id": x["id"],
                "game": x["game_code"],
                "bet": x["bet"],
                "win": x["win"],
                "profit": x["profit"],
                "multiplier": (
                    float(x["multiplier"])
                    if x["multiplier"] is not None
                    else None
                ),
                "created_at": x["created_at"],
            }

            for x in history
        ]
    }


# ============================================================
# ECONOMY
# ============================================================

@app.get("/api/economy/{user_id}")
async def economy(
    user_id: int,
):

    user = await get_user(user_id)

    if not user:
        raise HTTPException(
            404,
            "User not found"
        )

    transactions = await get_transactions(
        user_id,
        30
    )

    return {
        "balance": user["balance"],

        "transactions": [
            {
                "id": x["id"],
                "amount": x["amount"],
                "before": x["balance_before"],
                "after": x["balance_after"],
                "reason": x["reason"],
                "meta": x["meta"],
                "created_at": x["created_at"],
            }

            for x in transactions
        ]
    }


# ============================================================
# GAMES
# ============================================================

@app.get("/api/games")
async def games():

    return {
        "games": [

            {
                "code": "dice",
                "title": "🎲 Dice",
                "type": "telegram",
                "pvp": True,
            },

            {
                "code": "slots",
                "title": "🎰 Slots",
                "type": "casino",
                "pvp": False,
            },

            {
                "code": "mines",
                "title": "💣 Mines",
                "type": "strategy",
                "pvp": False,
            },

            {
                "code": "crash",
                "title": "📈 Crash",
                "type": "arcade",
                "pvp": False,
            },

            {
                "code": "roulette",
                "title": "🎡 Roulette",
                "type": "casino",
                "pvp": True,
            },

            {
                "code": "football",
                "title": "⚽ Football",
                "type": "telegram",
                "pvp": True,
            },

            {
                "code": "basketball",
                "title": "🏀 Basketball",
                "type": "telegram",
                "pvp": True,
            },

            {
                "code": "darts",
                "title": "🎯 Darts",
                "type": "telegram",
                "pvp": True,
            },

            {
                "code": "bowling",
                "title": "🎳 Bowling",
                "type": "telegram",
                "pvp": True,
            },
        ]
    }


# ============================================================
# MISSIONS
# ============================================================

@app.get("/api/missions")
async def missions():

    rows = await get_active_missions()

    return {
        "missions": [

            {
                "id": x["id"],
                "title": x["title"],
                "description": x["description"],
                "kind": x["kind"],
                "target": x["target"],
                "target_value": x["target_value"],
                "reward": x["reward"],
            }

            for x in rows
        ]
    }


# ============================================================
# REFERRALS
# ============================================================

@app.get("/api/referrals/{user_id}")
async def referrals(
    user_id: int,
):

    user = await get_user(user_id)

    if not user:
        raise HTTPException(
            404,
            "User not found"
        )

    rows = await get_referrals(
        user_id
    )

    username = (
        settings.bot_username
        or "FenixCoinBot"
    )

    link = (
        f"https://t.me/{username}"
        f"?start=ref_{user_id}"
    )

    return {
        "reward": settings.ref_reward,

        "count": len(rows),

        "link": link,

        "referrals": [
            {
                "id": x["referred_id"],
                "username": x["username"],
                "first_name": x["first_name"],
                "reward": x["reward"],
                "created_at": x["created_at"],
            }

            for x in rows
        ]
    }


# ============================================================
# SHOP
# ============================================================

@app.get("/api/shop")
async def shop():

    rows = await get_shop()

    return {
        "items": [

            {
                "id": x["id"],
                "code": x["code"],
                "title": x["title"],
                "description": x["description"],
                "price": x["price"],
                "kind": x["kind"],
                "data": x["data"],
            }

            for x in rows
        ]
    }


# ============================================================
# INVENTORY
# ============================================================

@app.get("/api/inventory/{user_id}")
async def inventory(
    user_id: int,
):

    rows = await get_inventory(
        user_id
    )

    return {
        "items": [

            {
                "item_id": x["item_id"],
                "code": x["code"],
                "title": x["title"],
                "description": x["description"],
                "kind": x["kind"],
                "quantity": x["quantity"],
                "data": x["data"],
            }

            for x in rows
        ]
    }


# ============================================================
# LEADERBOARD
# ============================================================

@app.get("/api/leaderboard")
async def api_leaderboard():

    rows = await leaderboard(
        100
    )

    return {
        "players": [

            {
                "place": index + 1,
                "id": x["id"],
                "username": x["username"],
                "first_name": x["first_name"],
                "balance": x["balance"],
                "level": x["level"],
                "xp": x["xp"],
                "games": x["games"],
                "wins": x["wins"],
                "losses": x["losses"],
                "referrals": x["referrals"],
            }

            for index, x in enumerate(rows)
        ]
    }


# ============================================================
# ADMIN STATISTICS
# ============================================================

@app.get("/api/admin/stats")
async def admin_stats(
    x_admin_id: int | None = Header(
        default=None
    ),
):

    if x_admin_id not in settings.admins:

        raise HTTPException(
            403,
            "Admin access required"
        )

    return await get_stats()


# ============================================================
# CONFIG
# ============================================================

@app.get("/api/config")
async def config():

    return {
        "name": "Fenix Coin",
        "version": "ULTRA",

        "currency": {
            "name": "Fenix Coin",
            "symbol": "🔥",
        },

        "economy": {
            "start_balance":
                settings.start_balance,

            "ref_reward":
                settings.ref_reward,

            "min_bet":
                settings.min_bet,

            "max_bet":
                settings.max_bet,
        },

        "features": {
            "pvp": True,
            "pve": True,
            "missions": True,
            "referrals": True,
            "shop": True,
            "inventory": True,
            "leaderboard": True,
            "admin": True,
        }
    }