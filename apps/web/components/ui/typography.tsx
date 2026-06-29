import type { HTMLAttributes } from "react"; import { cn } from "@/lib/utils";
export function Metric({className,...props}:HTMLAttributes<HTMLParagraphElement>){return <p className={cn("tabular text-4xl font-bold tracking-[-.02em] md:text-5xl",className)} {...props}/>}
export function Label({className,...props}:HTMLAttributes<HTMLParagraphElement>){return <p className={cn("text-xs font-semibold uppercase tracking-[.08em] text-[var(--ink-secondary)]",className)} {...props}/>}
