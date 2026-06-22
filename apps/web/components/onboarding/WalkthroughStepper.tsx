"use client";

import { useState, useEffect } from 'react';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { X, MessageSquare, Pin, Lightbulb } from 'lucide-react';

const steps = [
  { icon: MessageSquare, title: "Ask a question", desc: "Type natural language queries to instantly generate DuckDB-backed charts." },
  { icon: Pin, title: "Pin useful charts", desc: "Found something interesting? Pin it directly to your dashboard." },
  { icon: Lightbulb, title: "Review insights", desc: "Our agent proactively flags trends, anomalies, and key drivers in the background." }
];

export function WalkthroughStepper() {
  const [isVisible, setIsVisible] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    // Only show if not seen before
    const seen = localStorage.getItem('readout_walkthrough_seen');
    if (!seen) {
      setIsVisible(true);
    }
  }, []);

  const dismiss = () => {
    localStorage.setItem('readout_walkthrough_seen', 'true');
    setIsVisible(false);
  };

  const nextStep = () => {
    if (currentStep === steps.length - 1) {
      dismiss();
    } else {
      setCurrentStep(s => s + 1);
    }
  };

  if (!isVisible) return null;

  const step = steps[currentStep];

  return (
    <div className="fixed bottom-6 right-6 z-50 animate-in slide-in-from-bottom-5">
      <Card className="w-80 p-5 flex flex-col gap-4 shadow-[var(--shadow-lift)] border-[var(--hairline)] relative">
        <button 
          onClick={dismiss} 
          className="absolute top-3 right-3 text-[var(--ink-secondary)] hover:text-[var(--ink)] transition-colors"
        >
          <X size={16} />
        </button>
        
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-[var(--accent)]/10 flex items-center justify-center text-[var(--accent)] shrink-0">
            <step.icon size={20} />
          </div>
          <div>
            <h4 className="font-bold text-[var(--ink)] text-sm">{step.title}</h4>
            <span className="text-xs text-[var(--ink-secondary)] uppercase tracking-widest font-semibold">Step {currentStep + 1} of {steps.length}</span>
          </div>
        </div>
        
        <p className="text-sm text-[var(--ink-secondary)] leading-relaxed">
          {step.desc}
        </p>

        <div className="flex justify-between items-center mt-2">
          <div className="flex gap-1.5">
            {steps.map((_, i) => (
              <div 
                key={i} 
                className={`h-1.5 rounded-full transition-all ${i === currentStep ? 'w-4 bg-[var(--accent)]' : 'w-1.5 bg-[var(--hairline)]'}`}
              />
            ))}
          </div>
          <Button size="sm" onClick={nextStep}>
            {currentStep === steps.length - 1 ? "Get Started" : "Next"}
          </Button>
        </div>
      </Card>
    </div>
  );
}
