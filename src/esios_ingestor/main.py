import typer
import asyncio
import uvicorn
import logging
from datetime import datetime
from sqlalchemy import select
from rich.console import Console
from rich.table import Table

from esios_ingestor.core.logger import setup_logging
from esios_ingestor.ingestion.service import ingest_data
from esios_ingestor.core.database import AsyncSessionLocal
from esios_ingestor.models.price import ElectricityPrice

app = typer.Typer(help="Esios Ingestor CLI")
console = Console()

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
        "esios_ingestor.web.app:app", 
        host=host, 
        port=port, 
        reload=reload
    )

@app.command()
def prices(
    limit: int = typer.Option(10, help="Number of prices to show"),
    date: str = typer.Option(None, help="Filter by date (YYYY-MM-DD)")
):
    """
    Show electricity prices from the database in a table.
    """
    async def _get_prices():
        async with AsyncSessionLocal() as session:
            query = select(ElectricityPrice).order_by(ElectricityPrice.timestamp.desc())
            
            if date:
                try:
                    # Filter for specific day (00:00 to 23:59)
                    start_dt = datetime.strptime(date, "%Y-%m-%d")
                    end_dt = start_dt.replace(hour=23, minute=59, second=59)
                    query = query.where(
                        ElectricityPrice.timestamp >= start_dt,
                        ElectricityPrice.timestamp <= end_dt
                    )
                except ValueError:
                    console.print("[red]Invalid date format. Use YYYY-MM-DD[/red]")
                    return []

            query = query.limit(limit)
            result = await session.execute(query)
            return result.scalars().all()

    try:
        results = asyncio.run(_get_prices())
    except Exception as e:
        console.print(f"[red]Error fetching prices: {e}[/red]")
        return

    if not results:
        console.print("[yellow]No prices found.[/yellow]")
        return

    table = Table(title=f"Electricity Prices (Top {len(results)})")
    table.add_column("Time (UTC)", style="cyan")
    table.add_column("Price (€/MWh)", style="green", justify="right")
    table.add_column("Zone", style="magenta")

    for p in results:
        table.add_row(
            p.timestamp.strftime("%Y-%m-%d %H:%M"),
            f"{p.price:.2f}",
            str(p.zone_id)
        )

    console.print(table)

if __name__ == "__main__":
    app()
