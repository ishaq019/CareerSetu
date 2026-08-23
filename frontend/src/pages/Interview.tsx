// Interview prep: generate a question (LLM or offline fallback), submit an
// answer, and get graded feedback. Difficulty adapts from the evaluation.
import { useState } from "react";
import { RefreshCw, Send } from "lucide-react";
import { api, ApiError } from "../lib/api";
import type { Evaluation, InterviewQuestion } from "../lib/types";
import { Page } from "../components/AppLayout";
import { Badge, Button, Card, ErrorAlert, Field, Input, ScoreGauge, Textarea } from "../components/ui";

const DIFFS = ["basic", "intermediate", "advanced"];

export default function Interview() {
  const [role, setRole] = useState("Software Engineer");
  const [topic, setTopic] = useState("general");
  const [difficulty, setDifficulty] = useState("intermediate");
  const [q, setQ] = useState<InterviewQuestion | null>(null);
  const [answer, setAnswer] = useState("");
  const [evalResult, setEvalResult] = useState<Evaluation | null>(null);
  const [loadingQ, setLoadingQ] = useState(false);
  const [grading, setGrading] = useState(false);
  const [error, setError] = useState("");

  async function getQuestion() {
    setError("");
    setEvalResult(null);
    setAnswer("");
    setLoadingQ(true);
    try {
      const res = await api.post<InterviewQuestion>("/interview/question", {
        role,
        topic,
        difficulty,
      });
      setQ(res);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not fetch a question.");
    } finally {
      setLoadingQ(false);
    }
  }

  async function grade() {
    if (!q || answer.trim().length < 5) {
      setError("Write a fuller answer before submitting.");
      return;
    }
    setError("");
    setGrading(true);
    try {
      const res = await api.post<Evaluation>("/interview/evaluate", {
        question: q.question,
        answer,
      });
      setEvalResult(res);
      if (res.next_difficulty && DIFFS.includes(res.next_difficulty)) setDifficulty(res.next_difficulty);
    } catch (e) {
      setError(
        e instanceof ApiError && e.status === 503
          ? "AI evaluation needs a configured LLM provider (set LLM_API_KEY on the backend)."
          : e instanceof Error
            ? e.message
            : "Evaluation failed.",
      );
    } finally {
      setGrading(false);
    }
  }

  return (
    <Page title="Interview prep" subtitle="Practice adaptive questions with evidence-based feedback.">
      <div className="stack" style={{ gap: 18 }}>
        <Card>
          <div className="two-col">
            <Field label="Target role">
              <Input value={role} onChange={(e) => setRole(e.target.value)} placeholder="e.g. Backend Engineer" />
            </Field>
            <Field label="Topic">
              <Input value={topic} onChange={(e) => setTopic(e.target.value)} placeholder="e.g. system design" />
            </Field>
          </div>
          <div style={{ display: "flex", gap: 14, alignItems: "flex-end", marginTop: 14, flexWrap: "wrap" }}>
            <Field label="Difficulty">
              <select className="input" value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
                {DIFFS.map((d) => (
                  <option key={d} value={d}>
                    {d[0].toUpperCase() + d.slice(1)}
                  </option>
                ))}
              </select>
            </Field>
            <Button loading={loadingQ} onClick={getQuestion}>
              <RefreshCw size={15} /> {q ? "New question" : "Get a question"}
            </Button>
          </div>
        </Card>

        {error && <ErrorAlert>{error}</ErrorAlert>}

        {q && (
          <Card>
            <div className="q-card">
              <div className="chips">
                <Badge>{q.topic}</Badge>
                <Badge tone={q.difficulty === "advanced" ? "bad" : q.difficulty === "basic" ? "good" : "warn"}>
                  {q.difficulty}
                </Badge>
              </div>
              <p className="q">{q.question}</p>
            </div>
            <div style={{ marginTop: 16 }}>
              <Field label="Your answer" hint="be specific and use concrete examples">
                <Textarea
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  placeholder="Structure your answer with situation, action, and measurable result…"
                  rows={7}
                />
              </Field>
            </div>
            <div style={{ marginTop: 14 }}>
              <Button loading={grading} onClick={grade}>
                <Send size={15} /> Submit for feedback
              </Button>
            </div>
          </Card>
        )}

        {evalResult && (
          <Card>
            <div className="report-top">
              <ScoreGauge value={Math.round(evalResult.score * 10)} label="SCORE" />
              <div className="stack" style={{ gap: 14 }}>
                <div className="chips">
                  <Badge tone={evalResult.evidence_quality === "strong" ? "good" : evalResult.evidence_quality === "weak" ? "bad" : "warn"}>
                    {evalResult.evidence_quality || "evidence"} evidence
                  </Badge>
                  <Badge>next: {evalResult.next_difficulty || difficulty}</Badge>
                </div>
                <div className="two-col">
                  <div>
                    <strong style={{ fontSize: 14 }}>Strengths</strong>
                    <ul className="pill-list good" style={{ marginTop: 8 }}>
                      {evalResult.strengths.length ? (
                        evalResult.strengths.map((s, i) => <li key={i}>{s}</li>)
                      ) : (
                        <li className="muted">No notable strengths flagged.</li>
                      )}
                    </ul>
                  </div>
                  <div>
                    <strong style={{ fontSize: 14 }}>Improvements</strong>
                    <ul className="pill-list warn" style={{ marginTop: 8 }}>
                      {evalResult.improvements.length ? (
                        evalResult.improvements.map((s, i) => <li key={i}>{s}</li>)
                      ) : (
                        <li className="muted">Solid — keep practicing.</li>
                      )}
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </Card>
        )}
      </div>
    </Page>
  );
}
