from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
def pvp_menu(): return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='⚔️ PvP',callback_data='pvp')],[InlineKeyboardButton(text='⬅️ Назад',callback_data='home')]])
