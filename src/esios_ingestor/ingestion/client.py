import httpx
import logging
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from esios_ingestor.core.config import settings
from esios_ingestor.schemas import EsiosResponse


logger = logging.getLogger(__name__)


class EsiosClient:
    BASE_URL = "https://api.esios.ree.es"
    INDICATOR_ID = "1001"

    def __init__(self):
        self.headers = {
            "x-api-key": settings.ESIOS_API_KEY,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    @retry(
        stop=stop_after_attempt(3), 
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError))
    )
    async def fetch_prices(self, start_date: datetime, end_date: datetime) -> EsiosResponse | None:
        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "geo_ids[]": [8741]
        }
        
        timeout = httpx.Timeout(10.0, connect=5.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            logger.info(f"Fetching ESIOS data from {start_date} to {end_date}")
            
            try:
                response = await client.get(
                    f"{self.BASE_URL}/indicators/{self.INDICATOR_ID}",
                    headers=self.headers,
                    params=params
                )
                response.raise_for_status()
                
                data = response.json()
                validated_data = EsiosResponse(**data)
                
                if not validated_data.indicator.values:
                    logger.warning("ESIOS returned 200 OK but 'values' list is empty.")
                    return None
                    
                return validated_data

            except httpx.HTTPStatusError as e:
                logger.error(f"ESIOS API Error {e.response.status_code}: {e.response.text}")
                raise e
            except Exception as e:
                logger.error(f"Failed to fetch data: {str(e)}")
                raise e
