"use client";

import { useState } from "react";
import Segmented from "@/components/ui/Segmented";
import { MODES } from "@/lib/modes";
import { Plus } from "@/components/ui/Icons";

const MODE_DETAILS: Record<string, { desc: string; samples: string[] }> = {
  qa: {
    desc: "Direct answers citing course slides, syllabus, and readings.",
    samples: [
      "What are the main prerequisites for this subject?",
      "Summarize the key concepts covered in the latest lecture.",
    ],
  },
  socratic: {
    desc: "Guided questions to help you diagnose and solve problems step-by-step.",
    samples: [
      "I'm confused about this concept, can you help me break it down?",
      "How should I start approaching this problem?",
    ],
  },
  evaluator: {
    desc: "Formative rubric critique on your reasoning, drafts, or code solutions.",
    samples: [
      "Evaluate my solution reasoning against course requirements.",
      "Check this code implementation for edge cases and time complexity.",
    ],
  },
};

export default function EmptyState({
  hasCourse,
  hasCourses,
  onNew,
  onSelectPrompt,
}: {
  hasCourse: boolean;
  hasCourses: boolean;
  onNew: () => void;
  onSelectPrompt?: (prompt: string, mode?: string) => void;
}) {
  const [selectedMode, setSelectedMode] = useState<string>("qa");
  const details = MODE_DETAILS[selectedMode] || MODE_DETAILS.qa;

  return (
    <div className="flex min-h-[55vh] flex-col items-center justify-center py-10 text-center">
      <div className="max-w-md">
        <h2 className="text-xl font-semibold tracking-tight sm:text-2xl">
          What would you like to explore?
        </h2>
        <p className="mt-2 text-xs leading-relaxed text-muted">
          Ask an academic question or select an inquiry mode grounded in your course documents.
        </p>

        {/* Minimal Mode Selector */}
        <div className="mt-6 flex flex-col items-center gap-2">
          <Segmented
            value={selectedMode}
            onChange={setSelectedMode}
            options={MODES}
            ariaLabel="Learning mode"
          />
          <p className="min-h-[1.5rem] text-xs text-muted">
            {details.desc}
          </p>
        </div>

        {/* Starter Prompts - Quiet list */}
        {onSelectPrompt && (
          <div className="mt-6 flex flex-col gap-1.5 text-left">
            {details.samples.map((sample, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => onSelectPrompt(sample, selectedMode)}
                className="group flex items-center justify-between rounded-lg border border-line bg-panel p-2.5 text-xs text-muted transition hover:border-line-strong hover:bg-panel-strong hover:text-ink"
              >
                <span className="truncate pr-2">{sample}</span>
                <span className="mono-label text-[10px] opacity-0 transition group-hover:opacity-100">
                  Ask →
                </span>
              </button>
            ))}
          </div>
        )}

        {hasCourse ? (
          <div className="mt-6">
            <button
              type="button"
              onClick={onNew}
              className="btn btn-primary inline-flex items-center gap-1.5 text-xs"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>Start New Session</span>
            </button>
          </div>
        ) : (
          <div className="mt-6 text-xs text-muted">
            {!hasCourses
              ? "No courses enrolled yet. Please contact your instructor."
              : "Select a course from the sidebar to begin."}
          </div>
        )}
      </div>
    </div>
  );
}
