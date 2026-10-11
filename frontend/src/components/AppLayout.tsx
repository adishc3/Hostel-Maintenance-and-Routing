import { useState } from "react";
import { ClipboardList, LogOut, Menu, Plus, ShieldCheck, Wrench, X } from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function AppLayout() {
  const { user, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const role = user?.role ?? "student";

  return (
    <div className="app-shell">
      <aside className={`sidebar ${menuOpen ? "sidebar-open" : ""}`}>
        <div className="brand-lockup">
          <span className="brand-mark">SH</span>
          <span><strong>Smart Hostel</strong><small>Maintenance desk</small></span>
          <button className="icon-button sidebar-close" aria-label="Close navigation" onClick={() => setMenuOpen(false)} type="button">
            <X size={18} />
          </button>
        </div>
        <p className="nav-caption">WORKSPACE</p>
        <nav className="side-nav" aria-label="Main navigation">
          {role === "student" && (
            <NavLink to="/app" end onClick={() => setMenuOpen(false)}><Plus size={17} /> New complaint</NavLink>
          )}
          {(role === "student" || role === "staff" || role === "admin") && (
            <NavLink to="/app/complaints" onClick={() => setMenuOpen(false)}><ClipboardList size={17} /> {role === "student" ? "My complaints" : role === "staff" ? "Department queue" : "All complaints"}</NavLink>
          )}
          {role === "admin" && <span className="nav-role"><ShieldCheck size={16} /> Administrator access</span>}
          {role === "staff" && <span className="nav-role"><Wrench size={16} /> Department staff</span>}
        </nav>
        <div className="sidebar-bottom">
          <div className="profile-chip">
            <span className="avatar">{user?.email.slice(0, 1).toUpperCase()}</span>
            <span className="profile-copy"><strong>{user?.email}</strong><small>{role}</small></span>
          </div>
          <button className="logout-button" onClick={logout} type="button"><LogOut size={16} /> Sign out</button>
        </div>
      </aside>
      {menuOpen && <button className="mobile-scrim" aria-label="Close navigation" onClick={() => setMenuOpen(false)} type="button" />}
      <main className="main-area">
        <header className="topbar">
          <button className="icon-button mobile-menu" aria-label="Open navigation" onClick={() => setMenuOpen(true)} type="button"><Menu size={20} /></button>
          <div><span className="topbar-kicker">HOSTEL OPERATIONS</span><strong>Maintenance workspace</strong></div>
          <span className="topbar-user">{user?.email}</span>
        </header>
        <Outlet />
      </main>
    </div>
  );
}
