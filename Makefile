.PHONY: up down ingest logs test install

install: ## Install dependencies using uv
	uv sync

up: ## Start infrastructure (DB + API)
	docker-compose up -d --build

down: ## Stop infrastructure
	docker-compose down

ingest: ## Run ETL pipeline manually
	docker-compose run --rm api esios ingest

prices: ## Show latest prices from CLI
	docker-compose run --rm api esios prices

logs: ## View logs
	docker-compose logs -f

test: ## Run the test suite
	docker-compose run --rm api uv run pytest tests/ -v