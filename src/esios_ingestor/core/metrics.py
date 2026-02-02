"""Metrics module for ESIOS Ingestor.

Provides Prometheus metrics for observability.
"""

import time

from fastapi import FastAPI
from prometheus_client import Counter, Gauge
from prometheus_fastapi_instrumentator import Instrumentator

ESIOS_LAST_SUCCESS_TIMESTAMP = Gauge(
    "esios_last_success_timestamp", "Unix timestamp of last successful data ingestion", ["zone_id"]
)

INGESTION_RECORDS_TOTAL = Counter(
    "esios_ingestion_records_total", "Total records ingested by status", ["status"]
)


def setup_instrumentator(app: FastAPI) -> Instrumentator:
    """Configure prometheus-fastapi-instrumentator for HTTP metrics.

    Provides automatic instrumentation for:
    - http_request_duration_seconds (p50, p95, p99 histograms)
    - http_requests_total
    - http_requests_in_progress
    """
    instrumentator = Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        should_respect_env_var=False,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/metrics"],
        inprogress_name="http_requests_inprogress",
        inprogress_labels=True,
    )

    instrumentator.instrument(app).expose(app)
    return instrumentator


def update_last_success_timestamp(zone_id: str = "8741") -> None:
    """Update the last successful ingestion timestamp.

    Args:
        zone_id: Geographic zone identifier (default: 8741 for Spain)
    """
    ESIOS_LAST_SUCCESS_TIMESTAMP.labels(zone_id=zone_id).set(time.time())
