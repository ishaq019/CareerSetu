// Sign in / sign up screen. Uses the AuthContext (which calls the correct
// /auth/login and /auth/signup endpoints — fixing the old /auth/signin bug).
import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { motion } from "motion/react";
import { api, ApiError } from "../lib/api";
import { useAuth } from "../lib/auth";
import { Aurora } from "../components/Aurora";
import { Brand, Button, ErrorAlert, Field, Input } from "../components/ui";

export default function Login() {
  const { user, login, signup } = useAuth();
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string })?.from || "/app";

  const [mode, setMode] = useState<"signin" | "signup">(
    params.get("mode") === "signup" ? "signup" : "signin",
  );
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    if (user) navigate(from, { replace: true });
  }, [user, from, navigate]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (mode === "signin") await login(email.trim(), password);
      else await signup(email.trim(), password);
      navigate(from, { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Authentication failed. Try again.");
    } finally {
      setBusy(false);
    }
  }

  async function google() {
    setError("");
    setNotice("");
    try {
      const res = await api.get<{ message: string }>("/auth/google", { auth: false });
      setNotice(res.message);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Google sign-in is unavailable.");
    }
  }

  return (
    <div className="auth-screen">
      <Aurora />
      <motion.div
        className="auth-card card"
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <Brand />
        <h1>{mode === "signin" ? "Welcome back" : "Create your account"}</h1>
        <p>
          Core job-fit analysis is free and needs no account. Sign in to save history and unlock
          the AI interview, resume, cover-letter and chat tools.
        </p>

        <div className="tabs" role="tablist">
          <button
            role="tab"
            aria-selected={mode === "signin"}
            className={mode === "signin" ? "active" : ""}
            onClick={() => setMode("signin")}
          >
            Sign in
          </button>
          <button
            role="tab"
            aria-selected={mode === "signup"}
            className={mode === "signup" ? "active" : ""}
            onClick={() => setMode("signup")}
          >
            Sign up
          </button>
        </div>

        <Button variant="ghost" block onClick={google}>
          Continue with Google
        </Button>
        {notice && (
          <div className="alert alert-info" style={{ marginTop: 12 }}>
            {notice}
          </div>
        )}
        <div className="divider">or use email</div>

        <form className="stack" onSubmit={submit} style={{ gap: 14 }}>
          <Field label="Email">
            <Input
              type="email"
              value={email}
              autoComplete="email"
              placeholder="you@example.com"
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </Field>
          <Field label="Password" hint="at least 8 characters">
            <Input
              type="password"
              value={password}
              autoComplete={mode === "signin" ? "current-password" : "new-password"}
              placeholder="••••••••"
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </Field>
          {error && <ErrorAlert>{error}</ErrorAlert>}
          <Button type="submit" block loading={busy} disabled={!email || password.length < 8}>
            {mode === "signin" ? "Sign in" : "Create account"}
          </Button>
        </form>

        <p className="muted" style={{ fontSize: 12, marginTop: 16, textAlign: "center" }}>
          Avoid uploading secrets or confidential company documents.
        </p>
        <p style={{ textAlign: "center", marginTop: 14, fontSize: 13.5 }}>
          <Link to="/" className="muted">
            ← Back to home
          </Link>
        </p>
      </motion.div>
    </div>
  );
}
