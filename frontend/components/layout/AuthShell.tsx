"use client";

import Link from "next/link";
import ThemeToggle from "@/components/layout/ThemeToggle";

export default function AuthShell({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string;
  subtitle: string;
  children: React.ReactNode;
  footer: React.ReactNode;
  note?: string;
}) {
  return (
    <div className="flex min-h-[100dvh] flex-col items-center justify-center bg-bg px-4 py-12 text-ink">
      <div className="w-full max-w-sm">
        {/* Brand Bar */}
        <div className="mb-6 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <span className="brand-dot" />
            <span className="text-[15px] font-semibold tracking-tight">Socratica</span>
          </Link>
          <ThemeToggle />
        </div>

        {/* Card */}
        <div className="rounded-xl border border-line-strong bg-panel p-6 shadow-xs">
          <h1 className="text-xl font-semibold tracking-tight">
            {title}
          </h1>
          <p className="mt-1.5 text-xs leading-relaxed text-muted">{subtitle}</p>

          <div className="mt-6">{children}</div>
        </div>

        {/* Footer */}
        <div className="mt-4 text-center text-xs text-muted">{footer}</div>
      </div>
    </div>
  );
}
