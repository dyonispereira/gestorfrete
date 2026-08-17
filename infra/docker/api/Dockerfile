FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1

WORKDIR /app

RUN pip install --no-cache-dir poetry==1.8.3

COPY apps/api/pyproject.toml apps/api/poetry.lock* ./
RUN poetry install --no-root --only main

COPY apps/api/ .

EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000"]
