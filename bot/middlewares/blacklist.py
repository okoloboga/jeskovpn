from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from utils.admin_auth import is_admin
from config import get_config, Admin
from services.admin_req import is_user_blacklisted

class BlacklistMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user_id = str(data["event_from_user"].id)
        admin = get_config(Admin, "admin")
        admin_id = admin.id
        
        # Проверка админа через бэкенд
        if await is_admin(user_id, admin_id):
            return await handler(event, data)
        
        # Проверка черного списка через бэкенд
        if await is_user_blacklisted(int(user_id)):
            return
        
        return await handler(event, data)
