# ESIOS Electricity Price Ingestor

[![CI/CD Pipeline](https://github.com/Angelgx298/ESIOS-App/actions/workflows/ci.yml/badge.svg)](https://github.com/Angelgx298/ESIOS-App/actions)

ETL pipeline and REST API for ingesting electricity prices from the Spanish electricity market operator (ESIOS). Built with Python 3.12, FastAPI, and PostgreSQL.

## Architecture

[![Architecture Diagram](./docs/architecture.svg)](./docs/architecture.svg)

## Core Features

### ETL Pipeline

* Idempotent data ingestion with automatic gap detection
* Exponential backoff retry logic for network failures
* Strict schema validation with Pydantic V2

### REST API

* `/prices` – Query electricity prices with pagination
* `/prices/stats` – Aggregated analytics (avg, max, min, peak hours)
* `/health` – Service health check (verifies database connectivity, returns 503 if DB is down)
* `/ready` – Readiness probe for orchestrators (Kubernetes, Docker Swarm)

### Production Readiness

* **Graceful shutdown** – Proper resource cleanup on SIGTERM with 30s timeout for in-flight requests
* **Connection pooling** – SQLAlchemy pool configuration (size=10, max_overflow=20) for high concurrency
* **Health checks** – Real database connectivity verification with appropriate HTTP status codes
* **Structured logging** – Application lifecycle events (startup/shutdown) for observability
* **Prometheus metrics** – HTTP latency tracking (p50/p95/p99) via /metrics endpoint

### CLI Interface

* `esios ingest` – Trigger ETL pipeline
* `esios prices` – Display prices in formatted table
* `esios server` – Start FastAPI web server

## Technical Stack

| Component        | Technology         | Rationale                                     |
| ---------------- | ------------------ | --------------------------------------------- |
| Language         | Python 3.12        | Type hints, performance improvements          |
| Package Manager  | uv                 | 10–100x faster than pip, deterministic builds |
| Web Framework    | FastAPI            | Async-native, auto-generated OpenAPI docs     |
| Database         | PostgreSQL 16      | ACID compliance, advanced indexing            |
| ORM              | SQLAlchemy (async) | Non-blocking I/O for concurrent requests      |
| Validation       | Pydantic V2        | Runtime type checking, data contracts         |
| Testing          | pytest + httpx     | Async test support, integration tests         |
| Observability    | Prometheus         | Metrics collection, p99 latency tracking      |
| Containerization | Docker Compose     | Reproducible development environment          |
| CI/CD            | GitHub Actions     | Automated linting and testing                 |

## Quick Start

### Prerequisites

* Docker and Docker Compose
* [ESIOS API Key](https://api.esios.ree.es/)

### Setup

```bash
git clone https://github.com/Angelgx298/ESIOS-App.git
cd ESIOS-App

cp .env.example .env
# Edit .env and set ESIOS_API_KEY=your_token_here

make up
make ingest
make prices

open http://localhost:8000/docs
```

## API Examples

```bash
curl "http://localhost:8000/prices?limit=24"
curl "http://localhost:8000/prices/stats?days=7"
curl "http://localhost:8000/health"
curl "http://localhost:8000/ready"
curl "http://localhost:8000/metrics"
```

**Prices Response:**

```json
[
  {
    "timestamp": "2026-01-27T00:00:00Z",
    "price": 58.85,
    "zone_id": 8741
  },
  {
    "timestamp": "2026-01-26T23:00:00Z",
    "price": 71.82,
    "zone_id": 8741
  }
]
```

**Statistics Response (`/prices/stats`):**

```json
{
  "period": "last_7_days",
  "avg_price": 124.38,
  "max_price": 272.07,
  "min_price": 54.84,
  "peak_hour": 19,
  "cheapest_hour": 3
}
```

**Health Check Response (healthy):**

```json
{
  "status": "healthy",
  "database": "connected",
  "service": "esios-ingestor"
}
```

**Health Check Response (unhealthy - HTTP 503):**

```json
{
  "detail": {
    "status": "unhealthy",
    "database": "disconnected"
  }
}
```

## Performance Benchmarks

| Metric                     | Value     | Notes                               |
| -------------------------- | --------- | ----------------------------------- |
| Initial ingestion (7 days) | ~4-5s     | ~170 hourly records (API dependent) |
| API latency (mean)         | ~20ms     | <10 concurrent requests             |
| API latency (p95)          | ~25ms     | 95th percentile                     |
| API latency (p99)          | ~50-200ms | Worst 1% (spikes during DB writes)  |
| Throughput                 | ~500 req/s| Async PostgreSQL                    |
| Database size              | ~10 MB    | Per year of data with indexes       |
| Cold startup               | ~10s      | Docker + PostgreSQL + migrations    |
| Container build            | ~15-30s   | From scratch (layer cached: ~5s)    |

### Load Testing Results

Tested with Apache Bench (ab) on local Docker environment:

```bash
ab -n 1000 -c 10 http://localhost:8000/prices?limit=10
```

**Results:**
* Requests/sec: ~513
* Mean latency: ~19.5 ms
* Failed requests: 0
* 90% of requests served within ~25ms

*Note: Performance varies based on hardware, network latency to ESIOS API, and database state.*

### Scalability

* Idempotent upserts prevent duplicate data
* Automatic gap detection enables incremental ingestion
* Async DB operations handle concurrent API traffic

## Observability

### Prometheus Metrics

The application exposes metrics at `/metrics` endpoint for monitoring:

**HTTP Metrics (automatic):**
* `http_request_duration_seconds` – Request latency with p50, p95, p99 histograms
* `http_requests_total` – Total requests by method, status, and endpoint
* `http_requests_inprogress` – Current requests being processed

**Note:** HTTP metrics appear after the first request is made to any endpoint (lazy initialization).

**Access Prometheus UI:**
```bash
open http://localhost:9090
```

**Example Queries:**
```promql
# p99 latency
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))

# Total requests per endpoint
sum by (handler) (rate(http_requests_total[5m]))
```

## Troubleshooting

### API returns 401/403

```bash
cat .env | grep ESIOS_API_KEY
curl -H "x-api-key: YOUR_KEY" \
  "https://api.esios.ree.es/indicators/1001"
```

### Database connection failed

```bash
make status
docker logs esios-app-db-1
```

### Ingestion returns no data

```bash
make logs
make ingest
```

Common causes:

* Date range in the future
* Network timeouts
* API rate limiting

## Development

```bash
make test
make lint
make format
```

## Project Structure

```text
esios-app/
├── src/esios_ingestor/
│   ├── core/
│   ├── ingestion/
│   ├── models/
│   ├── web/
│   ├── schemas.py
│   └── main.py
├── tests/
├── docker-compose.yml
└── Makefile
```

## Design Decisions

* **Idempotent upserts** via `ON CONFLICT DO NOTHING`
* **Async SQLAlchemy** for higher concurrency
* **Tenacity retries** with exponential backoff
* **UTC timestamps** to avoid timezone bugs
* **Graceful shutdown** – 30s timeout allows in-flight requests to complete, proper connection pool cleanup
* **Connection pooling** – Configured pool size and overflow limits prevent resource exhaustion under load
* **Separate /health and /ready endpoints** – Health for liveness (is app running?), ready for readiness (can it serve traffic?)

## Makefile Commands

```bash
make help
make up
make down
make clean
make reload
make status
make ingest
make prices
make test
make lint
make format
make logs
make db-migrate
make db-clean
make db-stats
make test-api
make benchmark
```

## Database Schema

```sql
CREATE TABLE electricity_prices (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    price FLOAT NOT NULL,
    zone_id INTEGER NOT NULL,
    CONSTRAINT uq_price_timestamp_zone UNIQUE (timestamp, zone_id)
);

CREATE INDEX idx_timestamp ON electricity_prices(timestamp DESC);
CREATE INDEX idx_zone_timestamp ON electricity_prices(zone_id, timestamp DESC);
CREATE INDEX idx_timestamp_brin ON electricity_prices USING BRIN(timestamp);
```
