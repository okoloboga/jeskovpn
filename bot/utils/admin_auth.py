from config import get_config, Admin 

def is_admin(user_id: str, admin_id: list) -> bool:
    return user_id in admin_id
