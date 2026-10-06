"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/AuthContext";
import Link from "next/link";
import AuthShell from "@/components/layout/AuthShell";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      router.replace("/chat");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  const fillDemo = (demoEmail: string, demoPass: string) => {
    setEmail(demoEmail);
    setPassword(demoPass);
    setError(null);
  };

  return (
    <AuthShell
      title="Sign In"
      subtitle="Access your academic courses and guided assistant."
      footer={
        <>
          Don&apos;t have an account?{" "}
          <Link href="/register" className="font-medium text-ink underline underline-offset-4 hover:text-accent">
            Register
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="email" className="mb-1 block text-xs font-medium text-ink">
            Academic Email
          </label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
            className="input"
            placeholder="student@univ.ac.id"
          />
        </div>

        <div>
          <label htmlFor="password" className="mb-1 block text-xs font-medium text-ink">
            Password
          </label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
            className="input"
            placeholder="••••••••"
          />
        </div>

        {error && (
          <div className="rounded-lg border border-danger/30 bg-danger/10 px-3 py-2 text-xs text-danger">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="btn btn-primary w-full justify-center text-xs"
        >
          {loading ? "Signing In…" : "Sign In"}
        </button>

        {/* Demo Fast-Fill presets */}
        <div className="hairline-t pt-3">
          <p className="mono-label text-[10px] text-muted mb-2">
            Demo Credentials
          </p>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => fillDemo("student_11151e@univ.ac.id", "Password123!")}
              className="flex-1 rounded border border-line bg-panel-strong px-2 py-1 text-xs text-muted transition hover:border-line-strong hover:text-ink"
            >
              Student
            </button>
            <button
              type="button"
              onClick={() => fillDemo("lecturer_11151e@univ.ac.id", "Password123!")}
              className="flex-1 rounded border border-line bg-panel-strong px-2 py-1 text-xs text-muted transition hover:border-line-strong hover:text-ink"
            >
              Lecturer
            </button>
          </div>
        </div>
      </form>
    </AuthShell>
  );
}
