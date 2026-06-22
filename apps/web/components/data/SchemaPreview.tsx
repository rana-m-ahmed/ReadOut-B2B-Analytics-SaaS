"use client";

import { ProfileResponse } from '../../lib/api/client';
import { Card } from '../ui/card';
import { AlertCircle, CheckCircle2, AlertTriangle, Hash, Type, Calendar, Fingerprint, PieChart, Info } from 'lucide-react';
import clsx from 'clsx';

function TypeIcon({ type }: { type: string }) {
  switch (type) {
    case 'number': return <Hash size={16} className="text-blue-500" />;
    case 'string': return <Type size={16} className="text-green-500" />;
    case 'date': return <Calendar size={16} className="text-purple-500" />;
    case 'category': return <PieChart size={16} className="text-amber-500" />;
    case 'boolean': return <Fingerprint size={16} className="text-red-500" />;
    default: return <Info size={16} className="text-[var(--ink-secondary)]" />;
  }
}

export function SchemaPreview({ profile }: { profile: ProfileResponse }) {
  const isHealthy = profile.quality_score >= 80;
  const isWarning = profile.quality_score >= 50 && profile.quality_score < 80;

  return (
    <div className="flex flex-col gap-6 w-full max-w-5xl mx-auto" data-testid="schema-preview">
      {/* Summary Header */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-4 flex flex-col justify-center items-start border-[var(--hairline)] shadow-[var(--shadow-float)]">
          <span className="text-sm font-semibold text-[var(--ink-secondary)] uppercase tracking-wider mb-1">Rows Detected</span>
          <span className="text-3xl font-bold font-mono text-[var(--ink)]">{profile.row_count.toLocaleString()}</span>
        </Card>

        <Card className="p-4 flex flex-col justify-center items-start border-[var(--hairline)] shadow-[var(--shadow-float)]">
          <span className="text-sm font-semibold text-[var(--ink-secondary)] uppercase tracking-wider mb-1">Data Quality</span>
          <div className="flex items-center gap-2">
            <span className={clsx(
              "text-3xl font-bold font-mono",
              isHealthy ? "text-[var(--success)]" : isWarning ? "text-[var(--warning)]" : "text-[var(--danger)]"
            )}>
              {profile.quality_score}%
            </span>
            {isHealthy ? <CheckCircle2 className="text-[var(--success)]" size={24} /> : <AlertTriangle className={isWarning ? "text-[var(--warning)]" : "text-[var(--danger)]"} size={24} />}
          </div>
        </Card>

        <Card className="p-4 flex flex-col justify-center items-start border-[var(--hairline)] shadow-[var(--shadow-float)]">
          <span className="text-sm font-semibold text-[var(--ink-secondary)] uppercase tracking-wider mb-1">Columns</span>
          <span className="text-3xl font-bold font-mono text-[var(--ink)]">{profile.columns.length}</span>
        </Card>
      </div>

      {profile.warnings.length > 0 && (
        <div className="bg-[var(--warning)]/10 border border-[var(--warning)]/20 p-4 rounded-[var(--radius-card)] flex flex-col gap-2">
          <div className="flex items-center gap-2 text-[var(--warning)] font-bold">
            <AlertCircle size={20} />
            <h4>Schema Warnings</h4>
          </div>
          <ul className="list-disc pl-8 text-sm text-[var(--ink-secondary)] space-y-1">
            {profile.warnings.map((w, i) => <li key={i}>{w}</li>)}
          </ul>
        </div>
      )}

      {/* Columns Table */}
      <Card className="overflow-hidden border-[var(--hairline)] shadow-[var(--shadow-float)]">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-[var(--surface-subtle)] text-[var(--ink-secondary)]">
              <tr>
                <th className="px-6 py-4 font-semibold uppercase tracking-wider">Column</th>
                <th className="px-6 py-4 font-semibold uppercase tracking-wider">Type</th>
                <th className="px-6 py-4 font-semibold uppercase tracking-wider">Fill Rate</th>
                <th className="px-6 py-4 font-semibold uppercase tracking-wider">Sample Data</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--hairline)] bg-[var(--surface)]">
              {profile.columns.map((col, idx) => {
                const fillRate = 100 - (col.missing_percent || 0);
                return (
                  <tr key={idx} className="hover:bg-[var(--surface-subtle)]/50 transition-colors">
                    <td className="px-6 py-4">
                      {/* Strictly rendering display_name per Phase requirement */}
                      <span className="font-bold text-[var(--ink)]" data-testid={`display-name-${idx}`}>{col.display_name}</span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <TypeIcon type={col.data_type} />
                        <span className="font-medium capitalize text-[var(--ink-secondary)]">{col.data_type}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2 w-32">
                        <span className="font-mono text-xs w-10 text-right">{fillRate.toFixed(0)}%</span>
                        <div className="flex-1 h-1.5 bg-[var(--hairline)] rounded-full overflow-hidden">
                          <div 
                            className={clsx("h-full rounded-full", fillRate > 80 ? "bg-[var(--success)]" : fillRate > 50 ? "bg-[var(--warning)]" : "bg-[var(--danger)]")}
                            style={{ width: `${fillRate}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex flex-wrap gap-1 max-w-xs">
                        {col.sample_values?.slice(0, 3).map((val, i) => (
                          <span key={i} className="inline-block px-2 py-0.5 bg-[var(--canvas)] border border-[var(--hairline)] rounded text-xs text-[var(--ink-secondary)] truncate max-w-[100px]">
                            {String(val)}
                          </span>
                        ))}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
