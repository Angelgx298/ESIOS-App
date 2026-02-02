import time

import pytest

from esios_ingestor.core.metrics import (
    ESIOS_LAST_SUCCESS_TIMESTAMP,
    INGESTION_RECORDS_TOTAL,
    update_last_success_timestamp,
)


def test_update_last_success_timestamp():
    """Test that timestamp gauge is updated correctly."""
    update_last_success_timestamp(zone_id="8741")

    metric = ESIOS_LAST_SUCCESS_TIMESTAMP.labels(zone_id="8741")
    value = metric._value.get()

    assert value > time.time() - 5
    assert value <= time.time()


def test_update_last_success_timestamp_different_zones():
    """Test timestamp tracking for different zones."""
    update_last_success_timestamp(zone_id="8741")
    update_last_success_timestamp(zone_id="8742")

    value_1 = ESIOS_LAST_SUCCESS_TIMESTAMP.labels(zone_id="8741")._value.get()
    value_2 = ESIOS_LAST_SUCCESS_TIMESTAMP.labels(zone_id="8742")._value.get()

    assert value_1 > 0
    assert value_2 > 0


def test_ingestion_records_counter():
    """Test ingestion counter increments correctly."""
    # Store initial values
    initial_success = INGESTION_RECORDS_TOTAL.labels(status="success")._value.get()
    initial_failed = INGESTION_RECORDS_TOTAL.labels(status="failed")._value.get()

    INGESTION_RECORDS_TOTAL.labels(status="success").inc(5)
    INGESTION_RECORDS_TOTAL.labels(status="failed").inc(2)

    # Check delta
    final_success = INGESTION_RECORDS_TOTAL.labels(status="success")._value.get()
    final_failed = INGESTION_RECORDS_TOTAL.labels(status="failed")._value.get()

    assert final_success - initial_success == 5
    assert final_failed - initial_failed == 2


@pytest.mark.asyncio
async def test_metrics_endpoint_available(client):
    """Test that /metrics endpoint is available."""
    # Make a request first to generate some metrics
    await client.get("/health")

    response = await client.get("/metrics")

    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]

    content = response.text
    # Should contain Prometheus format metrics
    assert "# HELP" in content or "# TYPE" in content or "http" in content
