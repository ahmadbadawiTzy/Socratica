"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import Modal from "@/components/ui/Modal";
import {
  FileText,
  Plus,
  Trash,
  AlertTriangle,
} from "@/components/ui/Icons";

export default function DocumentManager({
  courseId,
  onClose,
}: {
  courseId: string;
  onClose: () => void;
}) {
  const [docs, setDocs] = useState<Awaited<ReturnType<typeof api.documents.list>>>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    api.documents.list(courseId).then(setDocs).catch(console.error);
  }, [courseId]);

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("document_name", file.name);
      const doc = await api.documents.upload(courseId, fd);
      setDocs((prev) => [...prev, doc]);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  async function handleDelete(docId: string) {
    try {
      await api.documents.delete(courseId, docId);
      setDocs((prev) => prev.filter((d) => d.id !== docId));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to delete document");
    }
  }

  const renderStatus = (status: string) => {
    if (status === "ready") {
      return <span className="text-xs text-muted">Ready</span>;
    }
    if (status === "failed") {
      return <span className="text-xs text-danger">Failed</span>;
    }
    return <span className="text-xs text-warn">Processing…</span>;
  };

  return (
    <Modal open title="Course Materials" onClose={onClose}>
      <div className="space-y-4">
        {/* Upload Trigger */}
        <div>
          <input
            ref={fileRef}
            type="file"
            className="hidden"
            accept=".pdf,.docx,.pptx,.txt,.md"
            onChange={handleUpload}
          />
          <button
            type="button"
            onClick={() => fileRef.current?.click()}
            disabled={uploading}
            className="flex w-full items-center justify-center gap-2 rounded-lg border border-dashed border-line-strong bg-panel-strong/40 p-4 text-xs font-medium text-ink transition hover:border-ink hover:bg-panel-strong disabled:opacity-50"
          >
            <Plus className="h-4 w-4 text-muted" />
            <span>{uploading ? "Ingesting file…" : "Upload syllabus or lecture materials"}</span>
          </button>
        </div>

        {error && (
          <div className="flex items-center gap-2 rounded-lg border border-danger/30 bg-danger/10 px-3 py-2 text-xs text-danger">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Documents List */}
        <div>
          <div className="mb-2 flex items-center justify-between">
            <span className="mono-label text-[10px]">Indexed Files</span>
            <span className="mono-label text-[10px] text-muted">
              {docs.length} total
            </span>
          </div>

          <div className="max-h-64 space-y-1.5 overflow-y-auto pr-0.5">
            {docs.length === 0 ? (
              <div className="py-6 text-center text-xs text-muted">
                No course materials added yet.
              </div>
            ) : (
              docs.map((doc) => (
                <div
                  key={doc.id}
                  className="flex items-center justify-between gap-3 rounded-md border border-line bg-panel p-2.5 transition hover:border-line-strong"
                >
                  <div className="flex min-w-0 items-center gap-2.5">
                    <FileText className="h-4 w-4 shrink-0 text-muted" />
                    <div className="min-w-0">
                      <p className="truncate text-xs font-medium text-ink">
                        {doc.document_name}
                      </p>
                      <div className="mt-0.5">{renderStatus(doc.ingestion_status)}</div>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => handleDelete(doc.id)}
                    className="text-muted hover:text-danger"
                    aria-label={`Delete ${doc.document_name}`}
                    title="Delete document"
                  >
                    <Trash className="h-3.5 w-3.5" />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </Modal>
  );
}
