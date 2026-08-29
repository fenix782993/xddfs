from aiogram.types import InlineKeyboardMarkup,InlineKeyboardButton
def kb(rows): return InlineKeyboardMarkup(inline_keyboard=rows)
def main():
 return kb([
 [InlineKeyboardButton(text="🎮 ИГРЫ",callback_data="games"),InlineKeyboardButton(text="👤 ПРОФИЛЬ",callback_data="profile")],
 [InlineKeyboardButton(text="⚔️ PVP",callback_data="pvp"),InlineKeyboardButton(text="🤖 PVE",callback_data="pve")],
 [InlineKeyboardButton(text="🎯 МИССИИ",callback_data="missions"),InlineKeyboardButton(text="👥 РЕФЕРАЛЫ",callback_data="refs")],
 [InlineKeyboardButton(text="🏆 ТОП",callback_data="top"),InlineKeyboardButton(text="🎁 БОНУС",callback_data="bonus")],
 [InlineKeyboardButton(text="🛍️ SHOP",callback_data="shop"),InlineKeyboardButton(text="📜 ПРАВИЛА",callback_data="rules")]])
def games():
 names=[("🎲 Dice","dice"),("🎯 Darts","darts"),("⚽ Football","football"),("🏀 Basketball","basketball"),
 ("🎳 Bowling","bowling"),("🎰 Slots","slots"),("💣 Mines","mines"),("📈 Crash","crash"),("🎡 Roulette","roulette")]
 rows=[]
 for i in range(0,len(names),2):
  row=[InlineKeyboardButton(text=names[i][0],callback_data="game:"+names[i][1])]
  if i+1<len(names): row.append(InlineKeyboardButton(text=names[i+1][0],callback_data="game:"+names[i+1][1]))
  rows.append(row)
 rows.append([InlineKeyboardButton(text="⬅️ Назад",callback_data="home")])
 return kb(rows)
def back(): return kb([[InlineKeyboardButton(text="⬅️ Назад",callback_data="home")]])
