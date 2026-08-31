// Dashboard: a quick snapshot (saved analyses, best score, interview attempts)
// plus a grid of tool shortcuts.
import { useEffect, useState, type KeyboardEvent } from "react";
import { useNavigate } from "react-router-dom";
import {
  BrainCircuit,
  FileText,
  Gauge,
  MessageSquare,
  PenLine,
  Map as MapIcon,
} from "lucide-react";
import { api, ApiError } from "../lib/api";
import { useAuth } from "../lib/auth";
import type { HistoryItem, InterviewAttempt } from "../lib/types";
import { Page } from "../components/AppLayout";
import { Button, Card, ErrorAlert } from "../components/ui";

const TOOLS = [
  { to: "/app/analyze", icon: Gauge, title: "Job-fit analysis", body: "Score a resume against a role and save the report." },
  { to: "/app/interview", icon: BrainCircuit, title: "Interview prep", body: "Practice adaptive questions with graded feedback." },
  { to: "/app/chat", icon: MessageSquare, title: "Career chat", body: "Ask questions answered from a cited knowledge base." },
  { to: "/app/resume", icon: FileText, title: "Resume builder", body: "Generate ATS-aligned bullets and keywords." },
  { to: "/app/cover-letter", icon: PenLine, title: "Cover letter", body: "Draft a tailored letter grounded in your resume." },
  { to: "/app/roadmap", icon: MapIcon, title: "Learning roadmap", body: "Turn skill gaps into a saved study plan." },
];

export default function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [attempts, setAttempts] = useState<InterviewAttempt[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    let active = true;
    const fail = (fallback: string) => (e: unknown) => {
      if (active) setError(e instanceof ApiError ? e.message : fallback);
    };
    setError(null);
    api
      .get<HistoryItem[]>("/analysis/history")
      .then((items) => active && setHistory(items || []))
      .catch(fail("Could not load your saved analyses."));
    api
      .get<InterviewAttempt[]>("/interview/history")
      .then((items) => active && setAttempts(items || []))
      .catch(fail("Could not load interview attempts."));
    return () => {
      active = false;
    };
  }, [reload]);

  const best = history.reduce((m, h) => Math.max(m, h.match_score), 0);
  const name = user?.email.split("@")[0] ?? "there";

  function activateCard(e: KeyboardEvent<HTMLDivElement>, to: string) {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      navigate(to);
    }
  }

  return (
    <Page
      title={`Welcome back, ${name}`}
      subtitle="Your career workspace at a glance."
      actions={
        error ? (
          <Button variant="ghost" onClick={() => setReload((n) => n + 1)}>
            Retry
          </Button>
        ) : undefined
      }
    >
      {error && (
        <div style={{ marginBottom: 16 }}>
          <ErrorAlert>{error}</ErrorAlert>
        </div>
      )}
      <div className="tiles" style={{ marginBottom: 24 }}>
        <Card className="tile">
          <span className="k">{history.length}</span>
          <span className="l">Saved analyses</span>
        </Card>
        <Card className="tile">
          <span className="k" style={{ color: best >= 80 ? "var(--good)" : best >= 60 ? "var(--warn)" : "var(--text)" }}>
            {best || "—"}
          </span>
          <span className="l">Best match score</span>
        </Card>
        <Card className="tile">
          <span className="k">{attempts.length}</span>
          <span className="l">Interview attempts</span>
        </Card>
      </div>

      <div className="tool-grid">
        {TOOLS.map((t) => (
          <Card
            key={t.to}
            className="tool"
            role="button"
            tabIndex={0}
            onClick={() => navigate(t.to)}
            onKeyDown={(e) => activateCard(e, t.to)}
          >
            <div className="ic">
              <t.icon size={19} />
            </div>
            <h3>{t.title}</h3>
            <p>{t.body}</p>
          </Card>
        ))}
      </div>
    </Page>
  );
}
