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

    def listen(self):
        pubsub = self.client.pubsub()
        pubsub.subscribe(settings.redis_progress_channel)
        for message in pubsub.listen():
            if message["type"] != "message":
                continue
            yield message["data"]
