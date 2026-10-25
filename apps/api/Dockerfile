FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY apps/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY packages /packages
COPY services /services
COPY domains /domains
COPY scripts /scripts
COPY data /data
COPY apps/api/app ./app
ENV PYTHONPATH=/packages/shared:/packages/ai-gateway/app:/packages:/services \
    VECTOR_DB_PATH=/data/iran_tax_vectors.json \
    EMBEDDING_PROVIDER=fallback
EXPOSE 8000
CMD ["sh", "-c", "python /scripts/seed_knowledge.py || true; uvicorn app.main:app --host 0.0.0.0 --port 8000"]
