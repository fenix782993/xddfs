from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


def games_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="🎲 Dice",
                    callback_data="game:dice"
                ),
                InlineKeyboardButton(
                    text="🎰 Slots",
                    callback_data="game:slots"
                ),
            ],

            [
                InlineKeyboardButton(
                    text="💣 Mines",
                    callback_data="game:mines"
                ),
                InlineKeyboardButton(
                    text="📈 Crash",
                    callback_data="game:crash"
                ),
            ],

            [
                InlineKeyboardButton(
                    text="🎡 Roulette",
                    callback_data="game:roulette"
                ),
            ],

            [
                InlineKeyboardButton(
                    text="⚽ Football",
                    callback_data="game:football"
                ),
                InlineKeyboardButton(
                    text="🏀 Basketball",
                    callback_data="game:basketball"
                ),
            ],

            [
                InlineKeyboardButton(
                    text="🎯 Darts",
                    callback_data="game:darts"
                ),
                InlineKeyboardButton(
                    text="🎳 Bowling",
                    callback_data="game:bowling"
                ),
            ],

            [
                InlineKeyboardButton(
                    text="⚔️ PvP Бои",
                    callback_data="pvp"
                ),
            ],

            [
                InlineKeyboardButton(
                    text="🤖 PvE Бои",
                    callback_data="pve"
                ),
            ],

            [
                InlineKeyboardButton(
                    text="◀️ Назад",
                    callback_data="home"
                )
            ],
        ]
    )


def bet_menu(game: str):

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="💰 10",
                    callback_data=f"bet:{game}:10"
                ),
                InlineKeyboardButton(
                    text="💰 50",
                    callback_data=f"bet:{game}:50"
                ),
            ],

            [
                InlineKeyboardButton(
                    text="💰 100",
                    callback_data=f"bet:{game}:100"
                ),
                InlineKeyboardButton(
                    text="💰 500",
                    callback_data=f"bet:{game}:500"
                ),
            ],

            [
                InlineKeyboardButton(
                    text="💰 1 000",
                    callback_data=f"bet:{game}:1000"
                ),
                InlineKeyboardButton(
                    text="💰 5 000",
                    callback_data=f"bet:{game}:5000"
                ),
            ],

            [
                InlineKeyboardButton(
                    text="◀️ К играм",
                    callback_data="games"
                )
            ]
        ]
    )