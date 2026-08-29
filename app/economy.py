from app.db import (
    get_user,
    change_balance,
    add_xp,
)


async def get_balance(user_id: int) -> int:
    user = await get_user(user_id)

    if not user:
        return 0

    return int(user["balance"])


async def deposit(
    user_id: int,
    amount: int,
    reason: str = "deposit",
    meta: dict | None = None,
):
    if amount <= 0:
        raise ValueError("invalid_amount")

    return await change_balance(
        user_id,
        amount,
        reason,
        meta,
    )


async def withdraw(
    user_id: int,
    amount: int,
    reason: str = "withdraw",
    meta: dict | None = None,
):
    if amount <= 0:
        raise ValueError("invalid_amount")

    return await change_balance(
        user_id,
        -amount,
        reason,
        meta,
    )


async def reward(
    user_id: int,
    amount: int,
    reason: str,
    xp: int = 0,
):
    balance = await deposit(
        user_id,
        amount,
        reason,
    )

    if xp > 0:
        await add_xp(
            user_id,
            xp,
        )

    return balance


async def spend(
    user_id: int,
    amount: int,
    reason: str,
    meta: dict | None = None,
):
    return await withdraw(
        user_id,
        amount,
        reason,
        meta,
    )


def format_coins(value: int) -> str:
    return f"{value:,}".replace(",", " ")