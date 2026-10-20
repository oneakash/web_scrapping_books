FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/app/data

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libxml2-dev \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scrapyd.conf /etc/scrapyd/scrapyd.conf
COPY . /app

RUN chmod +x /app/entrypoint.sh

EXPOSE 6800

ENTRYPOINT ["/app/entrypoint.sh"]