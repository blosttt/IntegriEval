"use client";

import { FileText, X } from "lucide-react";
import { useDashboard } from "./DashboardContext";
import { Button, ModalFrame } from "./ui";

export default function MarkdownPreviewModal() {
  const { previewMdModal, setPreviewMdModal, reportMarkdown } = useDashboard();
  if (!previewMdModal) return null;
  return (
    <ModalFrame maxWidth="max-w-3xl" className="flex max-h-[85vh] flex-col space-y-4">
      <div className="flex items-center justify-between border-b border-line pb-3">
        <h3 className="flex items-center gap-2 text-sm font-bold text-fg">
          <FileText className="h-4 w-4 text-brand-ink" /> Vista Previa del Trabajo Convertido a Markdown
        </h3>
        <Button variant="muted" onClick={() => setPreviewMdModal(false)}>
          <X className="h-4 w-4" />
        </Button>
      </div>
      <div className="flex-1 overflow-y-auto rounded-control bg-raised p-4 font-mono leading-relaxed whitespace-pre-wrap text-fg">
        {reportMarkdown}
      </div>
    </ModalFrame>
  );
}
