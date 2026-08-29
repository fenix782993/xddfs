from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
)

from app.config import settings


def main_menu():

    buttons = [
        [
            InlineKeyboardButton(
                text="🎮 ИГРЫ",
                callback_data="games",
            ),
            InlineKeyboardButton(
                text="⚔️ PVP",
                callback_data="pvp",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🤖 PVE",
                callback_data="pve",
            ),
            InlineKeyboardButton(
                text="🎯 МИССИИ",
                callback_data="missions",
            ),
        ],
        [
            InlineKeyboardButton(
                text="👤 ПРОФИЛЬ",
                callback_data="profile",
            ),
            InlineKeyboardButton(
                text="👥 РЕФЕРАЛЫ",
                callback_data="referrals",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🏆 РЕЙТИНГ",
                callback_data="leaderboard",
            ),
            InlineKeyboardButton(
                text="🎁 БОНУС",
                callback_data="bonus",
            ),
        ],
    ]

    if settings.webapp_url:

        buttons.append(
            [
                InlineKeyboardButton(
                    text="🔥 ОТКРЫТЬ FENIX COIN",
                    web_app=WebAppInfo(
                        url=settings.webapp_url
                    ),
                )
            ]
        )

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


def back():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="home",
                )
            ]
        ]
    )


def games_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎲 Dice",
                    callback_data="game_dice",
                ),
                InlineKeyboardButton(
                    text="🎯 Darts",
                    callback_data="game_darts",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⚽ Football",
                    callback_data="game_football",
                ),
                InlineKeyboardButton(
                    text="🏀 Basketball",
                    callback_data="game_basketball",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🎳 Bowling",
                    callback_data="game_bowling",
                ),
                InlineKeyboardButton(
                    text="🎰 Slots",
                    callback_data="game_slots",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="💣 Mines",
                    callback_data="game_mines",
                ),
                InlineKeyboardButton(
                    text="📈 Crash",
                    callback_data="game_crash",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🎡 Roulette",
                    callback_data="game_roulette",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="home",
                )
            ],
        ]
    )


def pvp_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚔️ Создать бой",
                    callback_data="pvp_create",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔎 Найти бой",
                    callback_data="pvp_find",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 Мои бои",
                    callback_data="pvp_my",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="home",
                )
            ],
        ]
    )