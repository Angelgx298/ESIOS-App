# ESIOS Electricity Price Ingestor

[![CI/CD Pipeline](https://github.com/Angelgx298/ESIOS-App/actions/workflows/ci.yml/badge.svg)](https://github.com/TU_USUARIO/ESIOS-App/actions)

ETL pipeline and REST API for ingesting electricity prices from the Spanish electricity market operator (ESIOS). Built with Python 3.12, FastAPI, and PostgreSQL.

## Architecture
[![CI/CD Pipeline](./docs/architecture.svg)](./docs/architecture.svg)


## Core Features

### ETL Pipeline

- Idempotent data ingestion with automatic gap detection  
- Exponential backoff retry logic for network failures  
- Strict schema validation with Pydantic V2  

### REST API

- `/prices` – Query electricity prices with pagination  
- `/prices/stats` – Aggregated analytics (avg, max, min, peak hours)  
- `/health` – Service health check  

### CLI Interface

- `esios ingest` – Trigger ETL pipeline  
- `esios prices` – Display prices in formatted table  

## Technical Stack

| Component        | Technology            | Rationale |
|------------------|-----------------------|-----------|
| Language         | Python 3.12           | Type hints, performance improvements |
| Package Manager  | uv                    | 10-100x faster than pip, deterministic builds |
| Web Framework    | FastAPI               | Async-native, auto-generated OpenAPI docs |
| Database         | PostgreSQL 16         | ACID compliance, advanced indexing |
| ORM              | SQLAlchemy (async)    | Non-blocking I/O for concurrent requests |
| Validation       | Pydantic V2           | Runtime type checking, data contracts |
| Testing          | pytest + httpx        | Async test support, integration tests |
| Containerization | Docker Compose        | Reproducible development environment |
| CI/CD            | GitHub Actions        | Automated linting and testing |

## Quick Start

### Prerequisites

- Docker and Docker Compose  
- ESIOS API Token (register here)  

### Setup

```bash
# Clone repository
git clone https://github.com/Angelgx298/ESIOS-App.git
cd ESIOS-App

# Configure environment
cp .env.example .env
# Edit .env and set ESIOS_API_KEY=your_token_here

# Start infrastructure
make up

# Run initial data ingestion (fetches last 7 days)
make ingest

# Query data via CLI
make prices

# Access API documentation
open http://localhost:8000/docs
```

## API Examples

```bash
# Get latest 24 prices
curl "http://localhost:8000/prices?limit=24"

# Get statistics for last 7 days
curl "http://localhost:8000/prices/stats?days=7"
```

**Response:**

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

## Development

### Running Tests

```bash
make test
```

### Code Quality

```bash
# Lint code
make lint

# Auto-format
make format
```

## Project Structure

```text
esios-app/
├── src/esios_ingestor/
│   ├── core/              # Configuration, database, logging
│   ├── ingestion/         # ETL client and service logic
│   ├── models/            # SQLAlchemy ORM models
│   ├── web/               # FastAPI routes and application
│   ├── schemas.py         # Pydantic data contracts
│   └── main.py            # CLI entrypoint (Typer)
├── tests/                 # Integration tests
├── docker-compose.yml     # Infrastructure definition
└── Makefile               # Development commands
```

## Design Decisions

### Why Idempotent Upsert?

The ETL uses PostgreSQL's `ON CONFLICT DO NOTHING` to ensure that re-running ingestion never duplicates data. This allows safe retries and backfills without complex deduplication logic.

### Why Async SQLAlchemy?

The API serves multiple concurrent requests. Async I/O prevents blocking the event loop during database queries, improving throughput under load.

### Why Tenacity for Retries?

Network failures are common with external APIs. Exponential backoff with jitter prevents thundering herd problems and respects rate limits.

### Why UTC Timestamps?

All timestamps are stored in UTC to avoid timezone conversion bugs. The ESIOS API returns local Spanish time (CET/CEST), which is normalized during validation.

## Makefile Commands

```bash
make up        # Start all services (DB + API)
make down      # Stop all services
make ingest    # Run ETL pipeline
make prices    # Show prices in terminal
make test      # Run test suite
make lint      # Check code quality
make format    # Auto-format code
make logs      # View application logs
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
```