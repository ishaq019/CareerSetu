// Authenticated application shell: persistent sidebar navigation, a mobile
// nav bar, and the ProtectedRoute guard that redirects signed-out users.
import { type ReactNode } from "react";
import { NavLink, Navigate, Outlet, useLocation } from "react-router-dom";
import {
  BrainCircuit,
  FileText,
  Gauge,
  History,
  LayoutDashboard,
  LogOut,
  Map as MapIcon,
  MessageSquare,
  PenLine,
} from "lucide-react";
import { useAuth } from "../lib/auth";
import { Brand, Button } from "./ui";

const NAV = [
  { to: "/app", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/app/analyze", label: "Job-fit analysis", icon: Gauge, end: false },
  { to: "/app/interview", label: "Interview prep", icon: BrainCircuit, end: false },
  { to: "/app/chat", label: "Career chat", icon: MessageSquare, end: false },
  { to: "/app/resume", label: "Resume builder", icon: FileText, end: false },
  { to: "/app/cover-letter", label: "Cover letter", icon: PenLine, end: false },
  { to: "/app/roadmap", label: "Learning roadmap", icon: MapIcon, end: false },
  { to: "/app/history", label: "Saved analyses", icon: History, end: false },
];

function NavItems() {
  return (
    <nav className="side-nav">
      {NAV.map(({ to, label, icon: Icon, end }) => (
        <NavLink key={to} to={to} end={end}>
          <Icon size={17} />
          {label}
        </NavLink>
      ))}
    </nav>
  );
}

export function ProtectedRoute() {
  const { user, ready } = useAuth();
  const location = useLocation();
  if (!ready)
    return (
      <div className="center-load">
        <span className="spinner" style={{ borderTopColor: "var(--a1)" }} />
        Loading your workspace…
      </div>
    );
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  return <Outlet />;
}

export function AppLayout() {
  const { user, logout } = useAuth();
  return (
    <div className="app">
      <aside className="sidebar">
        <Brand to="/app" />
        <NavItems />
        <div className="side-foot">
          <div className="who">
            Signed in as
            <b>{user?.email}</b>
          </div>
          <Button variant="ghost" block onClick={logout}>
            <LogOut size={15} /> Sign out
          </Button>
        </div>
      </aside>

      <div className="mobilebar">
        <Brand to="/app" />
        <Button variant="quiet" onClick={logout} aria-label="Sign out">
          <LogOut size={16} />
        </Button>
      </div>

      <main className="main">
        <div className="mobilebar" style={{ borderTop: "none", position: "static" }}>
          <NavItems />
        </div>
        <Outlet />
      </main>
    </div>
  );
}

export function Page({
  title,
  subtitle,
  actions,
  children,
}: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
}) {
  return (
    <>
      <div className="pagehead">
        <div style={{ display: "flex", justifyContent: "space-between", gap: 16, flexWrap: "wrap" }}>
          <div>
            <h1>{title}</h1>
            {subtitle && <p>{subtitle}</p>}
          </div>
          {actions}
        </div>
      </div>
      <div className="page">{children}</div>
    </>
  );
}
