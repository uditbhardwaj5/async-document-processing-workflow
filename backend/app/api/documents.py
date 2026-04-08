import json
from typing import Generator

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.document import DocumentListResponse, DocumentResponse, ProgressEvent, ReviewUpdateRequest
from app.services.document_service import (
    create_document_from_upload,
    export_documents,
    finalize_document,
    get_document_or_404,
    list_documents,
    retry_document,
    update_review_data,
)
from app.utils.redis_progress import ProgressSubscriber

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=list[DocumentResponse])
def upload_documents(files: list[UploadFile] = File(...), db: Session = Depends(get_db)):
    created = [create_document_from_upload(db, upload) for upload in files]
    return created


@router.get("", response_model=DocumentListResponse)
def get_documents(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
    status: str | None = Query(default=None),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    items, total = list_documents(db, page, page_size, search, status, sort_by, sort_order)
    return DocumentListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: str, db: Session = Depends(get_db)):
    return get_document_or_404(db, document_id)


@router.post("/{document_id}/retry", response_model=DocumentResponse)
def retry_failed_document(document_id: str, db: Session = Depends(get_db)):
    return retry_document(db, document_id)


@router.patch("/{document_id}/review", response_model=DocumentResponse)
def update_document_review(document_id: str, payload: ReviewUpdateRequest, db: Session = Depends(get_db)):
    return update_review_data(db, document_id, payload.reviewed_data)


@router.post("/{document_id}/finalize", response_model=DocumentResponse)
def finalize_document_review(document_id: str, db: Session = Depends(get_db)):
    return finalize_document(db, document_id)


@router.get("/export/download")
def export_data(
    format: str = Query(default="json", pattern="^(json|csv)$"),
    finalized_only: bool = Query(default=True),
    db: Session = Depends(get_db),
):
    mime_type, payload = export_documents(db, format, finalized_only)
    extension = "json" if format == "json" else "csv"
    return Response(
        content=payload,
        media_type=mime_type,
        headers={"Content-Disposition": f"attachment; filename=documents_export.{extension}"},
    )


@router.get("/{document_id}/progress/stream")
def stream_document_progress(document_id: str):
    subscriber = ProgressSubscriber()

    def event_stream() -> Generator[str, None, None]:
        for raw in subscriber.listen():
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if payload.get("document_id") != document_id:
                continue
            event = ProgressEvent(**payload)
            yield f"data: {event.model_dump_json()}\\n\\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
