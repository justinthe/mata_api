FROM python:3.12-slim

WORKDIR /app

# libexpat1: rasterio's manylinux wheel (bundled GDAL) dynamically links it,
# not present in the slim base image. postgresql-client: psql, used by
# entrypoint.sh to apply the migration on hosts with no local DB tooling.
RUN apt-get update && apt-get install -y --no-install-recommends libexpat1 postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared ./shared
COPY backend/app ./app
COPY backend/tests ./tests
COPY ingest.py .
COPY ingest ./ingest
COPY migrations ./migrations
COPY data ./data
COPY backend/entrypoint.sh .
RUN chmod +x entrypoint.sh

CMD ["./entrypoint.sh"]
