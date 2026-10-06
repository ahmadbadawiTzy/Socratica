FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml ./
# Install only main dependencies (not dev) for production image
RUN pip install --no-cache-dir ".[dev]" 2>/dev/null || pip install --no-cache-dir \
    fastapi uvicorn[standard] pydantic pydantic-settings sqlalchemy alembic asyncpg \
    python-dotenv httpx python-multipart

# Copy application source
COPY . .

EXPOSE 8000

CMD ["uvicorn", "asgi:app", "--host", "0.0.0.0", "--port", "8000"]
