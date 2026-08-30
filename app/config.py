import os

class Settings:
    database_url = os.getenv("DATABASE_URL", "")
    bot_token = os.getenv("BOT_TOKEN", "")
    webapp_url = os.getenv("WEBAPP_URL", "")
    start_balance = int(os.getenv("START_BALANCE", "1000"))
    ref_reward = int(os.getenv("REF_REWARD", "600"))
    min_bet = int(os.getenv("MIN_BET", "10"))
    max_bet = int(os.getenv("MAX_BET", "100000"))
    house_edge = float(os.getenv("HOUSE_EDGE", "0.03"))

settings = Settings()
