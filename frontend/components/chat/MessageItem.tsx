"use client";

import { useState } from "react";
import type { Citation, Message } from "@/lib/api";
import Markdown from "@/components/ui/Markdown";
import { Copy, Check, AlertTriangle } from "@/components/ui/Icons";

function CitationPill({ citation }: { citation: Citation }) {
  const parts = [
    citation.document_name,
    citation.page ? `p. ${citation.page}` : null,
    citation.section || null,
  ].filter(Boolean);

  return (
    <span
      className="inline-flex items-center rounded border border-line bg-panel-strong px-1.5 py-0.5 font-mono text-[10.5px] text-muted"
      title={parts.join(" · ")}
    >
      {parts.join(" · ")}
    </span>
  );
}

export default function MessageItem({ msg }: { msg: Message }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (!navigator.clipboard) return;
    navigator.clipboard.writeText(msg.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (msg.role === "user") {
    return (
      <div className="mb-6 flex justify-end">
        <div className="max-w-[85%] sm:max-w-[75%]">
          <div className="rounded-lg border border-line-strong bg-panel px-3.5 py-2.5 text-[13.5px] leading-relaxed text-ink shadow-2xs">
            <div className="whitespace-pre-wrap break-words">{msg.content}</div>
          </div>
        </div>
      </div>
    );
  }

  const isError = msg.id.startsWith("err-");

  return (
    <div className="group mb-6 flex justify-start">
      <div className="w-full max-w-full">
        {/* Assistant Header */}
        <div className="mb-1 flex items-center justify-between text-xs text-muted">
          <span className="font-semibold text-ink">Socratica</span>
          {!isError && (
            <button
              type="button"
              onClick={handleCopy}
              className="opacity-0 transition group-hover:opacity-100 hover:text-ink"
              title="Copy response"
              aria-label="Copy response"
            >
              {copied ? (
                <span className="flex items-center gap-1 text-success text-[11px]">
                  <Check className="h-3 w-3" />
                  <span>Copied</span>
                </span>
              ) : (
                <Copy className="h-3.5 w-3.5" />
              )}
            </button>
          )}
        </div>

        {isError ? (
          <div className="flex items-start gap-2 rounded-lg border border-danger/30 bg-danger/10 px-3.5 py-2.5 text-xs text-danger">
            <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
            <span className="whitespace-pre-wrap">{msg.content.replace(/^⚠️\s*/, "")}</span>
          </div>
        ) : (
          <div className="py-1">
            <Markdown text={msg.content} />

            {/* Citations List - Compact & Understated */}
            {msg.citations && msg.citations.length > 0 && (
              <div className="mt-3 flex flex-wrap items-center gap-1.5 pt-2 hairline-t">
                <span className="mono-label text-[10px]">Sources:</span>
                {msg.citations.map((c, i) => (
                  <CitationPill key={i} citation={c} />
                ))}
              </div>
            )}

            {/* Escalation notice */}
            {msg.meta?.status === "escalated" && (
              <div className="mt-3 rounded border border-warn/30 bg-warn/10 px-3 py-1.5 text-xs text-warn">
                <span>Forwarded to instructor for review</span>
                {Boolean(msg.meta?.escalation_id) && (
                  <span className="ml-2 font-mono text-[10px] opacity-80">
                    Ref: {String(msg.meta?.escalation_id).slice(0, 8)}
                  </span>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export function ThinkingBubble() {
  return (
    <div className="mb-6 flex justify-start" role="status" aria-live="polite">
      <div className="flex items-center gap-2 py-1 text-xs text-muted">
        <span className="brand-dot animate-pulse-dot" />
        <span className="mono-label text-xs">Formulating response…</span>
      </div>
    </div>
  );
}
