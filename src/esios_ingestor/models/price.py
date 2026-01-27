from datetime import datetime
from sqlalchemy import Float, Integer, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from esios_ingestor.core.database import Base

class ElectricityPrice(Base):
    __tablename__ = "electricity_prices"
    
    # Composite unique constraint: We can't have two prices for the same zone at the same time.
    __table_args__ = (
        UniqueConstraint('timestamp', 'zone_id', name='uq_price_timestamp_zone'),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    price: Mapped[float] = mapped_column(Float) # EUR/MWh
    zone_id: Mapped[int] = mapped_column(Integer) # 8741 for Peninsula

    def __repr__(self):
        return f"<Price(time={self.timestamp}, val={self.price})>"
