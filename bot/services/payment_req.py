import requests

async def deposit(user_id: int, amount: float, payment_type: str) -> None:
    """Mock balance deposit."""
    print(f"Deposited {amount} for user {user_id} via {payment_type}")

async def payment_ukassa_process(user_id: int, amount: float, payment_type: str) -> None:
    """Mock ЮKassa payment."""
    print(f"ЮKassa payment of {amount} for user {user_id}, type: {payment_type}")

async def payment_crypto_process(user_id: int, amount: float, payment_type: str) -> None:
    """Mock crypto payment."""
    print(f"Crypto payment of {amount} for user {user_id}, type: {payment_type}")

async def payment_balance_process(user_id: int, amount: float, payment_type: str) -> None:
    """Mock balance payment."""
    print(f"Balance payment of {amount} for user {user_id}, type: {payment_type}")
