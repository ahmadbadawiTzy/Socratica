"use client";

import { useEffect, useRef } from "react";
import Segmented from "@/components/ui/Segmented";
import { MODES } from "@/lib/modes";
import {
  FileText,
  Paperclip,
  Send,
  X,
} from "@/components/ui/Icons";

export default function Composer({
  mode,
  onModeChange,
  value,
  onChange,
  onSubmit,
  sending,
  file,
  onFile,
}: {
  mode: string;
  onModeChange: (mode: string) => void;
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  sending: boolean;
  file: File | null;
  onFile: (file: File | null) => void;
}) {
  const taRef = useRef<HTMLTextAreaElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const ta = taRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = `${Math.min(ta.scrollHeight, 120)}px`;
  }, [value]);

  const canSend = !sending && (value.trim().length > 0 || file !== null);

  return (
    <div className="shrink-0 hairline-t bg-bg/95 px-4 py-3 backdrop-blur-md sm:px-6">
      <div className="mx-auto w-full max-w-3xl">
        {/* Attached file chip */}
        {file && (
          <div className="mb-2 flex items-center gap-2 rounded-md border border-line bg-panel px-2.5 py-1.5 text-xs">
            <FileText className="h-3.5 w-3.5 shrink-0 text-muted" />
            <span className="truncate font-medium text-ink">{file.name}</span>
            <span className="mono-label text-[10px]">
              ({(file.size / 1024).toFixed(0)} KB)
            </span>
            <button
              type="button"
              className="ml-auto text-muted hover:text-danger"
              onClick={() => onFile(null)}
              aria-label="Remove attached file"
            >
              <X className="h-3 w-3" />
            </button>
          </div>
        )}

        {/* Input Container */}
        <div className="rounded-lg border border-line-strong bg-panel p-2 transition focus-within:border-ink">
          <input
            ref={fileRef}
            type="file"
            className="hidden"
            accept=".pdf,.docx,.pptx,.txt,.md,.py,.js,.ts,.java,.cpp,.c"
            onChange={(e) => onFile(e.target.files?.[0] ?? null)}
          />

          <div className="flex items-end gap-2">
            <button
              type="button"
              className="icon-btn text-muted hover:text-ink"
              onClick={() => fileRef.current?.click()}
              title="Attach document or solution"
              aria-label="Attach file"
            >
              <Paperclip className="h-4 w-4" />
            </button>

            <textarea
              ref={taRef}
              value={value}
              onChange={(e) => onChange(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  if (canSend) onSubmit();
                }
              }}
              placeholder={
                mode === "socratic"
                  ? "Where are you stuck, or what would you like guidance on?"
                  : mode === "evaluator"
                  ? "Paste your work or solution for feedback…"
                  : "Ask a question about your course materials…"
              }
              rows={1}
              className="max-h-[120px] min-h-[36px] flex-1 resize-none bg-transparent py-1 text-sm text-ink outline-none placeholder:text-muted"
            />

            <button
              type="button"
              className="icon-btn-primary disabled:opacity-40"
              onClick={onSubmit}
              disabled={!canSend}
              aria-label="Send message"
              title="Send (Enter)"
            >
              <Send className="h-3.5 w-3.5" />
            </button>
          </div>

          {/* Mode Switcher and Keyboard Shortcut Helper */}
          <div className="mt-2 flex flex-wrap items-center justify-between gap-2 hairline-t pt-2">
            <Segmented
              value={mode}
              onChange={onModeChange}
              options={MODES}
              ariaLabel="Response mode"
            />
            <span className="mono-label text-[10px] text-muted">
              Return to send
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
