"use client";

import { useRef, useEffect } from "react";
import { useAppStore } from "../../lib/store/useAppStore";
import { AskMessage } from "./AskMessage";
import { motion, AnimatePresence } from "framer-motion";

export function AskThread() {
  const askMessages = useAppStore(state => state.askMessages);
  const isAsking = useAppStore(state => state.isAsking);
  const askingQuestion = useAppStore(state => state.askingQuestion);
  const loadingStage = useAppStore(state => state.loadingStage);
  
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView?.({ behavior: 'smooth' });
  }, [askMessages.length, isAsking, loadingStage]);

  if (askMessages.length === 0 && !isAsking) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-[var(--ink-secondary)] p-8">
        <p>No questions asked yet.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 p-4 w-full h-full overflow-y-auto">
      <AnimatePresence initial={false}>
        {askMessages.map((msg) => (
          <motion.div
            key={msg.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full"
          >
            <AskMessage message={msg} />
          </motion.div>
        ))}
        
        {isAsking && askingQuestion && (
          <motion.div
            key="loading-exchange"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.98 }}
            className="w-full"
            data-testid="ask-loading"
          >
            <AskMessage 
              message={{
                id: 'loading',
                status: 'loading',
                question: askingQuestion,
                loadingStage: loadingStage || "Thinking..."
              }} 
            />
          </motion.div>
        )}
      </AnimatePresence>
      <div ref={bottomRef} className="h-4 w-full shrink-0" />
    </div>
  );
}
