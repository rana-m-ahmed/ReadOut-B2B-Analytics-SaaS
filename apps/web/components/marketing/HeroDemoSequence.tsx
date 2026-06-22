"use client";

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { MessageSquare, Sparkles, Pin } from 'lucide-react';

const sequence = [
  { state: 'typing', text: "Show me Q3 revenue by region", duration: 2500 },
  { state: 'loading', duration: 1000 },
  { state: 'result', duration: 4000 },
];

export function HeroDemoSequence() {
  const [stepIndex, setStepIndex] = useState(0);
  const [typedText, setTypedText] = useState("");

  const currentStep = sequence[stepIndex];

  useEffect(() => {
    let timeout: NodeJS.Timeout;

    if (currentStep.state === 'typing') {
      let charIndex = 0;
      const typeInterval = setInterval(() => {
        const text = currentStep.text || "";
        setTypedText(text.substring(0, charIndex + 1));
        charIndex++;
        if (charIndex >= text.length) {
          clearInterval(typeInterval);
          timeout = setTimeout(() => {
            setStepIndex((s) => (s + 1) % sequence.length);
          }, 800); // Wait a bit after typing finishes
        }
      }, 50);
      return () => {
        clearInterval(typeInterval);
        clearTimeout(timeout);
      };
    } else {
      timeout = setTimeout(() => {
        setStepIndex((s) => (s + 1) % sequence.length);
        if (sequence[(stepIndex + 1) % sequence.length].state === 'typing') {
          setTypedText(""); // Reset for next loop
        }
      }, currentStep.duration);
    }

    return () => clearTimeout(timeout);
  }, [stepIndex, currentStep]);

  return (
    <div className="w-full max-w-2xl mx-auto flex flex-col gap-4 p-4">
      {/* Search Input Mock */}
      <div className="relative flex items-center bg-[var(--surface)] border border-[var(--hairline)] rounded-[var(--radius-pill)] shadow-[var(--shadow-float)] p-2 px-4 h-14">
        <MessageSquare size={20} className="text-[var(--ink-secondary)] mr-3 shrink-0" />
        <span className="text-[var(--ink)] font-medium text-lg flex-1">
          {typedText}
          {currentStep.state === 'typing' && (
            <motion.span
              animate={{ opacity: [1, 0] }}
              transition={{ repeat: Infinity, duration: 0.8 }}
              className="inline-block w-0.5 h-5 bg-[var(--accent)] ml-1 align-middle"
            />
          )}
        </span>
        <button className="bg-[var(--accent)] text-[var(--accent-on)] w-8 h-8 rounded-full flex items-center justify-center shrink-0">
          <Sparkles size={16} />
        </button>
      </div>

      {/* Result Card Mock */}
      <div className="h-[300px] relative">
        <AnimatePresence mode="wait">
          {currentStep.state === 'loading' && (
            <motion.div
              key="loading"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.98 }}
              className="absolute inset-0 flex flex-col items-center justify-center bg-[var(--surface-subtle)] rounded-[var(--radius-card)] border border-[var(--hairline)]"
            >
              <div className="w-8 h-8 rounded-full border-2 border-[var(--accent)] border-t-transparent animate-spin mb-4" />
              <span className="text-sm font-semibold tracking-widest uppercase text-[var(--ink-secondary)]">Analyzing intent...</span>
            </motion.div>
          )}

          {currentStep.state === 'result' && (
            <motion.div
              key="result"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.98 }}
              className="absolute inset-0 bg-[var(--surface)] rounded-[var(--radius-card)] border border-[var(--hairline)] shadow-[var(--shadow-lift)] overflow-hidden flex flex-col"
            >
              <div className="p-4 border-b border-[var(--hairline)] flex justify-between items-start bg-[var(--surface-subtle)]/50">
                <div>
                  <h3 className="font-bold text-[var(--ink)]">Q3 Revenue by Region</h3>
                  <p className="text-sm text-[var(--ink-secondary)]">West region saw a 14% anomalous drop in April.</p>
                </div>
                <button className="text-[var(--ink-secondary)] hover:text-[var(--accent)] flex items-center gap-1 text-sm font-medium">
                  <Pin size={16} />
                  Pin
                </button>
              </div>
              <div className="flex-1 p-6 flex items-end justify-center gap-4">
                {/* Fake Bar Chart */}
                {[
                  { label: "East", h: "60%" },
                  { label: "West", h: "40%" },
                  { label: "North", h: "80%" },
                  { label: "South", h: "50%" },
                ].map((bar, i) => (
                  <div key={i} className="flex flex-col items-center gap-2 w-16">
                    <motion.div
                      initial={{ height: 0 }}
                      animate={{ height: bar.h }}
                      transition={{ delay: i * 0.1, type: "spring", stiffness: 100 }}
                      className="w-full bg-[var(--accent)] rounded-t-[var(--radius-control)] opacity-80"
                    />
                    <span className="text-xs font-semibold uppercase tracking-widest text-[var(--ink-secondary)]">{bar.label}</span>
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
