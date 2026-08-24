// Route map. Public: landing + auth. Protected app shell: dashboard and tools.
import { Navigate, Route, Routes } from "react-router-dom";
import { Aurora } from "./components/Aurora";
import { AppLayout, AdminRoute, ProtectedRoute } from "./components/AppLayout";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Analyze from "./pages/Analyze";
import Interview from "./pages/Interview";
import Chat from "./pages/Chat";
import Resume from "./pages/Resume";
import CoverLetter from "./pages/CoverLetter";
import Roadmap from "./pages/Roadmap";
import History from "./pages/History";
import Knowledge from "./pages/Knowledge";

export default function App() {
  return (
    <>
      <Aurora />
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />

        <Route element={<ProtectedRoute />}>
          <Route path="/app" element={<AppLayout />}>
            <Route index element={<Dashboard />} />
            <Route path="analyze" element={<Analyze />} />
            <Route path="interview" element={<Interview />} />
            <Route path="chat" element={<Chat />} />
            <Route path="resume" element={<Resume />} />
            <Route path="cover-letter" element={<CoverLetter />} />
            <Route path="roadmap" element={<Roadmap />} />
            <Route path="history" element={<History />} />
            <Route element={<AdminRoute />}>
              <Route path="knowledge" element={<Knowledge />} />
            </Route>
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}
