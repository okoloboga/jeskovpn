import requests

async def delete_ticket(user_id: int) -> None:
    """Mock ticket deletion."""
    print(f"Deleted ticket for user {user_id}")
