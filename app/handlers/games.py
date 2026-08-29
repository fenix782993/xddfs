from aiogram import Router,F
from aiogram.types import CallbackQuery
from app.keyboards import games,back
from app.ui import visual
from app.db import balance,result,xp
from app.native import EMOJI,win
from app.games import crash_point,roulette,slots
r=Router()
DESC={
"dice":"Telegram Dice 1–6. Максимум выигрывает.","darts":"Telegram Darts. Максимальная точность выигрывает.",
"football":"Telegram Football. Удачный удар определяет результат.","basketball":"Telegram Basketball. Попадание приносит победу.",
"bowling":"Telegram Bowling. Максимум кеглей — победа.","slots":"Telegram Slots. Редкие комбинации дают выплату.",
"mines":"Mines 5×5. Открывай клетки и избегай мин.","crash":"Crash. Забери раунд до остановки множителя.",
"roulette":"Roulette 0–36. Полная ставка будет в Mini App."}
@r.callback_query(F.data=="games")
async def menu(c):
    await c.answer();await c.message.delete()
    await c.message.answer_photo(visual("FENIX GAMES","Telegram Native + server games.\\nУ каждой игры отдельная механика.","🎮"),reply_markup=games())
@r.callback_query(F.data.startswith("game:"))
async def info(c):
    k=c.data.split(":")[1];await c.answer();await c.message.delete()
    await c.message.answer_photo(visual(k.upper(),DESC[k]+"\\n\\n💰 V1 ставка: 100 🔥","🎮"),reply_markup=back())
@r.callback_query(F.data.startswith("play:"))
async def play(c):
    k=c.data.split(":")[1]
    if k in EMOJI:
        try: await balance(c.from_user.id,-100,"native_bet:"+k)
        except: return await c.answer("Недостаточно Fenix Coin",show_alert=True)
        d=await c.message.answer_dice(emoji=EMOJI[k]);w=win(k,d.dice.value)
        if w: await balance(c.from_user.id,500,"native_win:"+k)
        await result(c.from_user.id,w);await xp(c.from_user.id,25 if w else 5)
        return await c.answer("🏆 Победа!" if w else "💀 Не повезло")
    if k=="crash": await c.message.answer(f"📈 Crash x{crash_point()}")
    elif k=="roulette": await c.message.answer(f"🎡 Roulette: {roulette()}")
    elif k=="slots": await c.message.answer(f"🎰 {slots()}")
    elif k=="mines": await c.message.answer("💣 Mines 5×5: полноценное поле подключается через Mini App API.")
