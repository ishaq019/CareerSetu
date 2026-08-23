// Resume builder: generates ATS-aligned summary, skills, bullets and keywords
// from the resume + target job. Requires a configured LLM (503 otherwise).
import { useState } from "react";
import { Copy, FileText, Sparkles } from "lucide-react";
import { api, ApiError } from "../lib/api";
import type { ResumeDraft } from "../lib/types";
import { Page } from "../components/AppLayout";
import { UploadTextarea } from "../components/UploadTextarea";
import { Badge, Button, Card, EmptyState, ErrorAlert } from "../components/ui";

function copy(text: string) {
  navigator.clipboard?.writeText(text).catch(() => {});
}

function BulletCard({ title, items }: { title: string; items: string[] }) {
  if (!items?.length) return null;
  return (
    <Card>
      <div className="card-h">
        <h3>{title}</h3>
        <Button variant="quiet" onClick={() => copy(items.join("\n"))}>
          <Copy size={14} /> Copy
        </Button>
      </div>
      <ul className="pill-list good" style={{ gap: 10 }}>
        {items.map((b, i) => (
          <li key={i}>{b}</li>
        ))}
      </ul>
    </Card>
  );
}

export default function Resume() {
  const [resume, setResume] = useState("");
  const [jd, setJd] = useState("");
  const [draft, setDraft] = useState<ResumeDraft | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function generate() {
    if (resume.trim().length < 30 || jd.trim().length < 30) {
      setError("Add at least 30 characters to both fields.");
      return;
    }
    setError("");
    setBusy(true);
    try {
      const res = await api.post<ResumeDraft>("/documents/resume/create", {
        resume_text: resume,
        job_description: jd,
      });
      setDraft(res);
    } catch (e) {
      setError(
        e instanceof ApiError && e.status === 503
          ? "Resume generation needs a configured LLM provider (set LLM_API_KEY on the backend)."
          : e instanceof Error
            ? e.message
            : "Generation failed.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <Page title="Resume builder" subtitle="ATS-aligned content grounded in your real experience — no invented facts.">
      <div className="stack" style={{ gap: 18 }}>
        <Card>
          <div className="two-col">
            <UploadTextarea label="Current resume" hint="paste or upload" value={resume} onChange={setResume} placeholder="Paste your current resume…" />
            <UploadTextarea label="Target job description" value={jd} onChange={setJd} placeholder="Paste the target job description…" />
          </div>
          {error && (
            <div style={{ marginTop: 14 }}>
              <ErrorAlert>{error}</ErrorAlert>
            </div>
          )}
          <div style={{ marginTop: 16 }}>
            <Button loading={busy} onClick={generate}>
              <Sparkles size={15} /> Generate resume content
            </Button>
          </div>
        </Card>

        {!draft ? (
          <Card>
            <EmptyState icon={<FileText size={22} />} title="Your generated content will appear here">
              Provide a resume and a target job, then generate.
            </EmptyState>
          </Card>
        ) : (
          <>
            <Card>
              <div className="card-h">
                <h3>Professional summary</h3>
                <Button variant="quiet" onClick={() => copy(draft.summary)}>
                  <Copy size={14} /> Copy
                </Button>
              </div>
              <p style={{ fontSize: 14.5, color: "var(--text-soft)" }}>{draft.summary}</p>
            </Card>

            {draft.skills?.length > 0 && (
              <Card>
                <h3 style={{ marginBottom: 12 }}>Skills</h3>
                <div className="tag-wrap">
                  {draft.skills.map((s) => (
                    <Badge key={s}>{s}</Badge>
                  ))}
                </div>
              </Card>
            )}

            <BulletCard title="Experience bullets" items={draft.experience_bullets} />
            <BulletCard title="Project bullets" items={draft.project_bullets} />

            {draft.ats_keywords?.length > 0 && (
              <Card>
                <h3 style={{ marginBottom: 12 }}>ATS keywords</h3>
                <div className="tag-wrap">
                  {draft.ats_keywords.map((k) => (
                    <Badge tone="warn" key={k}>
                      {k}
                    </Badge>
                  ))}
                </div>
              </Card>
            )}
          </>
        )}
      </div>
    </Page>
  );
}
