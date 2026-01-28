import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert

from esios_ingestor.core.database import AsyncSessionLocal
from esios_ingestor.ingestion.client import EsiosClient
from esios_ingestor.models.price import ElectricityPrice

logger = logging.getLogger(__name__)


async def get_last_recorded_timestamp() -> datetime | None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(func.max(ElectricityPrice.timestamp))
        last_date = result.scalar()

        if last_date and last_date.tzinfo is None:
            last_date = last_date.replace(tzinfo=UTC)

        return last_date


async def ingest_data(start_date: datetime | None = None, end_date: datetime | None = None):
    """
    Idempotent ETL flow: Fetch only new data -> Upsert to DB.

    Args:
        start_date: Custom start date (optional)
        end_date: Custom end date (optional)
    """
    client = EsiosClient()
    now = datetime.now(UTC)

    if start_date and end_date:
        target_start = start_date.replace(tzinfo=UTC) if start_date.tzinfo is None else start_date
        target_end = end_date.replace(tzinfo=UTC) if end_date.tzinfo is None else end_date
        logger.info(f"Using custom date range: {target_start} to {target_end}")
    else:
        last_date = await get_last_recorded_timestamp()
        target_end = now + timedelta(days=2)

        if not last_date:
            logger.info("Database empty. Starting initial load (last 7 days).")
            target_start = now - timedelta(days=7)
        else:
            target_start = last_date + timedelta(hours=1)

            if target_start >= target_end:
                logger.info("Data is up to date.")
                return

    try:
        esios_data = await client.fetch_prices(target_start, target_end)

        if not esios_data:
            logger.info("No new data received from API.")
            return

        async with AsyncSessionLocal() as session:
            records_count = 0

            for item in esios_data.indicator.values:
                stmt = (
                    insert(ElectricityPrice)
                    .values(
                        timestamp=item.datetime_utc,
                        price=item.value,
                        zone_id=item.geo_id,
                    )
                    .on_conflict_do_nothing(index_elements=["timestamp", "zone_id"])
                )

                await session.execute(stmt)
                records_count += 1

            await session.commit()
            logger.info(f"Ingestion complete. Processed {records_count} records.")

    except Exception:
        logger.error("Ingestion process failed.", exc_info=True)
        raise
