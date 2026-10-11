import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { api, clearSessionToken, getSessionToken, saveSessionToken } from "../api/client";
import type { User } from "../types";

interface AuthValue {
  user: User | null;
  loading: boolean;
  login(email: string, password: string): Promise<User>;
  register(email: string, password: string): Promise<string>;
  logout(): void;
}

const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    if (!getSessionToken()) {
      setLoading(false);
      return () => {
        active = false;
      };
    }
    api
      .currentUser()
      .then((current) => {
        if (active) setUser(current);
      })
      .catch(() => {
        clearSessionToken();
        if (active) setUser(null);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    const onUnauthorized = () => {
      setUser(null);
      setLoading(false);
    };
    window.addEventListener("smart-hostel:unauthorized", onUnauthorized);
    return () => window.removeEventListener("smart-hostel:unauthorized", onUnauthorized);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const result = await api.login(email, password);
    saveSessionToken(result.access_token);
    try {
      const current = await api.currentUser();
      setUser(current);
      setLoading(false);
      return current;
    } catch (error) {
      clearSessionToken();
      throw error;
    }
  }, []);

  const register = useCallback(async (email: string, password: string) => {
    const result = await api.register(email, password);
    return result.message;
  }, []);

  const logout = useCallback(() => {
    clearSessionToken();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, loading, login, register, logout }),
    [user, loading, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
