"use client";

import { useState } from "react";
import { User, Sparkles, Pin, MessageCircle, FileCode2, Info, ChevronLeft, ChevronRight, AlertCircle } from "lucide-react";
import { ChartRenderer } from "../charts/ChartRenderer";
import { useAppStore } from "../../lib/store/useAppStore";
import { formatCurrency, formatPercent, formatInteger } from "../../lib/format";

interface AskMessageProps {
  message: any;
}

export function AskMessage({ message }: AskMessageProps) {
  const { status, question, loadingStage, response, isDegraded, errorMessage } = message;
  const openQueryPlanDrawer = useAppStore(state => state.openQueryPlanDrawer);
  const submitAskQuestion = useAppStore(state => state.submitAskQuestion);
  
  const [tablePage, setTablePage] = useState(0);
  const rowsPerPage = 5;

  const renderQuestion = () => {
    const lowerQ = question.toLowerCase();
    const isFollowup = [
      "break that down by", "break down by", "only for", "show as a", "what caused that?", "why did"
    ].some(p => lowerQ.includes(p)) || (lowerQ.includes("compare") && lowerQ.includes("previous"));

    return (
      <div className="flex items-start gap-4 w-full">
        <div className="w-8 h-8 rounded-full bg-[var(--surface-subtle)] flex items-center justify-center shrink-0 border border-[var(--hairline)]">
          <User size={16} className="text-[var(--ink-secondary)]" />
        </div>
        <div className="flex-1 pt-1 text-lg font-medium text-[var(--ink)] flex items-center flex-wrap gap-2">
          {question}
          {isFollowup && (
            <span className="text-[10px] font-bold uppercase tracking-widest text-[var(--accent)] bg-[var(--accent)]/10 px-2 py-0.5 rounded-[var(--radius-pill)] select-none">
              Follow-up
            </span>
          )}
        </div>
      </div>
    );
  };

  const renderLoading = () => (
    <div className="flex items-start gap-4 w-full mt-4">
      <div className="w-8 h-8 rounded-full bg-[var(--accent)]/10 flex items-center justify-center shrink-0 border border-[var(--accent)]/20">
        <Sparkles size={16} className="text-[var(--accent)] animate-pulse" />
      </div>
      <div className="flex-1 pt-1 flex items-center gap-3">
        <div className="w-4 h-4 rounded-full border-2 border-[var(--accent)] border-t-transparent animate-spin" />
        <span className="text-sm font-semibold tracking-widest uppercase text-[var(--ink-secondary)]">
          {loadingStage}
        </span>
      </div>
    </div>
  );

  const renderError = () => (
    <div className="flex items-start gap-4 w-full mt-4" data-testid="ask-error-state">
      <div className="w-8 h-8 rounded-full bg-[var(--danger)]/10 flex items-center justify-center shrink-0 border border-[var(--danger)]/20">
        <AlertCircle size={16} className="text-[var(--danger)]" />
      </div>
      <div className="flex-1 pt-1 text-[var(--ink)] bg-[var(--surface-subtle)] rounded-[var(--radius-card)] p-4 border border-[var(--danger)]/20">
        {isDegraded ? (
          <p className="font-medium text-[var(--ink-secondary)]">
            We're having trouble answering right now. Please try again shortly.
          </p>
        ) : (
          <p className="font-medium text-[var(--danger)]">
            {errorMessage || "An error occurred while answering."}
          </p>
        )}
      </div>
    </div>
  );

  const renderClarification = (clarification: { code: string; message: string }) => (
    <div className="flex items-start gap-4 w-full mt-4" data-testid="ask-clarification-state">
      <div className="w-8 h-8 rounded-full bg-[var(--warning)]/10 flex items-center justify-center shrink-0 border border-[var(--warning)]/20">
        <Info size={16} className="text-[var(--warning)]" />
      </div>
      <div className="flex-1 pt-1 text-[var(--ink)]">
        <div className="bg-[var(--surface-subtle)] border border-[var(--hairline)] rounded-[var(--radius-card)] p-4 shadow-[var(--shadow-float)]">
          <p className="text-[var(--ink)] font-medium">{clarification.message}</p>
          <div className="mt-4 flex flex-wrap gap-2">
            {response.suggested_followups?.map((followup: string, i: number) => (
              <button 
                key={i} 
                className="text-xs font-semibold uppercase tracking-widest bg-[var(--surface)] hover:bg-[var(--surface-subtle)] border border-[var(--hairline)] rounded-[var(--radius-pill)] px-3 py-1.5 text-[var(--ink-secondary)] transition-colors"
                onClick={() => submitAskQuestion(followup)}
              >
                {followup}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  const renderTable = (chartPayload: any) => {
    if (!chartPayload?.data || chartPayload.data.length === 0) return null;
    if (chartPayload.type === 'metric_card') return null; // Metric cards don't need tables

    const data = chartPayload.data;
    const totalPages = Math.ceil(data.length / rowsPerPage);
    const visibleData = data.slice(tablePage * rowsPerPage, (tablePage + 1) * rowsPerPage);
    
    // Determine columns dynamically from first row
    const columns = Object.keys(data[0]);

    return (
      <div className="mt-6 border border-[var(--hairline)] rounded-[var(--radius-control)] overflow-hidden bg-[var(--surface)]">
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-[var(--surface-subtle)] border-b border-[var(--hairline)] uppercase text-xs tracking-widest text-[var(--ink-secondary)]">
              <tr>
                {columns.map(col => (
                  <th key={col} className="px-4 py-2 font-semibold whitespace-nowrap">{col.replace(/_/g, ' ')}</th>
                ))}
              </tr>
            </thead>
            <tbody className="tabular-nums">
              {visibleData.map((row: any, i: number) => (
                <tr key={i} className="border-b border-[var(--hairline)] last:border-0 hover:bg-[var(--surface-subtle)]/50 transition-colors">
                  {columns.map(col => (
                    <td key={col} className="px-4 py-2 text-[var(--ink)]">
                      {typeof row[col] === 'number' ? row[col].toLocaleString(undefined, { maximumFractionDigits: 2 }) : String(row[col])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-2 bg-[var(--surface-subtle)] border-t border-[var(--hairline)]">
            <span className="text-xs text-[var(--ink-secondary)] font-medium">
              Page {tablePage + 1} of {totalPages}
            </span>
            <div className="flex items-center gap-1">
              <button 
                onClick={() => setTablePage(p => Math.max(0, p - 1))}
                disabled={tablePage === 0}
                className="p-1 rounded-[var(--radius-control)] hover:bg-[var(--surface)] disabled:opacity-50 transition-colors"
              >
                <ChevronLeft size={16} className="text-[var(--ink-secondary)]" />
              </button>
              <button 
                onClick={() => setTablePage(p => Math.min(totalPages - 1, p + 1))}
                disabled={tablePage === totalPages - 1}
                className="p-1 rounded-[var(--radius-control)] hover:bg-[var(--surface)] disabled:opacity-50 transition-colors"
              >
                <ChevronRight size={16} className="text-[var(--ink-secondary)]" />
              </button>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderSuccess = () => {
    if (response?.clarification_required) {
      return renderClarification(response.clarification_required);
    }

    return (
      <div className="flex items-start gap-4 w-full mt-4">
        <div className="w-8 h-8 rounded-full bg-[var(--accent)]/10 flex items-center justify-center shrink-0 border border-[var(--accent)]/20">
          <Sparkles size={16} className="text-[var(--accent)]" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="bg-[var(--surface)] border border-[var(--hairline)] rounded-[var(--radius-card)] p-5 shadow-[var(--shadow-lift)] w-full">
            <p className="text-[var(--ink)] text-lg mb-6 leading-relaxed">
              {response.summary}
            </p>
            
            {response.chart && (
              <div className="w-full h-[400px]">
                <ChartRenderer payload={response.chart} />
              </div>
            )}

            {renderTable(response.chart)}

            {/* Interactive Footer */}
            <div className="mt-6 pt-4 border-t border-[var(--hairline)] flex flex-wrap items-center gap-3">
              <button className="flex items-center gap-1.5 text-sm font-medium text-[var(--ink-secondary)] hover:text-[var(--ink)] transition-colors px-3 py-1.5 rounded-[var(--radius-control)] hover:bg-[var(--surface-subtle)]">
                <Pin size={16} />
                Pin to dashboard
              </button>
              <button 
                onClick={() => {
                  const input = document.querySelector('input[type="text"]') as HTMLInputElement;
                  if (input) input.focus();
                }}
                className="flex items-center gap-1.5 text-sm font-medium text-[var(--ink-secondary)] hover:text-[var(--ink)] transition-colors px-3 py-1.5 rounded-[var(--radius-control)] hover:bg-[var(--surface-subtle)]"
              >
                <MessageCircle size={16} />
                Ask follow-up
              </button>
              <button 
                onClick={() => openQueryPlanDrawer(response.answer_id)}
                className="flex items-center gap-1.5 text-sm font-medium text-[var(--ink-secondary)] hover:text-[var(--ink)] transition-colors px-3 py-1.5 rounded-[var(--radius-control)] hover:bg-[var(--surface-subtle)] ml-auto"
              >
                <FileCode2 size={16} />
                Show query plan
              </button>
            </div>
          </div>

          {/* Suggested Followups */}
          {response.suggested_followups && response.suggested_followups.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2 ml-2">
              {response.suggested_followups.map((followup: string, i: number) => (
                <button 
                  key={i} 
                  className="text-xs font-semibold uppercase tracking-widest bg-[var(--surface)] hover:bg-[var(--surface-subtle)] border border-[var(--hairline)] rounded-[var(--radius-pill)] px-3 py-1.5 text-[var(--ink-secondary)] transition-colors shadow-sm"
                  onClick={() => submitAskQuestion(followup)}
                >
                  {followup}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col w-full max-w-4xl mx-auto py-2">
      {renderQuestion()}
      {status === 'loading' && renderLoading()}
      {status === 'error' && renderError()}
      {status === 'success' && renderSuccess()}
    </div>
  );
}
