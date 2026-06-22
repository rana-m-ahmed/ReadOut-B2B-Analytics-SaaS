"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { createClient } from '../../lib/supabase/client';
import { Button } from '../../components/ui/button';
import { HeroDemoSequence } from '../../components/marketing/HeroDemoSequence';
import { Database, Zap, ShieldAlert, LineChart, MessageSquare } from 'lucide-react';

export default function MarketingPage() {
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleDemoLaunch = async () => {
    try {
      setIsLoading(true);
      const supabase = createClient();
      const { error } = await supabase.auth.signInAnonymously();
      if (error) throw error;
      router.push('/overview');
    } catch (err) {
      console.error("Failed to launch demo:", err);
      setIsLoading(false); // Only reset if failed. On success we redirect.
    }
  };

  return (
    <div className="min-h-screen bg-[var(--canvas)] flex flex-col">
      {/* Nav Stub */}
      <header className="h-16 flex items-center justify-between px-6 md:px-12 shrink-0">
        <div className="font-bold text-xl tracking-tight text-[var(--ink)]">ReadOut</div>
        <Button variant="outline" size="sm" onClick={() => router.push('/login')}>Sign In</Button>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center px-4 py-12 md:py-24 text-center">
        {/* Hero Section */}
        <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight text-[var(--ink)] mb-4">
          Ask your data <span className="text-[var(--accent)]">anything.</span>
        </h1>
        
        {/* One-line problem statement */}
        <p className="text-lg md:text-xl text-[var(--ink-secondary)] max-w-2xl mb-10 font-medium">
          Stop writing fragile SQL and staring at stale dashboards. ReadOut turns natural language into verified queries, automated insights, and instant answers.
        </p>

        {/* Prominent CTA */}
        <Button 
          data-testid="launch-demo-btn"
          size="lg" 
          onClick={handleDemoLaunch} 
          disabled={isLoading}
          className="text-lg px-8 py-6 mb-16 rounded-[var(--radius-pill)] shadow-[var(--shadow-lift)] transition-transform hover:-translate-y-1"
        >
          {isLoading ? "Provisioning Sandbox..." : "Launch Demo Dashboard"}
        </Button>

        {/* Hero Visual Asset (Animation Strip) */}
        <div className="w-full max-w-4xl mb-24">
          <HeroDemoSequence />
        </div>

        {/* Feature Row */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 max-w-6xl w-full text-left mb-24">
          {[
            { icon: MessageSquare, title: "NL to SQL to Chart", desc: "Ask questions in plain English. Get back DuckDB-verified answers and auto-selected charts." },
            { icon: Zap, title: "Automated Insights", desc: "Our agent ranks key drivers, trends, and segment shifts proactively without you asking." },
            { icon: ShieldAlert, title: "Anomaly Detection", desc: "Statistical isolation forests detect revenue drops and usage spikes automatically." },
            { icon: LineChart, title: "Query Transparency", desc: "Every answer includes the exact SQL query plan and confidence score so you can trust the data." }
          ].map((feat, i) => (
            <div key={i} className="flex flex-col gap-3">
              <div className="w-10 h-10 rounded-[var(--radius-control)] bg-[var(--accent)]/10 flex items-center justify-center text-[var(--accent)]">
                <feat.icon size={20} />
              </div>
              <h3 className="font-bold text-[var(--ink)]">{feat.title}</h3>
              <p className="text-sm text-[var(--ink-secondary)] leading-relaxed">{feat.desc}</p>
            </div>
          ))}
        </div>

        {/* Tech Credibility Strip */}
        <div className="w-full max-w-4xl border-t border-[var(--hairline)] pt-8 flex flex-col items-center">
          <p className="text-xs font-semibold uppercase tracking-widest text-[var(--ink-secondary)] mb-6">Powered by industry-standard open source</p>
          <div className="flex flex-wrap justify-center gap-8 md:gap-12 opacity-50 grayscale hover:grayscale-0 transition-all duration-300">
            <span className="font-mono font-bold text-lg">Next.js</span>
            <span className="font-mono font-bold text-lg">FastAPI</span>
            <span className="font-mono font-bold text-lg">DuckDB</span>
            <span className="font-mono font-bold text-lg">Supabase</span>
            <span className="font-mono font-bold text-lg">Groq</span>
          </div>
        </div>
      </main>
    </div>
  );
}
