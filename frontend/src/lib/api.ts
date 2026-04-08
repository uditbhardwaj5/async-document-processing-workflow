import { DocumentItem, DocumentListResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api";

export async function uploadDocuments(files: File[]): Promise<DocumentItem[]> {
  const body = new FormData();
  files.forEach((file) => body.append("files", file));

  const res = await fetch(`${API_BASE}/documents/upload`, { method: "POST", body });
  if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
  return res.json();
}

export async function listDocuments(params: {
  page?: number;
  page_size?: number;
  search?: string;
  status?: string;
  sort_by?: string;
  sort_order?: "asc" | "desc";
}): Promise<DocumentListResponse> {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") query.set(key, String(value));
  });

  const res = await fetch(`${API_BASE}/documents?${query.toString()}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`List fetch failed: ${res.status}`);
  return res.json();
}

export async function getDocument(id: string): Promise<DocumentItem> {
  const res = await fetch(`${API_BASE}/documents/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Document fetch failed: ${res.status}`);
  return res.json();
}

export async function retryDocument(id: string): Promise<DocumentItem> {
  const res = await fetch(`${API_BASE}/documents/${id}/retry`, { method: "POST" });
  if (!res.ok) throw new Error(`Retry failed: ${res.status}`);
  return res.json();
}

export async function updateReview(id: string, reviewedData: Record<string, unknown>): Promise<DocumentItem> {
  const res = await fetch(`${API_BASE}/documents/${id}/review`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reviewed_data: reviewedData }),
  });
  if (!res.ok) throw new Error(`Review update failed: ${res.status}`);
  return res.json();
}

export async function finalizeDocument(id: string): Promise<DocumentItem> {
  const res = await fetch(`${API_BASE}/documents/${id}/finalize`, { method: "POST" });
  if (!res.ok) throw new Error(`Finalize failed: ${res.status}`);
  return res.json();
}

export function getProgressStreamUrl(id: string): string {
  const base = API_BASE.replace(/\/$/, "");
  return `${base}/documents/${id}/progress/stream`;
}

export function getExportUrl(format: "json" | "csv"): string {
  return `${API_BASE}/documents/export/download?format=${format}&finalized_only=true`;
}
