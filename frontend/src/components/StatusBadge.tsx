import { DocumentStatus } from "../lib/types";

export function StatusBadge({ status }: { status: DocumentStatus }) {
  return <span className={`badge ${status}`}>{status}</span>;
}
