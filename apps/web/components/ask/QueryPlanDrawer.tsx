"use client";

import { useAppStore } from "../../lib/store/useAppStore";
import { motion, AnimatePresence } from "framer-motion";
import { X, Code2, Database } from "lucide-react";

export function QueryPlanDrawer() {
  const { isOpen, answerId } = useAppStore(state => state.queryPlanDrawer);
  const closeQueryPlanDrawer = useAppStore(state => state.closeQueryPlanDrawer);
  const askMessages = useAppStore(state => state.askMessages);

  // Find the exact message to extract the query plan and SQL
  const message = askMessages.find(m => m.id === answerId);
  const queryPlan = message?.response?.query_plan;
  const debugSql = message?.response?.debug_sql;

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={closeQueryPlanDrawer}
            className="fixed inset-0 z-40 bg-[var(--canvas)]/20 backdrop-blur-sm"
            data-testid="query-plan-backdrop"
          />

          {/* Drawer */}
          <motion.div
            initial={{ x: "100%", opacity: 0.5 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: "100%", opacity: 0.5 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
            className="fixed right-0 top-0 bottom-0 z-50 w-full max-w-2xl bg-[var(--surface)] border-l border-[var(--hairline)] shadow-2xl flex flex-col"
            data-testid="query-plan-drawer"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--hairline)] shrink-0 bg-[var(--surface-subtle)]">
              <h2 className="text-lg font-semibold text-[var(--ink)] tracking-tight">Query Plan</h2>
              <button
                onClick={closeQueryPlanDrawer}
                className="p-2 rounded-full hover:bg-[var(--surface)] text-[var(--ink-secondary)] hover:text-[var(--ink)] transition-colors"
                aria-label="Close drawer"
              >
                <X size={20} />
              </button>
            </div>

            {/* Content Container */}
            <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-8 bg-[var(--canvas)]">
              
              {/* Intent Section */}
              <section className="flex flex-col gap-3">
                <header className="flex items-center gap-2 text-[var(--ink-secondary)] font-medium">
                  <Code2 size={18} />
                  <h3 className="text-sm tracking-wide uppercase">What the model decided</h3>
                </header>
                {queryPlan ? (
                  <div className="bg-[var(--surface)] border border-[var(--hairline)] rounded-[var(--radius-card)] p-4 shadow-[var(--shadow-float)] overflow-x-auto">
                    <pre className="font-mono text-sm text-[var(--ink)]" data-testid="debug-json">
                      {JSON.stringify(queryPlan, null, 2)}
                    </pre>
                  </div>
                ) : (
                  <div className="p-4 border border-[var(--hairline)] rounded-[var(--radius-card)] text-[var(--ink-secondary)] italic">
                    No query plan available for this response.
                  </div>
                )}
              </section>

              {/* SQL Section */}
              <section className="flex flex-col gap-3">
                <header className="flex items-center gap-2 text-[var(--ink-secondary)] font-medium">
                  <Database size={18} />
                  <h3 className="text-sm tracking-wide uppercase">What the backend ran</h3>
                </header>
                {debugSql ? (
                  <div className="bg-[var(--surface)] border border-[var(--hairline)] rounded-[var(--radius-card)] p-4 shadow-[var(--shadow-float)] overflow-x-auto">
                    <pre className="font-mono text-sm text-[var(--ink)]" data-testid="debug-sql">
                      {debugSql}
                    </pre>
                  </div>
                ) : (
                  <div className="p-4 border border-[var(--hairline)] rounded-[var(--radius-card)] text-[var(--ink-secondary)] italic">
                    No SQL text available for this response.
                  </div>
                )}
              </section>

            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
