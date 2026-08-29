import asyncio,logging
from aiogram import Bot,Dispatcher
from app.config import settings
from app.db import init_db,close_db
from app.handlers import start,menu,games,missions,admin,pvp
logging.basicConfig(level=logging.INFO)
async def main():
    if not settings.bot_token or not settings.database_url: raise RuntimeError("BOT_TOKEN and DATABASE_URL required")
    await init_db();bot=Bot(settings.bot_token);dp=Dispatcher()
    for x in [start,menu,games,missions,admin,pvp]: dp.include_router(x.r)
    try: await dp.start_polling(bot)
    finally: await bot.session.close();await close_db()
if __name__=="__main__": asyncio.run(main())
