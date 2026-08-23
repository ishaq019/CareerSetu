// Shared UI primitives for CareerSetu. Small, composable, and styled entirely
// through the design-system classes in styles.css.
import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { Sparkles } from "lucide-react";

export function Spinner() {
  return <span className="spinner" aria-hidden />;
}

type BtnProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "ghost" | "quiet" | "danger";
  loading?: boolean;
  block?: boolean;
  size?: "md" | "lg";
};
export function Button({
  variant = "primary",
  loading,
  block,
  size = "md",
  children,
  disabled,
  className = "",
  ...rest
}: BtnProps) {
  return (
    <button
      className={`btn btn-${variant}${block ? " btn-block" : ""}${size === "lg" ? " btn-lg" : ""} ${className}`}
      disabled={disabled || loading}
      {...rest}
    >
      {loading && <Spinner />}
      {children}
    </button>
  );
}

export function Card({
  children,
  className = "",
  ...rest
}: { children: ReactNode; className?: string } & React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={`card ${className}`} {...rest}>
      {children}
    </div>
  );
}

export function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: ReactNode;
}) {
  return (
    <div className="field">
      <label>
        {label}
        {hint && <span className="hint"> — {hint}</span>}
      </label>
      {children}
    </div>
  );
}

export const Input = forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  function Input(props, ref) {
    return <input ref={ref} className="input" {...props} />;
  },
);

export const Textarea = forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement>
>(function Textarea(props, ref) {
  return <textarea ref={ref} className="textarea" {...props} />;
});

export function Badge({
  children,
  tone,
}: {
  children: ReactNode;
  tone?: "good" | "warn" | "bad";
}) {
  return <span className={`badge${tone ? ` badge-${tone}` : ""}`}>{children}</span>;
}

export function Brand({ to = "/" }: { to?: string }) {
  return (
    <Link to={to} className="brand">
      <span className="mark">
        <Sparkles size={17} />
      </span>
      CareerSetu
    </Link>
  );
}

export function ErrorAlert({ children }: { children: ReactNode }) {
  return (
    <div className="alert alert-error" role="alert">
      {children}
    </div>
  );
}

export function EmptyState({
  icon,
  title,
  children,
}: {
  icon: ReactNode;
  title: string;
  children?: ReactNode;
}) {
  return (
    <div className="empty">
      <div className="ic">{icon}</div>
      <strong>{title}</strong>
      {children && <p className="muted" style={{ marginTop: 6 }}>{children}</p>}
    </div>
  );
}

// Conic-free SVG ring gauge — the app's signature score element.
export function ScoreGauge({ value, label = "MATCH" }: { value: number; label?: string }) {
  const v = Math.max(0, Math.min(100, value));
  const r = 74;
  const c = 2 * Math.PI * r;
  const offset = c - (v / 100) * c;
  const tone = v >= 80 ? "var(--good)" : v >= 60 ? "var(--warn)" : "var(--bad)";
  return (
    <div className="gauge">
      <svg width="168" height="168" viewBox="0 0 168 168">
        <defs>
          <linearGradient id="gauge-grad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="var(--a1)" />
            <stop offset="100%" stopColor="var(--a2)" />
          </linearGradient>
        </defs>
        <circle className="gauge-track" cx="84" cy="84" r={r} strokeWidth="12" />
        <circle
          className="gauge-fill"
          cx="84"
          cy="84"
          r={r}
          strokeWidth="12"
          stroke={v >= 60 ? "url(#gauge-grad)" : tone}
          strokeDasharray={c}
          strokeDashoffset={offset}
        />
      </svg>
      <div className="gauge-num">
        <b>{v}</b>
        <small>{label}</small>
      </div>
    </div>
  );
}
