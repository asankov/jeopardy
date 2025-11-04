FROM python:3.13-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock README.md ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY jeopardy/ ./jeopardy/
COPY dataset.csv ./

ENV PYTHONUNBUFFERED=1

CMD ["uv", "run", "python", "-m", "jeopardy.ingester.ingest_data"]
