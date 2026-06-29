import type { ReactNode } from "react";
import { ArrowUpRight, Check, Sparkles } from "lucide-react";
import { ReadoutLogo } from "@/components/brand/readout-logo";

export function AuthShell({ eyebrow, title, description, children, footer }: { eyebrow: string; title: string; description: string; children: ReactNode; footer?: ReactNode }) {
  return (
    <main className="auth-shell min-h-dvh lg:grid lg:grid-cols-[1.08fr_.92fr]">
      <section className="auth-story relative hidden overflow-hidden p-10 text-white lg:flex lg:flex-col xl:p-14">
        <div className="marketing-noise" aria-hidden="true"/>
        <ReadoutLogo className="relative z-10"/>
        <div className="auth-story__orbit" aria-hidden="true"><span/><span/><span/><span/></div>
        <div className="auth-signal-card" aria-hidden="true">
          <div className="flex items-center justify-between"><span className="auth-micro-label">LIVE SIGNAL</span><span className="flex items-center gap-1.5 text-[8px] text-white/70"><i className="size-1.5 rounded-full bg-[var(--marketing-mint)]"/>GROUNDED</span></div>
          <p className="mt-8 text-xs text-white/70">Revenue movement</p>
          <div className="mt-2 flex items-end justify-between"><strong className="text-3xl tracking-[-.05em]">+31.4%</strong><ArrowUpRight className="text-[var(--marketing-mint)]" size={19}/></div>
          <svg className="mt-7 w-full" viewBox="0 0 360 90" role="img" aria-label="Revenue trend rising"><path d="M2 78 C48 76 54 58 92 63 S154 55 178 48 S226 56 254 31 S306 22 358 8" fill="none" stroke="var(--marketing-mint)" strokeWidth="3"/><path d="M2 78 C48 76 54 58 92 63 S154 55 178 48 S226 56 254 31 S306 22 358 8 V90 H2Z" fill="url(#auth-chart-fill)"/><defs><linearGradient id="auth-chart-fill" x1="0" y1="0" x2="0" y2="1"><stop stopColor="var(--marketing-mint)" stopOpacity=".22"/><stop offset="1" stopColor="var(--marketing-mint)" stopOpacity="0"/></linearGradient></defs></svg>
          <div className="mt-5 flex items-center gap-2 border-t border-white/[.07] pt-4 text-[9px] text-white/70"><Check size={11} className="text-[var(--marketing-mint)]"/>Query plan validated against 12 columns</div>
        </div>
        <div className="relative z-10 mt-auto max-w-xl">
          <p className="auth-micro-label flex items-center gap-2 text-[var(--marketing-mint)]"><Sparkles size={12}/>THE SIGNAL ROOM</p>
          <p className="mt-5 text-[clamp(2.6rem,4vw,4.8rem)] font-semibold leading-[.92] tracking-[-.065em]">Ask the question.<br/><span className="font-serif font-normal italic text-[var(--marketing-mint)]">Keep the evidence.</span></p>
          <p className="mt-6 max-w-md text-sm leading-6 text-white/70">A focused workspace for turning business data into decisions you can explain.</p>
        </div>
        <p className="relative z-10 mt-10 text-[9px] font-semibold uppercase tracking-[.16em] text-white/70">Answers grounded in your data</p>
      </section>

      <section className="auth-form-side relative grid min-h-dvh place-items-center px-5 py-12 md:px-10">
        <div className="auth-form-glow" aria-hidden="true"/>
        <div className="relative w-full max-w-md">
          <ReadoutLogo className="mb-12 lg:hidden"/>
          <p className="auth-micro-label text-[var(--marketing-mint)]">{eyebrow}</p>
          <h1 className="mt-4 text-4xl font-semibold tracking-[-.055em] md:text-5xl">{title}</h1>
          <p className="mt-4 max-w-sm text-sm leading-6 text-white/70">{description}</p>
          <div className="mt-9">{children}</div>
          {footer && <div className="mt-7 border-t border-white/[.08] pt-6 text-center text-sm text-white/70">{footer}</div>}
        </div>
      </section>
    </main>
  );
}
