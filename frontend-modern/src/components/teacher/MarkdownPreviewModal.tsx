"use client";

import { FileText, X } from "lucide-react";
import { ModalFrame } from "./ui";

export default function MarkdownPreviewModal({
  markdown,
  onClose,
}: {
  markdown: string;
  onClose: () => void;
}) {
  return (
    <ModalFrame maxWidth="max-w-3xl" className="flex max-h-[85vh] flex-col space-y-4">
      <div className="flex items-center justify-between border-b border-line pb-3">
        <h3 className="flex items-center gap-2 text-sm font-bold text-fg">
          <FileText className="h-4 w-4 text-brand-ink" /> Vista Previa del Trabajo Convertido a Markdown
        </h3>
        <button type="button" onClick={onClose} className="text-muted hover:text-fg">
          <X className="h-4 w-4" />
        </button>
      </div>
      <div className="flex-1 overflow-y-auto whitespace-pre-wrap rounded-control bg-canvas p-4 font-mono leading-relaxed text-fg">
        {markdown}
      </div>
    </ModalFrame>
  );
}
