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

### CLI Interface

* `esios ingest` – Trigger ETL pipeline
* `esios prices` – Display prices in formatted table

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
```

**Prices Response:**

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

| Metric                     | Value     | Notes                   |
| -------------------------- | --------- | ----------------------- |
| Initial ingestion (7 days) | ~14.8s    | 179 hourly records      |
| Full year ingestion        | ~60s      | ~8,760 records          |
| API latency (mean)         | 15ms      | <10 concurrent requests |
| API latency (p99)          | 100ms     | Worst 1%                |
| Throughput                 | 641 req/s | Async PostgreSQL        |
| Database size (1 year)     | ~3.5 MB   | With indexes            |
| Cold startup               | 7.5s      | Docker + PostgreSQL     |
| Container build            | ~6s       | Layer caching enabled   |

### Load Testing Results

```bash
ab -n 1000 -c 10 http://localhost:8000/prices?limit=10
```

* Requests/sec: 641.48
* Mean latency: 15.6 ms
* p95: 16 ms
* p99: 100 ms
* Failed requests: 0

### Scalability

* Idempotent upserts prevent duplicate data
* Automatic gap detection enables incremental ingestion
* Async DB operations handle concurrent API traffic

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
