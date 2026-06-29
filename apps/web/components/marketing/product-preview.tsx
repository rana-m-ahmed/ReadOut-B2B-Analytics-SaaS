"use client";

import { ArrowUpRight, Check, ChevronDown, Command, MoreHorizontal, MousePointer2, Sparkles } from "lucide-react";

const bars = [38, 53, 46, 66, 58, 81, 72, 92, 84, 100, 89, 96];

export function ProductPreview() {
  return (
    <div data-testid="product-preview" className="product-preview">
      <div className="product-preview__chrome">
        <div className="flex items-center gap-1.5" aria-hidden="true"><span/><span/><span/></div>
        <div className="product-preview__address"><span className="size-1.5 rounded-full bg-[var(--marketing-mint)]"/>Live demo mode · sales-review</div>
        <MoreHorizontal size={16} />
      </div>

      <div className="product-preview__shell">
        <aside className="product-preview__sidebar" aria-label="Product preview navigation">
          <div className="flex size-8 items-center justify-center rounded-lg bg-[var(--marketing-violet)] text-white"><Sparkles size={15}/></div>
          <div className="mt-8 grid gap-3" aria-hidden="true"><span className="is-active"/><span/><span/><span/></div>
          <div className="mt-auto size-7 rounded-full border border-white/10 bg-white/5"/>
        </aside>

        <div className="min-w-0 flex-1">
          <header className="product-preview__header">
            <div><p className="text-[10px] font-semibold uppercase tracking-[.14em] text-white/35">Overview</p><p className="mt-1 text-sm font-semibold">Revenue pulse</p></div>
            <span className="product-preview__dataset" aria-hidden="true">Demo sales <ChevronDown size={12}/></span>
          </header>

          <div className="product-preview__content">
            <div className="product-preview__stats">
              <div><span>Net revenue</span><strong>$1.84m</strong><small className="text-[var(--marketing-mint)]">↑ 18.4%</small></div>
              <div><span>Orders</span><strong>4,892</strong><small>+306 this period</small></div>
              <div><span>Avg. order</span><strong>$376</strong><small className="text-[var(--marketing-mint)]">↑ 4.2%</small></div>
            </div>

            <div className="product-preview__grid">
              <div className="product-preview__chart">
                <div className="flex items-start justify-between"><div><p className="text-[10px] text-white/38">Revenue by month</p><p className="mt-1 text-xs font-semibold">Momentum is building</p></div><span className="product-preview__status"><span/>LIVE</span></div>
                <div className="product-preview__bars" role="img" aria-label="Monthly revenue bars trending upward">
                  {bars.map((height, index) => (
                    <span key={index} style={{height:`${height}%`}} className={index === 9 ? "is-highlight" : ""}/>
                  ))}
                </div>
                <div className="flex justify-between text-[8px] font-semibold uppercase tracking-widest text-white/22"><span>Jan</span><span>Apr</span><span>Aug</span><span>Dec</span></div>
              </div>

              <div className="product-preview__insight">
                <div className="flex items-center justify-between"><span className="flex size-7 items-center justify-center rounded-full bg-[var(--marketing-violet)] text-white"><Sparkles size={12}/></span><ArrowUpRight size={14} className="text-white/32"/></div>
                <p className="mt-7 text-[9px] font-semibold uppercase tracking-[.15em] text-white/35">Signal found</p>
                <p className="mt-2 text-sm font-semibold leading-5">West is accelerating <span className="text-[var(--marketing-mint)]">31% above</span> baseline.</p>
                <div className="mt-4 flex items-center gap-2 text-[9px] text-white/32"><Check size={11} className="text-[var(--marketing-mint)]"/> High confidence</div>
              </div>
            </div>

            <div className="product-preview__ask">
              <span className="flex size-7 items-center justify-center rounded-lg bg-white/[.06]"><Command size={12}/></span>
              <span className="text-white/42">Ask Readout</span>
              <span className="ml-auto overflow-hidden whitespace-nowrap font-medium text-white">Why did the West grow?</span>
              <span className="product-preview__send"><ArrowUpRight size={12}/></span>
            </div>
          </div>
        </div>
      </div>
      <div className="product-preview__cursor" aria-hidden="true"><MousePointer2 size={18}/><span>you</span></div>
    </div>
  );
}
