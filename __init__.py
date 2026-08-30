import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    bot_token: str = os.getenv('BOT_TOKEN', '').strip()
    database_url: str = os.getenv('DATABASE_URL', '').strip()
    webapp_url: str = os.getenv('WEBAPP_URL', '').strip().rstrip('/')
    bot_username: str = os.getenv('BOT_USERNAME', '').strip().lstrip('@')
    start_balance: int = int(os.getenv('START_BALANCE', '1000'))
    ref_reward: int = int(os.getenv('REF_REWARD', '600'))
    min_bet: int = int(os.getenv('MIN_BET', '10'))
    max_bet: int = int(os.getenv('MAX_BET', '100000'))
    house_edge: float = float(os.getenv('HOUSE_EDGE', '0.05'))
    admin_ids: tuple[int, ...] = tuple(int(x) for x in os.getenv('ADMIN_IDS', '').replace(' ', '').split(',') if x.isdigit())

settings = Settings()
