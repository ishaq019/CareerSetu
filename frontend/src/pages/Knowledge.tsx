// Admin-only knowledge ingestion: drag-and-drop interview-prep PDFs/DOCX into
// the trusted CareerSetu knowledge base. These documents ground the Career chat
// and interview-prep question generation for all users. Restricted to admins
// (KNOWLEDGE_ADMIN_EMAILS on the backend); the route is also guarded client-side.
import { useCallback, useRef, useState } from "react";
import { CheckCircle2, ShieldCheck, UploadCloud } from "lucide-react";
import { api, ApiError } from "../lib/api";
import type { KnowledgeIngestResult } from "../lib/types";
import { Page } from "../components/AppLayout";
import { Button, Card, ErrorAlert, Spinner } from "../components/ui";

type Done = KnowledgeIngestResult & { at: string };

export default function Knowledge() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [dragging, setDragging] = useState(false);
  const [log, setLog] = useState<Done[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  const ingest = useCallback(async (file?: File) => {
    if (!file) return;
    setError("");
    const name = file.name.toLowerCase();
    if (!name.endsWith(".pdf") && !name.endsWith(".docx")) {
      setError("Only PDF and DOCX files can be ingested.");
      return;
    }
    setBusy(true);
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await api.post<KnowledgeIngestResult>("/documents/knowledge/ingest", form);
      setLog((l) => [{ ...res, at: new Date().toLocaleTimeString() }, ...l]);
    } catch (e) {
      setError(
        e instanceof ApiError && e.status === 403
          ? "Your account is not a CareerSetu administrator."
          : e instanceof ApiError && e.status === 503
            ? "Knowledge store is not configured (check Chroma settings on the backend)."
            : e instanceof Error
              ? e.message
              : "Ingestion failed.",
      );
    } finally {
      setBusy(false);
    }
  }, []);

  return (
    <Page
      title="Knowledge base"
      subtitle="Upload trusted interview-prep material. It grounds Career chat and interview questions for every user."
    >
      <div className="stack" style={{ gap: 18 }}>
        <Card>
          <div
            className={`dropzone${dragging ? " dragging" : ""}`}
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragging(false);
              ingest(e.dataTransfer.files?.[0]);
            }}
            onClick={() => inputRef.current?.click()}
            role="button"
            tabIndex={0}
            style={{
              border: "1.5px dashed var(--line)",
              borderRadius: 14,
              padding: "36px 20px",
              textAlign: "center",
              cursor: busy ? "wait" : "pointer",
              background: dragging ? "rgba(255,255,255,.04)" : "transparent",
            }}
          >
            <div style={{ display: "flex", justifyContent: "center", marginBottom: 10, color: "var(--a1)" }}>
              {busy ? <Spinner /> : <UploadCloud size={30} />}
            </div>
            <strong style={{ display: "block", fontSize: 15 }}>
              {busy ? "Indexing…" : "Drop a PDF or DOCX here, or click to browse"}
            </strong>
            <p className="muted" style={{ marginTop: 6, fontSize: 13 }}>
              Documents are chunked and indexed into the trusted knowledge base.
            </p>
            <input
              ref={inputRef}
              type="file"
              accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              disabled={busy}
              style={{ display: "none" }}
              onChange={(e) => ingest(e.target.files?.[0])}
            />
          </div>
          {error && (
            <div style={{ marginTop: 14 }}>
              <ErrorAlert>{error}</ErrorAlert>
            </div>
          )}
        </Card>

        <Card>
          <div className="card-h">
            <h3>
              <ShieldCheck size={16} style={{ verticalAlign: "-2px", marginRight: 6, color: "var(--good)" }} />
              Ingested this session
            </h3>
          </div>
          {log.length === 0 ? (
            <p className="muted" style={{ fontSize: 13 }}>No documents ingested yet.</p>
          ) : (
            <ul className="pill-list good" style={{ gap: 10 }}>
              {log.map((d, i) => (
                <li key={i}>
                  <CheckCircle2 size={14} style={{ verticalAlign: "-2px", marginRight: 6 }} />
                  <b>{d.filename}</b> — {d.chunks_indexed} chunk{d.chunks_indexed === 1 ? "" : "s"} indexed
                  <span className="muted" style={{ marginLeft: 8, fontSize: 12 }}>{d.at}</span>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </Page>
  );
}
