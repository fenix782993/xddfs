from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from app.config import settings

def main_menu(url=''):
    rows=[]
    if url: rows.append([InlineKeyboardButton(text='🔥 Открыть Fenix Coin',web_app=WebAppInfo(url=url))])
    rows += [[InlineKeyboardButton(text='🎮 Игры',callback_data='games'),InlineKeyboardButton(text='👤 Профиль',callback_data='profile')],
             [InlineKeyboardButton(text='🏆 Рейтинг',callback_data='rating'),InlineKeyboardButton(text='🎁 Бонус',callback_data='bonus')],
             [InlineKeyboardButton(text='⚔️ PvP',callback_data='pvp'),InlineKeyboardButton(text='👥 Рефералы',callback_data='refs')],
             [InlineKeyboardButton(text='🛒 Магазин',callback_data='shop')]]
    return InlineKeyboardMarkup(inline_keyboard=rows)
def back_menu(): return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='⬅️ Назад',callback_data='home')]])
