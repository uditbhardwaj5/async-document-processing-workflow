"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { getExportUrl, listDocuments, retryDocument, uploadDocuments } from "../lib/api";
import { DocumentItem, DocumentStatus } from "../lib/types";
import { StatusBadge } from "../components/StatusBadge";

export default function DashboardPage() {
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [total, setTotal] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<string>("");
  const [sortBy, setSortBy] = useState("created_at");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  async function refresh() {
    try {
      const data = await listDocuments({ page: 1, page_size: 50, search, status, sort_by: sortBy, sort_order: sortOrder });
      setDocs(data.items);
      setTotal(data.total);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load documents");
    }
  }

  useEffect(() => {
    refresh();
    const timer = setInterval(refresh, 3000);
    return () => clearInterval(timer);
  }, [search, status, sortBy, sortOrder]);

  async function onUpload(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const files = formData.getAll("files") as File[];
    if (files.length === 0) return;

    try {
      setUploading(true);
      await uploadDocuments(files);
      (e.target as HTMLFormElement).reset();
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  async function onRetry(id: string) {
    try {
      await retryDocument(id);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Retry failed");
    }
  }

  const stats = useMemo(() => {
    const counts: Record<DocumentStatus, number> = { queued: 0, processing: 0, completed: 0, failed: 0 };
    docs.forEach((d) => counts[d.status] += 1);
    return counts;
  }, [docs]);

  return (
    <main className="container grid" style={{ gap: 18 }}>
      <section className="card" style={{ animation: "fadein .5s ease" }}>
        <h1>async-document-processing-workflow</h1>
        <p style={{ color: "var(--muted)" }}>
          Upload documents, watch background processing progress, review extracted output, finalize records, and export.
        </p>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <a href={getExportUrl("json")}>Export Finalized JSON</a>
          <a href={getExportUrl("csv")}>Export Finalized CSV</a>
        </div>
      </section>

      <section className="grid grid-2">
        <div className="card">
          <h2>Upload</h2>
          <form onSubmit={onUpload}>
            <input type="file" name="files" multiple />
            <div style={{ marginTop: 10 }}>
              <button className="primary" disabled={uploading}>{uploading ? "Uploading..." : "Upload & Queue"}</button>
            </div>
          </form>
        </div>

        <div className="card">
          <h2>Overview</h2>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <span>Total: {total}</span>
            <span>Queued: {stats.queued}</span>
            <span>Processing: {stats.processing}</span>
            <span>Completed: {stats.completed}</span>
            <span>Failed: {stats.failed}</span>
          </div>
        </div>
      </section>

      <section className="card">
        <h2>Documents</h2>
        <div className="grid" style={{ gridTemplateColumns: "2fr 1fr 1fr 1fr", gap: 10, marginBottom: 12 }}>
          <input placeholder="Search filename" value={search} onChange={(e) => setSearch(e.target.value)} />
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">All statuses</option>
            <option value="queued">Queued</option>
            <option value="processing">Processing</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>
          <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
            <option value="created_at">Created</option>
            <option value="updated_at">Updated</option>
            <option value="filename">Filename</option>
            <option value="status">Status</option>
            <option value="progress">Progress</option>
          </select>
          <select value={sortOrder} onChange={(e) => setSortOrder(e.target.value as "asc" | "desc")}>
            <option value="desc">Desc</option>
            <option value="asc">Asc</option>
          </select>
        </div>

        <table>
          <thead>
            <tr>
              <th>Filename</th>
              <th>Status</th>
              <th>Progress</th>
              <th>Attempts</th>
              <th>Finalized</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {docs.map((doc) => (
              <tr key={doc.id}>
                <td>{doc.filename}</td>
                <td><StatusBadge status={doc.status} /></td>
                <td>
                  <div className="progress-track">
                    <div className="progress-bar" style={{ width: `${doc.progress}%` }} />
                  </div>
                  <small>{doc.progress}%</small>
                </td>
                <td>{doc.attempt_count}</td>
                <td>{doc.finalized ? "Yes" : "No"}</td>
                <td style={{ display: "flex", gap: 8 }}>
                  <Link href={`/documents/${doc.id}`}>Open</Link>
                  {doc.status === "failed" && (
                    <button onClick={() => onRetry(doc.id)}>Retry</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {error && <p style={{ color: "var(--danger)" }}>{error}</p>}
      </section>
    </main>
  );
}
