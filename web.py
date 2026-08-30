from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
def admin_menu(): return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='📊 Статистика',callback_data='admin_stats')],[InlineKeyboardButton(text='⬅️ Назад',callback_data='home')]])
