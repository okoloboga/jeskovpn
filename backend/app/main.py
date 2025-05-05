import uvicorn
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.api.endpoints import admin, user, referral, payment, device
from app.core.security import get_api_key
from app.core.config import get_app_config
from app.db.base import Base
from app.db.session import engine

# Create database tables
Base.metadata.create_all(bind=engine)

config = get_app_config()

app = FastAPI(title="VPN Service API")

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with authentication
app.include_router(user.router, prefix="/users", tags=["users"], dependencies=[Depends(get_api_key)])
app.include_router(referral.router, prefix="/referrals", tags=["referrals"], dependencies=[Depends(get_api_key)])
app.include_router(payment.router, prefix="/payments", tags=["payments"], dependencies=[Depends(get_api_key)])
app.include_router(device.router, prefix="/devices", tags=["devices"], dependencies=[Depends(get_api_key)])
app.include_router(admin.router, prefix="/admin", tags=["admin"], dependencies=[Depends(get_api_key)])

@app.get("/")
async def root():
    return {"message": "Welcome to VPN Service API"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=config.server.port,
        log_level=config.server.log_level.lower(),
    )
