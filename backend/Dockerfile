FROM python:3.11-slim

# System deps for Pillow, lxml, python-pptx
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc libxml2-dev libxslt-dev libjpeg-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Data dirs created at runtime via volume mounts
ENV SLIDEVAULT_THUMBNAILS_DIR=/data/thumbnails
ENV SLIDEVAULT_CACHE_DIR=/data/cache
ENV SLIDEVAULT_PRESENTATIONS_DIR=/data/presentations

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
