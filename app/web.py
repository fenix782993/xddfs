from fastapi import FastAPI,HTTPException
from app.db import init_db,pool,get_user
app=FastAPI(title="Fenix Coin Ultra API")
@app.on_event("startup")
async def startup(): await init_db()
@app.get("/")
async def root(): return {"ok":True,"service":"Fenix Coin Ultra","version":"ULTRA"}
@app.get("/health")
async def health(): return {"status":"healthy"}
@app.get("/api/profile/{uid}")
async def profile(uid:int):
    u=await get_user(uid)
    if not u: raise HTTPException(404,"user_not_found")
    return dict(u)
@app.get("/api/games")
async def games(): return [dict(x) for x in await pool.fetch("SELECT * FROM games WHERE enabled=TRUE ORDER BY id")]
@app.get("/api/missions")
async def missions(): return [dict(x) for x in await pool.fetch("SELECT * FROM missions WHERE active=TRUE ORDER BY id DESC")]
@app.get("/api/leaderboard")
async def leaderboard(): return [dict(x) for x in await pool.fetch("SELECT id,username,balance,wins FROM users WHERE banned=FALSE ORDER BY balance DESC LIMIT 50")]
