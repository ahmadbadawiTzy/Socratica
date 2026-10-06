"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/AuthContext";
import { api, Course } from "@/lib/api";
import KnowledgeGraph from "@/components/3d/KnowledgeGraph";
import ThemeToggle from "@/components/layout/ThemeToggle";
import { ArrowRight } from "@/components/ui/Icons";

export default function HomePage() {
  const { user, loading: authLoading, logout } = useAuth();
  const router = useRouter();
  const [courses, setCourses] = useState<Course[] | null>(null);

  useEffect(() => {
    if (!user) return;
    let isCurrent = true;
    api.courses
      .list()
      .then((data) => {
        if (isCurrent) setCourses(data);
      })
      .catch((err) => {
        console.error("Error loading courses:", err);
        if (isCurrent) setCourses([]);
      });

    return () => {
      isCurrent = false;
    };
  }, [user]);

  const loadingCourses = Boolean(user && courses === null);
  const courseList = courses ?? [];

  return (
    <div className="min-h-screen bg-bg text-ink">
      {/* Editorial Top Navigation */}
      <header className="hairline-b sticky top-0 z-30 bg-bg/90 backdrop-blur-md">
        <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-6">
          <Link href="/" className="flex items-center gap-2">
            <span className="brand-dot" />
            <span className="text-[15px] font-semibold tracking-tight">Socratica</span>
          </Link>

          <div className="flex items-center gap-3">
            <ThemeToggle />
            {authLoading ? null : user ? (
              <div className="flex items-center gap-3">
                <Link
                  href="/chat"
                  className="btn btn-primary text-xs"
                >
                  Open Chat
                </Link>
                <button
                  type="button"
                  onClick={() => {
                    logout();
                    router.push("/login");
                  }}
                  className="btn btn-ghost text-xs hidden sm:inline-flex"
                >
                  Sign Out
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link href="/login" className="btn btn-ghost text-xs">
                  Sign In
                </Link>
                <Link href="/register" className="btn btn-primary text-xs">
                  Register
                </Link>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="mx-auto max-w-5xl px-6 py-12 lg:py-16">
        {user ? (
          /* ── Authenticated Student/Lecturer Dashboard ────────────────────────── */
          <div>
            <div className="grid grid-cols-1 items-center gap-8 lg:grid-cols-12 lg:gap-12">
              <div className="lg:col-span-7">
                <p className="mono-label">Dashboard</p>
                <h1 className="mt-2 text-2xl font-semibold tracking-tight sm:text-3xl">
                  Welcome back, {user.display_name}.
                </h1>
                <p className="mt-2 text-sm leading-relaxed text-muted">
                  Continue learning with your course materials or ask a new question.
                </p>

                <div className="mt-6 flex items-center gap-3">
                  <Link
                    href="/chat"
                    className="btn btn-primary inline-flex items-center gap-2 text-xs"
                  >
                    <span>Continue to Chat</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </Link>
                  <span className="mono-label text-xs">
                    Role: {user.system_role}
                  </span>
                </div>
              </div>

              {/* Minimal 3D Knowledge Accent */}
              <div className="hidden lg:col-span-5 lg:block">
                <div className="relative">
                  <KnowledgeGraph className="h-[280px]" />
                </div>
              </div>
            </div>

            {/* Courses Section */}
            <section className="mt-14 hairline-t pt-10">
              <div className="flex items-baseline justify-between">
                <div>
                  <h2 className="text-lg font-semibold tracking-tight">Your Courses</h2>
                  <p className="mt-0.5 text-xs text-muted">
                    Select a course to view materials and start a guided session.
                  </p>
                </div>
                <Link
                  href="/chat"
                  className="mono-label text-xs text-muted hover:text-ink"
                >
                  All sessions →
                </Link>
              </div>

              {loadingCourses ? (
                <div className="mt-6 py-8 text-center mono-label text-xs">
                  Loading courses…
                </div>
              ) : courseList.length > 0 ? (
                <div className="mt-6 divide-y divide-line">
                  {courseList.map((course) => (
                    <div
                      key={course.id}
                      onClick={() => router.push("/chat")}
                      className="group flex cursor-pointer items-center justify-between py-4 transition hover:opacity-80"
                    >
                      <div className="min-w-0 pr-4">
                        <div className="flex items-center gap-2.5">
                          <span className="mono-label text-[11px] font-semibold text-accent">
                            {course.code}
                          </span>
                          <h3 className="truncate text-sm font-medium text-ink group-hover:text-accent">
                            {course.name}
                          </h3>
                        </div>
                        {course.description && (
                          <p className="mt-1 line-clamp-1 text-xs text-muted">
                            {course.description}
                          </p>
                        )}
                      </div>

                      <div className="flex shrink-0 items-center gap-4">
                        <span className="mono-label text-xs">
                          {course.document_count ?? 0} docs
                        </span>
                        <ArrowRight className="h-4 w-4 text-muted transition group-hover:translate-x-0.5 group-hover:text-ink" />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="mt-6 py-10 text-center">
                  <p className="text-sm font-medium">No courses enrolled</p>
                  <p className="mt-1 text-xs text-muted">
                    Contact your lecturer or teaching assistant to join your class workspace.
                  </p>
                </div>
              )}
            </section>
          </div>
        ) : (
          /* ── Public Visitor / Guest View ─────────────────────────────────────── */
          <div>
            <div className="grid grid-cols-1 items-center gap-8 lg:grid-cols-12 lg:gap-12">
              <div className="lg:col-span-7">
                <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl lg:leading-tight">
                  Academic inquiry grounded strictly in course materials.
                </h1>

                <p className="mt-4 text-sm leading-relaxed text-muted sm:text-base">
                  Socratica guides students through academic concepts step-by-step using
                  the Socratic method, verified citations, and rubrics.
                </p>

                <div className="mt-8 flex items-center gap-3">
                  <Link
                    href="/login"
                    className="btn btn-primary inline-flex items-center gap-2 text-xs"
                  >
                    <span>Launch Workspace</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </Link>
                  <Link href="/register" className="btn text-xs">
                    Register
                  </Link>
                </div>
              </div>

              {/* Minimal 3D Knowledge Accent */}
              <div className="lg:col-span-5">
                <KnowledgeGraph className="h-[300px] sm:h-[340px]" />
              </div>
            </div>

            {/* Editorial 3-Column Method Breakdown */}
            <section className="mt-16 hairline-t pt-12">
              <div className="grid grid-cols-1 gap-8 md:grid-cols-3 md:gap-10">
                <div>
                  <span className="mono-label text-xs">01</span>
                  <h2 className="mt-2 text-base font-semibold">Direct Q&amp;A</h2>
                  <p className="mt-1.5 text-xs leading-relaxed text-muted">
                    Receive clear, verified answers citing exact lecture slides, syllabus guidelines, and course readings.
                  </p>
                </div>

                <div>
                  <span className="mono-label text-xs">02</span>
                  <h2 className="mt-2 text-base font-semibold">Socratic Inquiry</h2>
                  <p className="mt-1.5 text-xs leading-relaxed text-muted">
                    Learn without spoilers. Socratica diagnoses misconceptions and asks guiding questions so you discover solutions on your own.
                  </p>
                </div>

                <div>
                  <span className="mono-label text-xs">03</span>
                  <h2 className="mt-2 text-base font-semibold">Work Evaluator</h2>
                  <p className="mt-1.5 text-xs leading-relaxed text-muted">
                    Submit assignments or code to receive formative rubric evaluations, edge case feedback, and targeted improvements.
                  </p>
                </div>
              </div>
            </section>
          </div>
        )}
      </main>

      {/* Editorial Footer */}
      <footer className="hairline-t mt-16 py-8 text-xs text-muted">
        <div className="mx-auto flex max-w-5xl flex-col items-center justify-between gap-3 px-6 sm:flex-row">
          <div className="flex items-center gap-2">
            <span className="brand-dot" />
            <span className="font-medium text-ink">Socratica</span>
            <span>— Socratic Teaching Assistant</span>
          </div>
          <p className="mono-label text-[11px]">
            Grounded Academic AI
          </p>
        </div>
      </footer>
    </div>
  );
}
