from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.esios_ingestor.core.logger import setup_logging

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    setup_logging()
    yield
    # Shutdown logic

app = FastAPI(title="Esios Ingestor API", lifespan=lifespan)

@app.get("/health")
async def health_check():
    """Simple health check to verify the app is running."""
    return {"status": "ok", "service": "esios-ingestor"}
