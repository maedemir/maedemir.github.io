FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/data \
    DATABASE_URL=sqlite:////data/litdb.sqlite3

RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY spatial_omics_litdb ./spatial_omics_litdb
RUN pip install --no-cache-dir .

VOLUME ["/data"]
EXPOSE 8000

CMD ["python", "-m", "spatial_omics_litdb.cli", "serve", "--host", "0.0.0.0", "--port", "8000"]
