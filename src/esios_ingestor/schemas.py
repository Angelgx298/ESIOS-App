from datetime import datetime
from typing import List
from pydantic import BaseModel

class EsiosValue(BaseModel):
    value: float
    datetime: str
    datetime_utc: datetime
    tz_time: str
    geo_id: int
    geo_name: str

class EsiosIndicator(BaseModel):
    name: str
    short_name: str
    id: int
    composited: bool
    step_type: str
    disaggregated: bool
    values: List[EsiosValue]

class EsiosResponse(BaseModel):
    indicator: EsiosIndicator
