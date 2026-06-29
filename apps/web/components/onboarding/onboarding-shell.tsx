import Link from "next/link";
import type { ReactNode } from "react";

export function OnboardingShell({
  step,
  title,
  description,
  children,
}: {
  step: number;
  title: string;
  description: string;
  children: ReactNode;
}) {
  return (
    <main className="min-h-dvh p-5 md:p-10">
      <div className="mx-auto max-w-3xl">
        <header className="mx-auto flex w-full justify-between">
          <Link href="/" className="text-xl font-bold">
            readout<span className="text-[var(--accent)]">.</span>
          </Link>
          <span className="text-sm text-[var(--ink-secondary)]">Step {step} of 3</span>
        </header>

        <div className="mt-16">
          <div
            className="mb-10 flex gap-2"
            role="progressbar"
            aria-label="Onboarding progress"
            aria-valuemin={1}
            aria-valuemax={3}
            aria-valuenow={step}
          >
            {[1, 2, 3].map((x) => (
              <span
                key={x}
                aria-hidden="true"
                className={`h-1.5 flex-1 rounded-full ${x <= step ? "bg-[var(--accent)]" : "bg-[var(--hairline)]"}`}
              />
            ))}
          </div>

          <h1 className="text-balance text-4xl font-bold">{title}</h1>
          <p className="mt-3 max-w-xl text-pretty leading-7 text-[var(--ink-secondary)]">
            {description}
          </p>

          <div className="mt-9">{children}</div>
        </div>
      </div>
    </main>
  );
}
