import os
import random
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from app.db import (
    init_db,
    close_db,
    ensure_user,
    get_user,
    get_games,
    get_game,
    play_game,
    get_game_history,
    get_transactions,
    leaderboard,
    get_referrals,
    get_active_missions,
    claim_mission,
    get_shop,
    get_inventory,
    get_stats,
    get_player_stats,
)

from app.games import (
    dice,
    darts,
    football,
    basketball,
    bowling,
    slots,
    mines,
    crash,
    roulette,
)


# =========================================================
# APP LIFESPAN
# =========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print("🔥 FENIX COIN ULTRA ONLINE")
    yield
    await close_db()


app = FastAPI(
    title="Fenix Coin Ultra",
    version="ULTRA",
    description="Fenix Coin Games Platform",
    lifespan=lifespan,
)


# =========================================================
# HELPERS
# =========================================================

def serialize(value):
    if hasattr(value, "items"):
        return {k: serialize(v) for k, v in value.items()}

    if isinstance(value, (list, tuple)):
        return [serialize(v) for v in value]

    if hasattr(value, "isoformat"):
        return value.isoformat()

    return value


def row_to_dict(row):
    if row is None:
        return None

    return {
        key: serialize(row[key])
        for key in row.keys()
    }


async def require_user(user_id: int):
    user = await get_user(user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Пользователь не найден",
        )

    if user["banned"]:
        raise HTTPException(
            status_code=403,
            detail="Пользователь заблокирован",
        )

    return user


# =========================================================
# REQUEST MODELS
# =========================================================

class UserRequest(BaseModel):
    user_id: int


class RegisterRequest(BaseModel):
    user_id: int
    username: str = ""
    first_name: str = ""
    ref: Optional[int] = None


class PlayRequest(BaseModel):
    user_id: int
    game: str
    bet: int = Field(gt=0, le=1000000)


class MissionClaimRequest(BaseModel):
    user_id: int
    mission_id: int


class ShopBuyRequest(BaseModel):
    user_id: int
    code: str


# =========================================================
# HEALTH
# =========================================================

@app.get("/")
async def root():
    return HTMLResponse(HTML)


@app.get("/health")
async def health():
    return {
        "ok": True,
        "service": "Fenix Coin Ultra",
        "version": "ULTRA",
        "status": "online",
    }


@app.get("/api")
async def api_info():
    return {
        "ok": True,
        "service": "Fenix Coin Ultra",
        "version": "ULTRA",
        "endpoints": [
            "/api/user",
            "/api/games",
            "/api/play",
            "/api/history",
            "/api/leaderboard",
            "/api/referrals",
            "/api/missions",
            "/api/shop",
            "/api/inventory",
            "/api/stats",
        ],
    }


# =========================================================
# USER
# =========================================================

@app.post("/api/register")
async def register(req: RegisterRequest):
    class TelegramUser:
        id = req.user_id
        username = req.username
        first_name = req.first_name

    row, created = await ensure_user(
        TelegramUser(),
        req.ref,
    )

    return {
        "ok": True,
        "created": created,
        "user": row_to_dict(row),
    }


@app.get("/api/user")
async def api_user(
    user_id: int = Query(...),
):
    user = await require_user(user_id)

    return {
        "ok": True,
        "user": row_to_dict(user),
    }


@app.post("/api/user")
async def api_user_post(req: UserRequest):
    user = await require_user(req.user_id)

    return {
        "ok": True,
        "user": row_to_dict(user),
    }


# =========================================================
# GAMES
# =========================================================

@app.get("/api/games")
async def api_games():
    games = await get_games()

    return {
        "ok": True,
        "games": [
            row_to_dict(x)
            for x in games
        ],
    }


@app.get("/api/games/{game_code}")
async def api_game(game_code: str):
    game = await get_game(game_code)

    if not game:
        raise HTTPException(
            status_code=404,
            detail="Игра не найдена",
        )

    return {
        "ok": True,
        "game": row_to_dict(game),
    }


# =========================================================
# GAME RESULT ENGINE
# =========================================================

def calculate_game(game_code: str):
    """
    Возвращает:
        win
        multiplier
        data
    """

    if game_code == "dice":
        r = dice()

        # 4-6 = победа
        win = r["value"] >= 4

        multiplier = 1.8 if win else 0

        return win, multiplier, r

    if game_code == "darts":
        r = darts()

        win = r["value"] >= 4

        multiplier = 1.8 if win else 0

        return win, multiplier, r

    if game_code == "football":
        r = football()

        win = r["goal"]

        multiplier = 2.0 if win else 0

        return win, multiplier, r

    if game_code == "basketball":
        r = basketball()

        win = r["score"]

        multiplier = 2.0 if win else 0

        return win, multiplier, r

    if game_code == "bowling":
        r = bowling()

        win = r["pins"] >= 4

        multiplier = 1.8 if win else 0

        return win, multiplier, r

    if game_code == "slots":
        r = slots()

        return (
            r["win"],
            r["multiplier"],
            r,
        )

    if game_code == "mines":
        r = mines()

        # Первый ход считается безопасным.
        win = True
        multiplier = 1.25

        return win, multiplier, {
            "size": r["size"],
            "mines": r["mines"],
        }

    if game_code == "crash":
        r = crash()

        if r["crashed"]:
            return False, 0, r

        # Автоматический cashout.
        return True, r["multiplier"], r

    if game_code == "roulette":
        r = roulette()

        # Автоматическая ставка на красное/чёрное.
        win = r["color"] == "red"

        multiplier = 2.0 if win else 0

        return win, multiplier, r

    raise ValueError("unknown_game")


# =========================================================
# PLAY
# =========================================================

@app.post("/api/play")
async def api_play(req: PlayRequest):

    user = await require_user(req.user_id)

    game = await get_game(req.game)

    if not game:
        raise HTTPException(
            status_code=404,
            detail="Игра не найдена",
        )

    if not game["enabled"]:
        raise HTTPException(
            status_code=400,
            detail="Игра временно отключена",
        )

    if req.bet < game["min_bet"]:
        raise HTTPException(
            status_code=400,
            detail=f"Минимальная ставка: {game['min_bet']} FC",
        )

    if req.bet > game["max_bet"]:
        raise HTTPException(
            status_code=400,
            detail=f"Максимальная ставка: {game['max_bet']} FC",
        )

    if user["balance"] < req.bet:
        raise HTTPException(
            status_code=400,
            detail="Недостаточно Fenix Coin",
        )

    try:
        win, multiplier, data = calculate_game(req.game)

        result = await play_game(
            req.user_id,
            req.game,
            req.bet,
            win,
            multiplier,
            data,
        )

        return {
            "ok": True,
            "result": result,
            "game_data": serialize(data),
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


# =========================================================
# HISTORY
# =========================================================

@app.get("/api/history")
async def api_history(
    user_id: int = Query(...),
    limit: int = Query(50, ge=1, le=200),
):
    await require_user(user_id)

    rows = await get_game_history(
        user_id,
        limit,
    )

    return {
        "ok": True,
        "history": [
            row_to_dict(x)
            for x in rows
        ],
    }


@app.get("/api/transactions")
async def api_transactions(
    user_id: int = Query(...),
    limit: int = Query(50, ge=1, le=200),
):
    await require_user(user_id)

    rows = await get_transactions(
        user_id,
        limit,
    )

    return {
        "ok": True,
        "transactions": [
            row_to_dict(x)
            for x in rows
        ],
    }


# =========================================================
# LEADERBOARD
# =========================================================

@app.get("/api/leaderboard")
async def api_leaderboard(
    limit: int = Query(100, ge=1, le=100),
):
    rows = await leaderboard(limit)

    result = []

    for position, row in enumerate(rows, start=1):
        item = row_to_dict(row)
        item["position"] = position
        result.append(item)

    return {
        "ok": True,
        "leaderboard": result,
    }


# =========================================================
# REFERRALS
# =========================================================

@app.get("/api/referrals")
async def api_referrals(
    user_id: int = Query(...),
):
    user = await require_user(user_id)

    rows = await get_referrals(user_id)

    return {
        "ok": True,
        "reward": 600,
        "count": user["referrals"],
        "referrals": [
            row_to_dict(x)
            for x in rows
        ],
    }


# =========================================================
# MISSIONS
# =========================================================

@app.get("/api/missions")
async def api_missions():
    rows = await get_active_missions()

    return {
        "ok": True,
        "missions": [
            row_to_dict(x)
            for x in rows
        ],
    }


@app.post("/api/missions/claim")
async def api_claim_mission(
    req: MissionClaimRequest,
):
    await require_user(req.user_id)

    success, result = await claim_mission(
        req.user_id,
        req.mission_id,
    )

    if not success:
        raise HTTPException(
            status_code=400,
            detail=result,
        )

    return {
        "ok": True,
        "reward": result,
    }


# =========================================================
# SHOP
# =========================================================

@app.get("/api/shop")
async def api_shop():
    rows = await get_shop()

    return {
        "ok": True,
        "items": [
            row_to_dict(x)
            for x in rows
        ],
    }


@app.get("/api/inventory")
async def api_inventory(
    user_id: int = Query(...),
):
    await require_user(user_id)

    rows = await get_inventory(user_id)

    return {
        "ok": True,
        "inventory": [
            row_to_dict(x)
            for x in rows
        ],
    }


@app.post("/api/shop/buy")
async def api_shop_buy(
    req: ShopBuyRequest,
):
    await require_user(req.user_id)

    from app.db import buy_item

    success, result = await buy_item(
        req.user_id,
        req.code,
    )

    if not success:
        raise HTTPException(
            status_code=400,
            detail=result,
        )

    return {
        "ok": True,
        "item": row_to_dict(result),
    }


# =========================================================
# STATS
# =========================================================

@app.get("/api/stats")
async def api_stats():
    stats = await get_stats()

    return {
        "ok": True,
        "stats": stats,
    }


@app.get("/api/player/stats")
async def api_player_stats(
    user_id: int = Query(...),
):
    await require_user(user_id)

    stats = await get_player_stats(user_id)

    return {
        "ok": True,
        "stats": row_to_dict(stats),
    }


# =========================================================
# BEAUTIFUL WEB UI
# =========================================================

HTML = r"""
<!DOCTYPE html>
<html lang="ru">
<head>

<meta charset="UTF-8">
<meta
    name="viewport"
    content="width=device-width,
    initial-scale=1,
    maximum-scale=1,
    user-scalable=no"
>

<title>Fenix Coin Ultra</title>

<script src="https://telegram.org/js/telegram-web-app.js"></script>

<style>

* {
    box-sizing: border-box;
    -webkit-tap-highlight-color: transparent;
}

:root {
    --bg: #07070b;
    --panel: #101016;
    --panel2: #16161f;
    --border: rgba(255,255,255,.08);
    --text: #ffffff;
    --muted: #8d8d9d;
    --red: #ff244c;
    --red2: #ff526f;
    --gold: #ffd45c;
    --green: #32e69b;
    --blue: #5a8cff;
}

body {
    margin: 0;
    min-height: 100vh;
    color: var(--text);
    background:
        radial-gradient(
            circle at 50% -10%,
            rgba(255,30,70,.25),
            transparent 40%
        ),
        radial-gradient(
            circle at 100% 30%,
            rgba(90,70,255,.12),
            transparent 35%
        ),
        var(--bg);

    font-family:
        Inter,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
}

button {
    font: inherit;
}

.app {
    width: 100%;
    max-width: 620px;
    min-height: 100vh;
    margin: auto;
    padding-bottom: 100px;
}

.header {
    position: sticky;
    top: 0;
    z-index: 20;

    display: flex;
    align-items: center;
    justify-content: space-between;

    padding: 18px 18px 14px;

    background:
        linear-gradient(
            180deg,
            rgba(7,7,11,.97),
            rgba(7,7,11,.78)
        );

    backdrop-filter: blur(18px);
}

.logo {
    display: flex;
    align-items: center;
    gap: 11px;
}

.logo-icon {
    width: 42px;
    height: 42px;

    display: grid;
    place-items: center;

    border-radius: 14px;

    background:
        linear-gradient(
            135deg,
            #ff173f,
            #8f102e
        );

    box-shadow:
        0 0 30px rgba(255,20,60,.28);

    font-size: 22px;
}

.logo-title {
    font-size: 17px;
    font-weight: 900;
    letter-spacing: .5px;
}

.logo-sub {
    color: var(--muted);
    font-size: 11px;
    margin-top: 2px;
}

.balance {
    padding: 9px 13px;

    border: 1px solid rgba(255,210,80,.15);
    border-radius: 13px;

    background: rgba(255,210,80,.07);

    color: var(--gold);
    font-size: 13px;
    font-weight: 800;
}

.content {
    padding: 10px 16px;
}

.hero {
    position: relative;
    overflow: hidden;

    margin: 8px 0 16px;
    padding: 24px;

    border-radius: 26px;

    background:
        linear-gradient(
            135deg,
            rgba(255,25,65,.25),
            rgba(120,20,50,.09)
        );

    border: 1px solid rgba(255,40,80,.16);

    box-shadow:
        inset 0 1px rgba(255,255,255,.05),
        0 20px 60px rgba(0,0,0,.25);
}

.hero:after {
    content: "🔥";
    position: absolute;
    right: -10px;
    bottom: -28px;
    font-size: 125px;
    opacity: .10;
    transform: rotate(-15deg);
}

.hero-label {
    color: var(--red2);
    font-size: 12px;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 1.5px;
}

.hero h1 {
    margin: 7px 0;
    font-size: 29px;
    line-height: 1.05;
}

.hero p {
    margin: 0;
    color: #b6b6c4;
    font-size: 13px;
    line-height: 1.5;
}

.section-title {
    display: flex;
    justify-content: space-between;
    align-items: center;

    margin: 22px 2px 11px;

    font-size: 17px;
    font-weight: 900;
}

.section-title span {
    color: var(--muted);
    font-size: 11px;
    font-weight: 600;
}

.games {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
}

.game {
    position: relative;
    overflow: hidden;

    min-height: 128px;
    padding: 16px;

    border: 1px solid var(--border);
    border-radius: 20px;

    background:
        linear-gradient(
            145deg,
            rgba(255,255,255,.055),
            rgba(255,255,255,.015)
        );

    color: white;
    text-align: left;

    cursor: pointer;

    transition:
        transform .16s,
        border-color .16s,
        background .16s;
}

.game:hover {
    border-color: rgba(255,40,80,.3);
    background: rgba(255,40,80,.07);
}

.game:active {
    transform: scale(.97);
}

.game-icon {
    font-size: 34px;
    margin-bottom: 11px;
}

.game-name {
    font-size: 15px;
    font-weight: 900;
}

.game-desc {
    margin-top: 4px;
    color: var(--muted);
    font-size: 10px;
}

.card {
    padding: 17px;

    border: 1px solid var(--border);
    border-radius: 20px;

    background: rgba(255,255,255,.035);
}

.profile {
    display: flex;
    align-items: center;
    gap: 14px;
}

.avatar {
    width: 58px;
    height: 58px;

    display: grid;
    place-items: center;

    border-radius: 18px;

    background:
        linear-gradient(
            135deg,
            #ff1f47,
            #7d1732
        );

    font-size: 25px;
    font-weight: 900;
}

.profile-name {
    font-size: 18px;
    font-weight: 900;
}

.profile-id {
    margin-top: 3px;
    color: var(--muted);
    font-size: 11px;
}

.stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
    margin-top: 14px;
}

.stat {
    padding: 13px 8px;
    text-align: center;

    border-radius: 15px;
    background: rgba(255,255,255,.04);
}

.stat-value {
    font-size: 17px;
    font-weight: 900;
}

.stat-label {
    margin-top: 3px;
    color: var(--muted);
    font-size: 9px;
}

.nav {
    position: fixed;
    z-index: 50;

    left: 50%;
    bottom: 12px;

    transform: translateX(-50%);

    width: min(590px, calc(100% - 24px));

    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 5px;

    padding: 8px;

    border:
        1px solid rgba(255,255,255,.08);

    border-radius: 23px;

    background:
        rgba(14,14,21,.91);

    backdrop-filter: blur(25px);

    box-shadow:
        0 20px 70px rgba(0,0,0,.6);
}

.nav button {
    border: 0;
    border-radius: 17px;

    padding: 9px 4px;

    background: transparent;
    color: #777784;

    cursor: pointer;
}

.nav button.active {
    background: rgba(255,30,65,.12);
    color: #ff4262;
}

.nav-icon {
    display: block;
    font-size: 18px;
}

.nav-text {
    display: block;
    margin-top: 3px;
    font-size: 9px;
    font-weight: 700;
}

.page {
    display: none;
}

.page.active {
    display: block;
}

.modal {
    position: fixed;
    inset: 0;
    z-index: 100;

    display: none;
    align-items: flex-end;

    background: rgba(0,0,0,.72);
    backdrop-filter: blur(8px);
}

.modal.show {
    display: flex;
}

.modal-box {
    width: 100%;
    max-width: 620px;
    margin: auto;

    padding: 22px;

    border:
        1px solid rgba(255,255,255,.08);

    border-radius: 28px 28px 0 0;

    background:
        linear-gradient(
            180deg,
            #171720,
            #0b0b10
        );

    box-shadow:
        0 -20px 80px rgba(0,0,0,.5);

    animation: up .2s ease;
}

@keyframes up {
    from {
        transform: translateY(100%);
    }
    to {
        transform: translateY(0);
    }
}

.modal-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.close {
    width: 36px;
    height: 36px;

    border: 0;
    border-radius: 12px;

    background: rgba(255,255,255,.07);
    color: white;

    cursor: pointer;
}

.game-big {
    text-align: center;
    padding: 25px 0;
}

.game-big-icon {
    font-size: 75px;
}

.game-result {
    margin-top: 10px;

    font-size: 26px;
    font-weight: 1000;
}

.bet-row {
    display: flex;
    gap: 8px;
    margin-top: 14px;
}

.bet-input {
    flex: 1;

    width: 100%;

    padding: 15px;

    border: 1px solid rgba(255,255,255,.09);
    border-radius: 15px;

    outline: none;

    background: rgba(255,255,255,.05);
    color: white;

    font-size: 16px;
    font-weight: 800;
}

.play-btn {
    width: 100%;

    margin-top: 10px;
    padding: 16px;

    border: 0;
    border-radius: 16px;

    background:
        linear-gradient(
            135deg,
            #ff1f48,
            #bd1438
        );

    color: white;

    font-weight: 900;
    cursor: pointer;

    box-shadow:
        0 12px 35px rgba(255,30,65,.2);
}

.quick-bets {
    display: grid;
    grid-template-columns: repeat(4,1fr);
    gap: 7px;
    margin-top: 9px;
}

.quick-bets button {
    padding: 9px 4px;

    border: 1px solid var(--border);
    border-radius: 11px;

    background: rgba(255,255,255,.04);
    color: #bbb;

    cursor: pointer;
    font-size: 11px;
}

.list {
    display: grid;
    gap: 8px;
}

.list-item {
    display: flex;
    align-items: center;
    justify-content: space-between;

    padding: 14px;

    border: 1px solid var(--border);
    border-radius: 15px;

    background: rgba(255,255,255,.035);
}

.rank {
    width: 35px;
    height: 35px;

    display: grid;
    place-items: center;

    border-radius: 11px;

    background: rgba(255,255,255,.06);

    font-weight: 900;
}

.row-left {
    display: flex;
    align-items: center;
    gap: 10px;
}

.muted {
    color: var(--muted);
}

.coin {
    color: var(--gold);
    font-weight: 900;
}

.green {
    color: var(--green);
}

.red {
    color: var(--red2);
}

.ref-box {
    text-align: center;
}

.ref-code {
    margin: 15px 0;

    padding: 14px;

    border-radius: 15px;

    background: rgba(255,255,255,.05);

    font-family: monospace;
    word-break: break-all;
}

.copy-btn {
    width: 100%;

    padding: 14px;

    border: 0;
    border-radius: 15px;

    background: rgba(255,255,255,.08);
    color: white;

    font-weight: 800;
}

.loading {
    padding: 30px;
    text-align: center;
    color: var(--muted);
}

.toast {
    position: fixed;
    z-index: 200;

    left: 50%;
    top: 20px;

    transform: translateX(-50%) translateY(-20px);

    padding: 12px 18px;

    border-radius: 14px;

    background: #20202a;
    border: 1px solid rgba(255,255,255,.1);

    opacity: 0;
    pointer-events: none;

    transition: .2s;

    font-size: 12px;
    font-weight: 800;
}

.toast.show {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
}

.empty {
    padding: 30px 10px;
    text-align: center;
    color: var(--muted);
}

</style>

</head>

<body>

<div class="app">

<header class="header">

    <div class="logo">

        <div class="logo-icon">
            🔥
        </div>

        <div>
            <div class="logo-title">
                FENIX COIN
            </div>

            <div class="logo-sub">
                ULTRA GAME PLATFORM
            </div>
        </div>

    </div>

    <div class="balance">
        💰 <span id="topBalance">0</span>
    </div>

</header>


<main class="content">


<!-- HOME -->

<section
    id="page-home"
    class="page active"
>

    <div class="hero">

        <div class="hero-label">
            FENIX COIN ULTRA
        </div>

        <h1>
            Играй.<br>
            Побеждай. 🔥
        </h1>

        <p>
            PvP, PvE, мини-игры, рейтинг,
            миссии и реферальная система.
        </p>

    </div>


    <div class="section-title">
        Игры
        <span>REAL GAMEPLAY</span>
    </div>

    <div
        id="games"
        class="games"
    ></div>

</section>


<!-- PROFILE -->

<section
    id="page-profile"
    class="page"
>

    <div class="section-title">
        Профиль
    </div>

    <div
        id="profile"
        class="card"
    >
        <div class="loading">
            Загрузка...
        </div>
    </div>

</section>


<!-- RATING -->

<section
    id="page-rating"
    class="page"
>

    <div class="section-title">
        🏆 Рейтинг
        <span>TOP PLAYERS</span>
    </div>

    <div
        id="leaderboard"
        class="list"
    ></div>

</section>


<!-- REFERRALS -->

<section
    id="page-referrals"
    class="page"
>

    <div class="section-title">
        👥 Рефералы
    </div>

    <div class="card ref-box">

        <div style="font-size:45px">
            🎁
        </div>

        <h2>
            Приглашай друзей
        </h2>

        <p class="muted">
            Получай
            <b class="coin">600 FC</b>
            за каждого приглашённого игрока.
        </p>

        <div
            id="refLink"
            class="ref-code"
        >
            —
        </div>

        <button
            class="copy-btn"
            onclick="copyReferral()"
        >
            📋 Скопировать ссылку
        </button>

        <div
            style="
                margin-top:15px;
                color:#ffd45c;
                font-weight:900
            "
        >
            Приглашено:
            <span id="refCount">0</span>
        </div>

    </div>

</section>


<!-- MISSIONS -->

<section
    id="page-missions"
    class="page"
>

    <div class="section-title">
        🎯 Миссии
        <span>REWARDS</span>
    </div>

    <div
        id="missions"
        class="list"
    ></div>

</section>


</main>


<!-- NAVIGATION -->

<nav class="nav">

    <button
        class="active"
        onclick="showPage('home', this)"
    >
        <span class="nav-icon">🏠</span>
        <span class="nav-text">Главная</span>
    </button>

    <button
        onclick="showPage('profile', this)"
    >
        <span class="nav-icon">👤</span>
        <span class="nav-text">Профиль</span>
    </button>

    <button
        onclick="showPage('rating', this)"
    >
        <span class="nav-icon">🏆</span>
        <span class="nav-text">Рейтинг</span>
    </button>

    <button
        onclick="showPage('referrals', this)"
    >
        <span class="nav-icon">👥</span>
        <span class="nav-text">Рефы</span>
    </button>

    <button
        onclick="showPage('missions', this)"
    >
        <span class="nav-icon">🎯</span>
        <span class="nav-text">Миссии</span>
    </button>

</nav>


<!-- GAME MODAL -->

<div
    id="gameModal"
    class="modal"
    onclick="
        if(event.target === this)
        closeGame()
    "
>

    <div class="modal-box">

        <div class="modal-head">

            <div>
                <div
                    id="modalGameName"
                    style="
                        font-size:20px;
                        font-weight:900
                    "
                >
                    Игра
                </div>

                <div
                    id="modalGameDesc"
                    class="muted"
                    style="font-size:11px"
                ></div>
            </div>

            <button
                class="close"
                onclick="closeGame()"
            >
                ✕
            </button>

        </div>


        <div class="game-big">

            <div
                id="modalIcon"
                class="game-big-icon"
            >
                🎮
            </div>

            <div
                id="gameResult"
                class="game-result"
            >
                Сделай ставку
            </div>

        </div>


        <div class="muted">
            Ставка в Fenix Coin
        </div>

        <div class="bet-row">

            <input
                id="bet"
                class="bet-input"
                type="number"
                value="250"
                min="1"
            >

        </div>


        <div class="quick-bets">

            <button onclick="setBet(100)">
                100
            </button>

            <button onclick="setBet(250)">
                250
            </button>

            <button onclick="setBet(500)">
                500
            </button>

            <button onclick="setBet(1000)">
                1000
            </button>

        </div>


        <button
            id="playButton"
            class="play-btn"
            onclick="playCurrentGame()"
        >
            🔥 ИГРАТЬ
        </button>

    </div>

</div>


<div
    id="toast"
    class="toast"
></div>

</div>


<script>

const tg =
    window.Telegram &&
    window.Telegram.WebApp
        ? window.Telegram.WebApp
        : null;

if (tg) {
    tg.ready();
    tg.expand();
}


let userId = 0;
let currentGame = null;
let gamesCache = [];


function getTelegramUser() {

    if (
        tg &&
        tg.initDataUnsafe &&
        tg.initDataUnsafe.user
    ) {
        return tg.initDataUnsafe.user;
    }

    /*
        Для тестирования через браузер.

        После открытия Mini App Telegram
        этот ID будет заменён реальным.
    */

    return {
        id: 1,
        username: "demo",
        first_name: "Fenix"
    };
}


async function api(
    url,
    options = {}
) {

    const response =
        await fetch(url, {
            headers: {
                "Content-Type":
                    "application/json"
            },
            ...options
        });

    const data =
        await response.json();

    if (!response.ok) {
        throw new Error(
            data.detail ||
            "Ошибка API"
        );
    }

    return data;
}


function toast(message) {

    const el =
        document.getElementById("toast");

    el.textContent = message;

    el.classList.add("show");

    setTimeout(() => {
        el.classList.remove("show");
    }, 2200);
}


async function registerUser() {

    const u =
        getTelegramUser();

    userId = u.id;

    try {

        await api(
            "/api/register",
            {
                method: "POST",
                body: JSON.stringify({
                    user_id: u.id,
                    username:
                        u.username || "",
                    first_name:
                        u.first_name || ""
                })
            }
        );

    } catch (e) {

        console.error(e);

    }
}


async function loadUser() {

    try {

        const data =
            await api(
                "/api/user?user_id=" +
                userId
            );

        const user =
            data.user;

        document.getElementById(
            "topBalance"
        ).textContent =
            Number(
                user.balance
            ).toLocaleString("ru-RU");

        document.getElementById(
            "profile"
        ).innerHTML = `

            <div class="profile">

                <div class="avatar">
                    ${
                        (
                            user.first_name ||
                            "F"
                        )[0].toUpperCase()
                    }
                </div>

                <div>

                    <div class="profile-name">
                        ${
                            user.first_name ||
                            user.username ||
                            "Игрок"
                        }
                    </div>

                    <div class="profile-id">
                        ID: ${user.id}
                    </div>

                </div>

            </div>

            <div class="stats">

                <div class="stat">
                    <div class="stat-value">
                        ${user.games}
                    </div>
                    <div class="stat-label">
                        ИГР
                    </div>
                </div>

                <div class="stat">
                    <div class="stat-value">
                        ${user.wins}
                    </div>
                    <div class="stat-label">
                        ПОБЕД
                    </div>
                </div>

                <div class="stat">
                    <div class="stat-value">
                        ${user.level}
                    </div>
                    <div class="stat-label">
                        LEVEL
                    </div>
                </div>

            </div>

            <div
                style="
                    margin-top:14px;
                    padding:15px;
                    border-radius:15px;
                    background:rgba(255,210,80,.06)
                "
            >

                <div class="muted">
                    Fenix Coin
                </div>

                <div
                    style="
                        margin-top:4px;
                        color:#ffd45c;
                        font-size:25px;
                        font-weight:1000
                    "
                >
                    💰
                    ${Number(user.balance)
                        .toLocaleString("ru-RU")}
                    FC
                </div>

            </div>
        `;

    } catch (e) {

        toast(e.message);

    }
}


async function loadGames() {

    try {

        const data =
            await api(
                "/api/games"
            );

        gamesCache =
            data.games;

        const container =
            document.getElementById(
                "games"
            );

        container.innerHTML =
            gamesCache.map(game => {

                return `

                    <button
                        class="game"
                        onclick="
                            openGame(
                                '${game.code}'
                            )
                        "
                    >

                        <div class="game-icon">
                            ${game.emoji}
                        </div>

                        <div class="game-name">
                            ${game.title}
                        </div>

                        <div class="game-desc">
                            ${game.description}
                        </div>

                    </button>

                `;

            }).join("");

    } catch (e) {

        toast(e.message);

    }
}


function openGame(code) {

    currentGame =
        gamesCache.find(
            x => x.code === code
        );

    if (!currentGame) {
        return;
    }

    document.getElementById(
        "modalGameName"
    ).textContent =
        currentGame.title;

    document.getElementById(
        "modalGameDesc"
    ).textContent =
        currentGame.description;

    document.getElementById(
        "modalIcon"
    ).textContent =
        currentGame.emoji;

    document.getElementById(
        "gameResult"
    ).textContent =
        "Сделай ставку";

    document.getElementById(
        "bet"
    ).value =
        Math.max(
            currentGame.min_bet,
            250
        );

    document.getElementById(
        "gameModal"
    ).classList.add("show");
}


function closeGame() {

    document.getElementById(
        "gameModal"
    ).classList.remove("show");
}


function setBet(value) {

    document.getElementById(
        "bet"
    ).value = value;
}


async function playCurrentGame() {

    if (!currentGame) {
        return;
    }

    const bet =
        Number(
            document.getElementById(
                "bet"
            ).value
        );

    if (!bet || bet <= 0) {

        toast(
            "Введите ставку"
        );

        return;
    }

    const button =
        document.getElementById(
            "playButton"
        );

    button.disabled = true;
    button.textContent =
        "⏳ ИГРАЕМ...";

    try {

        const data =
            await api(
                "/api/play",
                {
                    method: "POST",
                    body: JSON.stringify({
                        user_id: userId,
                        game:
                            currentGame.code,
                        bet: bet
                    })
                }
            );

        const result =
            data.result;

        const gameData =
            data.game_data;

        let text;

        if (result.win) {

            text =
                "🔥 ПОБЕДА +" +
                Number(
                    result.profit
                ).toLocaleString("ru-RU") +
                " FC";

            document.getElementById(
                "gameResult"
            ).className =
                "game-result green";

        } else {

            text =
                "💀 ПРОИГРЫШ " +
                Number(
                    result.profit
                ).toLocaleString("ru-RU") +
                " FC";

            document.getElementById(
                "gameResult"
            ).className =
                "game-result red";
        }

        if (
            gameData &&
            gameData.display
        ) {

            text =
                gameData.display +
                "<br>" +
                text;
        }

        if (
            gameData &&
            gameData.emoji
        ) {

            document.getElementById(
                "modalIcon"
            ).textContent =
                gameData.emoji;
        }

        document.getElementById(
            "gameResult"
        ).innerHTML =
            text;

        toast(
            result.win
                ? "🔥 Победа!"
                : "💀 Не повезло"
        );

        await loadUser();

    } catch (e) {

        toast(e.message);

    } finally {

        button.disabled = false;
        button.textContent =
            "🔥 ИГРАТЬ";
    }
}


async function loadLeaderboard() {

    try {

        const data =
            await api(
                "/api/leaderboard?limit=50"
            );

        const container =
            document.getElementById(
                "leaderboard"
            );

        if (
            !data.leaderboard.length
        ) {

            container.innerHTML =
                `<div class="empty">
                    Пока никого нет
                </div>`;

            return;
        }

        container.innerHTML =
            data.leaderboard.map(
                player => {

                    const medal =
                        player.position === 1
                            ? "🥇"
                            : player.position === 2
                            ? "🥈"
                            : player.position === 3
                            ? "🥉"
                            : player.position;

                    return `

                        <div class="list-item">

                            <div class="row-left">

                                <div class="rank">
                                    ${medal}
                                </div>

                                <div>

                                    <div
                                        style="
                                            font-weight:800
                                        "
                                    >
                                        ${
                                            player.first_name ||
                                            player.username ||
                                            "Игрок"
                                        }
                                    </div>

                                    <div
                                        class="muted"
                                        style="
                                            font-size:10px
                                        "
                                    >
                                        LVL ${
                                            player.level
                                        }
                                        ·
                                        ${
                                            player.wins
                                        } побед
                                    </div>

                                </div>

                            </div>

                            <div class="coin">
                                💰 ${
                                    Number(
                                        player.balance
                                    )
                                    .toLocaleString(
                                        "ru-RU"
                                    )
                                }
                            </div>

                        </div>

                    `;

                }
            ).join("");

    } catch (e) {

        toast(e.message);

    }
}


async function loadReferrals() {

    const data =
        await api(
            "/api/referrals?user_id=" +
            userId
        );

    document.getElementById(
        "refCount"
    ).textContent =
        data.count;

    const botUsername =
        tg &&
        tg.initDataUnsafe &&
        tg.initDataUnsafe.user
            ? "YOUR_BOT"
            : "YOUR_BOT";

    document.getElementById(
        "refLink"
    ).textContent =
        "https://t.me/" +
        botUsername +
        "?start=ref_" +
        userId;
}


function copyReferral() {

    const text =
        document.getElementById(
            "refLink"
        ).textContent;

    navigator.clipboard
        .writeText(text)
        .then(() => {
            toast(
                "Ссылка скопирована 🔥"
            );
        });
}


async function loadMissions() {

    try {

        const data =
            await api(
                "/api/missions"
            );

        const container =
            document.getElementById(
                "missions"
            );

        if (!data.missions.length) {

            container.innerHTML =
                `<div class="empty">
                    Новые миссии скоро появятся 🔥
                </div>`;

            return;
        }

        container.innerHTML =
            data.missions.map(
                mission => {

                    return `

                        <div class="list-item">

                            <div>

                                <div
                                    style="
                                        font-weight:900
                                    "
                                >
                                    🎯
                                    ${mission.title}
                                </div>

                                <div
                                    class="muted"
                                    style="
                                        margin-top:4px;
                                        font-size:10px
                                    "
                                >
                                    ${
                                        mission.description ||
                                        "Выполни миссию"
                                    }
                                </div>

                            </div>

                            <div
                                style="
                                    text-align:right
                                "
                            >

                                <div class="coin">
                                    +
                                    ${mission.reward}
                                    FC
                                </div>

                                <button
                                    onclick="
                                        claimMission(
                                            ${mission.id}
                                        )
                                    "
                                    style="
                                        margin-top:6px;
                                        padding:6px 9px;
                                        border:0;
                                        border-radius:8px;
                                        background:#ff244c;
                                        color:white;
                                        font-size:9px;
                                        font-weight:900
                                    "
                                >
                                    ЗАБРАТЬ
                                </button>

                            </div>

                        </div>

                    `;

                }
            ).join("");

    } catch (e) {

        toast(e.message);

    }
}


async function claimMission(id) {

    try {

        const data =
            await api(
                "/api/missions/claim",
                {
                    method: "POST",
                    body: JSON.stringify({
                        user_id: userId,
                        mission_id: id
                    })
                }
            );

        toast(
            "🎁 Получено +" +
            data.reward +
            " FC"
        );

        await loadUser();
        await loadMissions();

    } catch (e) {

        toast(e.message);

    }
}


function showPage(
    page,
    button
) {

    document
        .querySelectorAll(".page")
        .forEach(
            x => x.classList.remove(
                "active"
            )
        );

    document.getElementById(
        "page-" + page
    ).classList.add("active");


    document
        .querySelectorAll(".nav button")
        .forEach(
            x => x.classList.remove(
                "active"
            )
        );

    button.classList.add("active");


    if (page === "profile") {
        loadUser();
    }

    if (page === "rating") {
        loadLeaderboard();
    }

    if (page === "referrals") {
        loadReferrals();
    }

    if (page === "missions") {
        loadMissions();
    }
}


async function boot() {

    try {

        await registerUser();

        await Promise.all([
            loadUser(),
            loadGames()
        ]);

    } catch (e) {

        console.error(e);

        toast(
            "Ошибка запуска: " +
            e.message
        );
    }
}


boot();

</script>

</body>
</html>
"""


# =========================================================
# ERROR HANDLER
# =========================================================

@app.exception_handler(Exception)
async def global_exception_handler(
    request,
    exc,
):
    print(
        "🔥 INTERNAL ERROR:",
        repr(exc)
    )

    return JSONResponse(
        status_code=500,
        content={
            "ok": False,
            "error": "internal_server_error",
            "message": str(exc),
        },
    )