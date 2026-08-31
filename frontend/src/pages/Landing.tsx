// Public landing page: hero thesis, live guest analyzer (no account needed),
// how-it-works, and a feature grid that invites sign-up for the AI tools.
import { useRef, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "motion/react";
import {
  ArrowRight,
  BrainCircuit,
  FileText,
  Gauge,
  LockKeyhole,
  MessageSquare,
  PenLine,
  ShieldCheck,
} from "lucide-react";
import { api, ApiError } from "../lib/api";
import type { Analysis } from "../lib/types";
import { Button, Card, ErrorAlert } from "../components/ui";
import { AnalysisView } from "../components/AnalysisView";
import { UploadTextarea } from "../components/UploadTextarea";

const FEATURES = [
  { icon: Gauge, title: "Deterministic job-fit score", body: "A transparent, repeatable match score computed from real skill evidence — not a black box." },
  { icon: BrainCircuit, title: "Adaptive interview prep", body: "Get role-specific questions and evidence-based feedback that adapts to your answers." },
  { icon: MessageSquare, title: "Grounded career chat", body: "Answers cite the knowledge base they came from, so guidance stays accountable." },
  { icon: FileText, title: "ATS resume builder", body: "Rewrite bullets and keywords for the target role without inventing experience." },
  { icon: PenLine, title: "Tailored cover letters", body: "Draft a specific, honest cover letter grounded in your actual resume." },
  { icon: ShieldCheck, title: "Privacy by default", body: "Guest analysis never stores your resume. Save history only when you choose to." },
];

export default function Landing() {
  const [resume, setResume] = useState("");
  const [jd, setJd] = useState("");
  const [result, setResult] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const analyzerRef = useRef<HTMLDivElement>(null);

  async function run() {
    if (resume.trim().length < 30 || jd.trim().length < 30) {
      setError("Add at least 30 characters to both the resume and the job description.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const res = await api.post<Analysis>(
        "/analysis",
        { resume_text: resume, job_description: jd },
        { auth: false },
      );
      setResult(res);
      setTimeout(() => analyzerRef.current?.scrollIntoView({ behavior: "smooth" }), 60);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Analysis failed. Is the API running?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <header className="topbar">
        <div className="wrap">
          <Link to="/" className="brand">
            <span className="mark">
              <Gauge size={17} />
            </span>
            CareerSetu
          </Link>
          <nav>
            <a href="#analyze">Analyze</a>
            <a href="#how">How it works</a>
            <a href="#features">Features</a>
          </nav>
          <div className="actions">
            <Link to="/login">
              <Button variant="quiet">Sign in</Button>
            </Link>
            <Link to="/login?mode=signup">
              <Button variant="primary">Get started</Button>
            </Link>
          </div>
        </div>
      </header>

      <section className="hero wrap">
        <div className="hero-grid">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
          >
            <span className="eyebrow">
              <Gauge size={13} /> Job-fit intelligence
            </span>
            <h1 style={{ marginTop: 16 }}>
              Know your fit
              <br />
              <em>before you apply.</em>
            </h1>
            <p className="lead">
              Paste a resume and a job description to see matched skills, missing evidence,
              ATS-oriented coverage, and the exact edits that move you from maybe to yes.
            </p>
            <div className="cta-row">
              <Button
                size="lg"
                onClick={() => analyzerRef.current?.scrollIntoView({ behavior: "smooth" })}
              >
                Analyze my job fit <ArrowRight size={17} />
              </Button>
              <a href="#features">
                <Button variant="ghost" size="lg">
                  See features
                </Button>
              </a>
            </div>
            <p className="trust">
              <LockKeyhole size={13} /> No account required for the core analysis.
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.96, y: 16 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.15, ease: [0.22, 1, 0.36, 1] }}
          >
            <Card className="preview">
              <div className="prev-head">
                <span className="eyebrow">Sample report</span>
                <span
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: 30,
                    fontWeight: 700,
                    background: "var(--accent-grad)",
                    WebkitBackgroundClip: "text",
                    backgroundClip: "text",
                    color: "transparent",
                  }}
                >
                  82
                </span>
              </div>
              {[
                { c: "var(--good)", s: "React, FastAPI, PostgreSQL", m: "Strong, well-evidenced" },
                { c: "var(--warn)", s: "Docker", m: "Mentioned, needs proof" },
                { c: "var(--bad)", s: "Kubernetes", m: "Missing from resume" },
              ].map((row) => (
                <div className="prev-row" key={row.s}>
                  <span className="dot" style={{ background: row.c }} />
                  <div>
                    <strong>{row.s}</strong>
                    <br />
                    <small>{row.m}</small>
                  </div>
                </div>
              ))}
            </Card>
          </motion.div>
        </div>
      </section>

      <section id="analyze" className="section wrap" ref={analyzerRef}>
        <div className="section-head">
          <span className="eyebrow">Live analyzer</span>
          <h2>Start with your resume and target job.</h2>
          <p>
            Everything runs on a deterministic scoring engine, so the same inputs always give the
            same, explainable result.
          </p>
        </div>

        {!result ? (
          <Card>
            <div className="two-col">
              <UploadTextarea
                label="Your resume"
                hint="paste text or upload a file"
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
            {error && (
              <div style={{ marginTop: 16 }}>
                <ErrorAlert>{error}</ErrorAlert>
              </div>
            )}
            <div style={{ marginTop: 18 }}>
              <Button size="lg" loading={loading} onClick={run}>
                {loading ? "Analyzing your profile…" : "Analyze my job fit"}
                {!loading && <ArrowRight size={17} />}
              </Button>
            </div>
          </Card>
        ) : (
          <div className="stack">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
              <span className="eyebrow">Your report</span>
              <div style={{ display: "flex", gap: 10 }}>
                <Button variant="ghost" onClick={() => setResult(null)}>
                  New analysis
                </Button>
                <Link to="/login?mode=signup">
                  <Button>Save & unlock AI tools</Button>
                </Link>
              </div>
            </div>
            <AnalysisView a={result} />
          </div>
        )}
      </section>

      <section id="how" className="section wrap">
        <div className="section-head">
          <span className="eyebrow">How it works</span>
          <h2>Three steps from posting to a stronger application.</h2>
        </div>
        <div className="steps">
          <div className="step">
            <h3>Paste & analyze</h3>
            <p>Drop in your resume and the job description. The engine maps evidence to requirements.</p>
          </div>
          <div className="step">
            <h3>See the gaps</h3>
            <p>Get a transparent score, matched strengths, and the specific missing proof to add.</p>
          </div>
          <div className="step">
            <h3>Prepare & apply</h3>
            <p>Sign in to save history and use AI interview prep, resume, cover letter and chat.</p>
          </div>
        </div>
      </section>

      <section id="features" className="section wrap">
        <div className="section-head">
          <span className="eyebrow">Everything in one workspace</span>
          <h2>Tools that keep you honest and prepared.</h2>
        </div>
        <div className="feature-grid">
          {FEATURES.map((f) => (
            <Card className="feature" key={f.title}>
              <div className="ic">
                <f.icon size={20} />
              </div>
              <h3>{f.title}</h3>
              <p>{f.body}</p>
            </Card>
          ))}
        </div>
        <div style={{ marginTop: 32, display: "flex", justifyContent: "center" }}>
          <Link to="/login?mode=signup">
            <Button size="lg">
              Create your free account <ArrowRight size={17} />
            </Button>
          </Link>
        </div>
      </section>

      <footer className="footer">
        <div className="wrap">
          <Link to="/" className="brand" style={{ fontSize: 16 }}>
            <span className="mark" style={{ width: 26, height: 26 }}>
              <Gauge size={14} />
            </span>
            CareerSetu
          </Link>
          <span>Deterministic job-fit scoring with optional Groq-powered AI features.</span>
        </div>
      </footer>
    </div>
  );
}
