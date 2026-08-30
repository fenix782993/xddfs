from __future__ import annotations
import json, hashlib, hmac, time
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query, Header
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from app.config import settings
from app.db import (init_db,close_db,ensure_user,get_user,get_games,get_game,get_game_history,get_transactions,leaderboard,get_referrals,get_active_missions,claim_mission,get_shop,get_inventory,get_stats,get_player_stats,is_admin,create_pvp,get_open_pvp,get_pvp,join_pvp,finish_pvp,create_mines_round,get_active_mines_round,update_mines_round,finish_mines_round)
from app.games import play,create_mines_board,mines_multiplier

@asynccontextmanager
async def lifespan(app):
    await init_db(); print('🔥 FENIX COIN ULTRA ONLINE'); yield; await close_db()
app=FastAPI(title='Fenix Coin Ultra',version='ULTRA-MEGA-FULL',lifespan=lifespan)

def ser(x):
    if hasattr(x,'items'): return {k:ser(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)): return [ser(v) for v in x]
    if hasattr(x,'isoformat'): return x.isoformat()
    return x

def row(x): return None if x is None else {k:ser(x[k]) for k in x.keys()}
async def user_required(uid:int):
    u=await get_user(uid)
    if not u: raise HTTPException(404,'Пользователь не найден')
    if u['banned']: raise HTTPException(403,'Пользователь заблокирован')
    return u

class Register(BaseModel): user_id:int; username:str=''; first_name:str=''; last_name:str=''; ref:int|None=None
class PlayReq(BaseModel): user_id:int; game:str; bet:int=Field(gt=0,le=1000000); options:dict={}
class ClaimReq(BaseModel): user_id:int; mission_id:int
class ShopReq(BaseModel): user_id:int; code:str
class PvpCreate(BaseModel): user_id:int; game:str='dice'; stake:int=Field(gt=0)
class PvpJoin(BaseModel): user_id:int; match_id:int
class PvpFinish(BaseModel): user_id:int; match_id:int; creator_score:int; opponent_score:int
class MinesStart(BaseModel): user_id:int; bet:int=Field(gt=0); mines:int=Field(default=5,ge=1,le=24)
class MinesOpen(BaseModel): user_id:int; round_id:int; cell:int=Field(ge=0,le=24)
class MinesCashout(BaseModel): user_id:int; round_id:int

@app.get('/')
async def root(): return HTMLResponse(HTML)
@app.get('/health')
async def health(): return {'ok':True,'service':'Fenix Coin Ultra','version':'ULTRA-MEGA-FULL'}
@app.get('/api')
async def api_info(): return {'ok':True,'games':len(await get_games()),'features':['games','pvp','mines_rounds','missions','shop','inventory','referrals','leaderboard','admin','telegram']}

@app.post('/api/register')
async def register(r:Register):
    class T: pass
    t=T(); t.id=r.user_id; t.username=r.username; t.first_name=r.first_name; t.last_name=r.last_name
    u,created=await ensure_user(t,r.ref); return {'ok':True,'created':created,'user':row(u)}
@app.get('/api/user')
async def api_user(user_id:int=Query(...)): return {'ok':True,'user':row(await user_required(user_id))}
@app.get('/api/games')
async def api_games(): return {'ok':True,'games':[row(x) for x in await get_games()]}
@app.get('/api/history')
async def history(user_id:int,limit:int=50): await user_required(user_id); return {'ok':True,'history':[row(x) for x in await get_game_history(user_id,max(1,min(200,limit)))]}
@app.get('/api/transactions')
async def transactions(user_id:int,limit:int=50): await user_required(user_id); return {'ok':True,'transactions':[row(x) for x in await get_transactions(user_id,max(1,min(200,limit)))]}
@app.get('/api/leaderboard')
async def lb(limit:int=50): return {'ok':True,'leaderboard':[row(x) for x in await leaderboard(max(1,min(100,limit)))]}
@app.get('/api/referrals')
async def refs(user_id:int):
    u=await user_required(user_id); return {'ok':True,'count':u['referrals'],'reward':settings.ref_reward,'referrals':[row(x) for x in await get_referrals(user_id)],'bot_username':settings.bot_username}
@app.get('/api/missions')
async def missions(user_id:int|None=None): return {'ok':True,'missions':[row(x) for x in await get_active_missions()]}
@app.post('/api/missions/claim')
async def mission_claim(r:ClaimReq):
    await user_required(r.user_id)
    ok,v=await claim_mission(r.user_id,r.mission_id)
    if not ok: raise HTTPException(400,str(v))
    return {'ok':True,'reward':v}

@app.get('/api/shop')
async def shop(): return {'ok':True,'items':[row(x) for x in await get_shop()]}
@app.get('/api/inventory')
async def inventory(user_id:int): await user_required(user_id); return {'ok':True,'inventory':[row(x) for x in await get_inventory(user_id)]}
@app.post('/api/shop/buy')
async def shop_buy(r:ShopReq):
    await user_required(r.user_id); from app.db import buy_item
    ok,v=await buy_item(r.user_id,r.code)
    if not ok: raise HTTPException(400,str(v))
    return {'ok':True,'item':row(v)}
@app.get('/api/stats')
async def stats(): return {'ok':True,'stats':await get_stats()}
@app.get('/api/player/stats')
async def player_stats(user_id:int): await user_required(user_id); return {'ok':True,'stats':row(await get_player_stats(user_id))}

@app.post('/api/play')
async def play_api(r:PlayReq):
    await user_required(r.user_id)
    try: result=await play(r.user_id,r.game,r.bet,**r.options)
    except ValueError as e: raise HTTPException(400,str(e))
    return {'ok':True,'result':ser(result)}

@app.post('/api/mines/start')
async def mines_start(r:MinesStart):
    await user_required(r.user_id)
    active=await get_active_mines_round(r.user_id)
    if active: raise HTTPException(400,'У тебя уже есть активная игра Mines')
    board=create_mines_board(r.mines); rr=await create_mines_round(r.user_id,r.bet,r.mines,board['mine_positions'])
    return {'ok':True,'round':{'id':rr['id'],'bet':r.bet,'mines':r.mines,'opened':[],'multiplier':1}}
@app.post('/api/mines/open')
async def mines_open(r:MinesOpen):
    await user_required(r.user_id); rr=await get_active_mines_round(r.user_id)
    if not rr or int(rr['id'])!=r.round_id: raise HTTPException(400,'Раунд не найден')
    opened=rr['opened']; mines_pos=rr['mine_positions']
    if isinstance(opened,str): opened=json.loads(opened)
    if isinstance(mines_pos,str): mines_pos=json.loads(mines_pos)
    if r.cell in opened: raise HTTPException(400,'Клетка уже открыта')
    opened=sorted(opened+[r.cell]); hit=r.cell in mines_pos
    m=0 if hit else mines_multiplier(len(opened),int(rr['mines']))
    if hit:
        await update_mines_round(r.round_id,opened,0); await finish_mines_round(r.round_id,r.user_id,0,0,True)
        return {'ok':True,'hit_mine':True,'opened':opened,'mines':mines_pos,'multiplier':0,'finished':True,'win':0}
    await update_mines_round(r.round_id,opened,m)
    safe=25-int(rr['mines'])
    if len(opened)>=safe:
        win=int(int(rr['bet'])*m); await finish_mines_round(r.round_id,r.user_id,win,m,False)
        return {'ok':True,'hit_mine':False,'opened':opened,'multiplier':m,'finished':True,'win':win}
    return {'ok':True,'hit_mine':False,'opened':opened,'multiplier':m,'finished':False}
@app.post('/api/mines/cashout')
async def mines_cashout(r:MinesCashout):
    await user_required(r.user_id); rr=await get_active_mines_round(r.user_id)
    if not rr or int(rr['id'])!=r.round_id: raise HTTPException(400,'Раунд не найден')
    opened=rr['opened'];
    if isinstance(opened,str): opened=json.loads(opened)
    m=float(rr['multiplier']); win=int(int(rr['bet'])*m); await finish_mines_round(r.round_id,r.user_id,win,m,False)
    return {'ok':True,'finished':True,'win':win,'multiplier':m,'opened':opened}

@app.post('/api/pvp/create')
async def pvp_create(r:PvpCreate):
    await user_required(r.user_id)
    try: x=await create_pvp(r.user_id,r.stake,r.game)
    except ValueError as e: raise HTTPException(400,str(e))
    return {'ok':True,'match':row(x)}
@app.get('/api/pvp/open')
async def pvp_open(game:str|None=None): return {'ok':True,'matches':[row(x) for x in await get_open_pvp(game)]}
@app.post('/api/pvp/join')
async def pvp_join(r:PvpJoin):
    await user_required(r.user_id)
    try: x=await join_pvp(r.match_id,r.user_id)
    except ValueError as e: raise HTTPException(400,str(e))
    return {'ok':True,'match':row(x)}
@app.post('/api/pvp/finish')
async def pvp_finish(r:PvpFinish):
    await user_required(r.user_id); m=await get_pvp(r.match_id)
    if not m or m['status']!='active': raise HTTPException(400,'Матч не активен')
    if r.user_id not in (int(m['creator_id']),int(m['opponent_id'])): raise HTTPException(403,'Не участник')
    winner=int(m['creator_id']) if r.creator_score>r.opponent_score else int(m['opponent_id']) if r.opponent_score>r.creator_score else None
    if winner is None: raise HTTPException(400,'Ничья не поддерживается для выплаты')
    loser=int(m['opponent_id']) if winner==int(m['creator_id']) else int(m['creator_id'])
    x=await finish_pvp(r.match_id,winner,loser,r.creator_score,r.opponent_score); return {'ok':True,'match':row(x),'winner':winner}

@app.get('/api/admin')
async def admin(uid:int):
    if not await is_admin(uid): raise HTTPException(403,'Нет доступа')
    return {'ok':True,'stats':await get_stats(),'games':[row(x) for x in await get_games()]}

HTML=r'''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1"><title>Fenix Coin Ultra</title><script src="https://telegram.org/js/telegram-web-app.js"></script><style>
*{box-sizing:border-box}body{margin:0;background:#07050f;color:#fff;font-family:Inter,system-ui,sans-serif;background-image:radial-gradient(circle at 15% 0%,#6b21a855,transparent 30%),radial-gradient(circle at 90% 10%,#a21caf44,transparent 35%),linear-gradient(145deg,#08050e,#140a24 55%,#09050f)}button,input{font:inherit}button{cursor:pointer}.app{max-width:720px;margin:auto;min-height:100vh;padding-bottom:100px}.top{position:sticky;top:0;z-index:5;padding:15px;background:#0a0713dd;backdrop-filter:blur(20px);display:flex;justify-content:space-between;align-items:center}.brand{font-weight:1000;letter-spacing:.7px}.brand small{display:block;color:#a78bfa;font-size:9px}.bal{background:#7c3aed22;border:1px solid #a78bfa33;border-radius:14px;padding:9px 12px;color:#ddd6fe;font-weight:900}.content{padding:14px}.hero{padding:24px;border-radius:28px;border:1px solid #a78bfa33;background:linear-gradient(135deg,#6d28d933,#a21caf22);box-shadow:0 20px 80px #0008}.hero h1{font-size:34px;margin:8px 0}.hero p{color:#c4b5fd}.section{margin:20px 0 10px;font-size:18px;font-weight:1000}.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}.game{min-height:135px;text-align:left;padding:16px;border:1px solid #ffffff12;border-radius:22px;background:linear-gradient(145deg,#ffffff0b,#7c3aed0a);color:white;transition:.15s}.game:hover{transform:translateY(-2px);border-color:#a78bfa66}.icon{font-size:34px}.muted{color:#9ca3af;font-size:11px}.card{padding:16px;border:1px solid #ffffff12;background:#ffffff07;border-radius:20px;margin-bottom:10px}.row{display:flex;justify-content:space-between;align-items:center;gap:10px}.pill{padding:7px 10px;border-radius:10px;background:#8b5cf622;color:#ddd6fe;font-weight:900;font-size:11px}.nav{position:fixed;bottom:10px;left:50%;transform:translateX(-50%);width:min(680px,calc(100% - 20px));display:grid;grid-template-columns:repeat(6,1fr);gap:4px;padding:8px;border:1px solid #ffffff14;border-radius:24px;background:#0d0916eF;backdrop-filter:blur(20px);z-index:20}.nav button{border:0;background:transparent;color:#8b8795;border-radius:15px;padding:8px 3px}.nav button.active{background:#8b5cf622;color:#c4b5fd}.nav span{display:block;font-size:18px}.nav small{font-size:8px}.page{display:none}.page.active{display:block}.modal{position:fixed;inset:0;background:#000b;z-index:50;display:none;align-items:flex-end}.modal.show{display:flex}.sheet{width:100%;max-width:720px;margin:auto;background:linear-gradient(#1a102b,#0d0815);border-radius:28px 28px 0 0;padding:20px;max-height:92vh;overflow:auto}.close{float:right;border:0;background:#ffffff10;color:white;border-radius:10px;padding:8px}.big{text-align:center;padding:16px}.bigemoji{font-size:70px;animation:float 1.2s infinite alternate}@keyframes float{to{transform:translateY(-10px) rotate(4deg)}}.action{width:100%;border:0;border-radius:16px;padding:15px;background:linear-gradient(135deg,#7c3aed,#c026d3);color:white;font-weight:1000;margin-top:10px;box-shadow:0 12px 35px #7c3aed44}.input{width:100%;padding:14px;background:#ffffff09;border:1px solid #ffffff14;border-radius:14px;color:white;outline:0}.bets{display:grid;grid-template-columns:repeat(4,1fr);gap:7px;margin-top:8px}.bets button,.choice{padding:10px;border:1px solid #ffffff14;background:#ffffff08;color:white;border-radius:11px}.result{padding:15px;border-radius:16px;background:#ffffff08;margin:10px 0;text-align:center;font-weight:900}.win{color:#4ade80}.lose{color:#fb7185}.mines{display:grid;grid-template-columns:repeat(5,1fr);gap:7px;margin-top:12px}.cell{aspect-ratio:1;border:0;border-radius:12px;background:linear-gradient(145deg,#31204e,#171022);color:white;font-size:20px;font-weight:900}.cell.open{background:#6d28d955}.cell.mine{background:#be123c}.crash{height:220px;position:relative;border-radius:20px;background:linear-gradient(#7c3aed12,#0000),repeating-linear-gradient(0deg,#ffffff08 0 1px,transparent 1px 44px);overflow:hidden}.rocket{position:absolute;font-size:50px;bottom:15px;left:15px;filter:drop-shadow(0 0 15px #c084fc);transition:1s}.meter{text-align:center;font-size:42px;font-weight:1000;color:#ddd6fe}.tabs{display:flex;gap:7px;overflow:auto}.tabs button{white-space:nowrap}.list{display:grid;gap:8px}.admin{border:1px solid #f0abfc44;background:#a21caf11}.smallbtn{padding:8px 10px;border:0;border-radius:10px;background:#ffffff10;color:white}
</style></head><body><div class="app"><header class="top"><div class="brand">🔥 FENIX COIN<small>ULTRA MEGA FULL</small></div><div class="bal">💰 <span id="balance">0</span></div></header><main class="content">
<section id="home" class="page active"><div class="hero"><div class="muted">PURPLE GRID EDITION</div><h1>Играй. Сражайся. Забирай. ⚡</h1><p>Все игры, PvP, Mines, Crash, профиль, миссии, магазин, рефералы и админка в одной Mini App.</p></div><div class="section">🎮 Все игры</div><div id="games" class="grid"></div></section>
<section id="profile" class="page"><div class="section">👤 Профиль</div><div id="profileCard" class="card"></div><div class="section">📜 История</div><div id="history" class="list"></div></section>
<section id="pvp" class="page"><div class="section">⚔️ PvP Arena</div><div class="card"><div class="muted">Создай матч, заблокируй ставку и жди соперника.</div><input id="pvpStake" class="input" type="number" value="250" style="margin-top:10px"><select id="pvpGame" class="input" style="margin-top:8px"><option value="dice">🎲 Dice</option><option value="slots">🎰 Slots</option><option value="crash">📈 Crash</option></select><button class="action" onclick="createPvp()">⚔️ СОЗДАТЬ МАТЧ</button></div><div id="pvpList" class="list"></div></section>
<section id="social" class="page"><div class="section">👥 Рефералы</div><div id="refs" class="card"></div><div class="section">🎯 Миссии</div><div id="missions" class="list"></div><div class="section">🛒 Магазин</div><div id="shop" class="list"></div></section>
<section id="rating" class="page"><div class="section">🏆 Рейтинг</div><div id="ratingList" class="list"></div></section>
<section id="admin" class="page"><div class="section">🛡️ Admin Center</div><div id="adminBox" class="card admin"></div></section></main>
<nav class="nav"><button class="active" onclick="page('home',this)"><span>🏠</span><small>Главная</small></button><button onclick="page('profile',this)"><span>👤</span><small>Профиль</small></button><button onclick="page('pvp',this)"><span>⚔️</span><small>PvP</small></button><button onclick="page('social',this)"><span>🎁</span><small>Мир</small></button><button onclick="page('rating',this)"><span>🏆</span><small>Топ</small></button><button onclick="page('admin',this)"><span>🛡️</span><small>Admin</small></button></nav></div>
<div id="modal" class="modal"><div class="sheet"><button class="close" onclick="closeModal()">✕</button><div id="modalBody"></div></div></div>
<script>
const tg=window.Telegram?.WebApp||null;if(tg){tg.ready();tg.expand()}let U=0,G=[];const icons={dice:'🎲',darts:'🎯',football:'⚽',basketball:'🏀',bowling:'🎳',slots:'🎰',mines:'💣',crash:'📈',roulette:'🎡',coinflip:'🪙',blackjack:'🃏',reaction:'⚡',race:'🏁'};
function tu(){return tg?.initDataUnsafe?.user||{id:1,username:'demo',first_name:'Fenix'}}function esc(s){return String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]))}async function api(u,o={}){let r=await fetch(u,{headers:{'Content-Type':'application/json'},...o});let d=await r.json();if(!r.ok)throw Error(d.detail||d.error||'API error');return d}function post(u,b){return api(u,{method:'POST',body:JSON.stringify(b)})}function page(id,b){document.querySelectorAll('.page').forEach(x=>x.classList.remove('active'));document.getElementById(id).classList.add('active');document.querySelectorAll('.nav button').forEach(x=>x.classList.remove('active'));b.classList.add('active');if(id==='profile')loadProfile();if(id==='pvp')loadPvp();if(id==='social')loadSocial();if(id==='rating')loadRating();if(id==='admin')loadAdmin()}
function closeModal(){document.getElementById('modal').classList.remove('show')}function showModal(x){document.getElementById('modalBody').innerHTML=x;document.getElementById('modal').classList.add('show')}
async function boot(){let u=tu();U=u.id;await post('/api/register',{user_id:U,username:u.username||'',first_name:u.first_name||'',last_name:u.last_name||''});await Promise.all([loadUser(),loadGames()])}async function loadUser(){let d=await api('/api/user?user_id='+U);document.getElementById('balance').textContent=Number(d.user.balance).toLocaleString('ru-RU')}async function loadGames(){let d=await api('/api/games');G=d.games;document.getElementById('games').innerHTML=G.map(x=>`<button class="game" onclick="openGame('${x.code}')"><div class="icon">${x.emoji||icons[x.code]||'🎮'}</div><b>${esc(x.title)}</b><div class="muted">${esc(x.description||'')}</div><div class="pill" style="margin-top:10px;display:inline-block">${x.min_bet}–${x.max_bet}</div></button>`).join('')}
function openGame(code){let g=G.find(x=>x.code===code);if(!g)return;let extra='';if(code==='mines')extra=`<div class="tabs"><button class="choice" onclick="startMines()">💣 5 мин</button><button class="choice" onclick="startMines(8)">💣 8 мин</button><button class="choice" onclick="startMines(12)">💣 12 мин</button></div><div id="mineArea"></div>`;else if(code==='crash')extra=`<div class="crash"><div id="rocket" class="rocket">🚀</div></div><div id="crashMeter" class="meter">1.00x</div>`;else if(code==='roulette')extra=`<div class="tabs"><button class="choice" onclick="setChoice('red')">🔴 Red</button><button class="choice" onclick="setChoice('black')">⚫ Black</button><button class="choice" onclick="setChoice('odd')">1️⃣ Odd</button><button class="choice" onclick="setChoice('even')">2️⃣ Even</button></div>`;else if(code==='coinflip')extra=`<div class="tabs"><button class="choice" onclick="setChoice('heads')">🙂 Орёл</button><button class="choice" onclick="setChoice('tails')">🪙 Решка</button></div>`;else if(code==='blackjack')extra=`<div class="tabs"><button class="choice" onclick="setChoice('hit')">🃏 HIT</button><button class="choice" onclick="setChoice('stand')">✋ STAND</button></div>`;else if(code==='high_low')extra=`<div class="tabs"><button class="choice" onclick="setChoice('high')">⬆️ HIGH</button><button class="choice" onclick="setChoice('low')">⬇️ LOW</button></div>`;else if(code==='rps')extra=`<div class="tabs"><button class="choice" onclick="setChoice('rock')">🪨</button><button class="choice" onclick="setChoice('paper')">📄</button><button class="choice" onclick="setChoice('scissors')">✂️</button></div>`;else if(code==='color')extra=`<div class="tabs"><button class="choice" onclick="setChoice('red')">🔴</button><button class="choice" onclick="setChoice('black')">⚫</button><button class="choice" onclick="setChoice('blue')">🔵</button><button class="choice" onclick="setChoice('green')">🟢</button></div>`;showModal(`<div class="big"><div class="bigemoji" id="bigIcon">${g.emoji||icons[code]||'🎮'}</div><h2>${esc(g.title)}</h2><div class="muted">${esc(g.description||'')}</div></div><input id="bet" class="input" type="number" min="${g.min_bet}" max="${g.max_bet}" value="${Math.max(g.min_bet,250)}"><div class="bets">${[100,250,500,1000].map(x=>`<button onclick="document.getElementById('bet').value=${x}">${x}</button>`).join('')}</div>${extra}<div id="result" class="result">Готов к игре</div><button class="action" onclick="playGame('${code}')">🔥 ИГРАТЬ</button>`);window.choice='red'}
function setChoice(x){window.choice=x;document.getElementById('result').textContent='Выбрано: '+x}async function playGame(code){let bet=+document.getElementById('bet').value;if(code==='mines'||code==='crash')return code==='mines'?startMines():playCrash();let options={};if(['roulette','coinflip','blackjack','high_low','rps','color'].includes(code))options.choice=window.choice||'red';if(code==='blackjack')options.action=window.choice||'stand';try{let d=await post('/api/play',{user_id:U,game:code,bet,options});animateGame(code,d.result);await loadUser()}catch(e){document.getElementById('result').innerHTML='<span class="lose">❌ '+esc(e.message)+'</span>'}}
function animateGame(code,r){let el=document.getElementById('result');if(code==='slots'){let arr=['🍒','🍋','🍊','🍇','🔔','⭐','💎','🔥'];let i=0,t=setInterval(()=>{document.getElementById('bigIcon').textContent=arr[Math.floor(Math.random()*arr.length)]+' '+arr[Math.floor(Math.random()*arr.length)]+' '+arr[Math.floor(Math.random()*arr.length)];i++;if(i>12){clearInterval(t);document.getElementById('bigIcon').textContent=(r.symbols||[]).join(' ')}},80)}if(code==='dice'||code==='darts'||code==='football'||code==='basketball'||code==='bowling'){document.getElementById('bigIcon').animate([{transform:'rotate(-20deg) scale(.8)'},{transform:'rotate(20deg) scale(1.2)'},{transform:'rotate(0) scale(1)'}],{duration:700})}el.innerHTML=(r.profit>=0?'<span class="win">🎉 ПОБЕДА</span>':'<span class="lose">💀 ПРОИГРЫШ</span>')+'<br>'+esc(r.display||'')+'<br>📈 '+(r.multiplier??0)+'x · 💰 '+Number(r.win_amount||0).toLocaleString('ru-RU')+' FC'}
async function startMines(n=5){let bet=+document.getElementById('bet').value||250;try{let d=await post('/api/mines/start',{user_id:U,bet,mines:n});window.mineRound=d.round;renderMines();await loadUser()}catch(e){document.getElementById('result').textContent='❌ '+e.message}}function renderMines(){let r=window.mineRound;document.getElementById('result').innerHTML='💎 '+r.multiplier+'x · открыто '+r.opened.length;document.getElementById('mineArea').innerHTML='<div class="mines">'+Array.from({length:25},(_,i)=>`<button class="cell ${r.opened.includes(i)?'open':''}" onclick="openMine(${i})">${r.opened.includes(i)?'💎':'?'}</button>`).join('')+'</div><button class="action" onclick="cashoutMines()">💰 ЗАБРАТЬ</button>'}async function openMine(cell){let r=window.mineRound;try{let d=await post('/api/mines/open',{user_id:U,round_id:r.id,cell});r.opened=d.opened;r.multiplier=d.multiplier;renderMines();if(d.hit_mine){document.getElementById('result').innerHTML='<span class="lose">💣 МИНА! Ставка сгорела</span>';d.mines?.forEach(x=>{});document.querySelectorAll('.cell')[cell].textContent='💣'}if(d.finished){document.getElementById('result').innerHTML=(d.win?'🎉 ':'💀 ')+(d.win||0)+' FC';window.mineRound=null}await loadUser()}catch(e){alert(e.message)}}async function cashoutMines(){let r=window.mineRound;if(!r)return;try{let d=await post('/api/mines/cashout',{user_id:U,round_id:r.id});document.getElementById('result').innerHTML='<span class="win">💰 ЗАБРАНО '+d.win+' FC</span>';window.mineRound=null;await loadUser()}catch(e){alert(e.message)}}
async function playCrash(){let bet=+document.getElementById('bet').value||250;let target=1+Math.random()*5;target=Math.max(1.01,Math.min(10,+target.toFixed(2)));let meter=document.getElementById('crashMeter'),rocket=document.getElementById('rocket');let x=1;let timer=setInterval(()=>{x+=.05;meter.textContent=x.toFixed(2)+'x';rocket.style.left=Math.min(90,x*7)+'%';if(x>=target){clearInterval(timer);finishCrash(target)}},80)}async function finishCrash(target){try{let d=await post('/api/play',{user_id:U,game:'crash',bet:+document.getElementById('bet').value,options:{cashout:target}});document.getElementById('result').innerHTML=d.result.status==='cashed_out'?'<span class="win">🚀 CASHOUT '+target+'x</span>':'<span class="lose">💥 CRASH</span>';await loadUser()}catch(e){document.getElementById('result').textContent='❌ '+e.message}}
async function loadProfile(){let [u,h]=await Promise.all([api('/api/user?user_id='+U),api('/api/history?user_id='+U)]);document.getElementById('profileCard').innerHTML=`<div class="row"><div><b>${esc(u.user.first_name||u.user.username||'Игрок')}</b><div class="muted">ID ${u.user.id}</div></div><div class="pill">LVL ${u.user.level}</div></div><div style="margin-top:12px">💰 <b>${Number(u.user.balance).toLocaleString('ru-RU')}</b> FC</div><div class="muted" style="margin-top:8px">🎮 ${u.user.games} · 🏆 ${u.user.wins} · 💀 ${u.user.losses} · ⭐ ${u.user.xp} XP</div>`;document.getElementById('history').innerHTML=h.history.slice(0,20).map(x=>`<div class="card"><div class="row"><b>${icons[x.game_code]||'🎮'} ${esc(x.game_code)}</b><span class="${x.profit>0?'win':'lose'}">${x.profit>0?'+':''}${x.profit} FC</span></div><div class="muted">ставка ${x.bet} · ${x.multiplier||0}x</div></div>`).join('')||'<div class="muted">История пуста</div>'}
async function loadPvp(){let d=await api('/api/pvp/open');document.getElementById('pvpList').innerHTML=d.matches.map(x=>`<div class="card"><div class="row"><b>⚔️ #${x.id} ${esc(x.game_code)}</b><span>${x.stake} FC</span></div><button class="action" onclick="joinPvp(${x.id})">ВСТУПИТЬ</button></div>`).join('')||'<div class="muted">Открытых матчей нет</div>'}async function createPvp(){try{await post('/api/pvp/create',{user_id:U,game:document.getElementById('pvpGame').value,stake:+document.getElementById('pvpStake').value});loadPvp();await loadUser()}catch(e){alert(e.message)}}async function joinPvp(id){try{let d=await post('/api/pvp/join',{user_id:U,match_id:id});let s1=Math.floor(Math.random()*6)+1,s2=Math.floor(Math.random()*6)+1;await post('/api/pvp/finish',{user_id:U,match_id:id,creator_score:s1,opponent_score:s2});loadPvp();await loadUser();alert('Матч завершён: '+s1+':'+s2)}catch(e){alert(e.message)}}
async function loadSocial(){let [r,m,s]=await Promise.all([api('/api/referrals?user_id='+U),api('/api/missions'),api('/api/shop')]);let bot=r.bot_username||'YOUR_BOT';document.getElementById('refs').innerHTML=`<b>👥 Приглашено: ${r.count}</b><div class="muted" style="margin-top:8px">+${r.reward} FC за реферала</div><div class="card" style="margin-top:10px;word-break:break-all">https://t.me/${bot}?start=ref_${U}</div>`;document.getElementById('missions').innerHTML=m.missions.map(x=>`<div class="card"><div class="row"><b>🎯 ${esc(x.title)}</b><span class="pill">+${x.reward}</span></div><div class="muted">${esc(x.description||'')}</div></div>`).join('')||'<div class="muted">Миссий нет</div>';document.getElementById('shop').innerHTML=s.items.map(x=>`<div class="card"><div class="row"><b>${esc(x.title)}</b><span>${x.price} FC</span></div><div class="muted">${esc(x.description||'')}</div><button class="smallbtn" onclick="buy('${esc(x.code)}')">КУПИТЬ</button></div>`).join('')}async function buy(code){try{await post('/api/shop/buy',{user_id:U,code});await loadSocial();await loadUser();alert('Куплено 🔥')}catch(e){alert(e.message)}}async function loadRating(){let d=await api('/api/leaderboard?limit=50');document.getElementById('ratingList').innerHTML=d.leaderboard.map((x,i)=>`<div class="card"><div class="row"><b>${i+1}. ${esc(x.first_name||x.username||x.id)}</b><span>💰 ${Number(x.balance).toLocaleString('ru-RU')}</span></div><div class="muted">LVL ${x.level} · wins ${x.wins}</div></div>`).join('')}async function loadAdmin(){try{let d=await api('/api/admin?uid='+U);document.getElementById('adminBox').innerHTML=`<b>🛡️ ADMIN</b><div style="margin-top:10px">Users: ${d.stats.users}<br>Games: ${d.stats.games}<br>PvP: ${d.stats.pvp_matches}<br>Refs: ${d.stats.referrals}<br>Coins: ${Number(d.stats.total_coins).toLocaleString('ru-RU')}</div><div class="muted" style="margin-top:10px">Игры: ${d.games.length}</div>`}catch(e){document.getElementById('adminBox').innerHTML='<span class="muted">Админ-панель доступна только администраторам.</span>'}}
boot().catch(e=>alert('Ошибка запуска: '+e.message));
</script></body></html>'''
