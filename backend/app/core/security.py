from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import get_app_config

config = get_app_config()

class BearerTokenAuth(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(BearerTokenAuth, self).__init__(auto_error=auto_error)
        self.api_token = config.api.token

    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials:
        credentials: HTTPAuthorizationCredentials = await super(BearerTokenAuth, self).__call__(request)
        
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header is required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if credentials.scheme != "Bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header format must be Bearer {token}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if credentials.credentials != self.api_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return credentials.credentials

# Create an instance of the auth class to use as a dependency
bearer_auth = BearerTokenAuth()

# Function to use as a dependency in routes
async def get_api_key(token: str = Depends(bearer_auth)):
    return token
