from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime

from esios_ingestor.core.database import get_db
from esios_ingestor.models.price import ElectricityPrice
from pydantic import BaseModel

router = APIRouter()

class PriceResponse(BaseModel):
    timestamp: datetime
    price: float
    zone_id: int

    class Config:
        from_attributes = True

@router.get("/prices", response_model=List[PriceResponse])
async def get_prices(
    limit: int = Query(24, ge=1, le=168),
    start_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db)
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
