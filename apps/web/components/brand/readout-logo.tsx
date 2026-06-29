import Link from "next/link";
import { cn } from "@/lib/utils";

export function ReadoutMark({ className }: { className?: string }) {
  return <span aria-hidden="true" className={cn("readout-logo-mark", className)}>r<span>.</span></span>;
}

export function ReadoutLogo({ href = "/", compact = false, className }: { href?: string; compact?: boolean; className?: string }) {
  return (
    <Link href={href} className={cn("readout-logo", className)} aria-label="Readout">
      <ReadoutMark />
      {!compact && <span className="readout-logo__name">readout</span>}
    </Link>
  );
}
