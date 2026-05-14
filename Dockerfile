FROM python:3.12-slim-bookworm

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pyproject.toml .
COPY src ./src
COPY tests ./tests

RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uvicorn", "taskboard.main:app", "--host", "0.0.0.0", "--port", "8000"]
