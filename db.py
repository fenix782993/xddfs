from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
GAMES=[('dice','🎲 Dice'),('darts','🎯 Darts'),('football','⚽ Football'),('basketball','🏀 Basketball'),('bowling','🎳 Bowling'),('slots','🎰 Slots'),('mines','💣 Mines'),('crash','📈 Crash'),('roulette','🎡 Roulette'),('coinflip','🪙 Coin Flip'),('blackjack','🃏 Blackjack'),('reaction','⚡ Reaction'),('race','🏁 Race')]
def games_menu():
    rows=[]
    for i in range(0,len(GAMES),2): rows.append([InlineKeyboardButton(text=GAMES[i][1],callback_data='game:'+GAMES[i][0])]+([InlineKeyboardButton(text=GAMES[i+1][1],callback_data='game:'+GAMES[i+1][0])] if i+1<len(GAMES) else []))
    rows.append([InlineKeyboardButton(text='⬅️ Назад',callback_data='home')])
    return InlineKeyboardMarkup(inline_keyboard=rows)
def bet_menu(code):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=str(x),callback_data=f'bet:{code}:{x}') for x in (100,250,500,1000)],[InlineKeyboardButton(text='⬅️ Игры',callback_data='games')]])
