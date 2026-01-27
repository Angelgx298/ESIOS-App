import typer
import asyncio
import uvicorn
import logging
from esios_ingestor.core.logger import setup_logging
from esios_ingestor.ingestion.service import ingest_data

# Initialize Typer app
app = typer.Typer(help="Esios Ingestor CLI")

# Setup logging globally for CLI commands
setup_logging()
logger = logging.getLogger(__name__)

@app.command()
def ingest():
    """
    Triggers the ETL pipeline to fetch and store electricity prices.
    """
    logger.info("Starting ingestion process from CLI...")
    try:
        asyncio.run(ingest_data())
        logger.info("Ingestion process finished successfully.")
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise typer.Exit(code=1)

@app.command()
def server(
    host: str = "0.0.0.0", 
    port: int = 8000, 
    reload: bool = False
):
    """
    Starts the FastAPI web server.
    """
    logger.info(f"Starting API server on {host}:{port}")
    uvicorn.run(
        "src.esios_ingestor.web.app:app", 
        host=host, 
        port=port, 
        reload=reload
    )

if __name__ == "__main__":
    app()
