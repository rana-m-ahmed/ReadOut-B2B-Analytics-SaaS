import * as React from "react"
import { cn } from "@/lib/utils"

export function Metric({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "text-[40px] md:text-[56px] font-[700] tracking-[-0.02em] tabular-nums text-[var(--ink)]",
        className
      )}
      {...props}
    />
  )
}

export function LabelText({ className, ...props }: React.HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={cn(
        "text-[11px] md:text-[12px] font-[600] uppercase tracking-[0.08em] text-[var(--ink-secondary)] tabular-nums",
        className
      )}
      {...props}
    />
  )
}
