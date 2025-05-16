import aiohttp
from config import get_config, Admin
from services.admin_req import check_admin

async def is_admin(user_id: str, config_admin_id: list) -> bool:
    # Проверка через config.yaml
    if user_id in config_admin_id:
        return True
    
    # Проверка через бэкенд
    return await check_admin(int(user_id))
