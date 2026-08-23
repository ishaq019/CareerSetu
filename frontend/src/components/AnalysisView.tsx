// Reusable analysis report: score gauge, matched strengths, priority gaps and
// the roadmap. Shared by the guest landing page, the authed analyzer, and the
// saved-history detail view.
import { CheckCircle2, TriangleAlert } from "lucide-react";
import type { Analysis, SkillResult } from "../lib/types";
import { Badge, Card, ScoreGauge } from "./ui";

export function recLabel(rec: string) {
  if (rec === "STRONG_MATCH") return { text: "Strong match", tone: "good" as const };
  if (rec === "MATCH_WITH_IMPROVEMENTS")
    return { text: "Match with improvements", tone: "warn" as const };
  return { text: "Needs stronger evidence", tone: "bad" as const };
}

function SkillRow({ item }: { item: SkillResult }) {
  const strong = item.status === "strong";
  const missing = item.status === "missing";
  return (
    <div className="skill-item">
      <div
        className="s-ic"
        style={{
          background: strong ? "var(--good-bg)" : missing ? "var(--bad-bg)" : "var(--warn-bg)",
          color: strong ? "var(--good)" : missing ? "var(--bad)" : "var(--warn)",
        }}
      >
        {strong ? <CheckCircle2 size={15} /> : missing ? "!" : "~"}
      </div>
      <div>
        <strong>{item.skill}</strong>{" "}
        <span className="lv">
          {item.detected_level} → target {item.required_level}
        </span>
        <div className="ev">{item.evidence}</div>
      </div>
    </div>
  );
}

export function AnalysisView({ a }: { a: Analysis }) {
  const rec = recLabel(a.recommendation);
  return (
    <div className="stack" style={{ gap: 18 }}>
      <Card>
        <div className="report-top">
          <ScoreGauge value={a.match_score} />
          <div className="stack" style={{ gap: 12 }}>
            <Badge tone={rec.tone}>{rec.text}</Badge>
            <p style={{ fontSize: 15, color: "var(--text-soft)" }}>{a.summary}</p>
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13 }}>
                <span className="muted">ATS requirement coverage</span>
                <span style={{ fontFamily: "var(--font-mono)" }}>{a.ats_coverage}%</span>
              </div>
              <div className="meter" style={{ marginTop: 7 }}>
                <i style={{ width: `${a.ats_coverage}%` }} />
              </div>
            </div>
          </div>
        </div>
      </Card>

      <div className="two-col">
        <Card>
          <div className="card-h">
            <div>
              <h3>Matched evidence</h3>
              <p>Skills the resume already backs up.</p>
            </div>
            <Badge tone="good">{a.strengths.length}</Badge>
          </div>
          {a.strengths.length ? (
            a.strengths.map((s) => <SkillRow key={s.skill} item={s} />)
          ) : (
            <p className="muted" style={{ fontSize: 13.5 }}>
              No fully matched skills detected yet — focus on the priority gaps.
            </p>
          )}
        </Card>

        <Card>
          <div className="card-h">
            <div>
              <h3>Priority gaps</h3>
              <p>Where the resume needs clearer proof.</p>
            </div>
            <Badge tone="warn">{a.gaps.length}</Badge>
          </div>
          {a.gaps.length ? (
            a.gaps.map((s) => <SkillRow key={s.skill} item={s} />)
          ) : (
            <p className="muted" style={{ fontSize: 13.5 }}>
              Nothing major missing. Tighten wording and add measurable results.
            </p>
          )}
        </Card>
      </div>

      {a.roadmap.length > 0 && (
        <Card>
          <div className="card-h">
            <div>
              <h3>Next resume edits</h3>
              <p>Close the most visible gaps, add measurable proof, then re-analyze.</p>
            </div>
            <TriangleAlert size={18} className="muted" />
          </div>
          <div className="two-col">
            {a.roadmap.map((r) => (
              <div className="road" key={r.skill}>
                <Badge tone={r.priority === "high" ? "bad" : "warn"}>{r.priority} priority</Badge>
                <h4>{r.skill}</h4>
                <span className="lv" style={{ fontFamily: "var(--font-mono)", fontSize: 11 }}>
                  Target: {r.target_level}
                </span>
                <ul>
                  {r.steps.map((step) => (
                    <li key={step}>{step}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
