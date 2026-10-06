"use client";

import { HealthResponse } from "@/lib/api";

interface ServiceStatusBadgeProps {
  health: HealthResponse | null;
  onRefresh?: () => void;
}

export default function ServiceStatusBadge({ health, onRefresh }: ServiceStatusBadgeProps) {
  if (!health) {
    return (
      <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-neutral-100 dark:bg-neutral-800 text-muted border border-transparent">
        <span className="w-2 h-2 rounded-full bg-neutral-400 animate-pulse" />
        <span>Checking AI Service...</span>
      </div>
    );
  }

  const { langflow, gemini, status } = health;

  let label = "AI Service Connected";
  let dotColor = "bg-emerald-500";
  let textColor = "text-emerald-700 dark:text-emerald-400";
  let bgColor = "bg-emerald-50 dark:bg-emerald-950/40 border-emerald-200 dark:border-emerald-800";

  if (langflow.status === "not_connected") {
    label = "AI Service Not Connected";
    dotColor = "bg-rose-500";
    textColor = "text-rose-700 dark:text-rose-400";
    bgColor = "bg-rose-50 dark:bg-rose-950/40 border-rose-200 dark:border-rose-800";
  } else if (langflow.status === "connection_timeout" || gemini.status === "connection_timeout") {
    label = "Connection Timeout";
    dotColor = "bg-amber-500";
    textColor = "text-amber-700 dark:text-amber-400";
    bgColor = "bg-amber-50 dark:bg-amber-950/40 border-amber-200 dark:border-amber-800";
  } else if (gemini.status === "authentication_error") {
    label = "AI Authentication Error";
    dotColor = "bg-rose-500";
    textColor = "text-rose-700 dark:text-rose-400";
    bgColor = "bg-rose-50 dark:bg-rose-950/40 border-rose-200 dark:border-rose-800";
  } else if (gemini.status === "quota_exceeded") {
    label = "AI Service Quota Exceeded";
    dotColor = "bg-amber-600";
    textColor = "text-amber-800 dark:text-amber-400";
    bgColor = "bg-amber-50 dark:bg-amber-950/40 border-amber-200 dark:border-amber-800";
  } else if (gemini.status === "rate_limited") {
    label = "Rate Limited";
    dotColor = "bg-amber-500";
    textColor = "text-amber-700 dark:text-amber-400";
    bgColor = "bg-amber-50 dark:bg-amber-950/40 border-amber-200 dark:border-amber-800";
  } else if (gemini.status === "service_error" || status === "service_error") {
    label = "Service Error";
    dotColor = "bg-rose-500";
    textColor = "text-rose-700 dark:text-rose-400";
    bgColor = "bg-rose-50 dark:bg-rose-950/40 border-rose-200 dark:border-rose-800";
  } else if (gemini.status === "unknown" || gemini.status === "unknown_error") {
    label = "AI Service Checking";
    dotColor = "bg-neutral-400";
    textColor = "text-neutral-600 dark:text-neutral-400";
    bgColor = "bg-neutral-100 dark:bg-neutral-800 border-neutral-200 dark:border-neutral-700";
  }

  return (
    <button
      type="button"
      onClick={onRefresh}
      title="Status service AI aktual (Klik untuk probe ulang)"
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium border transition-colors ${bgColor} ${textColor}`}
    >
      <span className={`w-2 h-2 rounded-full ${dotColor}`} />
      <span>{label}</span>
    </button>
  );
}
