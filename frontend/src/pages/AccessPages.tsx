import { useState, type FormEvent } from "react";
import { ArrowRight, Building2, LockKeyhole, Mail } from "lucide-react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { ErrorNotice } from "../components/Feedback";
import type { UserRole } from "../types";

function homeForRole(role: UserRole): string {
  return role === "student" ? "/app" : "/app/complaints";
}

export function AccessPage({ mode }: { mode: "login" | "register" }) {
  const { user, login, register } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  if (user) return <Navigate to={homeForRole(user.role)} replace />;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setNotice("");
    try {
      if (mode === "register") {
        setNotice(await register(email.trim(), password));
        setPassword("");
      } else {
        const current = await login(email.trim(), password);
        navigate(homeForRole(current.role), { replace: true });
      }
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Could not complete your request.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-screen">
      <section className="auth-story">
        <Link className="brand-link" to="/login"><span className="brand-mark">SH</span><strong>Smart Hostel</strong></Link>
        <div className="story-copy">
          <p className="eyebrow">A BETTER WAY TO CARE FOR YOUR SPACE</p>
          <h1>Good stays start with things that work.</h1>
          <p>Report maintenance in a moment. Follow the repair all the way through.</p>
        </div>
        <div className="story-footer"><span><Building2 size={15} /> Campus maintenance, made clear</span><span>01 / 03</span></div>
      </section>
      <section className="auth-side">
        <div className="auth-card">
          <span className="auth-symbol"><Building2 size={19} /></span>
          <p className="eyebrow">{mode === "login" ? "WELCOME BACK" : "GET STARTED"}</p>
          <h2>{mode === "login" ? "Sign in to your account" : "Create your student account"}</h2>
          <p className="muted-copy">{mode === "login" ? "Use your hostel account to continue." : "Registration creates a student account."}</p>
          {error && <ErrorNotice message={error} />}
          {notice && <p className="success-notice" role="status">{notice} <Link to="/login">Sign in</Link></p>}
          <form className="auth-form" onSubmit={submit}>
            <label className="field">
              <span>Email address</span>
              <span className="input-with-icon"><Mail size={17} /><input autoComplete="email" required type="email" maxLength={254} value={email} onChange={(event) => setEmail(event.target.value)} placeholder="name@hostel.edu" /></span>
            </label>
            <label className="field">
              <span>Password</span>
              <span className="input-with-icon"><LockKeyhole size={17} /><input autoComplete={mode === "login" ? "current-password" : "new-password"} required type="password" minLength={8} maxLength={128} value={password} onChange={(event) => setPassword(event.target.value)} placeholder="At least 8 characters" /></span>
            </label>
            <button className="button button-primary auth-submit" type="submit" disabled={busy}>
              {busy ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}
              {!busy && <ArrowRight size={17} />}
            </button>
          </form>
          <p className="auth-switch">
            {mode === "login" ? "New to Smart Hostel?" : "Already registered?"}{" "}
            <Link to={mode === "login" ? "/register" : "/login"}>{mode === "login" ? "Create an account" : "Sign in"}</Link>
          </p>
          <p className="auth-security">Your session token is kept only for this browser session.</p>
        </div>
      </section>
    </main>
  );
}

export function LoginPage() {
  return <AccessPage mode="login" />;
}

export function RegisterPage() {
  return <AccessPage mode="register" />;
}
