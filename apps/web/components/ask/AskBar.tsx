"use client";

import { useState, useRef } from "react";
import { Send, Sparkles } from "lucide-react";
import { useAppStore } from "../../lib/store/useAppStore";
export function AskBar() {
  const [question, setQuestion] = useState("");
  const activeDatasetId = useAppStore((state) => state.activeDatasetId);
  const isAsking = useAppStore((state) => state.isAsking);
  const submitAskQuestion = useAppStore((state) => state.submitAskQuestion);
  
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || !activeDatasetId || isAsking) return;

    const submittedQuestion = question;
    setQuestion("");
    
    await submitAskQuestion(submittedQuestion);
    inputRef.current?.focus(); // Re-focus after asking
  };

  return (
    <form 
      onSubmit={handleSubmit}
      className="relative flex items-center bg-[var(--surface)] border border-[var(--hairline)] rounded-[var(--radius-pill)] shadow-[var(--shadow-float)] p-2 px-4 h-14 w-full focus-within:ring-2 focus-within:ring-[var(--accent)]/50 focus-within:border-[var(--accent)] transition-all"
    >
      <Sparkles size={20} className="text-[var(--accent)] mr-3 shrink-0" />
      <input
        ref={inputRef}
        type="text"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        disabled={isAsking || !activeDatasetId}
        placeholder={activeDatasetId ? "Ask a question about your data..." : "Select a dataset to ask questions"}
        className="text-[var(--ink)] font-medium text-lg flex-1 bg-transparent border-none outline-none placeholder:text-[var(--ink-secondary)]/50 disabled:opacity-50"
      />
      <button 
        type="submit"
        disabled={isAsking || !question.trim() || !activeDatasetId}
        className="bg-[var(--accent)] hover:bg-[var(--accent)]/90 text-[var(--accent-on)] w-10 h-10 rounded-full flex items-center justify-center shrink-0 disabled:opacity-50 disabled:cursor-not-allowed transition-colors ml-2"
        data-testid="ask-submit"
      >
        <Send size={18} className="ml-1" />
      </button>
    </form>
  );
}
