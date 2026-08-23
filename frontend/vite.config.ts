import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// `base` controls the public path assets are served from. On GitHub Pages a
// project site is served under /<repo>/, so the workflow passes VITE_BASE
// (from actions/configure-pages) at build time. Defaults to "/" for local dev.
export default defineConfig({
  base: process.env.VITE_BASE || "/",
  plugins: [react()],
  server: { port: 5173 },
});
