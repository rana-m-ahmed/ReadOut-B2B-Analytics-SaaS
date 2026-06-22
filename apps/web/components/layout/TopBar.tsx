"use client";
import { useCurrentUser } from '../../lib/auth/useCurrentUser';

export function TopBar() {
  const { isAnonymous } = useCurrentUser();

  return (
    <header className="hidden md:flex h-16 mt-4 mr-4 mb-4 ml-0 items-center justify-between px-6 bg-[var(--surface)] rounded-[var(--radius-card)] shadow-[var(--shadow-dock)] z-30 shrink-0">
      <div className="flex items-center gap-4">
        <div className="font-medium text-[var(--ink)]">Demo Dataset</div>
      </div>
      <div className="flex items-center gap-4">
        {isAnonymous && (
          <span className="text-[11px] uppercase font-semibold text-[var(--warning)] bg-[var(--warning)]/10 px-2 py-1 rounded-[var(--radius-pill)] tracking-widest">
            Demo Session
          </span>
        )}
        <div className="w-8 h-8 rounded-full bg-[var(--surface-subtle)] border border-[var(--hairline)]" />
      </div>
    </header>
  );
}
