export type DocumentStatus = "queued" | "processing" | "completed" | "failed";

export interface DocumentItem {
  id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  status: DocumentStatus;
  progress: number;
  error_message: string | null;
  attempt_count: number;
  celery_task_id: string | null;
  extracted_data: Record<string, unknown> | null;
  reviewed_data: Record<string, unknown> | null;
  finalized: boolean;
  finalized_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentListResponse {
  items: DocumentItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface ProgressEvent {
  document_id: string;
  event: string;
  progress: number;
  status: DocumentStatus;
  message?: string;
  timestamp: string;
}
