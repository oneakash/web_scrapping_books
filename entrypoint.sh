#!/bin/sh
set -e

mkdir -p /app/data /var/lib/scrapyd/eggs /var/lib/scrapyd/logs /var/lib/scrapyd/dbs
echo "Starting Scrapyd server..."
scrapyd --pidfile=/tmp/scrapyd.pid &
SCRAPYD_PID=$!

echo "Waiting for Scrapyd to accept connections..."
until python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:6800/daemonstatus.json')" >/dev/null 2>&1; do
    sleep 1
done
echo "Scrapyd is up. Deploying books_scraper project..."
scrapyd-deploy local -p books_scraper || {
    echo "Deployment failed! Printing logs..."
    cat /var/lib/scrapyd/logs/* 2>/dev/null || true
    exit 1
}
echo "Scrapyd is ready and project is deployed."
wait $SCRAPYD_PID