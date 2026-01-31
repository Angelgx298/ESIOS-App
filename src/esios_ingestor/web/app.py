import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import retry, stop_after_attempt, wait_fixed

from esios_ingestor.core.database import Base, engine, get_db
from esios_ingestor.core.logger import setup_logging
from esios_ingestor.web.routes import router as prices_router

logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(5), wait=wait_fixed(2))
async def init_db():
    logger.info("Initializing database connection...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables verified.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan with graceful startup and shutdown."""
    setup_logging()
    logger.info("Application starting up...")

    try:
        await init_db()
        logger.info("Application startup complete")
    except Exception as e:
        logger.error("Critical: Database connection failed.", exc_info=True)
        raise e

    yield

    # Graceful shutdown sequence
    logger.info("Shutting down application...")
    await engine.dispose()
    logger.info("Graceful shutdown complete")


app = FastAPI(title="Esios Ingestor API", lifespan=lifespan)

app.include_router(prices_router)


@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint that verifies database connectivity.
    Returns 200 if healthy, 503 if database is unreachable.
    """
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected", "service": "esios-ingestor"}
    except Exception:
        raise HTTPException(
            status_code=503, detail={"status": "unhealthy", "database": "disconnected"}
        ) from None


@app.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """
    Readiness probe for orchestrators (Kubernetes, Docker Swarm).
    Returns 200 when ready to receive traffic, 503 otherwise.
    """
    try:
        await db.execute(text("SELECT 1"))
        return {"ready": True}
    except Exception:
        raise HTTPException(status_code=503, detail={"ready": False}) from None
