"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/AuthContext";
import {
  api,
  Course,
  ConversationListItem,
  Conversation,
  Message,
  SendMessageResponse,
  HealthResponse,
} from "@/lib/api";
import Sidebar from "@/components/chat/Sidebar";
import Composer from "@/components/chat/Composer";
import MessageItem, { ThinkingBubble } from "@/components/chat/MessageItem";
import DocumentManager from "@/components/chat/DocumentManager";
import EmptyState from "@/components/chat/EmptyState";
import ServiceStatusBadge from "@/components/chat/ServiceStatusBadge";
import ThemeToggle from "@/components/layout/ThemeToggle";
import { Menu, BookOpen } from "@/components/ui/Icons";

export default function ChatPage() {
  const { user, logout, loading: authLoading } = useAuth();
  const router = useRouter();

  const [courses, setCourses] = useState<Course[]>([]);
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null);
  const [conversations, setConversations] = useState<ConversationListItem[]>([]);
  const [activeConv, setActiveConv] = useState<Conversation | null>(null);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [mode, setMode] = useState("qa");
  const [showDocs, setShowDocs] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const checkHealth = useCallback((probe = false) => {
    api.health
      .check(probe)
      .then(setHealth)
      .catch(() => {
        setHealth({
          status: "not_connected",
          service: "Socratica",
          langflow: { status: "not_connected" },
          gemini: { status: "unknown" },
          error: {
            code: "NOT_CONNECTED",
            message: "Langflow atau backend service tidak dapat diakses.",
          },
        });
      });
  }, []);

  // Poll health status regularly
  useEffect(() => {
    checkHealth(false);
    const interval = setInterval(() => checkHealth(false), 20000);
    return () => clearInterval(interval);
  }, [checkHealth]);

  // Redirect if not logged in
  useEffect(() => {
    if (!authLoading && !user) router.replace("/login");
  }, [authLoading, user, router]);

  // Load courses
  useEffect(() => {
    if (user) {
      api.courses
        .list()
        .then((data) => {
          setCourses(data);
          setSelectedCourse((prev) => prev ?? (data.length > 0 ? data[0] : null));
        })
        .catch(console.error);
    }
  }, [user]);

  // Load conversations
  useEffect(() => {
    if (user) api.conversations.list().then(setConversations).catch(console.error);
  }, [user]);

  // Scroll to bottom on new messages
  useEffect(() => {
    const reduce =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    messagesEndRef.current?.scrollIntoView({ behavior: reduce ? "auto" : "smooth" });
  }, [activeConv?.messages, sending]);

  const loadConversation = useCallback(
    async (convId: string) => {
      const conv = await api.conversations.get(convId);
      setActiveConv(conv);
      const course = courses.find((c) => c.id === conv.course_id);
      if (course) setSelectedCourse(course);
      setMode(conv.mode);
      setSidebarOpen(false);
    },
    [courses]
  );

  async function newConversation() {
    if (!selectedCourse) return;
    const conv = await api.conversations.create(selectedCourse.id, mode);
    setConversations((prev) => [conv, ...prev]);
    const full = await api.conversations.get(conv.id);
    setActiveConv(full);
    setSidebarOpen(false);
  }

  async function sendMessage() {
    if (!input.trim() && !uploadFile) return;
    if (!selectedCourse || sending) return;
    setSending(true);

    const content = uploadFile ? `[File: ${uploadFile.name}]\n\n${input}` : input;
    setInput("");
    setUploadFile(null);

    try {
      let conv = activeConv;
      if (!conv) {
        const created = await api.conversations.create(selectedCourse.id, mode);
        setConversations((prev) => [created, ...prev]);
        conv = await api.conversations.get(created.id);
        setActiveConv(conv);
      }

      const tempUserMsg: Message = {
        id: "temp-" + Date.now(),
        role: "user",
        content,
        citations: null,
        meta: null,
        created_at: new Date().toISOString(),
      };
      setActiveConv((prev) =>
        prev ? { ...prev, messages: [...prev.messages, tempUserMsg] } : prev
      );

      const res: SendMessageResponse = await api.conversations.sendMessage(
        conv.id,
        content,
        mode
      );

      const assistantMsg: Message = {
        id: res.assistant_message_id,
        role: "assistant",
        content: res.content,
        citations: res.citations,
        meta: {
          status: res.status,
          error_code: res.error_code,
          error_message: res.error_message,
          escalation_id: res.escalation_id,
        },
        created_at: new Date().toISOString(),
      };

      // Real health tracking from actual chat execution
      const degradedStatuses = [
        "quota_exceeded",
        "authentication_error",
        "rate_limited",
        "not_connected",
        "connection_timeout",
        "service_error",
      ];
      if (res.error_code || degradedStatuses.includes(res.status)) {
        const isNotConnected = res.status === "not_connected";
        setHealth({
          status: isNotConnected ? "not_connected" : "degraded",
          service: "Socratica",
          langflow: { status: isNotConnected ? "not_connected" : "connected" },
          gemini: { status: res.status },
          error: {
            code: res.error_code || res.status.toUpperCase(),
            message: res.error_message || res.content,
          },
        });
      } else {
        setHealth({
          status: "connected",
          service: "Socratica",
          langflow: { status: "connected" },
          gemini: { status: "connected" },
          error: null,
        });
      }

      setActiveConv((prev) => {
        if (!prev) return prev;
        const msgs = prev.messages.filter((m) => m.id !== tempUserMsg.id);
        const realUser: Message = { ...tempUserMsg, id: res.user_message_id };
        return { ...prev, messages: [...msgs, realUser, assistantMsg] };
      });

      setConversations((prev) =>
        prev.map((c) =>
          c.id === conv!.id ? { ...c, title: c.title || content.slice(0, 40) } : c
        )
      );
    } catch (err: unknown) {
      const errMsg: Message = {
        id: "err-" + Date.now(),
        role: "assistant",
        content:
          "⚠️ " + (err instanceof Error ? err.message : "Something went wrong. Please try again."),
        citations: null,
        meta: null,
        created_at: new Date().toISOString(),
      };
      setActiveConv((prev) =>
        prev ? { ...prev, messages: [...prev.messages, errMsg] } : prev
      );
    } finally {
      setSending(false);
    }
  }

  if (authLoading || !user) return null;

  const canManageDocs = user.system_role === "lecturer" || user.system_role === "ta";

  return (
    <div className="flex h-[100dvh] overflow-hidden bg-bg">
      <Sidebar
        user={user}
        courses={courses}
        selectedCourse={selectedCourse}
        onSelectCourse={(c) => {
          setSelectedCourse(c);
          setActiveConv(null);
        }}
        conversations={conversations}
        activeConvId={activeConv?.id ?? null}
        onSelectConv={loadConversation}
        onNewConv={newConversation}
        onOpenDocs={() => setShowDocs(true)}
        onLogout={() => {
          logout();
          router.push("/login");
        }}
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      {/* Main Workspace */}
      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        {/* Header Bar */}
        <header className="flex h-13 shrink-0 items-center justify-between hairline-b bg-bg/90 px-4 backdrop-blur-md">
          <div className="flex min-w-0 items-center gap-2.5">
            <button
              type="button"
              className="icon-btn md:hidden"
              onClick={() => setSidebarOpen(true)}
              aria-label="Open sidebar"
            >
              <Menu className="h-4 w-4" />
            </button>

            <div className="flex min-w-0 items-center gap-2 text-xs">
              <Link href="/" className="font-semibold text-ink hover:underline">
                Socratica
              </Link>
              {selectedCourse && (
                <>
                  <span className="text-muted">/</span>
                  <span className="truncate text-muted">
                    {selectedCourse.code} · {selectedCourse.name}
                  </span>
                </>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <ServiceStatusBadge health={health} onRefresh={() => checkHealth(true)} />
            {selectedCourse && canManageDocs && (
              <button
                type="button"
                onClick={() => setShowDocs(true)}
                className="btn btn-ghost hidden items-center gap-1.5 px-2.5 py-1 text-xs sm:inline-flex"
                title="Manage Course Materials"
              >
                <BookOpen className="h-3.5 w-3.5 text-muted" />
                <span>Materials</span>
              </button>
            )}
            <ThemeToggle />
          </div>
        </header>

        {/* Service Status Notification Banner (Condition-specific) */}
        {health && health.status !== "connected" && health.gemini.status !== "unknown" && (
          <div className="shrink-0 border-b border-border bg-bg px-4 py-2.5">
            <div className="mx-auto flex max-w-3xl items-center justify-between gap-3">
              <div className="text-xs">
                <span className="font-semibold">
                  {health.langflow.status === "not_connected"
                    ? "● AI Service Not Connected: "
                    : health.gemini.status === "quota_exceeded"
                    ? "● AI Service Quota Exceeded: "
                    : health.gemini.status === "authentication_error"
                    ? "● AI Authentication Error: "
                    : health.gemini.status === "connection_timeout" ||
                      health.langflow.status === "connection_timeout"
                    ? "● Connection Timeout: "
                    : health.gemini.status === "rate_limited"
                    ? "● Rate Limited: "
                    : "● Service Error: "}
                </span>
                <span className="text-muted">
                  {health.error?.message ||
                    (health.langflow.status === "not_connected"
                      ? "Langflow tidak dapat diakses."
                      : health.gemini.status === "quota_exceeded"
                      ? "Gemini API quota telah habis. Silakan gunakan kembali setelah quota tersedia atau konfigurasi credential Gemini yang valid."
                      : health.gemini.status === "authentication_error"
                      ? "Credential Gemini tidak valid atau ditolak."
                      : health.gemini.status === "rate_limited"
                      ? "Batas laju permintaan Gemini telah tercapai."
                      : "Service membutuhkan waktu terlalu lama untuk merespons.")}
                </span>
              </div>
              <button
                type="button"
                onClick={() => checkHealth(true)}
                className="btn btn-ghost shrink-0 px-2 py-0.5 text-[11px]"
              >
                Cek Ulang
              </button>
            </div>
          </div>
        )}

        {/* Message Viewport */}
        <main className="min-h-0 flex-1 overflow-y-auto px-4 sm:px-6">
          <div className="mx-auto w-full max-w-3xl py-6">
            {!activeConv ? (
              <EmptyState
                hasCourse={!!selectedCourse}
                hasCourses={courses.length > 0}
                onNew={newConversation}
                onSelectPrompt={(prompt, promptMode) => {
                  setInput(prompt);
                  if (promptMode) setMode(promptMode);
                }}
              />
            ) : (
              <>
                {activeConv.messages.map((msg) => (
                  <MessageItem key={msg.id} msg={msg} />
                ))}
                {sending && <ThinkingBubble />}
              </>
            )}
            <div ref={messagesEndRef} />
          </div>
        </main>

        {/* Composer */}
        {selectedCourse ? (
          <Composer
            mode={mode}
            onModeChange={setMode}
            value={input}
            onChange={setInput}
            onSubmit={sendMessage}
            sending={sending}
            file={uploadFile}
            onFile={setUploadFile}
          />
        ) : (
          <div className="shrink-0 hairline-t bg-panel px-4 py-3 text-center text-xs text-muted">
            Select a course in the sidebar to begin.
          </div>
        )}
      </div>

      {/* Document Manager Modal */}
      {showDocs && selectedCourse && (
        <DocumentManager
          courseId={selectedCourse.id}
          onClose={() => setShowDocs(false)}
        />
      )}
    </div>
  );
}
