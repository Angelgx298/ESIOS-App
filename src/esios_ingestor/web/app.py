from contextlib import asynccontextmanager
from fastapi import FastAPI
from tenacity import retry, stop_after_attempt, wait_fixed
import logging

from esios_ingestor.core.logger import setup_logging
from esios_ingestor.core.database import engine, Base
from esios_ingestor.models.price import ElectricityPrice 

logger = logging.getLogger(__name__)

@retry(stop=stop_after_attempt(5), wait=wait_fixed(2))
async def init_db():
    logger.info("Initializing database connection...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables verified.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    
    try:
        await init_db()
    except Exception as e:
        logger.error("Critical: Database connection failed.", exc_info=True)
        raise e
    
    yield
    
    await engine.dispose()

app = FastAPI(title="Esios Ingestor API", lifespan=lifespan)

@app.get("/health")
async def health_check():
    """Simple health check to verify the app is running."""
    return {"status": "ok", "service": "esios-ingestor"}
