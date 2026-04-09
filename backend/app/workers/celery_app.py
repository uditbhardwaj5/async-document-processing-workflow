import ssl

from celery import Celery

from app.core.config import get_settings

settings = get_settings()


def _redis_ssl_options(url: str) -> dict | None:
    if not url.startswith("rediss://"):
        return None
    req = (settings.redis_ssl_cert_reqs or "required").strip().lower()
    mapping = {
        "required": ssl.CERT_REQUIRED,
        "optional": ssl.CERT_OPTIONAL,
        "none": ssl.CERT_NONE,
    }
    return {"ssl_cert_reqs": mapping.get(req, ssl.CERT_REQUIRED)}

celery_app = Celery(
    "document_processing",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=settings.celery_broker_connection_retry_on_startup,
)

broker_ssl = _redis_ssl_options(settings.celery_broker_url)
if broker_ssl:
    celery_app.conf.broker_use_ssl = broker_ssl

backend_ssl = _redis_ssl_options(settings.celery_result_backend)
if backend_ssl:
    celery_app.conf.redis_backend_use_ssl = backend_ssl

celery_app.autodiscover_tasks(["app.workers"])
