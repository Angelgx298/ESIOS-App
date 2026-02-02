from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from esios_ingestor.core.database import get_db
from esios_ingestor.models.price import ElectricityPrice

router = APIRouter()


class PriceResponse(BaseModel):
    timestamp: datetime
    price: float
    zone_id: int
    model_config = ConfigDict(from_attributes=True)


@router.get("/prices", response_model=list[PriceResponse])
async def get_prices(
    limit: int = Query(24, ge=1, le=168),
    start_date: datetime | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Get electricity prices.
    By default returns the latest prices.
    """
    query = select(ElectricityPrice).order_by(ElectricityPrice.timestamp.desc())

    if start_date:
        query = query.where(ElectricityPrice.timestamp >= start_date)

    query = query.limit(limit)

    result = await db.execute(query)
    prices = result.scalars().all()

    return prices


@router.get("/prices/stats")
async def get_price_stats(
    days: int = Query(7, ge=1, le=30, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get aggregated statistics for electricity prices over the last N days.

    Returns:
        - avg_price: Average price in the period
        - max_price: Maximum price recorded
        - min_price: Minimum price recorded
        - peak_hour: Hour of day (0-23) with highest average price
        - cheapest_hour: Hour of day (0-23) with lowest average price
    """
    cutoff_date = datetime.now(UTC) - timedelta(days=days)

    stats_query = select(
        func.avg(ElectricityPrice.price).label("avg_price"),
        func.max(ElectricityPrice.price).label("max_price"),
        func.min(ElectricityPrice.price).label("min_price"),
    ).where(ElectricityPrice.timestamp >= cutoff_date)

    result = await db.execute(stats_query)
    stats = result.one()

    peak_query = (
        select(
            extract("hour", ElectricityPrice.timestamp).label("hour"),
            func.avg(ElectricityPrice.price).label("avg_price"),
        )
        .where(ElectricityPrice.timestamp >= cutoff_date)
        .group_by(extract("hour", ElectricityPrice.timestamp))
        .order_by(func.avg(ElectricityPrice.price).desc())
        .limit(1)
    )

    peak_result = await db.execute(peak_query)
    peak_hour = peak_result.scalar()

    cheap_query = (
        select(
            extract("hour", ElectricityPrice.timestamp).label("hour"),
            func.avg(ElectricityPrice.price).label("avg_price"),
        )
        .where(ElectricityPrice.timestamp >= cutoff_date)
        .group_by(extract("hour", ElectricityPrice.timestamp))
        .order_by(func.avg(ElectricityPrice.price).asc())
        .limit(1)
    )

    cheap_result = await db.execute(cheap_query)
    cheapest_hour = cheap_result.scalar()

    return {
        "period": f"last_{days}_days",
        "avg_price": round(float(stats.avg_price), 2) if stats.avg_price else None,
        "max_price": round(float(stats.max_price), 2) if stats.max_price else None,
        "min_price": round(float(stats.min_price), 2) if stats.min_price else None,
        "peak_hour": int(peak_hour) if peak_hour is not None else None,
        "cheapest_hour": int(cheapest_hour) if cheapest_hour is not None else None,
    }
