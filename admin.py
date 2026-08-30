from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
def profile_menu(): return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='⬅️ Назад',callback_data='home')]])
