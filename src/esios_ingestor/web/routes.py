from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
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
