#!/bin/sh
set -e

CELERY_CMD="celery -A app.workers.celery_app.celery_app worker -l info --uid=nobody --gid=nogroup --without-gossip --without-mingle --without-heartbeat"

cleanup() {
    echo "Received shutdown signal, stopping Celery worker..."
    if [ -n "$CELERY_PID" ]; then
        kill -TERM "$CELERY_PID" 2>/dev/null || true
        wait "$CELERY_PID" 2>/dev/null || true
    fi
    exit 0
}

trap cleanup TERM INT

while true; do
    echo "Starting Celery worker..."
    $CELERY_CMD &
    CELERY_PID=$!
    wait "$CELERY_PID"
    EXIT_CODE=$?
    echo "Celery worker exited with code $EXIT_CODE. Restarting in 2 seconds..."
    sleep 2
done
