import csv
import io
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Document, DocumentStatus
from app.utils.redis_progress import ProgressPublisher
from app.workers.tasks import process_document_task

settings = get_settings()
publisher = ProgressPublisher()


def _safe_filename(name: str) -> str:
    return "".join(c for c in name if c.isalnum() or c in {"-", "_", "."}) or "document"


def _upload_root() -> Path:
    root = Path(settings.upload_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root


def create_document_from_upload(db: Session, upload: UploadFile) -> Document:
    data = upload.file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large: {upload.filename}",
        )

    original_name = upload.filename or "document"
    filename = f"{uuid.uuid4()}_{_safe_filename(original_name)}"
    file_path = _upload_root() / filename
    with open(file_path, "wb") as f:
        f.write(data)

    doc = Document(
        filename=original_name,
        content_type=upload.content_type or "application/octet-stream",
        size_bytes=len(data),
        file_path=str(file_path),
        status=DocumentStatus.QUEUED,
        progress=0,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    task = process_document_task.delay(str(doc.id))
    doc.celery_task_id = task.id
    db.commit()
    db.refresh(doc)
    publisher.publish(
        {
            "document_id": str(doc.id),
            "event": "job_queued",
            "progress": 0,
            "status": DocumentStatus.QUEUED.value,
            "message": "Document queued for background processing",
        }
    )
    return doc


def list_documents(
    db: Session,
    page: int,
    page_size: int,
    search: str | None,
    status_filter: str | None,
    sort_by: str,
    sort_order: str,
):
    query = select(Document)
    count_query = select(func.count()).select_from(Document)

    if search:
        pattern = f"%{search}%"
        query = query.where(Document.filename.ilike(pattern))
        count_query = count_query.where(Document.filename.ilike(pattern))

    if status_filter:
        try:
            parsed_status = DocumentStatus(status_filter)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid status filter") from exc
        query = query.where(Document.status == parsed_status)
        count_query = count_query.where(Document.status == parsed_status)

    sort_field_map = {
        "created_at": Document.created_at,
        "updated_at": Document.updated_at,
        "filename": Document.filename,
        "status": Document.status,
        "progress": Document.progress,
    }
    sort_field = sort_field_map.get(sort_by, Document.created_at)
    ordering = desc(sort_field) if sort_order == "desc" else asc(sort_field)

    query = query.order_by(ordering).offset((page - 1) * page_size).limit(page_size)
    items = db.execute(query).scalars().all()
    total = db.execute(count_query).scalar_one()
    return items, total


def get_document_or_404(db: Session, document_id: str) -> Document:
    doc = db.get(Document, uuid.UUID(document_id))
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


def retry_document(db: Session, document_id: str) -> Document:
    doc = get_document_or_404(db, document_id)
    if doc.status != DocumentStatus.FAILED:
        raise HTTPException(status_code=400, detail="Only failed jobs can be retried")

    doc.status = DocumentStatus.QUEUED
    doc.progress = 0
    doc.error_message = None
    db.commit()

    task = process_document_task.delay(str(doc.id))
    doc.celery_task_id = task.id
    db.commit()
    db.refresh(doc)
    publisher.publish(
        {
            "document_id": str(doc.id),
            "event": "job_queued",
            "progress": 0,
            "status": DocumentStatus.QUEUED.value,
            "message": "Retry queued for background processing",
        }
    )
    return doc


def update_review_data(db: Session, document_id: str, reviewed_data: dict) -> Document:
    doc = get_document_or_404(db, document_id)
    if doc.finalized:
        raise HTTPException(status_code=400, detail="Finalized document cannot be edited")

    doc.reviewed_data = reviewed_data
    db.commit()
    db.refresh(doc)
    return doc


def finalize_document(db: Session, document_id: str) -> Document:
    doc = get_document_or_404(db, document_id)
    if doc.status != DocumentStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Only completed documents can be finalized")

    doc.finalized = True
    doc.finalized_at = datetime.now(timezone.utc)
    if doc.reviewed_data is None:
        doc.reviewed_data = doc.extracted_data
    db.commit()
    db.refresh(doc)
    return doc


def export_documents(db: Session, export_format: str, finalized_only: bool):
    query = select(Document)
    if finalized_only:
        query = query.where(Document.finalized.is_(True))

    docs = db.execute(query.order_by(desc(Document.updated_at))).scalars().all()

    if export_format == "json":
        payload = [
            {
                "id": str(doc.id),
                "filename": doc.filename,
                "status": doc.status.value,
                "finalized": doc.finalized,
                "created_at": doc.created_at.isoformat(),
                "updated_at": doc.updated_at.isoformat(),
                "result": doc.reviewed_data or doc.extracted_data,
            }
            for doc in docs
        ]
        return "application/json", json.dumps(payload, indent=2)

    if export_format == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "id",
                "filename",
                "status",
                "finalized",
                "created_at",
                "updated_at",
                "result_json",
            ],
        )
        writer.writeheader()
        for doc in docs:
            writer.writerow(
                {
                    "id": str(doc.id),
                    "filename": doc.filename,
                    "status": doc.status.value,
                    "finalized": doc.finalized,
                    "created_at": doc.created_at.isoformat(),
                    "updated_at": doc.updated_at.isoformat(),
                    "result_json": json.dumps(doc.reviewed_data or doc.extracted_data or {}),
                }
            )
        return "text/csv", output.getvalue()

    raise HTTPException(status_code=400, detail="Unsupported export format")
