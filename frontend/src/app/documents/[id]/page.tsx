"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { finalizeDocument, getDocument, getProgressStreamUrl, retryDocument, updateReview } from "../../../lib/api";
import { DocumentItem, ProgressEvent } from "../../../lib/types";
import { StatusBadge } from "../../../components/StatusBadge";

export default function DocumentDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;

  const [doc, setDoc] = useState<DocumentItem | null>(null);
  const [reviewText, setReviewText] = useState("{}");
  const [events, setEvents] = useState<ProgressEvent[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    try {
      const loaded = await getDocument(id);
      setDoc(loaded);
      setReviewText(JSON.stringify(loaded.reviewed_data ?? loaded.extracted_data ?? {}, null, 2));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch document");
    }
  }

  useEffect(() => {
    refresh();
    const timer = setInterval(refresh, 4000);
    return () => clearInterval(timer);
  }, [id]);

  useEffect(() => {
    const source = new EventSource(getProgressStreamUrl(id));
    source.onmessage = (msg) => {
      try {
        const event = JSON.parse(msg.data) as ProgressEvent;
        setEvents((prev) => [event, ...prev].slice(0, 25));
      } catch {
        // no-op
      }
    };
    source.onerror = () => {
      source.close();
    };
    return () => source.close();
  }, [id]);

  async function onSaveReview() {
    try {
      const parsed = JSON.parse(reviewText) as Record<string, unknown>;
      const updated = await updateReview(id, parsed);
      setDoc(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save review data");
    }
  }

  async function onFinalize() {
    try {
      const updated = await finalizeDocument(id);
      setDoc(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to finalize");
    }
  }

  async function onRetry() {
    try {
      const updated = await retryDocument(id);
      setDoc(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to retry");
    }
  }

  const parsedPreview = useMemo(() => {
    try {
      return JSON.parse(reviewText);
    } catch {
      return null;
    }
  }, [reviewText]);

  if (!doc) {
    return <main className="container"><p>Loading document...</p></main>;
  }

  return (
    <main className="container grid" style={{ gap: 14 }}>
      <Link href="/">Back to dashboard</Link>
      <section className="card">
        <h1>{doc.filename}</h1>
        <p style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <StatusBadge status={doc.status} />
          <span>{doc.progress}%</span>
          <span>Attempts: {doc.attempt_count}</span>
          <span>Finalized: {doc.finalized ? "Yes" : "No"}</span>
        </p>
        <div className="progress-track">
          <div className="progress-bar" style={{ width: `${doc.progress}%` }} />
        </div>
        {doc.error_message && <p style={{ color: "var(--danger)" }}>{doc.error_message}</p>}
        {doc.status === "failed" && <button onClick={onRetry}>Retry failed job</button>}
      </section>

      <section className="grid grid-2">
        <div className="card">
          <h2>Review & Edit Output</h2>
          <textarea rows={18} value={reviewText} onChange={(e) => setReviewText(e.target.value)} />
          <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
            <button onClick={onSaveReview}>Save Review</button>
            <button className="primary" onClick={onFinalize} disabled={doc.status !== "completed" || doc.finalized}>
              Finalize
            </button>
          </div>
          {!parsedPreview && <p style={{ color: "var(--danger)" }}>Review JSON is invalid.</p>}
        </div>

        <div className="card">
          <h2>Live Progress Events</h2>
          <div style={{ maxHeight: 420, overflow: "auto" }}>
            {events.length === 0 && <p style={{ color: "var(--muted)" }}>No events received yet.</p>}
            {events.map((event, idx) => (
              <div key={`${event.timestamp}-${idx}`} style={{ borderBottom: "1px solid var(--line)", padding: "8px 0" }}>
                <strong>{event.event}</strong>
                <p style={{ margin: 0, color: "var(--muted)" }}>{event.timestamp}</p>
                <p style={{ margin: 0 }}>Progress: {event.progress}% ({event.status})</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {error && <p style={{ color: "var(--danger)" }}>{error}</p>}
    </main>
  );
}
