# Use an official lightweight Python image
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy dependency files AND README
COPY pyproject.toml uv.lock README.md ./

# Install dependencies
RUN uv sync --frozen

# IMPORTANT: Add the virtual environment to the PATH
# This ensures that 'python' and 'uvicorn' point to the versions inside the venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy the source code
COPY src ./src

# Set PYTHONPATH so python can find our modules
ENV PYTHONPATH=/app/src

# Default command
CMD ["uvicorn", "esios_ingestor.web.app:app", "--host", "0.0.0.0", "--port", "8000"]
