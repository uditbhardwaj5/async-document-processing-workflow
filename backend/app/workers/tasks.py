import json
import uuid
from pathlib import Path
from time import sleep

from app.db.session import SessionLocal
from app.models import Document, DocumentStatus
from app.utils.redis_progress import ProgressPublisher
from app.workers.celery_app import celery_app

publisher = ProgressPublisher()


def _publish(document_id: str, event: str, progress: int, status: str, message: str | None = None):
    publisher.publish(
        {
            "document_id": document_id,
            "event": event,
            "progress": progress,
            "status": status,
            "message": message,
        }
    )


@celery_app.task(name="app.workers.tasks.process_document")
def process_document_task(document_id: str):
    db = SessionLocal()
    try:
        doc = db.get(Document, uuid.UUID(document_id))
        if not doc:
            return

        doc.status = DocumentStatus.PROCESSING
        doc.progress = 5
        doc.error_message = None
        doc.attempt_count += 1
        db.commit()
        _publish(document_id, "job_started", 5, DocumentStatus.PROCESSING.value)

        _publish(document_id, "document_parsing_started", 20, DocumentStatus.PROCESSING.value)
        doc.progress = 20
        db.commit()
        sleep(1)

        file_text = doc.source_text or ""
        if not file_text:
            file_path = Path(doc.file_path)
            if file_path.exists():
                file_text = file_path.read_text(encoding="utf-8", errors="ignore")[:2500]

        _publish(document_id, "document_parsing_completed", 45, DocumentStatus.PROCESSING.value)
        doc.progress = 45
        db.commit()
        sleep(1)

        _publish(document_id, "field_extraction_started", 65, DocumentStatus.PROCESSING.value)
        doc.progress = 65
        db.commit()
        sleep(1)

        tokens = [word.strip(".,!?;:\\n\\r\\t ").lower() for word in file_text.split()]
        tokens = [tok for tok in tokens if len(tok) > 3]
        unique_keywords = sorted(set(tokens))[:10]
        extracted = {
            "title": doc.filename.rsplit(".", 1)[0],
            "category": "general-document",
            "summary": file_text[:280] if file_text else "No parseable text content found.",
            "extracted_keywords": unique_keywords,
            "status": "ready_for_review",
            "metadata": {
                "filename": doc.filename,
                "file_type": doc.content_type,
                "size_bytes": doc.size_bytes,
            },
        }

        _publish(document_id, "field_extraction_completed", 85, DocumentStatus.PROCESSING.value)
        doc.progress = 85
        db.commit()
        sleep(1)

        doc.extracted_data = extracted
        doc.status = DocumentStatus.COMPLETED
        doc.progress = 100
        db.commit()

        _publish(document_id, "final_result_stored", 95, DocumentStatus.PROCESSING.value)
        _publish(document_id, "job_completed", 100, DocumentStatus.COMPLETED.value)
    except Exception as exc:
        doc = db.get(Document, uuid.UUID(document_id))
        if doc:
            doc.status = DocumentStatus.FAILED
            doc.error_message = str(exc)
            db.commit()
        _publish(document_id, "job_failed", 100, DocumentStatus.FAILED.value, str(exc))
        raise
    finally:
        db.close()
