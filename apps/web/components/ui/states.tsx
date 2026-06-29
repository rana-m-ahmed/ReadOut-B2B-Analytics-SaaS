import type { ReactNode } from "react";
import { Card } from "./card";
import { Button } from "./button";

export function Badge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: "neutral" | "success" | "warning";
}) {
  return (
    <span
      className={`inline-flex rounded-[var(--radius-pill)] border px-3 py-1 text-xs font-semibold ${
        tone === "warning"
          ? "border-[rgba(255,184,92,.2)] bg-[rgba(255,184,92,.12)] text-[var(--warning)]"
          : tone === "success"
            ? "border-[rgba(70,214,160,.2)] bg-[rgba(70,214,160,.12)] text-[var(--success)]"
            : "border-[var(--hairline)] bg-[var(--surface-subtle)]"
      }`}
    >
      {children}
    </span>
  );
}

export function Skeleton({ className = "h-24" }: { className?: string }) {
  return (
    <div
      aria-hidden="true"
      className={`${className} animate-pulse rounded-[var(--radius-control)] bg-[var(--surface-subtle)]`}
    />
  );
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <Card className="grid place-items-center gap-3 p-10 text-center">
      <div aria-hidden="true" className="grid size-14 place-items-center rounded-full bg-[var(--surface-subtle)]">
        ✦
      </div>
      <h2 className="text-xl font-bold">{title}</h2>
      <p className="max-w-md text-[var(--ink-secondary)]">{description}</p>
      {action}
    </Card>
  );
}

export function ErrorState({ message, retry }: { message: string; retry?: () => void }) {
  return (
    <Card role="alert" className="p-6">
      <h2 className="font-bold">Something went sideways</h2>
      <p className="my-2 text-[var(--ink-secondary)]">{message}</p>
      {retry && (
        <Button variant="secondary" onClick={retry}>
          Try again
        </Button>
      )}
    </Card>
  );
}

export function LoadingState({ label = "Loading your workspace" }: { label?: string }) {
  return (
    <div
      role="status"
      aria-live="polite"
      className="grid min-h-48 place-items-center text-sm text-[var(--ink-secondary)]"
    >
      <span className="animate-pulse">{label}…</span>
    </div>
  );
}
