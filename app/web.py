import hashlib, hmac, json, math, os, random, time
from contextlib import asynccontextmanager
from typing import Optional
from urllib.parse import parse_qsl

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from app.config import settings
from app.db import (
    init_db, close_db, ensure_user, get_user, get_games, get_game, play_game,
    get_game_history, get_transactions, leaderboard, get_referrals,
    get_active_missions, claim_mission, get_shop, get_inventory, get_stats,
    get_player_stats, create_pvp, join_pvp, finish_pvp,
    mines_start, mines_reveal, mines_cashout, mines_active,
    is_admin, admin_users, admin_set_game, admin_set_setting, admin_give, admin_take, set_ban,
)
from app.games import play as game_play

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print('🔥 FENIX COIN ULTRA V3 ONLINE')
    yield
    await close_db()

app = FastAPI(title='Fenix Coin Ultra V3', version='3.0', lifespan=lifespan)

class RegisterRequest(BaseModel):
    user_id: int
    username: str = ''
    first_name: str = ''
    last_name: str = ''
    ref: Optional[int] = None
    init_data: str = ''
class PlayRequest(BaseModel):
    user_id: int
    game: str
    bet: int = Field(gt=0, le=1_000_000)
    options: dict = {}
class MissionClaimRequest(BaseModel):
    user_id: int
    mission_id: int
class ShopBuyRequest(BaseModel):
    user_id: int
    code: str
class PVPCreateRequest(BaseModel):
    user_id: int
    game: str = 'dice'
    stake: int = Field(gt=0, le=1_000_000)
class PVPJoinRequest(BaseModel):
    user_id: int
    match_id: int
class PVPFinishRequest(BaseModel):
    user_id: int
    match_id: int
class MineStartRequest(BaseModel):
    user_id: int
    bet: int = Field(gt=0, le=1_000_000)
    mines: int = Field(default=5, ge=1, le=24)
class MineRevealRequest(BaseModel):
    user_id: int
    session_id: int
    cell: int = Field(ge=0, le=24)
class MineCashoutRequest(BaseModel):
    user_id: int
    session_id: int
class AdminMoneyRequest(BaseModel):
    admin_id: int
    user_id: int
    amount: int = Field(gt=0, le=100_000_000)
class AdminBanRequest(BaseModel):
    admin_id: int
    user_id: int
    banned: bool
class AdminGameRequest(BaseModel):
    admin_id: int
    code: str
    enabled: bool
class AdminSettingRequest(BaseModel):
    admin_id: int
    key: str
    value: str

def serial(v):
    if isinstance(v, dict): return {k: serial(x) for k,x in v.items()}
    if isinstance(v, (list,tuple)): return [serial(x) for x in v]
    if hasattr(v, 'isoformat'): return v.isoformat()
    return v

def row(v): return None if v is None else {k: serial(v[k]) for k in v.keys()}

async def require_user(uid:int):
    u=await get_user(uid)
    if not u: raise HTTPException(404,'Пользователь не зарегистрирован')
    if u['banned']: raise HTTPException(403,'Пользователь заблокирован')
    return u

async def require_admin(uid:int):
    await require_user(uid)
    if not await is_admin(uid): raise HTTPException(403,'Доступ только для администратора')

def telegram_valid(init_data:str, bot_token:str)->bool:
    if not init_data or not bot_token: return False
    try:
        vals=dict(parse_qsl(init_data, keep_blank_values=True))
        received=vals.pop('hash', None)
        auth_date=int(vals.get('auth_date','0'))
        if not received or abs(time.time()-auth_date)>86400: return False
        check='\n'.join(f'{k}={vals[k]}' for k in sorted(vals))
        secret=hmac.new(b'WebAppData', bot_token.encode(), hashlib.sha256).digest()
        calc=hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(calc, received)
    except Exception: return False

@app.get('/')
async def root(): return HTMLResponse(HTML)
@app.get('/health')
async def health(): return {'ok':True,'service':'Fenix Coin Ultra','version':'3.0','status':'online'}
@app.get('/api')
async def api_info(): return {'ok':True,'version':'3.0','features':['games','mines','crash','pvp','missions','shop','admin','telegram_auth']}

@app.post('/api/register')
async def register(req:RegisterRequest):
    if settings.bot_token and not telegram_valid(req.init_data, settings.bot_token):
        raise HTTPException(401,'Открой Mini App через Telegram. Telegram initData недействителен.')
    class TU: pass
    t=TU(); t.id=req.user_id; t.username=req.username; t.first_name=req.first_name; t.last_name=req.last_name
    u,created=await ensure_user(t,req.ref)
    return {'ok':True,'created':created,'user':row(u)}

@app.get('/api/user')
async def api_user(user_id:int=Query(...)): return {'ok':True,'user':row(await require_user(user_id))}
@app.get('/api/games')
async def api_games(): return {'ok':True,'games':[row(x) for x in await get_games()]}
@app.get('/api/games/{code}')
async def api_game(code:str):
    g=await get_game(code)
    if not g: raise HTTPException(404,'Игра не найдена')
    return {'ok':True,'game':row(g)}

@app.post('/api/play')
async def api_play(req:PlayRequest):
    u=await require_user(req.user_id); g=await get_game(req.game)
    if not g: raise HTTPException(404,'Игра не найдена')
    if not g['enabled']: raise HTTPException(400,'Игра отключена')
    if req.bet<g['min_bet'] or req.bet>g['max_bet']: raise HTTPException(400,f"Ставка: {g['min_bet']}–{g['max_bet']} FC")
    if u['balance']<req.bet: raise HTTPException(400,'Недостаточно FC')
    try: data=game_play(req.game,req.bet,**req.options)
    except TypeError as e: raise HTTPException(400,f'Некорректные параметры игры: {e}')
    except ValueError as e: raise HTTPException(400,str(e))
    result=await play_game(req.user_id,req.game,req.bet,data['win_amount'],data.get('multiplier'),data)
    return {'ok':True,'result':result,'game_data':serial(data)}

@app.get('/api/history')
async def history(user_id:int=Query(...),limit:int=Query(50,ge=1,le=200)):
    await require_user(user_id); return {'ok':True,'history':[row(x) for x in await get_game_history(user_id,limit)]}
@app.get('/api/transactions')
async def transactions(user_id:int=Query(...),limit:int=Query(50,ge=1,le=200)):
    await require_user(user_id); return {'ok':True,'transactions':[row(x) for x in await get_transactions(user_id,limit)]}
@app.get('/api/leaderboard')
async def lb(limit:int=Query(50,ge=1,le=100)):
    return {'ok':True,'leaderboard':[dict(row(x),position=i+1) for i,x in enumerate(await leaderboard(limit))]}
@app.get('/api/referrals')
async def refs(user_id:int=Query(...)):
    u=await require_user(user_id); return {'ok':True,'count':u['referrals'],'reward':settings.ref_reward,'referrals':[row(x) for x in await get_referrals(user_id)]}
@app.get('/api/missions')
async def missions(): return {'ok':True,'missions':[row(x) for x in await get_active_missions()]}
@app.post('/api/missions/claim')
async def mission_claim(req:MissionClaimRequest):
    await require_user(req.user_id); ok,result=await claim_mission(req.user_id,req.mission_id)
    if not ok: raise HTTPException(400,str(result))
    return {'ok':True,'reward':result}
@app.get('/api/shop')
async def shop(): return {'ok':True,'items':[row(x) for x in await get_shop()]}
@app.get('/api/inventory')
async def inventory(user_id:int=Query(...)):
    await require_user(user_id); return {'ok':True,'inventory':[row(x) for x in await get_inventory(user_id)]}
@app.post('/api/shop/buy')
async def shop_buy(req:ShopBuyRequest):
    await require_user(req.user_id)
    from app.db import buy_item
    ok,result=await buy_item(req.user_id,req.code)
    if not ok: raise HTTPException(400,str(result))
    return {'ok':True,'item':row(result)}
@app.get('/api/stats')
async def stats(): return {'ok':True,'stats':await get_stats()}
@app.get('/api/player/stats')
async def player_stats(user_id:int=Query(...)):
    await require_user(user_id); return {'ok':True,'stats':row(await get_player_stats(user_id))}

# Mines: persistent round state in PostgreSQL
@app.post('/api/mines/start')
async def mines_begin(req:MineStartRequest):
    await require_user(req.user_id)
    try: s=await mines_start(req.user_id,req.bet,5,req.mines)
    except ValueError as e: raise HTTPException(400,str(e))
    return {'ok':True,'session':row(s)}
@app.get('/api/mines/active')
async def mines_get(user_id:int=Query(...)):
    await require_user(user_id); return {'ok':True,'session':row(await mines_active(user_id))}
@app.post('/api/mines/reveal')
async def mines_open(req:MineRevealRequest):
    await require_user(req.user_id)
    try: return {'ok':True,'result':serial(await mines_reveal(req.user_id,req.session_id,req.cell))}
    except ValueError as e: raise HTTPException(400,str(e))
@app.post('/api/mines/cashout')
async def mines_out(req:MineCashoutRequest):
    await require_user(req.user_id)
    try: return {'ok':True,'result':serial(await mines_cashout(req.user_id,req.session_id))}
    except ValueError as e: raise HTTPException(400,str(e))

# PvP lobby + server-side resolution. Both players lock stake; winner receives prize.
@app.get('/api/pvp')
async def pvp_list():
    from app.db import check_pool
    db=check_pool(); rows=await db.fetch("SELECT id,creator_id,opponent_id,game_code,stake,prize,status,creator_score,opponent_score,started_at,finished_at FROM pvp_matches WHERE status IN ('open','active') ORDER BY id DESC LIMIT 50")
    return {'ok':True,'matches':[row(x) for x in rows]}
@app.post('/api/pvp/create')
async def pvp_create(req:PVPCreateRequest):
    await require_user(req.user_id)
    try: m=await create_pvp(req.user_id,req.stake,req.game)
    except ValueError as e: raise HTTPException(400,str(e))
    return {'ok':True,'match':row(m)}
@app.post('/api/pvp/join')
async def pvp_join(req:PVPJoinRequest):
    await require_user(req.user_id)
    try: m=await join_pvp(req.match_id,req.user_id)
    except ValueError as e: raise HTTPException(400,str(e))
    return {'ok':True,'match':row(m)}
@app.post('/api/pvp/finish')
async def pvp_finish(req:PVPFinishRequest):
    await require_user(req.user_id)
    from app.db import check_pool
    db=check_pool(); m=await db.fetchrow("SELECT * FROM pvp_matches WHERE id=$1 AND status='active'",req.match_id)
    if not m: raise HTTPException(404,'Матч не найден или уже завершён')
    if req.user_id not in (m['creator_id'],m['opponent_id']): raise HTTPException(403,'Вы не участник матча')
    a=random.randint(1,6); b=random.randint(1,6)
    if a==b: b=random.choice([x for x in range(1,7) if x!=a])
    winner=m['creator_id'] if a>b else m['opponent_id']; loser=m['opponent_id'] if winner==m['creator_id'] else m['creator_id']
    prize=await finish_pvp(req.match_id,winner,loser,a,b)
    return {'ok':True,'winner_id':winner,'creator_score':a,'opponent_score':b,'prize':prize}

# Admin
@app.get('/api/admin/overview')
async def admin_overview(admin_id:int=Query(...)):
    await require_admin(admin_id); return {'ok':True,'stats':await get_stats(),'users':[row(x) for x in await admin_users(100)]}
@app.post('/api/admin/give')
async def admin_give_api(req:AdminMoneyRequest):
    await require_admin(req.admin_id); return {'ok':True,'balance':await admin_give(req.admin_id,req.user_id,req.amount)}
@app.post('/api/admin/take')
async def admin_take_api(req:AdminMoneyRequest):
    await require_admin(req.admin_id); return {'ok':True,'balance':await admin_take(req.admin_id,req.user_id,req.amount)}
@app.post('/api/admin/ban')
async def admin_ban_api(req:AdminBanRequest):
    await require_admin(req.admin_id); await set_ban(req.admin_id,req.user_id,req.banned); return {'ok':True}
@app.post('/api/admin/game')
async def admin_game_api(req:AdminGameRequest):
    await require_admin(req.admin_id); g=await admin_set_game(req.code,req.enabled); return {'ok':True,'game':row(g)}
@app.post('/api/admin/setting')
async def admin_setting_api(req:AdminSettingRequest):
    await require_admin(req.admin_id); s=await admin_set_setting(req.key,req.value); return {'ok':True,'setting':row(s)}

@app.exception_handler(Exception)
async def errors(request,exc):
    print('🔥 INTERNAL ERROR:',repr(exc))
    return JSONResponse(500,{'ok':False,'error':'internal_server_error','message':str(exc)})

HTML=r'''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no"><title>Fenix Coin Ultra</title><script src="https://telegram.org/js/telegram-web-app.js"></script><style>
*{box-sizing:border-box}body{margin:0;background:#050509;color:#fff;font-family:Inter,system-ui,sans-serif}button,input{font:inherit}.app{max-width:680px;margin:auto;min-height:100vh;padding-bottom:105px;background:radial-gradient(circle at 50% -10%,#65102755,transparent 38%),#050509}.top{position:sticky;top:0;z-index:20;padding:15px 16px;display:flex;justify-content:space-between;align-items:center;background:#07070be8;backdrop-filter:blur(18px);border-bottom:1px solid #ffffff0d}.brand{display:flex;gap:10px;align-items:center}.flame{width:43px;height:43px;border-radius:15px;display:grid;place-items:center;background:linear-gradient(135deg,#ff194d,#7f0d2c);box-shadow:0 0 28px #ff164733;font-size:22px}.brand b{font-size:15px}.brand small{display:block;color:#8e8e9d;font-size:9px;margin-top:3px}.bal{color:#ffd75c;background:#ffd75c0c;border:1px solid #ffd75c22;padding:9px 12px;border-radius:14px;font-weight:900;font-size:12px}.content{padding:14px 15px}.hero{padding:24px;border:1px solid #ff315522;border-radius:25px;background:linear-gradient(135deg,#ff174d22,#69122b12);position:relative;overflow:hidden}.hero:after{content:'🔥';position:absolute;right:-5px;bottom:-35px;font-size:120px;opacity:.08}.hero small{color:#ff5977;font-weight:900;letter-spacing:1.5px}.hero h1{font-size:31px;line-height:1;margin:8px 0}.hero p{color:#aaaab8;font-size:12px;line-height:1.5}.tabs{display:flex;gap:7px;overflow:auto;margin:14px 0}.tabs button{white-space:nowrap;border:1px solid #ffffff10;background:#ffffff06;color:#aaa;padding:10px 13px;border-radius:13px;font-size:11px;font-weight:800}.tabs button.on{background:#ff174d18;color:#ff5573;border-color:#ff174d33}.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}.game{min-height:150px;text-align:left;padding:16px;border:1px solid #ffffff0d;border-radius:20px;background:linear-gradient(145deg,#ffffff09,#ffffff02);color:#fff;cursor:pointer;transition:.18s}.game:active{transform:scale(.97)}.game:hover{border-color:#ff2b5033}.ico{font-size:39px;filter:drop-shadow(0 5px 12px #000)}.game b{display:block;margin-top:12px;font-size:15px}.game small{display:block;color:#81818f;margin-top:5px;font-size:10px}.page{display:none}.page.on{display:block}.card{padding:17px;border:1px solid #ffffff0d;border-radius:20px;background:#ffffff05;margin-bottom:10px}.row{display:flex;justify-content:space-between;align-items:center;gap:10px}.muted{color:#898996}.green{color:#32e69b}.red{color:#ff5273}.gold{color:#ffd75c}.btn{width:100%;border:0;border-radius:15px;padding:14px;background:linear-gradient(135deg,#ff1d4e,#b90f36);color:#fff;font-weight:900;cursor:pointer}.btn.secondary{background:#ffffff0a;border:1px solid #ffffff10}.bet{width:100%;padding:14px;border-radius:14px;border:1px solid #ffffff10;background:#ffffff06;color:#fff;outline:none}.quick{display:grid;grid-template-columns:repeat(4,1fr);gap:7px;margin:8px 0}.quick button{border:1px solid #ffffff10;background:#ffffff05;color:#bbb;padding:9px;border-radius:10px}.nav{position:fixed;bottom:10px;left:50%;transform:translateX(-50%);z-index:50;width:min(650px,calc(100% - 20px));display:grid;grid-template-columns:repeat(5,1fr);gap:4px;padding:7px;background:#111118ee;border:1px solid #ffffff10;border-radius:23px;backdrop-filter:blur(20px)}.nav button{border:0;background:none;color:#737381;border-radius:17px;padding:8px 3px}.nav button.on{background:#ff174d14;color:#ff5473}.nav i{font-style:normal;display:block;font-size:18px}.nav small{font-size:8px;font-weight:800}.modal{position:fixed;inset:0;z-index:100;background:#000b;display:none;align-items:flex-end}.modal.on{display:flex}.sheet{width:100%;max-width:680px;margin:auto;background:linear-gradient(#171720,#08080d);border:1px solid #ffffff10;border-radius:27px 27px 0 0;padding:20px;max-height:92vh;overflow:auto}.close{border:0;background:#ffffff0b;color:#fff;border-radius:11px;width:36px;height:36px}.stage{text-align:center;padding:20px 0}.stageIcon{font-size:70px;min-height:85px;display:grid;place-items:center}.result{font-size:22px;font-weight:1000;min-height:30px}.anim{animation:pulse .7s infinite alternate}@keyframes pulse{to{transform:scale(1.1);filter:drop-shadow(0 0 20px #ff2855)}}.shake{animation:shake .12s infinite}@keyframes shake{25%{transform:translateX(-5px)}75%{transform:translateX(5px)}}.slots{display:flex;justify-content:center;gap:8px}.reel{width:72px;height:82px;display:grid;place-items:center;border-radius:15px;background:#0a0a10;border:1px solid #ffffff12;font-size:40px;overflow:hidden}.minegrid{display:grid;grid-template-columns:repeat(5,1fr);gap:7px;margin:15px 0}.cell{aspect-ratio:1;border:1px solid #ffffff0e;border-radius:12px;background:#ffffff08;color:#fff;font-size:23px;cursor:pointer}.cell.safe{background:#32e69b18;border-color:#32e69b44}.cell.mine{background:#ff174d22;border-color:#ff174d55}.rocket{font-size:65px;transition:transform .15s}.crashline{font-size:30px;font-weight:1000;color:#ffd75c}.list{display:grid;gap:8px}.item{padding:13px;border-radius:15px;background:#ffffff05;border:1px solid #ffffff09}.adminStat{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.adminStat .card{text-align:center}.toast{position:fixed;top:18px;left:50%;transform:translate(-50%,-15px);opacity:0;z-index:300;background:#20202a;border:1px solid #ffffff12;border-radius:13px;padding:11px 16px;font-size:11px;font-weight:900;transition:.2s}.toast.show{opacity:1;transform:translate(-50%,0)}
</style></head><body><div class="app"><header class="top"><div class="brand"><div class="flame">🔥</div><div><b>FENIX COIN</b><small>ULTRA GAME PLATFORM</small></div></div><div class="bal">💰 <span id="balance">0</span></div></header><main class="content"><section class="hero"><small>FENIX COIN ULTRA V3</small><h1>Играй по-настоящему.</h1><p>Анимации, серверная механика, Mines, Crash, PvP, рейтинг, магазин и админ-панель.</p></section><div class="tabs" id="tabs"><button class="on" onclick="tab('games',this)">🎮 Игры</button><button onclick="tab('pvp',this)">⚔️ PvP</button><button onclick="tab('shop',this)">🛒 Магазин</button><button onclick="tab('missions',this)">🎯 Миссии</button><button onclick="tab('admin',this)">⚙️ Admin</button></div><section id="games" class="page on"><div class="grid" id="gamesGrid"></div></section><section id="pvp" class="page"><div class="card"><b>⚔️ PvP-арена</b><p class="muted">Создай матч, соперник внесёт такую же ставку. Сервер определит результат.</p><input id="pvpStake" class="bet" type="number" value="250"><br><br><button class="btn" onclick="createPvp()">⚔️ Создать матч</button></div><div class="list" id="pvpList"></div></section><section id="shop" class="page"><div class="list" id="shopList"></div></section><section id="missions" class="page"><div class="list" id="missionList"></div></section><section id="admin" class="page"><div id="adminBox" class="card">Проверка доступа...</div></section></main><nav class="nav"><button class="on" onclick="tab('games',this)"><i>🎮</i><small>Игры</small></button><button onclick="tab('pvp',this)"><i>⚔️</i><small>PvP</small></button><button onclick="tab('shop',this)"><i>🛒</i><small>Магазин</small></button><button onclick="tab('missions',this)"><i>🎯</i><small>Миссии</small></button><button onclick="tab('admin',this)"><i>⚙️</i><small>Admin</small></button></nav></div><div id="modal" class="modal" onclick="if(event.target===this)closeModal()"><div class="sheet"><div class="row"><div><b id="mTitle">Игра</b><small id="mDesc" class="muted" style="display:block;margin-top:4px"></small></div><button class="close" onclick="closeModal()">✕</button></div><div class="stage"><div id="stageIcon" class="stageIcon">🎮</div><div id="stage" class="result">Готов?</div><div id="extra"></div></div><input id="bet" class="bet" type="number" value="250"><div class="quick"><button onclick="setBet(100)">100</button><button onclick="setBet(250)">250</button><button onclick="setBet(500)">500</button><button onclick="setBet(1000)">1000</button></div><div id="gameControls"><button class="btn" onclick="playCurrent()">🔥 ИГРАТЬ</button></div></div></div><div id="toast" class="toast"></div><script>
const tg=window.Telegram?.WebApp;tg?.ready();tg?.expand();const U=tg?.initDataUnsafe?.user;let uid=U?.id||0, games=[],current=null,minesSession=null;
const demo=()=>{if(!uid){show('Открой Mini App из Telegram');throw Error('Telegram user отсутствует')}};
async function api(url,opt={}){opt.headers={...(opt.headers||{}),'Content-Type':'application/json'};const r=await fetch(url,opt);const d=await r.json();if(!r.ok)throw Error(d.detail||d.message||'Ошибка API');return d}
function show(x){const e=document.getElementById('toast');e.textContent=x;e.classList.add('show');setTimeout(()=>e.classList.remove('show'),2200)}
function tab(id,b){document.querySelectorAll('.page').forEach(x=>x.classList.remove('on'));document.getElementById(id).classList.add('on');document.querySelectorAll('.nav button').forEach(x=>x.classList.remove('on'));if(b?.parentElement?.classList.contains('nav'))b.classList.add('on');else{const n=[...document.querySelectorAll('.nav button')].find(x=>x.textContent.includes(id==='games'?'Игры':id==='pvp'?'PvP':id==='shop'?'Магазин':id==='missions'?'Миссии':'Admin'));n?.classList.add('on')}if(id==='pvp')loadPvp();if(id==='shop')loadShop();if(id==='missions')loadMissions();if(id==='admin')loadAdmin()}
async function boot(){try{demo();const init=tg?.initData||'';await api('/api/register',{method:'POST',body:JSON.stringify({user_id:uid,username:U.username||'',first_name:U.first_name||'',last_name:U.last_name||'',init_data:init})});await loadUser();await loadGames();}catch(e){show(e.message);console.error(e)}}
async function loadUser(){const d=await api('/api/user?user_id='+uid);document.getElementById('balance').textContent=Number(d.user.balance).toLocaleString('ru-RU')}
async function loadGames(){const d=await api('/api/games');games=d.games;document.getElementById('gamesGrid').innerHTML=games.map(g=>`<button class="game" onclick="openGame('${g.code}')"><div class="ico">${g.emoji}</div><b>${g.title}</b><small>${g.description||''}</small><small>${g.min_bet}–${g.max_bet} FC</small></button>`).join('')}
function openGame(code){current=games.find(g=>g.code===code);if(!current)return;document.getElementById('modal').classList.add('on');document.getElementById('mTitle').textContent=current.title;document.getElementById('mDesc').textContent=current.description||'';document.getElementById('stageIcon').textContent=current.emoji;document.getElementById('stage').textContent='Готов?';document.getElementById('extra').innerHTML='';document.getElementById('bet').value=Math.max(current.min_bet,250);if(code==='mines')setupMines();else if(code==='crash')setupCrash()}
function closeModal(){document.getElementById('modal').classList.remove('on');minesSession=null}
function setBet(n){document.getElementById('bet').value=n}
async function playCurrent(){if(!current)return;const bet=+document.getElementById('bet').value;const icon=document.getElementById('stageIcon');const st=document.getElementById('stage');if(current.code==='mines'){return startMines()}if(current.code==='crash'){return playCrash()}icon.classList.add('anim');st.textContent='🎬 Анимация...';await new Promise(r=>setTimeout(r,current.code==='slots'?1000:650));try{const d=await api('/api/play',{method:'POST',body:JSON.stringify({user_id:uid,game:current.code,bet,options:{}})});renderResult(d.game_data,d.result);await loadUser()}catch(e){show(e.message)}finally{icon.classList.remove('anim')}}
function renderResult(g,r){const st=document.getElementById('stage'),icon=document.getElementById('stageIcon');st.className='result '+(r.win?'green':'red');st.innerHTML=(g.display||'')+'<br>'+(r.win?'🔥 ПОБЕДА +':'💀 ПРОИГРЫШ ')+Number(r.profit).toLocaleString('ru-RU')+' FC';if(g.reels){document.getElementById('extra').innerHTML='<div class="slots">'+g.reels.map(x=>`<div class="reel">${x}</div>`).join('')+'</div>'}icon.textContent=g.emoji||current.emoji;show(r.win?'🔥 Победа':'💀 Проигрыш')}
function setupCrash(){document.getElementById('stageIcon').innerHTML='<div class="rocket">🚀</div>';document.getElementById('stage').innerHTML='<div class="crashline">1.00x</div>';document.getElementById('extra').innerHTML='<small class="muted">Нажми ИГРАТЬ — ракета будет расти, пока сервер не определит краш.</small>'}
async function playCrash(){const bet=+document.getElementById('bet').value,icon=document.getElementById('stageIcon'),st=document.getElementById('stage');icon.classList.add('anim');try{const d=await api('/api/play',{method:'POST',body:JSON.stringify({user_id:uid,game:'crash',bet,options:{cashout_target:2.00}})});const end=+d.game_data.crash_at;let x=1;const t=setInterval(()=>{x=Math.min(end,x+(end-1)/30);st.innerHTML='<div class="crashline">'+x.toFixed(2)+'x</div>';icon.querySelector('.rocket').style.transform=`translate(${Math.min(150,x*2)}px,${-Math.min(70,(x-1)*2)}px)`;if(x>=end){clearInterval(t);renderResult(d.game_data,d.result);icon.classList.remove('anim')}},50);await loadUser()}catch(e){icon.classList.remove('anim');show(e.message)}}
function setupMines(){document.getElementById('stage').textContent='💣 Выбери клетки';document.getElementById('gameControls').innerHTML='<button class="btn" onclick="startMines()">💣 НАЧАТЬ MINES</button>'}
async function startMines(){const bet=+document.getElementById('bet').value;try{const d=await api('/api/mines/start',{method:'POST',body:JSON.stringify({user_id:uid,bet,mines:5})});minesSession=d.session;renderMineGrid();await loadUser()}catch(e){show(e.message)}}
function renderMineGrid(){const opened=JSON.parse(minesSession.opened||'[]');document.getElementById('extra').innerHTML='<div class="minegrid">'+Array.from({length:25},(_,i)=>`<button id="c${i}" class="cell ${opened.includes(i)?'safe':''}" onclick="reveal(${i})">${opened.includes(i)?'💎':'?'}</button>`).join('')+'</div><div class="gold">Множитель: <b id="mult">'+(minesSession.multiplier||1)+'x</b></div>';document.getElementById('gameControls').innerHTML='<button class="btn" onclick="cashout()">💰 ЗАБРАТЬ</button>';document.getElementById('stage').textContent='Открывай клетки'}
async function reveal(cell){if(!minesSession)return;try{const d=await api('/api/mines/reveal',{method:'POST',body:JSON.stringify({user_id:uid,session_id:minesSession.id,cell})});const r=d.result;if(r.status==='lost'){r.mine_positions.forEach(i=>document.getElementById('c'+i).textContent='💣');r.mine_positions.forEach(i=>document.getElementById('c'+i).classList.add('mine'));document.getElementById('stage').innerHTML='💥 МИНА';document.getElementById('stage').className='result red';document.getElementById('gameControls').innerHTML='<button class="btn secondary" onclick="closeModal()">Закрыть</button>';minesSession=null}else{minesSession.opened=JSON.stringify(r.opened);minesSession.multiplier=r.multiplier;renderMineGrid();document.getElementById('mult').textContent=r.multiplier+'x'}}catch(e){show(e.message)}}
async function cashout(){if(!minesSession)return;try{const d=await api('/api/mines/cashout',{method:'POST',body:JSON.stringify({user_id:uid,session_id:minesSession.id})});document.getElementById('stage').innerHTML='💰 +'+Number(d.result.profit).toLocaleString('ru-RU')+' FC';document.getElementById('stage').className='result green';document.getElementById('gameControls').innerHTML='<button class="btn secondary" onclick="closeModal()">Закрыть</button>';await loadUser();minesSession=null}catch(e){show(e.message)}}
async function createPvp(){try{const d=await api('/api/pvp/create',{method:'POST',body:JSON.stringify({user_id:uid,stake:+document.getElementById('pvpStake').value,game:'dice'})});show('Матч #'+d.match.id+' создан');await loadUser();loadPvp()}catch(e){show(e.message)}}
async function loadPvp(){try{const d=await api('/api/pvp');document.getElementById('pvpList').innerHTML=d.matches.length?d.matches.map(m=>`<div class="item"><div class="row"><b>⚔️ #${m.id} · ${m.game_code}</b><span class="gold">${m.stake} FC</span></div><small class="muted">${m.status==='open'?'Ждёт соперника':'Матч идёт'}</small><br><br>${m.status==='open'&&m.creator_id!==uid?`<button class="btn" onclick="joinPvp(${m.id})">Войти</button>`:m.status==='active'&&[m.creator_id,m.opponent_id].includes(uid)?`<button class="btn" onclick="finishPvp(${m.id})">🎲 СРАЗИТЬСЯ</button>`:''}</div>`).join(''):'<div class="card muted">Пока нет открытых матчей.</div>'}catch(e){show(e.message)}}
async function joinPvp(id){try{await api('/api/pvp/join',{method:'POST',body:JSON.stringify({user_id:uid,match_id:id})});show('Ты вошёл в матч');await loadUser();loadPvp()}catch(e){show(e.message)}}
async function finishPvp(id){try{const d=await api('/api/pvp/finish',{method:'POST',body:JSON.stringify({user_id:uid,match_id:id})});show(d.winner_id===uid?'🔥 ТЫ ПОБЕДИЛ!':'💀 Ты проиграл');await loadUser();loadPvp()}catch(e){show(e.message)}}
async function loadShop(){try{const d=await api('/api/shop');document.getElementById('shopList').innerHTML=d.items.length?d.items.map(x=>`<div class="item row"><div><b>${x.title}</b><small class="muted" style="display:block">${x.description||''}</small></div><button class="btn" style="width:auto" onclick="buy('${x.code}')">${x.price} FC</button></div>`).join(''):'<div class="card muted">Магазин пуст.</div>'}catch(e){show(e.message)}}
async function buy(code){try{await api('/api/shop/buy',{method:'POST',body:JSON.stringify({user_id:uid,code})});show('Покупка успешна');await loadUser();loadShop()}catch(e){show(e.message)}}
async function loadMissions(){try{const d=await api('/api/missions');document.getElementById('missionList').innerHTML=d.missions.map(x=>`<div class="item row"><div><b>🎯 ${x.title}</b><small class="muted" style="display:block">${x.description||''}</small></div><button class="btn" style="width:auto" onclick="claim(${x.id})">+${x.reward}</button></div>`).join('')||'<div class="card muted">Миссий пока нет.</div>'}catch(e){show(e.message)}}
async function claim(id){try{const d=await api('/api/missions/claim',{method:'POST',body:JSON.stringify({user_id:uid,mission_id:id})});show('🎁 +'+d.reward+' FC');await loadUser();loadMissions()}catch(e){show(e.message)}}
async function loadAdmin(){try{const d=await api('/api/admin/overview?admin_id='+uid);document.getElementById('adminBox').innerHTML='<b>⚙️ ADMIN PANEL</b><div class="adminStat" style="margin-top:12px"><div class="card"><b>'+d.stats.users+'</b><small class="muted">Игроков</small></div><div class="card"><b>'+d.stats.games+'</b><small class="muted">Игр</small></div><div class="card"><b>'+d.stats.pvp_matches+'</b><small class="muted">PvP</small></div></div><hr style="border-color:#ffffff0b"><b>Выдать FC</b><input id="aid" class="bet" placeholder="ID игрока"><input id="aamt" class="bet" style="margin-top:7px" placeholder="Количество"><button class="btn" style="margin-top:7px" onclick="give()">💰 Выдать</button><hr style="border-color:#ffffff0b"><div class="list">'+d.users.slice(0,30).map(u=>`<div class="item"><div class="row"><b>${u.first_name||u.username||'Игрок'}</b><span class="gold">${Number(u.balance).toLocaleString()} FC</span></div><small class="muted">ID ${u.id} · LVL ${u.level} · ${u.games} игр ${u.banned?' · 🚫 BANNED':''}</small></div>`).join('')+'</div>'}catch(e){document.getElementById('adminBox').innerHTML='<b>🔒 Нет доступа</b><p class="muted">Добавь свой Telegram ID в ADMIN_IDS на Render.</p>';}}
async function give(){try{await api('/api/admin/give',{method:'POST',body:JSON.stringify({admin_id:uid,user_id:+document.getElementById('aid').value,amount:+document.getElementById('aamt').value})});show('FC выданы');loadAdmin()}catch(e){show(e.message)}}boot();</script></body></html>'''
