import requests

from typing import Optional, Dict, Any
from datetime import datetime

async def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    """Mock user data."""
    return {
        "user_id": user_id,
        "balance": 500.0,
        "is_subscribed": True,
        "devices": ["android", "iphone"],
        "combo_cells": ["combo_5"],
        "subscription_expires": datetime.utcnow().isoformat(),
    }

async def create_user(user_id: int, first_name: str, last_name: str, username: str) -> None:
    """Mock user creation."""
    print(f"Created user {user_id}: {first_name} {last_name} (@{username})")

async def add_referral(payload: str, user_id: str) -> None:
    """Mock referral addition."""
    print(f"Added referral {payload} for user {user_id}")

async def send_ticket(content: str, user_id: int, username: str) -> None:
    """Mock ticket creation."""
    print(f"Ticket from user {user_id} (@{username}): {content}")

async def get_ticket_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Mock ticket retrieval."""
    return {"user_id": user_id, "content": "Sample ticket", "created_at": datetime.utcnow().isoformat()}
