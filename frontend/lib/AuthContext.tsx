"use client";
import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { api, UserProfile, clearTokens, getAccessToken } from "@/lib/api";

interface AuthContextValue {
  user: UserProfile | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, displayName: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadUser() {
      if (getAccessToken()) {
        try {
          setUser(await api.auth.me());
        } catch {
          clearTokens();
        }
      }
      setLoading(false);
    }
    void loadUser();
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const profile = await api.auth.login(email, password);
    setUser(profile);
  }, []);

  const register = useCallback(async (email: string, password: string, displayName: string) => {
    await api.auth.register(email, password, displayName);
    await login(email, password);
  }, [login]);

  const logout = useCallback(() => {
    api.auth.logout();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
