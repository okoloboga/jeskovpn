from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN
from app.core.config import get_app_config

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)
config = get_app_config()

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if not api_key_header:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Could not validate API key"
        )
    
    # Extract the token part from "Bearer {token}"
    if api_key_header.startswith("Bearer "):
        token = api_key_header.replace("Bearer ", "")
    else:
        token = api_key_header
    
    if token != config.api.token:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Invalid API key"
        )
    
    return token
