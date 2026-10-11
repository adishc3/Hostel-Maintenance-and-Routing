import { Navigate, Outlet, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth/AuthContext";
import { AppLayout } from "./components/AppLayout";
import { ComplaintDetail } from "./components/ComplaintDetail";
import { Loading } from "./components/Feedback";
import { LoginPage, RegisterPage } from "./pages/AccessPages";
import { ComplaintQueue } from "./pages/ComplaintQueue";
import { StudentDashboard } from "./pages/StudentDashboard";
import type { UserRole } from "./types";

function homeForRole(role: UserRole): string {
  return role === "student" ? "/app" : "/app/complaints";
}

function ProtectedRoute({ roles }: { roles?: UserRole[] }) {
  const { user, loading } = useAuth();
  if (loading) return <main className="auth-loading"><Loading label="Checking your session…" /></main>;
  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to={homeForRole(user.role)} replace />;
  return <Outlet />;
}

function IndexRedirect() {
  const { user, loading } = useAuth();
  if (loading) return <main className="auth-loading"><Loading label="Checking your session…" /></main>;
  return <Navigate to={user ? homeForRole(user.role) : "/login"} replace />;
}

function WorkspaceHome() {
  const { user } = useAuth();
  return user?.role === "student"
    ? <StudentDashboard />
    : <Navigate to="/app/complaints" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<IndexRedirect />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route element={<ProtectedRoute />}>
        <Route path="/app" element={<AppLayout />}>
          <Route index element={<WorkspaceHome />} />
          <Route path="complaints" element={<ComplaintQueue />} />
          <Route path="complaints/:id" element={<ComplaintDetail />} />
        </Route>
      </Route>
      <Route path="*" element={<IndexRedirect />} />
    </Routes>
  );
}
