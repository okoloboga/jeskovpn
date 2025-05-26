import uvicorn
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

from app.api.endpoints import admin, user, referral, payment, device, raffles
from app.core.security import get_api_key
from app.core.config import get_app_config
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.services.subscription_cleanup import cleanup_expired_subscriptions

logger = logging.getLogger(__name__)

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
app.include_router(raffles.router, prefix="/raffles", tags=["raffles"], dependencies=[Depends(get_api_key)])

# Initialize scheduler
scheduler = AsyncIOScheduler(timezone="UTC")

@app.on_event("startup")
async def startup_event():
    # Create a new database session for the scheduler
    async def run_cleanup():
        async with SessionLocal() as db:
            try:
                stats = await cleanup_expired_subscriptions(db)
                logger.info(f"Subscription cleanup completed: {stats}")
            except Exception as e:
                logger.error(f"Subscription cleanup failed: {e}")
    
    # Schedule daily cleanup at 00:00 UTC
    scheduler.add_job(
        run_cleanup,
        trigger=CronTrigger(hour=0, minute=0),
        id="subscription_cleanup",
        replace_existing=True
    )
    scheduler.start()
    logger.info("Scheduler started")

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
    logger.info("Scheduler stopped")

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
