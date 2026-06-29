"use client";
import { useEffect, useId, useRef, type ReactNode } from "react";
import { X } from "lucide-react";
import { Button } from "./button";
const focusable =
  'button:not([disabled]),a[href],input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])';
export function Drawer({
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
  const panel = useRef<HTMLElement>(null);
  const prior = useRef<HTMLElement | null>(null);
  const titleId = useId();

  useEffect(() => {
    if (!open) return;
    prior.current = document.activeElement as HTMLElement;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const timer = requestAnimationFrame(() => {
      const target = panel.current?.querySelector<HTMLElement>(focusable) ?? panel.current;
      target?.focus();
    });
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onOpenChange(false);
        return;
      }
      if (event.key !== "Tab" || !panel.current) return;
      const nodes = [...panel.current.querySelectorAll<HTMLElement>(focusable)];
      if (!nodes.length) {
        event.preventDefault();
        panel.current.focus();
        return;
      }
      const first = nodes[0];
      const last = nodes[nodes.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", handleKey);
    return () => {
      cancelAnimationFrame(timer);
      document.removeEventListener("keydown", handleKey);
      document.body.style.overflow = previousOverflow;
      prior.current?.focus();
    };
  }, [open, onOpenChange]);

  if (!open) return null;
  return (
    <div
      className="fixed inset-0 z-50 bg-[color-mix(in_srgb,var(--ink)_25%,transparent)]"
      onMouseDown={() => onOpenChange(false)}
    >
      <aside
        ref={panel}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onMouseDown={(e) => e.stopPropagation()}
        className="absolute bottom-0 right-0 top-0 w-full max-w-lg overflow-auto bg-[var(--surface)] p-6 pb-[max(1.5rem,env(safe-area-inset-bottom))] shadow-[var(--shadow-lift)] md:rounded-l-[var(--radius-modal)]"
      >
        <h2 id={titleId} className="pr-12 text-xl font-bold">{title}</h2>
        <Button
          variant="ghost"
          size="icon"
          className="absolute right-3 top-3"
          onClick={() => onOpenChange(false)}
          aria-label="Close"
        >
          <X size={18} />
        </Button>
        <div className="mt-6">{children}</div>
      </aside>
    </div>
  );
}
