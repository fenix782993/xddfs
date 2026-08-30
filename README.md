from __future__ import annotations
import random, secrets
from typing import Any, Dict, List, Optional
from app.db import play_game, get_game

SLOT_SYMBOLS = ['🍒','🍋','🍊','🍇','🔔','⭐','💎','🔥']
ROULETTE_RED = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
RPS = {'rock','paper','scissors'}
COLORS = ['red','black','blue','green','yellow']

def _safe_bet(bet:int)->int:
    bet=int(bet)
    if bet<=0: raise ValueError('Ставка должна быть больше 0')
    return bet

def _payout(game, user_id, bet, multiplier, data):
    win=int(bet*max(0,float(multiplier)))
    return play_game(user_id, game, bet, win, multiplier, data)

async def play_dice(user_id:int, bet:int):
    bet=_safe_bet(bet); value=random.randint(1,6); m={1:0,2:0,3:0,4:1.5,5:2,6:3}[value]
    r=await _payout('dice',user_id,bet,m,{'value':value,'type':'dice'})
    return {**r,'value':value,'multiplier':m,'display':f'🎲 Выпало {value}'}

async def play_darts(user_id:int, bet:int):
    bet=_safe_bet(bet); value=random.randint(1,6); m={1:0,2:0,3:1.5,4:2,5:3,6:5}[value]
    r=await _payout('darts',user_id,bet,m,{'value':value,'type':'darts'})
    return {**r,'value':value,'multiplier':m,'display':f'🎯 Результат {value}'}

async def play_football(user_id:int, bet:int):
    bet=_safe_bet(bet); value=random.randint(1,5); m={1:0,2:0,3:1.5,4:2.5,5:4}[value]
    r=await _payout('football',user_id,bet,m,{'value':value,'type':'football'})
    return {**r,'value':value,'multiplier':m,'display':f'⚽ Удар: {value}'}

async def play_basketball(user_id:int, bet:int):
    bet=_safe_bet(bet); value=random.randint(1,5); m={1:0,2:0,3:1.5,4:2.5,5:4}[value]
    r=await _payout('basketball',user_id,bet,m,{'value':value,'type':'basketball'})
    return {**r,'value':value,'multiplier':m,'display':f'🏀 Бросок: {value}'}

async def play_bowling(user_id:int, bet:int):
    bet=_safe_bet(bet); value=random.randint(1,6); m={1:0,2:0,3:1.25,4:1.75,5:2.5,6:5}[value]
    r=await _payout('bowling',user_id,bet,m,{'value':value,'type':'bowling'})
    return {**r,'value':value,'multiplier':m,'display':f'🎳 Кегли: {value}'}

def _slots_spin(): return [random.choice(SLOT_SYMBOLS) for _ in range(3)]
def _slots_multiplier(s):
    a,b,c=s
    if a==b==c=='💎': return 20
    if a==b==c=='🔥': return 15
    if a==b==c=='⭐': return 10
    if a==b==c: return 8
    if a==b or a==c or b==c: return 2
    return 0

async def play_slots(user_id:int, bet:int):
    bet=_safe_bet(bet); symbols=_slots_spin(); m=_slots_multiplier(symbols)
    r=await _payout('slots',user_id,bet,m,{'symbols':symbols,'type':'slots'})
    return {**r,'symbols':symbols,'multiplier':m,'display':' '.join(symbols)}

async def play_roulette(user_id:int, bet:int, choice='red'):
    bet=_safe_bet(bet); choice=str(choice).lower()
    if choice not in {'red','black','green','odd','even'}: raise ValueError('Неверная ставка рулетки')
    n=random.randint(0,36); color='green' if n==0 else ('red' if n in ROULETTE_RED else 'black'); m=0
    if choice==color: m=14 if color=='green' else 2
    elif choice=='odd' and n and n%2: m=2
    elif choice=='even' and n and n%2==0: m=2
    r=await _payout('roulette',user_id,bet,m,{'number':n,'color':color,'choice':choice})
    return {**r,'number':n,'color':color,'choice':choice,'multiplier':m,'display':f'🎡 {n} · {color}'}

def _crash_multiplier():
    # 25% of rounds land above 3x; after that the tail gets progressively rarer.
    if random.random() < 0.75:
        return round(random.uniform(1.00, 2.99), 2)
    r=random.random()
    if r < 0.60: return round(random.uniform(3.01, 5.00),2)
    if r < 0.88: return round(random.uniform(5.01,10.00),2)
    if r < 0.97: return round(random.uniform(10.01,25.00),2)
    return round(random.uniform(25.01,100.00),2)

async def play_crash(user_id:int, bet:int, cashout:Optional[float]=None):
    bet=_safe_bet(bet); crash_at=_crash_multiplier(); cashout=float(cashout or crash_at)
    if cashout<1: raise ValueError('Cashout должен быть >= 1.0')
    m=cashout if cashout<=crash_at else 0
    status='cashed_out' if m else 'crashed'
    r=await _payout('crash',user_id,bet,m,{'crash_at':crash_at,'cashout':cashout,'status':status})
    return {**r,'crash_at':crash_at,'cashout':cashout,'status':status,'display':f'📈 {"CASHOUT" if m else "CRASH"}'}

MINES_CELLS=25
def create_mines_board(mines=5):
    mines=max(1,min(24,int(mines))); return {'size':5,'mines':mines,'mine_positions':secrets.SystemRandom().sample(range(25),mines),'opened':[]}
def mines_multiplier(opened,mines):
    safe=25-mines
    if opened<=0:return 1
    if opened>=safe:return 24
    p=1
    for i in range(opened): p*= (safe-i)/(25-i)
    return round(.96/max(p,.0001),2)
async def play_mines(user_id:int, bet:int, mines=5, opened:Optional[List[int]]=None, mine_positions:Optional[List[int]]=None):
    bet=_safe_bet(bet); mines=int(mines); opened=sorted(set(int(x) for x in (opened or [])))
    if not 1<=mines<=24: raise ValueError('Количество мин: 1–24')
    if any(x<0 or x>=25 for x in opened): raise ValueError('Клетка: 0–24')
    positions=list(mine_positions) if mine_positions is not None else create_mines_board(mines)['mine_positions']
    hit=bool(set(opened)&set(positions)); m=0 if hit else mines_multiplier(len(opened),mines); win=int(bet*m)
    r=await play_game(user_id,'mines',bet,win,m,{'mines':mines,'opened':opened,'mine_positions':positions,'hit_mine':hit})
    return {**r,'mines':mines,'opened':opened,'mine_positions':positions,'hit_mine':hit,'multiplier':m,'display':'💣 МИНА!' if hit else f'💎 Безопасно · {m}x'}

async def play_high_low(user_id:int,bet:int,choice='high'):
    bet=_safe_bet(bet); choice=choice.lower();
    if choice not in {'high','low'}: raise ValueError('choice high/low')
    v=random.randint(1,100); ok=v>=51 if choice=='high' else v<=50; m=1.9 if ok else 0
    r=await _payout('high_low',user_id,bet,m,{'value':v,'choice':choice}); return {**r,'value':v,'choice':choice,'multiplier':m}
async def play_coinflip(user_id:int,bet:int,choice='heads'):
    bet=_safe_bet(bet); choice=choice.lower();
    if choice not in {'heads','tails'}: raise ValueError('heads/tails')
    v=random.choice(['heads','tails']); m=1.9 if v==choice else 0
    r=await _payout('coinflip',user_id,bet,m,{'choice':choice,'result':v}); return {**r,'choice':choice,'result_value':v,'multiplier':m}
async def play_rps(user_id:int,bet:int,choice='rock'):
    bet=_safe_bet(bet); choice=choice.lower()
    if choice not in RPS: raise ValueError('rock/paper/scissors')
    enemy=random.choice(tuple(RPS)); win=(choice,enemy) in {('rock','scissors'),('scissors','paper'),('paper','rock')}; draw=choice==enemy; m=1 if draw else (1.9 if win else 0)
    r=await _payout('rps',user_id,bet,m,{'player':choice,'enemy':enemy,'winner':'draw' if draw else ('player' if win else 'enemy')}); return {**r,'player':choice,'enemy':enemy,'winner':'draw' if draw else ('player' if win else 'enemy'),'multiplier':m}
async def play_color(user_id:int,bet:int,choice='red'):
    bet=_safe_bet(bet); choice=choice.lower()
    if choice not in COLORS: raise ValueError('Неверный цвет')
    v=random.choice(COLORS); m=4 if v==choice else 0
    r=await _payout('color',user_id,bet,m,{'choice':choice,'result':v}); return {**r,'choice':choice,'result_color':v,'multiplier':m}

async def play_blackjack(user_id:int,bet:int,action='stand'):
    bet=_safe_bet(bet); action=action.lower();
    if action not in {'hit','stand'}: raise ValueError('action hit/stand')
    player=[random.randint(1,11),random.randint(1,11)]; dealer=[random.randint(1,11),random.randint(1,11)]
    ps=sum(player); ds=sum(dealer)
    if action=='hit': ps+=random.randint(1,11)
    if ps>21: m=0; outcome='bust'
    elif ds>21 or ps>ds: m=2; outcome='win'
    elif ps==ds: m=1; outcome='draw'
    else: m=0; outcome='lose'
    r=await _payout('blackjack',user_id,bet,m,{'player':player,'dealer':dealer,'player_total':ps,'dealer_total':ds,'outcome':outcome})
    return {**r,'player_total':ps,'dealer_total':ds,'outcome':outcome,'multiplier':m}

async def play_reaction(user_id:int,bet:int):
    bet=_safe_bet(bet); ms=random.randint(180,1400); m=3 if ms<350 else 2 if ms<600 else 1.5 if ms<900 else 0
    r=await _payout('reaction',user_id,bet,m,{'milliseconds':ms}); return {**r,'milliseconds':ms,'multiplier':m}
async def play_race(user_id:int,bet:int):
    bet=_safe_bet(bet); roll=[random.randint(1,100) for _ in range(3)]; place=1+sum(x>roll[0] for x in roll[1:]); m={1:3,2:1.5,3:0}[place]
    r=await _payout('race',user_id,bet,m,{'rolls':roll,'place':place}); return {**r,'rolls':roll,'place':place,'multiplier':m}

GAME_HANDLERS={'dice':play_dice,'darts':play_darts,'football':play_football,'basketball':play_basketball,'bowling':play_bowling,'slots':play_slots,'mines':play_mines,'crash':play_crash,'roulette':play_roulette,'coinflip':play_coinflip,'blackjack':play_blackjack,'reaction':play_reaction,'race':play_race,'high_low':play_high_low,'rps':play_rps,'color':play_color}

async def play(user_id:int,game_code:str,bet:int,**kwargs):
    code=str(game_code).lower().strip(); handler=GAME_HANDLERS.get(code)
    if not handler: raise ValueError(f"Игра '{code}' не найдена")
    game=await get_game(code)
    if not game: raise ValueError(f"Игра '{code}' не зарегистрирована в БД")
    if not game['enabled']: raise ValueError('Игра временно отключена')
    bet=_safe_bet(bet)
    if bet<int(game['min_bet']): raise ValueError(f"Минимальная ставка: {game['min_bet']}")
    if bet>int(game['max_bet']): raise ValueError(f"Максимальная ставка: {game['max_bet']}")
    return await handler(user_id,bet,**kwargs)

async def available_games():
    from app.db import get_games
    return [dict(x) for x in await get_games()]
