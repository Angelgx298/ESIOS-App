.PHONY: help up down ingest prices logs test lint format format-check install
.PHONY: status reload clean db-clean db-stats db-migrate test-api benchmark

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies using uv
	uv sync

up: ## Start infrastructure (DB + API)
	docker-compose up -d --build

down: ## Stop infrastructure
	docker-compose down

clean: ## Remove containers and volumes
	docker-compose down -v
	docker system prune -f

reload: down clean up ## Clean restart with fresh database

status: ## Show running containers
	@echo "Container status:"
	@docker ps --filter "name=esios" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

ingest: ## Run ETL pipeline manually
	docker-compose run --rm api esios ingest

prices: ## Show latest prices from CLI
	docker-compose run --rm api esios prices

logs: ## View logs
	docker-compose logs -f

test: ## Run test suite
	docker-compose run --rm api uv run pytest tests/ -v

lint: ## Run code linter
	docker-compose run --rm api uv run ruff check src/ tests/

format: ## Auto-format code
	docker-compose run --rm api uv run ruff format src/ tests/

format-check: ## Check code formatting
	docker-compose run --rm api uv run ruff format --check src/ tests/

db-migrate: ## Run database migrations
	docker exec -i esios-app-db-1 psql -U esios -d esios_db < migrations/001_add_indexes.sql

db-clean: ## Delete all data (keeps schema)
	@echo "Cleaning database..."
	@docker exec -it esios-app-db-1 psql -U esios -d esios_db -c "TRUNCATE TABLE electricity_prices RESTART IDENTITY CASCADE;"
	@echo "Database cleaned"

db-stats: ## Show database statistics
	@echo "Database statistics:"
	@docker exec -it esios-app-db-1 psql -U esios -d esios_db -c "\
		SELECT \
			COUNT(*) as total_records, \
			MIN(timestamp) as earliest_data, \
			MAX(timestamp) as latest_data, \
			COUNT(DISTINCT zone_id) as zones, \
			pg_size_pretty(pg_total_relation_size('electricity_prices')) as table_size \
		FROM electricity_prices;"

test-api: ## Test API health and endpoints
	@echo "Testing API health..."
	@curl -sf http://localhost:8000/health > /dev/null && echo "Health check: OK" || (echo "Health check: FAILED" && exit 1)
	@echo "Testing /prices endpoint..."
	@curl -sf "http://localhost:8000/prices?limit=5" > /dev/null && echo "Prices endpoint: OK" || (echo "Prices endpoint: FAILED" && exit 1)
	@echo "All API tests passed"

benchmark: ## Run performance benchmarks
	@echo "Running ingestion benchmark..."
	@time docker-compose run --rm api esios ingest --start-date 2026-01-20 --end-date 2026-01-27
	@echo "\nRunning API load test (requires apache-bench)..."
	@ab -n 1000 -c 10 -q http://localhost:8000/prices?limit=10 | grep -E "Requests per second|Time per request|Transfer rate"
