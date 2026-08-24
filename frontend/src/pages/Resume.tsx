// Resume builder: produces an ATS-tailored resume from the candidate's resume +
// a target job. The backend returns compilable LaTeX plus the deterministic gap
// analysis. Users can download the .tex or save an in-browser PDF (print).
import { useState } from "react";
import { Download, FileText, Printer, Sparkles } from "lucide-react";
import { api, ApiError } from "../lib/api";
import type { LatexResumeContent, LatexResumeResult } from "../lib/types";
import { Page } from "../components/AppLayout";
import { UploadTextarea } from "../components/UploadTextarea";
import { Badge, Button, Card, EmptyState, ErrorAlert, ScoreGauge } from "../components/ui";

function downloadTex(latex: string, filename: string) {
  const blob = new Blob([latex], { type: "application/x-tex" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename || "resume.tex";
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function esc(s: string): string {
  return (s || "").replace(/[&<>"]/g, (c) =>
    c === "&" ? "&amp;" : c === "<" ? "&lt;" : c === ">" ? "&gt;" : "&quot;",
  );
}

// Render the structured resume as a print-optimised HTML document and open the
// browser print dialog (Save as PDF). This is a faithful visual resume — not a
// compile of the .tex — so it needs no server-side TeX toolchain.
function printResume(c: LatexResumeContent) {
  const contacts = [c.contact.phone, c.contact.email, c.contact.location, c.contact.portfolio, c.contact.linkedin, c.contact.github]
    .filter(Boolean)
    .map(esc)
    .join(" &nbsp;•&nbsp; ");
  const section = (title: string, body: string) =>
    body ? `<h2>${esc(title)}</h2>${body}` : "";
  const bullets = (items: string[]) =>
    items?.length ? `<ul>${items.map((b) => `<li>${esc(b)}</li>`).join("")}</ul>` : "";

  const skills = c.skill_groups
    ?.filter((g) => g.items?.length)
    .map((g) => `<p><b>${esc(g.category)}:</b> ${g.items.map(esc).join(", ")}</p>`)
    .join("") || "";
  const experience = c.experience
    ?.filter((x) => x.company || x.role)
    .map(
      (x) =>
        `<div class="entry"><div class="row"><b>${esc([x.role, x.company].filter(Boolean).join(" — "))}</b><span>${esc(x.date)}</span></div>${x.location ? `<div class="sub">${esc(x.location)}</div>` : ""}${bullets(x.bullets)}</div>`,
    )
    .join("") || "";
  const projects = c.projects
    ?.filter((p) => p.name)
    .map((p) => {
      const links = [p.github && `<a href="${esc(p.github)}">Code</a>`, p.live && `<a href="${esc(p.live)}">Live</a>`]
        .filter(Boolean)
        .join(" | ");
      const right = [links, esc(p.date)].filter(Boolean).join(" &nbsp; ");
      return `<div class="entry"><div class="row"><b>${esc(p.name)}</b><span>${right}</span></div>${p.tech_stack ? `<div class="sub">${esc(p.tech_stack)}</div>` : ""}${bullets(p.bullets)}</div>`;
    })
    .join("") || "";
  const education = c.education
    ?.filter((e) => e.institution || e.degree)
    .map(
      (e) =>
        `<div class="entry"><div class="row"><b>${esc(e.institution)}</b><span>${esc(e.date)}</span></div><div class="sub">${esc([e.degree, e.detail].filter(Boolean).join(" — "))}</div></div>`,
    )
    .join("") || "";
  const certs = bullets(c.certifications);

  const html = `<!doctype html><html><head><meta charset="utf-8"><title>${esc(c.contact.name || "Resume")}</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: Georgia, "Times New Roman", serif; color: #111; max-width: 780px; margin: 32px auto; padding: 0 28px; line-height: 1.4; }
  header { text-align: center; margin-bottom: 14px; }
  header h1 { font-size: 26px; margin: 0 0 4px; letter-spacing: 1px; text-transform: uppercase; }
  header .title { font-size: 13px; color: #333; margin-bottom: 4px; }
  header .contacts { font-size: 12px; color: #444; }
  header a { color: #1f2937; text-decoration: none; }
  h2 { font-size: 14px; text-transform: uppercase; letter-spacing: 1px; border-bottom: 1.5px solid #111; padding-bottom: 2px; margin: 16px 0 8px; }
  p { margin: 3px 0; font-size: 13px; }
  .entry { margin-bottom: 9px; }
  .row { display: flex; justify-content: space-between; gap: 12px; font-size: 13px; }
  .row span { color: #444; white-space: nowrap; font-size: 12px; }
  .sub { font-style: italic; color: #444; font-size: 12px; margin: 1px 0 2px; }
  ul { margin: 3px 0 3px 18px; padding: 0; }
  li { font-size: 12.5px; margin: 1px 0; }
  @media print { body { margin: 0; } }
</style></head><body>
<header>
  <h1>${esc(c.contact.name || "Your Name")}</h1>
  ${c.contact.title ? `<div class="title">${esc(c.contact.title)}</div>` : ""}
  <div class="contacts">${contacts}</div>
</header>
${section("Summary", c.objective ? `<p>${esc(c.objective)}</p>` : "")}
${section("Skills", skills)}
${section("Experience", experience)}
${section("Projects", projects)}
${section("Education", education)}
${section("Certifications", certs)}
<script>window.onload=function(){setTimeout(function(){window.print();},250);};</script>
</body></html>`;

  const w = window.open("", "_blank");
  if (!w) {
    alert("Please allow pop-ups to save the resume as a PDF.");
    return;
  }
  w.document.open();
  w.document.write(html);
  w.document.close();
}

// PLACEHOLDER_COMPONENT

function Tags({ items, tone }: { items: string[]; tone?: "good" | "warn" | "bad" }) {
  if (!items?.length) return <span className="muted" style={{ fontSize: 13 }}>None detected.</span>;
  return (
    <div className="tag-wrap">
      {items.map((s) => (
        <Badge key={s} tone={tone}>
          {s}
        </Badge>
      ))}
    </div>
  );
}

export default function Resume() {
  const [resume, setResume] = useState("");
  const [jd, setJd] = useState("");
  const [result, setResult] = useState<LatexResumeResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function generate() {
    if (resume.trim().length < 30 || jd.trim().length < 30) {
      setError("Add at least 30 characters to both the resume and the job description.");
      return;
    }
    setError("");
    setBusy(true);
    try {
      const res = await api.post<LatexResumeResult>("/documents/resume/latex", {
        resume_text: resume,
        job_description: jd,
      });
      setResult(res);
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
    <Page
      title="Resume builder"
      subtitle="Tailors your real resume to a target job — surfaces missing skills and ATS keywords, then exports LaTeX or a print-ready PDF."
    >
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
              <Sparkles size={15} /> Build tailored resume
            </Button>
          </div>
        </Card>

        {!result ? (
          <Card>
            <EmptyState icon={<FileText size={22} />} title="Your tailored resume will appear here">
              Provide a resume and a target job, then generate — you'll get the LaTeX source and a
              PDF you can save from your browser.
            </EmptyState>
          </Card>
        ) : (
          <>
            <Card>
              <div className="report-top">
                <ScoreGauge value={result.match_score} label="MATCH" />
                <div className="stack" style={{ gap: 14, flex: 1 }}>
                  <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                    <Button onClick={() => downloadTex(result.latex, result.filename)}>
                      <Download size={15} /> Download .tex
                    </Button>
                    <Button variant="ghost" onClick={() => printResume(result.content)}>
                      <Printer size={15} /> Save as PDF
                    </Button>
                  </div>
                  <div>
                    <strong style={{ fontSize: 13 }}>Missing skills the job asks for</strong>
                    <div style={{ marginTop: 8 }}>
                      <Tags items={result.missing_skills} tone="bad" />
                    </div>
                  </div>
                  {result.partial_skills?.length > 0 && (
                    <div>
                      <strong style={{ fontSize: 13 }}>Partially covered</strong>
                      <div style={{ marginTop: 8 }}>
                        <Tags items={result.partial_skills} tone="warn" />
                      </div>
                    </div>
                  )}
                  <div>
                    <strong style={{ fontSize: 13 }}>ATS keywords woven in</strong>
                    <div style={{ marginTop: 8 }}>
                      <Tags items={result.ats_keywords} tone="good" />
                    </div>
                  </div>
                </div>
              </div>
            </Card>

            <Card>
              <div className="card-h">
                <h3>Tailored summary</h3>
              </div>
              <p style={{ fontSize: 14.5, color: "var(--text-soft)" }}>{result.content.objective}</p>
            </Card>

            <Card>
              <div className="card-h">
                <h3>LaTeX source</h3>
                <Button variant="quiet" onClick={() => downloadTex(result.latex, result.filename)}>
                  <Download size={14} /> {result.filename}
                </Button>
              </div>
              <pre
                style={{
                  maxHeight: 340,
                  overflow: "auto",
                  fontFamily: "var(--font-mono)",
                  fontSize: 12,
                  background: "rgba(0,0,0,.25)",
                  padding: 14,
                  borderRadius: 10,
                  whiteSpace: "pre-wrap",
                }}
              >
                {result.latex}
              </pre>
            </Card>
          </>
        )}
      </div>
    </Page>
  );
}
