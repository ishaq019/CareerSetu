import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// `base` controls the public path assets are served from. On GitHub Pages a
// project site is served under /<repo>/ (here: /CareerSetu/), so the deploy
// workflow passes VITE_BASE (from actions/configure-pages `base_path`) at
// build time. We normalise it to a leading + trailing slash. Local dev
// (`vite serve`) always uses "/". `import.meta.env.BASE_URL` mirrors this, so
// the React Router basename follows automatically.
function normaliseBase(raw?: string): string {
  const value = (raw ?? "").trim();
  // Default to root for non-GitHub-Pages deployments. The Pages workflow sets
  // VITE_BASE="/CareerSetu/" at build time, so the public site still resolves
  // to /CareerSetu/. Local dev also uses "/".
  if (!value || value === "/") return "/";
  const withLead = value.startsWith("/") ? value : `/${value}`;
  return withLead.endsWith("/") ? withLead : `${withLead}/`;
}

export default defineConfig(({ command }) => ({
  // Dev server runs at "/"; production builds are served under the Pages sub-path.
  base: command === "build" ? normaliseBase(process.env.VITE_BASE) : "/",
  plugins: [react()],
  server: { port: 5173 },
}));
