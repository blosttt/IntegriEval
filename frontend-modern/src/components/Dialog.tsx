"use client";

import { useEffect, useRef, type ReactNode } from "react";
import { X } from "lucide-react";
import { IconButton, cx } from "./ui";

export default function Dialog({
  title,
  children,
  onClose,
  wide = false,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
  wide?: boolean;
}) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const previous = document.activeElement as HTMLElement;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    ref.current?.querySelector<HTMLElement>("button,input,select,textarea")?.focus();
    const handler = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
      }
      if (event.key === "Tab") {
        const items = Array.from(
          ref.current?.querySelectorAll<HTMLElement>(
            "button:not(:disabled),input:not(:disabled),select:not(:disabled),textarea:not(:disabled),a[href]",
          ) || [],
        );
        const first = items[0];
        const last = items[items.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last?.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first?.focus();
        }
      }
    };
    document.addEventListener("keydown", handler);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", handler);
      previous?.focus();
    };
  }, []);

  return (
    <div
      className="fixed inset-0 z-[9999] flex items-center justify-center bg-[#000b] p-5 backdrop-blur-[5px]"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className={cx(
          "max-h-[calc(100dvh-40px)] w-full overflow-auto rounded-[14px] border border-line bg-surface font-ui text-fg shadow-[0_24px_100px_#0008]",
          wide ? "max-w-[860px]" : "max-w-[590px]",
        )}
        role="dialog"
        aria-modal="true"
        aria-labelledby="ie-dialog-title"
        ref={ref}
      >
        <header className="flex items-center justify-between gap-[18px] border-b border-line px-6 py-[19px]">
          <h2 id="ie-dialog-title" className="text-[17px] text-fg">
            {title}
          </h2>
          <IconButton onClick={onClose} aria-label="Cerrar modal">
            <X size={19} />
          </IconButton>
        </header>
        {children}
      </div>
    </div>
  );
}
