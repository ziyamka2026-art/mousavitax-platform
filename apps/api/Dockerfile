FROM python:3.12-slim

# Keep the repository's expected directory layout inside the image.
# apps/api/app/main.py and cases.py resolve ROOT via Path(__file__).parents[3].
WORKDIR /repo/apps/api

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY apps/api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY packages /repo/packages
COPY domains /repo/domains
COPY apps/api/app ./app

ENV PYTHONPATH=/repo/packages/shared:/repo/packages/ai-gateway/app
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
