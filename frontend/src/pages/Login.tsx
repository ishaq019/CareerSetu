// Sign in / sign up screen. Uses the AuthContext (which calls the correct
// /auth/login and /auth/signup endpoints — fixing the old /auth/signin bug).
import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { motion } from "motion/react";
import { apiBaseUrl, ApiError } from "../lib/api";
import { useAuth } from "../lib/auth";
import { Aurora } from "../components/Aurora";
import { Brand, Button, ErrorAlert, Field, Input } from "../components/ui";

const OAUTH_ERRORS: Record<string, string> = {
  oauth_not_configured: "Google sign-in isn't configured on the server yet.",
  invalid_state: "Your sign-in session expired. Please try again.",
  missing_code: "Google sign-in was cancelled or incomplete.",
  token_exchange_failed: "Google sign-in failed during token exchange.",
  google_unreachable: "Couldn't reach Google. Check your connection and retry.",
  email_unverified: "Your Google account email must be verified to sign in.",
  access_denied: "Google sign-in was cancelled.",
  account_persist_failed:
    "We couldn't save your account. The server database may be missing a migration (run alembic upgrade head).",
};

export default function Login() {
  const { user, login, signup, loginWithToken } = useAuth();
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

  // Handle the Google OAuth redirect: the backend returns either
  // `#token=<jwt>` (success) or `?error=<code>` (failure).
  useEffect(() => {
    const hash = new URLSearchParams(window.location.hash.replace(/^#/, ""));
    const token = hash.get("token");
    const errCode = params.get("error");
    if (token) {
      window.history.replaceState(null, "", window.location.pathname);
      loginWithToken(token)
        .then(() => navigate("/app", { replace: true }))
        .catch(() => setError("Google sign-in could not be completed. Please try again."));
    } else if (errCode) {
      setError(OAUTH_ERRORS[errCode] || "Google sign-in failed. Please try again.");
    }
  }, [params, loginWithToken, navigate]);

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

  function google() {
    setError("");
    setNotice("");
    // Full-page redirect to begin the server-side OAuth flow.
    window.location.href = `${apiBaseUrl}/auth/google`;
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
