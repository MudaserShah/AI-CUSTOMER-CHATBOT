# syntax=docker/dockerfile:1

FROM python:3.13-slim AS base

# Prevent Python from writing .pyc files / buffering stdout — makes
# container logs show up immediately instead of being buffered.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System packages needed to build a couple of Python deps (this project
# pulls in langchain_huggingface -> sentence-transformers -> torch, and
# tokenizers/tiktoken, some of which need a C compiler on certain
# platforms even though most ship prebuilt wheels). Kept minimal and
# removed from the final layer isn't possible in a single-stage build,
# which is why this still ends up as a fairly large image — see
# DEPLOYMENT.md for notes on trimming it further if that matters to you.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies first, separately from app code, so Docker's
# layer cache skips this (slow, since it includes torch) whenever only
# your source files change rather than requirements.txt.
COPY requirements.txt .
RUN pip install -r requirements.txt

# Now copy the actual application.
COPY src/ ./src/
COPY migrations/ ./migrations/
COPY alembic.ini .

# Run as a non-root user — a container escape or dependency RCE
# shouldn't hand the attacker root inside the container.
RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p /app/uploads /app/markdown_files \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# No --reload here (that's dev-only and lives behind main.py's
# `if __name__ == "__main__"` block, which this CMD bypasses entirely
# by invoking uvicorn directly).
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
