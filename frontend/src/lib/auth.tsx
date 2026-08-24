// Auth context: holds the current user, hydrates from a stored JWT on load,
// and exposes login/signup/logout used across the app.
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { api, clearToken, getToken, setToken } from "./api";
import type { TokenResponse, User } from "./types";

type AuthState = {
  user: User | null;
  ready: boolean; // finished the initial token check
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string) => Promise<void>;
  loginWithToken: (token: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let active = true;
    const token = getToken();
    if (!token) {
      setReady(true);
      return;
    }
    api
      .get<User>("/auth/me")
      .then((u) => active && setUser(u))
      .catch(() => {
        clearToken();
        if (active) setUser(null);
      })
      .finally(() => active && setReady(true));
    return () => {
      active = false;
    };
  }, []);

  const authenticate = useCallback(async (path: string, email: string, password: string) => {
    const res = await api.post<TokenResponse>(path, { email, password }, { auth: false });
    setToken(res.access_token);
    setUser(res.user);
  }, []);

  const login = useCallback(
    (email: string, password: string) => authenticate("/auth/login", email, password),
    [authenticate],
  );
  const signup = useCallback(
    (email: string, password: string) => authenticate("/auth/signup", email, password),
    [authenticate],
  );
  // Adopt a token issued out-of-band (e.g. the Google OAuth redirect) and load
  // the corresponding user.
  const loginWithToken = useCallback(async (token: string) => {
    setToken(token);
    const u = await api.get<User>("/auth/me");
    setUser(u);
  }, []);
  const logout = useCallback(() => {
    clearToken();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, ready, login, signup, loginWithToken, logout }),
    [user, ready, login, signup, loginWithToken, logout],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
