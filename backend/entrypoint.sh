#!/bin/sh
set -e

# Trap SIGTERM and SIGINT to allow graceful shutdown
_term() {
    echo "Caught signal, shutting down Celery worker..."
    if [ -n "$CELERY_PID" ]; then
        kill -TERM "$CELERY_PID" 2>/dev/null
        wait "$CELERY_PID"
    fi
    exit 0
}

trap _term TERM INT

echo "Starting Celery worker..."

while true; do
    celery -A app.workers.celery_app.celery_app worker \
        -l info \
        --uid=nobody \
        --gid=nogroup \
        --without-gossip \
        --without-mingle \
        --without-heartbeat &
    CELERY_PID=$!

    wait "$CELERY_PID"
    EXIT_CODE=$?

    echo "Celery worker exited with code $EXIT_CODE. Restarting in 2 seconds..."
    sleep 2
done
