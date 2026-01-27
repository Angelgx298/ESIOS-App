# Use an official lightweight Python image
FROM python:3.12-slim

# Install system dependencies (curl is often needed for healthchecks/debugging)
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Install uv (The modern package manager)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files first (Better caching)
COPY pyproject.toml uv.lock ./

# Install dependencies into the system python (no venv needed inside docker)
RUN uv sync --frozen --system

# Copy the source code
COPY src ./src

# Set PYTHONPATH so python can find our modules
ENV PYTHONPATH=/app/src

# Default command (can be overridden by docker-compose)
CMD ["uvicorn", "esios_ingestor.web.app:app", "--host", "0.0.0.0", "--port", "8000"]
