import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert

from src.esios_ingestor.core.database import AsyncSessionLocal
from src.esios_ingestor.models.price import ElectricityPrice
from src.esios_ingestor.ingestion.client import EsiosClient

logger = logging.getLogger(__name__)

async def get_last_recorded_timestamp() -> datetime | None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(func.max(ElectricityPrice.timestamp))
        last_date = result.scalar()
        
        # Normalize to UTC
        if last_date and last_date.tzinfo is None:
            last_date = last_date.replace(tzinfo=timezone.utc)
            
        return last_date

async def ingest_data():
    """Idempotent ETL flow: Fetch only new data -> Upsert to DB."""
    client = EsiosClient()
    
    last_date = await get_last_recorded_timestamp()
    now = datetime.now(timezone.utc)
    target_end = now + timedelta(days=2) 

    if not last_date:
        logger.info("Database empty. Starting initial load (last 7 days).")
        start_date = now - timedelta(days=7)
    else:
        start_date = last_date + timedelta(hours=1)
        
        if start_date >= target_end:
            logger.info("Data is up to date.")
            return

    try:
        esios_data = await client.fetch_prices(start_date, target_end)
        
        if not esios_data:
            logger.info("No new data received from API.")
            return

        async with AsyncSessionLocal() as session:
            records_count = 0
            
            for item in esios_data.indicator.values:
                stmt = insert(ElectricityPrice).values(
                    timestamp=item.datetime_utc,
                    price=item.value,
                    zone_id=item.geo_id
                ).on_conflict_do_nothing(
                    index_elements=['timestamp', 'zone_id']
                )
                
                await session.execute(stmt)
                records_count += 1
            
            await session.commit()
            logger.info(f"Ingestion complete. Processed {records_count} records.")

    except Exception:
        logger.error("Ingestion process failed.", exc_info=True)
