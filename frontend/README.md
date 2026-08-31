# 🎨 CareerSetu — Frontend

A modern, dark **SaaS-style** single-page app for CareerSetu, built with React 19, TypeScript and Vite. It wires every backend endpoint into a clean, router-based multi-page experience.

## 🧱 Tech stack

- ⚛️ **React 19** + **TypeScript 5.9**
- ⚡ **Vite 7** — dev server & build
- 🧭 **react-router-dom 7** — multi-page routing
- 🎞️ **motion** (Framer Motion) — animations
- 🎨 Hand-crafted CSS design system (no Tailwind)
- 🔗 **lucide-react** — icons

## 🚀 Quick start

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

The app runs at http://localhost:5173.

```env
# frontend/.env
VITE_API_BASE_URL=http://localhost:8000/api/v1

# Set this to the public path the app is served from. For the public GitHub
# Pages build, the deploy workflow sets VITE_BASE=/CareerSetu/ at build time.
# For other hosts served at the domain root, leave it empty.
VITE_BASE=
```

## 📜 Scripts

| Command | Description |
|---|---|
| `npm run dev` | ▶️ Start the Vite dev server |
| `npm run build` | 📦 Type-check (`tsc -b`) and build for production |
| `npm run preview` | 👀 Preview the production build locally |

## 🗺️ Pages

| Route | Page | Access |
|---|---|---|
| `/` | Landing + guest analysis | 🌐 Public |
| `/login` | Sign in / sign up | 🌐 Public |
| `/app` | Dashboard | 🔐 Auth |
| `/app/analyze` | Resume ↔ JD analysis | 🔐 Auth |
| `/app/interview` | Adaptive interview | 🔐 Auth |
| `/app/chat` | Grounded chat | 🔐 Auth |
| `/app/resume` | Resume optimization | 🔐 Auth |
| `/app/cover-letter` | Cover-letter generator | 🔐 Auth |
| `/app/roadmap` | Learning roadmap | 🔐 Auth |
| `/app/history` | Saved history | 🔐 Auth |

## 📂 Structure

```text
frontend/src/
├─ main.tsx          app bootstrap (Router + AuthProvider)
├─ App.tsx           route map
├─ lib/              api client · types · auth context
├─ components/       UI kit · layout · shared views
├─ pages/            one file per route
└─ styles.css        design system
```

## 🔐 Auth

JWTs from the backend are managed by the `AuthProvider` context in `src/lib/auth.tsx`; protected routes redirect unauthenticated users to `/login`.

## 📦 Build

```bash
npm run build      # output in dist/
```

Deploy `dist/` to any static host (Vercel, Netlify, Cloudflare Pages). The build embeds two variables:

- `VITE_API_BASE_URL` — absolute base URL of the deployed backend (with `/api/v1` suffix).
- `VITE_BASE` — public path the app is served from. Leave empty for domain-root deployments; set to `/<repo>/` for GitHub Pages project sites (the deploy workflow already does this).

The Pages site (`syedishaq.me/CareerSetu/`) uses `VITE_BASE=/CareerSetu/` and `VITE_API_BASE_URL=https://career-setu-azure.vercel.app/api/v1`.
