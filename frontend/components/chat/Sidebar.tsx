"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import type { Course, ConversationListItem, UserProfile } from "@/lib/api";
import { modeLabel } from "@/lib/modes";
import { cn } from "@/lib/cn";
import {
  ChevronDown,
  LogOut,
  Plus,
  X,
  Compass,
} from "@/components/ui/Icons";

export default function Sidebar({
  user,
  courses,
  selectedCourse,
  onSelectCourse,
  conversations,
  activeConvId,
  onSelectConv,
  onNewConv,
  onOpenDocs,
  onLogout,
  open,
  onClose,
}: {
  user: UserProfile;
  courses: Course[];
  selectedCourse: Course | null;
  onSelectCourse: (course: Course | null) => void;
  conversations: ConversationListItem[];
  activeConvId: string | null;
  onSelectConv: (id: string) => void;
  onNewConv: () => void;
  onOpenDocs: () => void;
  onLogout: () => void;
  open: boolean;
  onClose: () => void;
}) {
  const [searchQuery, setSearchQuery] = useState("");
  const canManageDocs = user.system_role === "lecturer" || user.system_role === "ta";

  const filteredConversations = useMemo(() => {
    let list = selectedCourse
      ? conversations.filter((c) => c.course_id === selectedCourse.id)
      : conversations;

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      list = list.filter((c) => (c.title || "").toLowerCase().includes(q));
    }
    return list;
  }, [conversations, selectedCourse, searchQuery]);

  return (
    <>
      {open && (
        <div
          className="fixed inset-0 z-30 bg-black/40 backdrop-blur-xs md:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex w-[260px] flex-col border-r border-line bg-panel transition-transform duration-200",
          "md:static md:z-auto md:translate-x-0 md:transition-none",
          open ? "translate-x-0" : "-translate-x-full"
        )}
        aria-label="Workspace Sidebar"
      >
        {/* Brand Header */}
        <div className="flex items-center justify-between px-4 py-3.5 hairline-b">
          <Link href="/" className="flex items-center gap-2">
            <span className="brand-dot" />
            <span className="text-sm font-semibold tracking-tight text-ink">
              Socratica
            </span>
          </Link>
          <button
            type="button"
            className="icon-btn md:hidden"
            onClick={onClose}
            aria-label="Close sidebar"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Course Selection */}
        <div className="px-3 py-3 hairline-b space-y-2">
          <div className="relative">
            <select
              id="sidebar-course"
              value={selectedCourse?.id || ""}
              onChange={(e) => {
                const found = courses.find((c) => c.id === e.target.value) || null;
                onSelectCourse(found);
              }}
              className="input appearance-none pr-8 text-xs font-medium"
            >
              <option value="">Select course…</option>
              {courses.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.code} — {c.name}
                </option>
              ))}
            </select>
            <ChevronDown className="pointer-events-none absolute right-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted" />
          </div>

          {selectedCourse && (
            <div className="flex items-center gap-1.5">
              <button
                type="button"
                className="btn btn-primary w-full justify-center text-xs py-1.5"
                onClick={onNewConv}
              >
                <Plus className="h-3.5 w-3.5" />
                <span>New Chat</span>
              </button>
              {canManageDocs && (
                <button
                  type="button"
                  className="btn btn-ghost text-xs py-1.5 px-2 shrink-0"
                  onClick={onOpenDocs}
                  title="Manage Course Materials"
                >
                  Materials
                </button>
              )}
            </div>
          )}
        </div>

        {/* Sessions List */}
        <div className="flex min-h-0 flex-1 flex-col px-3 py-3">
          <div className="mb-2 flex items-center justify-between px-1">
            <span className="mono-label text-[10px]">History</span>
            {filteredConversations.length > 0 && (
              <span className="mono-label text-[10px] text-muted">
                {filteredConversations.length}
              </span>
            )}
          </div>

          {conversations.length > 4 && (
            <div className="mb-2">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search history…"
                className="w-full rounded border border-line bg-panel-strong px-2 py-1 text-xs placeholder:text-muted focus:border-ink focus:outline-none"
              />
            </div>
          )}

          <div className="flex-1 overflow-y-auto pr-0.5 space-y-0.5">
            {filteredConversations.length === 0 ? (
              <div className="py-6 text-center text-xs text-muted">
                {selectedCourse
                  ? "No sessions yet."
                  : "Select a course to view history."}
              </div>
            ) : (
              filteredConversations.map((conv) => {
                const active = conv.id === activeConvId;
                return (
                  <button
                    key={conv.id}
                    type="button"
                    onClick={() => onSelectConv(conv.id)}
                    className={cn(
                      "flex w-full items-center justify-between rounded-md px-2.5 py-1.5 text-left text-xs transition",
                      active
                        ? "bg-panel-strong font-medium text-ink border border-line"
                        : "text-muted hover:bg-panel-strong hover:text-ink"
                    )}
                  >
                    <span className="truncate pr-2">
                      {conv.title || "Untitled Session"}
                    </span>
                    <span className="mono-label text-[9px] text-muted shrink-0">
                      {modeLabel(conv.mode)}
                    </span>
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* Footer Navigation & Sign Out */}
        <div className="hairline-t p-3 space-y-1">
          <Link
            href="/"
            className="flex items-center gap-2 rounded-md px-2 py-1.5 text-xs text-muted transition hover:bg-panel-strong hover:text-ink"
          >
            <Compass className="h-3.5 w-3.5" />
            <span>Dashboard</span>
          </Link>
          <div className="flex items-center justify-between px-2 py-1.5 text-xs text-muted">
            <span className="truncate font-medium text-ink">{user.display_name}</span>
            <button
              type="button"
              onClick={onLogout}
              className="text-muted hover:text-danger"
              title="Sign Out"
              aria-label="Sign out"
            >
              <LogOut className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}
