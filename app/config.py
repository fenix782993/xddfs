import os
from dataclasses import dataclass
from dotenv import load_dotenv
load_dotenv()

def ids(v):
    return {int(x.strip()) for x in (v or "").split(",") if x.strip()}

@dataclass(frozen=True)
class Settings:
    bot_token: str = os.getenv("BOT_TOKEN","")
    database_url: str = os.getenv("DATABASE_URL","")
    admin_ids: set[int] = None
    admin_channel_id: int|None = None
    bot_username: str = os.getenv("BOT_USERNAME","")
    webapp_url: str = os.getenv("WEBAPP_URL","")
    ref_reward: int = int(os.getenv("REF_REWARD","600"))
    start_balance: int = int(os.getenv("START_BALANCE","1000"))
    min_bet: int = int(os.getenv("MIN_BET","10"))
    max_bet: int = int(os.getenv("MAX_BET","100000"))
    house_edge: float = float(os.getenv("HOUSE_EDGE","0.05"))

settings = Settings(
    admin_ids=ids(os.getenv("ADMIN_IDS")),
    admin_channel_id=int(os.getenv("ADMIN_CHANNEL_ID")) if os.getenv("ADMIN_CHANNEL_ID") else None
)
