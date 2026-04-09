import json
from datetime import datetime, timezone

import redis

from app.core.config import get_settings

settings = get_settings()


class ProgressPublisher:
    def __init__(self) -> None:
        self.client = redis.Redis.from_url(settings.redis_url, decode_responses=True)

    def publish(self, payload: dict) -> None:
        payload["timestamp"] = datetime.now(timezone.utc).isoformat()
        self.client.publish(settings.redis_progress_channel, json.dumps(payload))


class ProgressSubscriber:
    def __init__(self) -> None:
        self.client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        self.pubsub: redis.client.PubSub | None = None

    def listen(self):
        self.pubsub = self.client.pubsub()
        self.pubsub.subscribe(settings.redis_progress_channel)
        try:
            for message in self.pubsub.listen():
                if message["type"] != "message":
                    continue
                yield message["data"]
        finally:
            self.close()

    def close(self) -> None:
        if self.pubsub is None:
            return
        try:
            self.pubsub.unsubscribe(settings.redis_progress_channel)
        except Exception:
            pass
        self.pubsub.close()
        self.pubsub = None
