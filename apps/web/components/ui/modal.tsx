"use client";
import { useEffect, useRef, type ReactNode } from "react";
import { X } from "lucide-react";
import { Button } from "./button";
const focusable =
  'button:not([disabled]),a[href],input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])';
export function Modal({
  open,
  onOpenChange,
  title,
  children,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  title: string;
  children: ReactNode;
}) {
  const panel = useRef<HTMLElement>(null),
    prior = useRef<HTMLElement | null>(null);
  useEffect(() => {
    if (!open) return;
    prior.current = document.activeElement as HTMLElement;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const timer = requestAnimationFrame(() =>
      panel.current?.querySelector<HTMLElement>(focusable)?.focus(),
    );
    function key(e: KeyboardEvent) {
      if (e.key === "Escape") onOpenChange(false);
      if (e.key === "Tab" && panel.current) {
        const nodes = [
          ...panel.current.querySelectorAll<HTMLElement>(focusable),
        ];
        if (!nodes.length) return;
        const first = nodes[0],
          last = nodes[nodes.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    }
    document.addEventListener("keydown", key);
    return () => {
      cancelAnimationFrame(timer);
      document.removeEventListener("keydown", key);
      document.body.style.overflow = previousOverflow;
      prior.current?.focus();
    };
  }, [open, onOpenChange]);
  if (!open) return null;
  return (
    <div
      role="presentation"
      onMouseDown={() => onOpenChange(false)}
      className="fixed inset-0 z-50 grid place-items-end bg-[color-mix(in_srgb,var(--ink)_28%,transparent)] backdrop-blur-sm sm:place-items-center sm:p-4"
    >
      <section
        ref={panel}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        onMouseDown={(e) => e.stopPropagation()}
        className="relative max-h-[100dvh] w-full overflow-auto rounded-t-[var(--radius-modal)] bg-[var(--surface)] p-6 pb-[max(1.5rem,env(safe-area-inset-bottom))] shadow-[var(--shadow-lift)] sm:max-w-xl sm:rounded-[var(--radius-modal)]"
      >
        <h2 id="modal-title" className="pr-12 text-xl font-bold">
          {title}
        </h2>
        <div className="mt-5">{children}</div>
        <Button
          variant="ghost"
          size="icon"
          className="absolute right-3 top-3"
          aria-label="Close"
          onClick={() => onOpenChange(false)}
        >
          <X size={18} />
        </Button>
      </section>
    </div>
  );
}
