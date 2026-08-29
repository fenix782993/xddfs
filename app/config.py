import os
from dataclasses import dataclass


def env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


@dataclass
class Settings:
    # Telegram
    bot_token: str = os.getenv("BOT_TOKEN", "")
    bot_username: str = os.getenv("BOT_USERNAME", "")

    # PostgreSQL
    database_url: str = os.getenv("DATABASE_URL", "")

    # Admin
    admin_ids: str = os.getenv("ADMIN_IDS", "")

    # Economy
    start_balance: int = env_int(
        "START_BALANCE",
        1000
    )

    ref_reward: int = env_int(
        "REF_REWARD",
        600
    )

    min_bet: int = env_int(
        "MIN_BET",
        10
    )

    max_bet: int = env_int(
        "MAX_BET",
        100000
    )

    house_edge: float = env_float(
        "HOUSE_EDGE",
        0.05
    )

    # Web
    webapp_url: str = os.getenv(
        "WEBAPP_URL",
        ""
    )

    @property
    def admins(self) -> list[int]:
        result = []

        for value in self.admin_ids.split(","):
            value = value.strip()

            if not value:
                continue

            try:
                result.append(int(value))
            except ValueError:
                pass

        return result


settings = Settings()