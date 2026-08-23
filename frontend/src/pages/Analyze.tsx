// Authenticated analyzer: same engine as the guest tool, plus a "save to
// history" toggle so the report is persisted to the account.
import { useState } from "react";
import { ArrowRight, Check } from "lucide-react";
import { api, ApiError } from "../lib/api";
import type { Analysis } from "../lib/types";
import { Page } from "../components/AppLayout";
import { AnalysisView } from "../components/AnalysisView";
import { UploadTextarea } from "../components/UploadTextarea";
import { Button, Card, ErrorAlert } from "../components/ui";

export default function Analyze() {
  const [resume, setResume] = useState("");
  const [jd, setJd] = useState("");
  const [save, setSave] = useState(true);
  const [result, setResult] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);

  async function run() {
    if (resume.trim().length < 30 || jd.trim().length < 30) {
      setError("Add at least 30 characters to both fields.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const res = await api.post<Analysis>("/analysis", {
        resume_text: resume,
        job_description: jd,
        save,
      });
      setResult(res);
      setSaved(save && res.id != null);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Analysis failed.");
    } finally {
      setLoading(false);
    }
  }

  function reset() {
    setResult(null);
    setSaved(false);
  }

  return (
    <Page
      title="Job-fit analysis"
      subtitle="Score a resume against a role, then save the report to your history."
      actions={result ? <Button variant="ghost" onClick={reset}>New analysis</Button> : undefined}
    >
      {!result ? (
        <Card>
          <div className="two-col">
            <UploadTextarea
              label="Your resume"
              hint="paste or upload"
              value={resume}
              onChange={setResume}
              placeholder="Paste your resume content here…"
            />
            <UploadTextarea
              label="Job description"
              hint="the full posting works best"
              value={jd}
              onChange={setJd}
              placeholder="Paste the job description here…"
            />
          </div>

          <label style={{ display: "flex", alignItems: "center", gap: 10, marginTop: 16, fontSize: 14, cursor: "pointer" }}>
            <input type="checkbox" checked={save} onChange={(e) => setSave(e.target.checked)} />
            Save this analysis to my history
          </label>

          {error && (
            <div style={{ marginTop: 14 }}>
              <ErrorAlert>{error}</ErrorAlert>
            </div>
          )}
          <div style={{ marginTop: 16 }}>
            <Button size="lg" loading={loading} onClick={run}>
              {loading ? "Analyzing…" : "Analyze job fit"} {!loading && <ArrowRight size={16} />}
            </Button>
          </div>
        </Card>
      ) : (
        <div className="stack">
          {saved && (
            <div className="alert alert-info">
              <Check size={16} /> Saved to your history.
            </div>
          )}
          <AnalysisView a={result} />
        </div>
      )}
    </Page>
  );
}
