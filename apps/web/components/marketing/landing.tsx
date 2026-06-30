"use client";

import Link from "next/link";
import {
  ArrowDown,
  ArrowRight,
  Asterisk,
  Braces,
  Check,
  FileSpreadsheet,
  Fingerprint,
  LineChart,
  Search,
  ShieldCheck,
  Sparkles,
  WandSparkles,
  Zap,
} from "lucide-react";
import { ProductPreview } from "@/components/marketing/product-preview";
import { ReadoutLogo } from "@/components/brand/readout-logo";

const capabilities = [
  {
    icon: Search,
    index: "01",
    label: "Ask",
    title: "Start with the question, not the query language.",
    copy: "Write what you need to know in plain English. Readout resolves the metric and dimension against the columns that actually exist.",
    accent: "violet",
  },
  {
    icon: LineChart,
    index: "02",
    label: "See",
    title: "The answer arrives in the shape that explains it best.",
    copy: "A visual, a direct summary, and the next useful question appear together so the room can move from finding to deciding.",
    accent: "cyan",
  },
  {
    icon: Zap,
    index: "03",
    label: "Notice",
    title: "Important movement stops hiding in averages.",
    copy: "Readout scans for unusual changes and ranks useful discoveries, giving operators a calm, prioritized signal feed.",
    accent: "amber",
  },
];

const marquee = ["PLAIN ENGLISH", "SCHEMA GROUNDED", "VISUAL ANSWERS", "ANOMALY SCANS", "VISIBLE REASONING"];

function SignalOrbital() {
  return (
    <div className="signal-orbital" aria-hidden="true">
      <div className="signal-orbital__ring signal-orbital__ring--outer" />
      <div className="signal-orbital__ring signal-orbital__ring--mid" />
      <div className="signal-orbital__ring signal-orbital__ring--inner" />
      <div className="signal-orbital__core">
        <Asterisk size={32} />
      </div>
      <span className="signal-orbital__node signal-orbital__node--one">
        <FileSpreadsheet size={15} />
      </span>
      <span className="signal-orbital__node signal-orbital__node--two">
        <Braces size={15} />
      </span>
      <span className="signal-orbital__node signal-orbital__node--three">
        <LineChart size={15} />
      </span>
      <span className="signal-orbital__label signal-orbital__label--one">raw rows</span>
      <span className="signal-orbital__label signal-orbital__label--two">grounded query</span>
      <span className="signal-orbital__label signal-orbital__label--three">clear signal</span>
    </div>
  );
}

export function Landing() {
  return (
    <div className="marketing-page relative overflow-hidden bg-[var(--marketing-ink)] text-[var(--marketing-paper)]">
      <a href="#main-content" className="marketing-skip-link">
        Skip to content
      </a>

      <nav aria-label="Primary navigation" className="marketing-nav fixed inset-x-0 top-0 z-50">
        <div className="mx-auto flex h-[76px] max-w-[1440px] items-center justify-between px-5 md:px-9">
          <ReadoutLogo className="rounded-full focus-visible:outline-offset-4" />
          <div className="hidden items-center gap-1 rounded-full border border-white/10 bg-white/[.035] p-1 text-sm text-white/65 backdrop-blur-xl md:flex">
            <a className="rounded-full px-4 py-2 transition-colors hover:bg-white/[.07] hover:text-white" href="#platform">
              Platform
            </a>
            <a className="rounded-full px-4 py-2 transition-colors hover:bg-white/[.07] hover:text-white" href="#workflow">
              Workflow
            </a>
            <a className="rounded-full px-4 py-2 transition-colors hover:bg-white/[.07] hover:text-white" href="#trust">
              Trust
            </a>
          </div>
          <div className="flex items-center gap-2 text-sm font-semibold">
            <Link className="hidden min-h-11 items-center px-4 text-white/70 transition hover:text-white sm:inline-flex" href="/login">
              Sign in
            </Link>
            <Link className="marketing-button marketing-button--light min-h-11 px-5" href="/demo">
              Enter demo <ArrowRight size={15} />
            </Link>
          </div>
        </div>
      </nav>

      <main id="main-content" tabIndex={-1}>
        <section className="marketing-hero marketing-hero--compact relative overflow-hidden pt-[76px]">
          <div className="marketing-noise" aria-hidden="true" />
          <div className="marketing-hero__beam" aria-hidden="true" />

          <div className="marketing-hero__visual pointer-events-none absolute right-[-9rem] top-14 hidden size-[40rem] opacity-60 lg:block">
            <SignalOrbital />
          </div>

          <div className="relative mx-auto grid max-w-[1440px] gap-12 px-5 pb-10 pt-16 md:px-9 lg:grid-cols-[1.06fr_.94fr] lg:items-center lg:gap-10 lg:pt-20">
            <div className="relative z-10">
              <p className="marketing-hero__eyebrow mb-6 flex items-center gap-3 text-[11px] font-bold uppercase tracking-[.22em] text-white/75">
                <span className="relative inline-flex size-2 rounded-full bg-[var(--marketing-mint)]" />
                Business intelligence, brought down to earth
              </p>
              <h1 className="marketing-hero__headline max-w-[880px] text-[clamp(3.8rem,7.2vw,7rem)] font-semibold leading-[.86] tracking-[-.075em]">
                Your data is <span className="marketing-handwriting">talking.</span>
                <br />
                Now hear what matters.
              </h1>
              <p className="marketing-hero__copy mt-7 max-w-[610px] text-base leading-7 text-white/80 md:text-lg">
                Readout turns a CSV and a plain-English question into a visual, evidence-backed answer, then keeps watch for the changes worth your attention.
              </p>
              <div className="marketing-hero__actions mt-8 flex flex-col items-start gap-3 sm:flex-row">
                <Link
                  data-testid="launch-demo-btn"
                  className="marketing-button marketing-button--mint min-h-14 px-7 text-[15px]"
                  href="/demo"
                >
                  Explore a live dataset <ArrowRight size={17} />
                </Link>
                <Link
                  data-testid="signup-cta"
                  className="marketing-button marketing-button--ghost min-h-14 px-7 text-[15px]"
                  href="/signup"
                >
                  Create your workspace
                </Link>
              </div>
              <div className="marketing-hero__meta mt-9 flex max-w-2xl flex-wrap gap-x-7 gap-y-3 border-t border-white/10 pt-5 text-xs text-white/70">
                {["No account for the demo", "Query plan included", "Built for CSV data"].map((item) => (
                  <span className="flex items-center gap-2" key={item}>
                    <Check size={13} className="text-[var(--marketing-mint)]" />
                    {item}
                  </span>
                ))}
              </div>
            </div>

            <div className="marketing-hero__preview relative z-10 lg:translate-y-14">
              <div className="marketing-preview-label">
                <span>LIVE PRODUCT STORY</span>
                <span>01 / 04</span>
              </div>
              <div className="marketing-preview-wrap">
                <div className="marketing-preview-glow" aria-hidden="true" />
                <ProductPreview />
              </div>
              <p className="mt-4 max-w-md text-xs leading-5 text-white/65">
                A real interface, not a concept render. Open the demo and ask a follow-up.
              </p>
            </div>
          </div>

          <a
            href="#platform"
            aria-label="Continue to platform overview"
            className="absolute bottom-8 left-1/2 hidden -translate-x-1/2 flex-col items-center gap-2 text-[10px] font-bold uppercase tracking-[.2em] text-white/70 lg:flex"
          >
            Follow the signal <ArrowDown size={14} />
          </a>
        </section>

        <div className="marketing-marquee" aria-label="Readout capabilities">
          <div className="marketing-marquee__track">
            {[...marquee, ...marquee].map((item, index) => (
              <span key={`${item}-${index}`}>
                {item}
                <Asterisk size={18} />
              </span>
            ))}
          </div>
        </div>

        <section id="platform" className="marketing-paper relative text-[var(--marketing-ink)]">
          <div className="mx-auto max-w-[1440px] px-5 py-28 md:px-9 md:py-40">
            <div className="grid gap-12 lg:grid-cols-[.62fr_1.38fr] lg:gap-24">
              <div>
                <p className="marketing-eyebrow text-[var(--marketing-violet)]">The signal layer</p>
                <p className="mt-6 max-w-xs text-sm leading-6 text-[var(--marketing-ink-muted)]">
                  Most analytics tools wait for you to know where to look. Readout helps you find the question hiding underneath the dashboard.
                </p>
              </div>
              <h2 className="max-w-4xl text-[clamp(3rem,5.8vw,6rem)] font-semibold leading-[.94] tracking-[-.065em]">
                One dataset.
                <br />
                <span className="font-serif font-normal italic text-[var(--marketing-violet)]">Four ways to know.</span>
              </h2>
            </div>

            <div className="mt-20 border-t border-[var(--marketing-rule)] md:mt-28">
              {capabilities.map(({ icon: Icon, index, label, title, copy, accent }) => (
                <article key={index} className="capability-row group">
                  <div className={`capability-icon capability-icon--${accent}`}>
                    <Icon size={22} />
                  </div>
                  <p className="text-xs font-bold tracking-[.16em] text-[var(--marketing-ink-faint)]">
                    {index} / {label.toUpperCase()}
                  </p>
                  <h3 className="max-w-xl text-2xl font-semibold leading-tight tracking-[-.04em] md:text-4xl">{title}</h3>
                  <p className="max-w-md leading-7 text-[var(--marketing-ink-muted)]">{copy}</p>
                  <ArrowRight className="capability-arrow" size={22} />
                </article>
              ))}
            </div>
          </div>
        </section>

        <section id="workflow" className="marketing-workflow relative py-28 md:py-40">
          <div className="marketing-noise" aria-hidden="true" />
          <div className="relative mx-auto max-w-[1440px] px-5 md:px-9">
            <div className="flex flex-col justify-between gap-8 md:flex-row md:items-end">
              <div>
                <p className="marketing-eyebrow text-[var(--marketing-mint)]">From question to consequence</p>
                <h2 className="mt-7 max-w-4xl text-[clamp(3.2rem,6.2vw,6.6rem)] font-semibold leading-[.9] tracking-[-.07em]">
                  Follow the thread.
                  <br />
                  Keep the evidence.
                </h2>
              </div>
              <p className="max-w-sm text-base leading-7 text-white/75">
                Every answer carries its context with it: the question, interpreted metric, query plan, chart, and plain-language reading.
              </p>
            </div>

            <div className="workflow-stage mt-20 md:mt-28">
              <div className="workflow-rail" aria-hidden="true">
                <span />
                <span />
                <span />
                <span />
              </div>
              <div className="workflow-step workflow-step--question">
                <span className="workflow-step__number">01</span>
                <p className="workflow-step__label">You ask</p>
                <div className="workflow-question">
                  <span className="size-2 rounded-full bg-[var(--marketing-mint)]" />
                  Which region changed most this quarter?
                  <WandSparkles size={17} />
                </div>
              </div>
              <div className="workflow-step workflow-step--resolve">
                <span className="workflow-step__number">02</span>
                <p className="workflow-step__label">Readout resolves</p>
                <div className="grid grid-cols-2 gap-2">
                  <span className="workflow-chip">Metric <b>Revenue</b></span>
                  <span className="workflow-chip">Group <b>Region</b></span>
                  <span className="workflow-chip">Window <b>Quarter</b></span>
                  <span className="workflow-chip">Intent <b>Compare</b></span>
                </div>
              </div>
              <div className="workflow-step workflow-step--answer">
                <span className="workflow-step__number">03</span>
                <p className="workflow-step__label">The signal surfaces</p>
                <div className="workflow-answer">
                  <div>
                    <span className="text-xs text-white/70">Largest movement</span>
                    <p className="mt-1 text-2xl font-semibold">
                      West <span className="text-[var(--marketing-mint)]">+31%</span>
                    </p>
                  </div>
                  <svg viewBox="0 0 180 56" role="img" aria-label="West region trend rises 31 percent">
                    <path
                      d="M2 48 C28 44 34 38 58 40 S91 30 110 32 S142 7 178 8"
                      fill="none"
                      stroke="var(--marketing-mint)"
                      strokeWidth="3"
                    />
                    <path
                      d="M2 48 C28 44 34 38 58 40 S91 30 110 32 S142 7 178 8 V56 H2Z"
                      fill="url(#workflow-fill)"
                    />
                    <defs>
                      <linearGradient id="workflow-fill" x1="0" y1="0" x2="0" y2="1">
                        <stop stopColor="var(--marketing-mint)" stopOpacity=".28" />
                        <stop offset="1" stopColor="var(--marketing-mint)" stopOpacity="0" />
                      </linearGradient>
                    </defs>
                  </svg>
                </div>
              </div>
              <div className="workflow-step workflow-step--action">
                <span className="workflow-step__number">04</span>
                <p className="workflow-step__label">You decide</p>
                <div className="workflow-action">
                  <Check size={18} />
                  <span>Signal pinned to overview</span>
                  <span className="ml-auto text-xs text-white/70">just now</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="trust" className="marketing-trust relative overflow-hidden bg-[var(--marketing-violet)] text-white">
          <div className="marketing-trust__orb" aria-hidden="true" />
          <div className="relative mx-auto grid max-w-[1440px] gap-16 px-5 py-28 md:px-9 md:py-40 lg:grid-cols-[.9fr_1.1fr] lg:items-center">
            <div>
              <div className="mb-9 flex size-14 items-center justify-center rounded-full border border-white/20 bg-white/10">
                <Fingerprint size={25} />
              </div>
              <p className="marketing-eyebrow text-white">Trust is part of the interface</p>
              <h2 className="mt-7 max-w-xl text-[clamp(3.2rem,5.5vw,6rem)] font-semibold leading-[.9] tracking-[-.07em]">
                No black box.
                <br />
                <span className="font-serif font-normal italic text-[var(--marketing-mint)]">Just receipts.</span>
              </h2>
              <p className="mt-8 max-w-lg text-lg leading-8 text-white/90">
                Readout constrains every question to your uploaded schema, exposes how it interpreted your intent, and lets you inspect the plan behind the answer.
              </p>
            </div>
            <div className="query-receipt">
              <div className="query-receipt__top">
                <span>ANSWER RECEIPT</span>
                <span className="flex items-center gap-2">
                  <span className="size-1.5 rounded-full bg-[var(--marketing-mint)]" />
                  GROUNDED
                </span>
              </div>
              <div className="query-receipt__body">
                <p className="query-receipt__label">Interpreted intent</p>
                <p className="mt-2 text-xl font-medium">Compare total revenue by region for the current quarter.</p>
                <div className="my-7 h-px bg-white/10" />
                <p className="query-receipt__label">Validated against</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  <span className="receipt-token">revenue · numeric</span>
                  <span className="receipt-token">region · category</span>
                  <span className="receipt-token">order date · date</span>
                </div>
                <div className="my-7 h-px bg-white/10" />
                <div className="flex items-center justify-between">
                  <div>
                    <p className="query-receipt__label">Confidence</p>
                    <p className="mt-1 text-3xl font-semibold">94%</p>
                  </div>
                  <div className="flex items-center gap-2 rounded-full bg-[var(--marketing-mint)] px-4 py-2 text-xs font-bold text-[var(--marketing-ink)]">
                    <ShieldCheck size={15} />
                    Plan validated
                  </div>
                </div>
              </div>
              <div className="query-receipt__tear" aria-hidden="true" />
            </div>
          </div>
        </section>

        <section className="marketing-paper relative overflow-hidden text-[var(--marketing-ink)]">
          <div className="marketing-cta-orbit" aria-hidden="true">
            <SignalOrbital />
          </div>
          <div className="relative mx-auto max-w-[1440px] px-5 py-28 text-center md:px-9 md:py-44">
            <Sparkles className="mx-auto text-[var(--marketing-violet)]" size={30} />
            <p className="marketing-eyebrow mt-8 text-[var(--marketing-violet)]">The shortest route to clarity</p>
            <h2 className="mx-auto mt-7 max-w-5xl text-[clamp(3.5rem,7.8vw,8rem)] font-semibold leading-[.86] tracking-[-.075em]">
              There&apos;s a signal in your data.
              <br />
              <span className="font-serif font-normal italic text-[var(--marketing-violet)]">Go find it.</span>
            </h2>
            <p className="mx-auto mt-8 max-w-xl text-lg leading-8 text-[var(--marketing-ink-muted)]">
              Step into a working sample dataset. No setup, no account, no tour disguised as a product.
            </p>
            <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
              <Link className="marketing-button marketing-button--dark min-h-14 px-8" href="/demo">
                Open the live workspace <ArrowRight size={17} />
              </Link>
              <Link className="marketing-button marketing-button--paper min-h-14 px-8" href="/signup">
                Start with your data
              </Link>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-white/10 bg-[var(--marketing-ink)] text-white">
        <div className="mx-auto grid max-w-[1440px] gap-10 px-5 py-10 md:grid-cols-[1fr_auto] md:items-end md:px-9">
          <div>
            <ReadoutLogo />
            <p className="mt-4 max-w-xs text-sm leading-6 text-white/42">Analytics that answers back and shows its work.</p>
          </div>
          <div className="flex flex-wrap items-center gap-x-6 gap-y-3 text-sm text-white/48">
            <span>© 2026 Readout</span>
            <Link className="hover:text-white" href="/privacy">
              Privacy
            </Link>
            <Link className="hover:text-white" href="/terms">
              Terms
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
