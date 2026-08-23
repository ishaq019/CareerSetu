// Cover letter generator: grounded in the resume + job description, with
// company/role/tone controls. Requires a configured LLM (503 otherwise).
import { useMemo, useState } from "react";
import { Copy, PenLine } from "lucide-react";
import { api, ApiError } from "../lib/api";
import type { CoverLetterDraft } from "../lib/types";
import { Page } from "../components/AppLayout";
import { UploadTextarea } from "../components/UploadTextarea";
import { Button, Card, EmptyState, ErrorAlert, Field, Input } from "../components/ui";

const TONES = ["professional", "enthusiastic", "concise", "warm"];

export default function CoverLetter() {
  const [resume, setResume] = useState("");
  const [jd, setJd] = useState("");
  const [company, setCompany] = useState("");
  const [role, setRole] = useState("");
  const [tone, setTone] = useState("professional");
  const [draft, setDraft] = useState<CoverLetterDraft | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const fullText = useMemo(() => {
    if (!draft) return "";
    return [draft.greeting, draft.opening, ...draft.body, draft.closing, draft.signature]
      .filter(Boolean)
      .join("\n\n");
  }, [draft]);

  async function generate() {
    if (resume.trim().length < 30 || jd.trim().length < 30) {
      setError("Add at least 30 characters to both the resume and job description.");
      return;
    }
    setError("");
    setBusy(true);
    try {
      const res = await api.post<CoverLetterDraft>("/documents/cover-letter", {
        resume_text: resume,
        job_description: jd,
        company,
        role,
        tone,
      });
      setDraft(res);
    } catch (e) {
      setError(
        e instanceof ApiError && e.status === 503
          ? "Cover-letter generation needs a configured LLM provider (set LLM_API_KEY on the backend)."
          : e instanceof Error
            ? e.message
            : "Generation failed.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <Page title="Cover letter" subtitle="A specific, honest letter drawn only from your resume and the role.">
      <div className="stack" style={{ gap: 18 }}>
        <Card>
          <div className="two-col">
            <UploadTextarea label="Your resume" hint="paste or upload" value={resume} onChange={setResume} placeholder="Paste your resume…" />
            <UploadTextarea label="Job description" value={jd} onChange={setJd} placeholder="Paste the job description…" />
          </div>
          <div className="two-col" style={{ marginTop: 14 }}>
            <Field label="Company" hint="optional">
              <Input value={company} onChange={(e) => setCompany(e.target.value)} placeholder="e.g. Acme Corp" />
            </Field>
            <Field label="Role" hint="optional">
              <Input value={role} onChange={(e) => setRole(e.target.value)} placeholder="e.g. Senior Backend Engineer" />
            </Field>
          </div>
          <div style={{ marginTop: 14, maxWidth: 260 }}>
            <Field label="Tone">
              <select className="input" value={tone} onChange={(e) => setTone(e.target.value)}>
                {TONES.map((t) => (
                  <option key={t} value={t}>
                    {t[0].toUpperCase() + t.slice(1)}
                  </option>
                ))}
              </select>
            </Field>
          </div>
          {error && (
            <div style={{ marginTop: 14 }}>
              <ErrorAlert>{error}</ErrorAlert>
            </div>
          )}
          <div style={{ marginTop: 16 }}>
            <Button loading={busy} onClick={generate}>
              <PenLine size={15} /> Generate cover letter
            </Button>
          </div>
        </Card>

        {!draft ? (
          <Card>
            <EmptyState icon={<PenLine size={22} />} title="Your cover letter will appear here">
              Fill in the resume and job description, then generate.
            </EmptyState>
          </Card>
        ) : (
          <Card>
            <div className="card-h">
              <h3>Draft cover letter</h3>
              <Button variant="quiet" onClick={() => navigator.clipboard?.writeText(fullText)}>
                <Copy size={14} /> Copy all
              </Button>
            </div>
            <div className="stack" style={{ gap: 14, fontSize: 14.5, color: "var(--text-soft)", lineHeight: 1.7 }}>
              <p>{draft.greeting}</p>
              <p>{draft.opening}</p>
              {draft.body.map((b, i) => (
                <p key={i}>{b}</p>
              ))}
              <p>{draft.closing}</p>
              <p style={{ whiteSpace: "pre-line" }}>{draft.signature}</p>
            </div>
          </Card>
        )}
      </div>
    </Page>
  );
}
