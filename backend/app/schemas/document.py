from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    filename: str
    content_type: str
    size_bytes: int
    status: str
    progress: int
    error_message: str | None
    attempt_count: int
    celery_task_id: str | None
    extracted_data: dict[str, Any] | None
    reviewed_data: dict[str, Any] | None
    finalized: bool
    finalized_at: datetime | None
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int
    page: int
    page_size: int


class ReviewUpdateRequest(BaseModel):
    reviewed_data: dict[str, Any]


class ProgressEvent(BaseModel):
    document_id: str
    event: str
    progress: int
    status: str
    message: str | None = None
    timestamp: datetime


class ExportFormat(BaseModel):
    format: Literal["json", "csv"]
