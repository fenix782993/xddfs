from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


def main_menu(
    webapp_url: str = "",
) -> InlineKeyboardMarkup:

    rows = []

    if webapp_url:
        rows.append([
            InlineKeyboardButton(
                text="🔥 ОТКРЫТЬ FENIX COIN",
                web_app={
                    "url": webapp_url
                }
            )
        ])

    rows.extend([
        [
            InlineKeyboardButton(
                text="👤 Профиль",
                callback_data="profile"
            ),
            InlineKeyboardButton(
                text="🎮 Игры",
                callback_data="games"
            ),
        ],

        [
            InlineKeyboardButton(
                text="⚔️ PvP",
                callback_data="pvp"
            ),
            InlineKeyboardButton(
                text="🤖 PvE",
                callback_data="pve"
            ),
        ],

        [
            InlineKeyboardButton(
                text="🎯 Миссии",
                callback_data="missions"
            ),
            InlineKeyboardButton(
                text="🎁 Бонус",
                callback_data="daily"
            ),
        ],

        [
            InlineKeyboardButton(
                text="👥 Рефералы",
                callback_data="referrals"
            ),
            InlineKeyboardButton(
                text="🏆 Рейтинг",
                callback_data="leaderboard"
            ),
        ],

        [
            InlineKeyboardButton(
                text="🛒 Магазин",
                callback_data="shop"
            ),
            InlineKeyboardButton(
                text="🎒 Инвентарь",
                callback_data="inventory"
            ),
        ],

        [
            InlineKeyboardButton(
                text="📜 Правила",
                callback_data="rules"
            ),
        ],
    ])

    return InlineKeyboardMarkup(
        inline_keyboard=rows
    )


def back_menu() -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="◀️ Назад",
                    callback_data="home"
                )
            ]
        ]
    )