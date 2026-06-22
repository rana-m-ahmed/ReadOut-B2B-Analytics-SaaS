"use client";

import { useState, useEffect } from "react";
import { DatasetListItem, ProfileResponse, apiClient } from "../../lib/api/client";
import { Card } from "../ui/card";
import { Button } from "../ui/button";
import { Loader2, ChevronDown, ChevronUp, Trash2, Database, AlertTriangle, CheckCircle2, Hash, Type, Calendar, PieChart, Fingerprint, Info } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import clsx from "clsx";

function TypeIcon({ type }: { type: string }) {
  switch (type) {
    case 'number': return <Hash size={14} className="text-blue-500" />;
    case 'string': return <Type size={14} className="text-green-500" />;
    case 'date': return <Calendar size={14} className="text-purple-500" />;
    case 'category': return <PieChart size={14} className="text-amber-500" />;
    case 'boolean': return <Fingerprint size={14} className="text-red-500" />;
    default: return <Info size={14} className="text-[var(--ink-secondary)]" />;
  }
}

export function DatasetCard({ 
  dataset, 
  onDelete 
}: { 
  dataset: DatasetListItem; 
  onDelete: (id: string) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const [profile, setProfile] = useState<ProfileResponse | null>(null);
  const [loadingProfile, setLoadingProfile] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const fetchProfile = async () => {
    if (profile || loadingProfile) return;
    setLoadingProfile(true);
    try {
      const data = await apiClient.getDatasetProfile(dataset.id);
      setProfile(data);
    } catch (e) {
      console.error("Failed to fetch profile", e);
    } finally {
      setLoadingProfile(false);
    }
  };

  useEffect(() => {
    fetchProfile();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dataset.id]);

  const toggleExpand = () => {
    setExpanded(!expanded);
  };

  const isHealthy = profile && profile.quality_score >= 80;
  const isWarning = profile && profile.quality_score >= 50 && profile.quality_score < 80;
  
  return (
    <Card className="flex flex-col border-[var(--hairline)] shadow-[var(--shadow-lift)] transition-shadow hover:shadow-[var(--shadow-float)] overflow-hidden" data-testid="dataset-card">
      <div className="flex items-center justify-between p-4 bg-[var(--surface)]">
        <div className="flex items-center gap-4 flex-1">
          <div className="w-10 h-10 rounded-[var(--radius-control)] bg-[var(--accent)]/10 flex items-center justify-center shrink-0">
            <Database className="text-[var(--accent)]" size={20} />
          </div>
          <div>
            <h3 className="font-bold text-[var(--ink)] flex items-center gap-2">
              {dataset.name}
              {profile && (
                <span className={clsx(
                  "text-xs px-2 py-0.5 rounded-full font-semibold inline-flex items-center gap-1",
                  isHealthy ? "bg-[var(--success)]/10 text-[var(--success)]" : isWarning ? "bg-[var(--warning)]/10 text-[var(--warning)]" : "bg-[var(--danger)]/10 text-[var(--danger)]"
                )} data-testid="quality-badge">
                  {isHealthy ? <CheckCircle2 size={12} /> : <AlertTriangle size={12} />}
                  {profile.quality_score}
                </span>
              )}
            </h3>
            <p className="text-sm text-[var(--ink-secondary)] mt-0.5">
              {dataset.row_count.toLocaleString()} rows • {(dataset.file_size_bytes / (1024 * 1024)).toFixed(1)} MB • Analyzed {formatDistanceToNow(new Date(dataset.updated_at))} ago
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {showConfirm ? (
            <div className="flex items-center gap-2 mr-2 animate-in fade-in zoom-in" data-testid="delete-confirm">
              <span className="text-xs text-[var(--ink-secondary)] font-medium">Delete dataset?</span>
              <Button size="sm" variant="outline" onClick={() => setShowConfirm(false)} data-testid="cancel-delete">Cancel</Button>
              <Button size="sm" className="bg-[var(--danger)] text-white hover:bg-[var(--danger)]/90" onClick={() => onDelete(dataset.id)} data-testid="confirm-delete">Confirm</Button>
            </div>
          ) : (
            <Button size="sm" variant="ghost" className="text-[var(--danger)] hover:bg-[var(--danger)]/10" onClick={() => setShowConfirm(true)} data-testid="start-delete">
              <Trash2 size={16} />
            </Button>
          )}

          <Button size="sm" variant="ghost" onClick={toggleExpand}>
            {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </Button>
        </div>
      </div>

      {expanded && (
        <div className="border-t border-[var(--hairline)] bg-[var(--surface-subtle)] p-4">
          {!profile && loadingProfile && (
            <div className="flex items-center justify-center py-4 text-[var(--ink-secondary)]">
              <Loader2 className="animate-spin mr-2" size={16} />
              <span className="text-sm">Loading column details...</span>
            </div>
          )}
          {!profile && !loadingProfile && (
            <div className="text-center py-4 text-[var(--ink-secondary)] text-sm">Failed to load profile details.</div>
          )}
          {profile && (
            <div className="overflow-x-auto rounded-[var(--radius-card)] border border-[var(--hairline)] bg-[var(--surface)] shadow-[var(--shadow-float)]" data-testid="column-table">
              <table className="w-full text-left text-xs">
                <thead className="bg-[var(--surface-subtle)] text-[var(--ink-secondary)]">
                  <tr>
                    <th className="px-4 py-3 font-semibold uppercase tracking-wider">Column</th>
                    <th className="px-4 py-3 font-semibold uppercase tracking-wider">Role</th>
                    <th className="px-4 py-3 font-semibold uppercase tracking-wider">Type</th>
                    <th className="px-4 py-3 font-semibold uppercase tracking-wider">Fill Rate</th>
                    <th className="px-4 py-3 font-semibold uppercase tracking-wider">Unique</th>
                    <th className="px-4 py-3 font-semibold uppercase tracking-wider">Sample Values</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--hairline)]">
                  {profile.columns.map((col, idx) => {
                    const fillRate = 100 - (col.missing_percent || 0);
                    return (
                      <tr key={idx} className="hover:bg-[var(--surface-subtle)]/50 transition-colors">
                        <td className="px-4 py-3">
                          <span className="font-bold text-[var(--ink)]" data-testid={`display-name-${idx}`}>{col.display_name}</span>
                        </td>
                        <td className="px-4 py-3 text-[var(--ink-secondary)] capitalize">{col.semantic_role || '-'}</td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-1.5">
                            <TypeIcon type={col.data_type} />
                            <span className="font-medium capitalize text-[var(--ink-secondary)]">{col.data_type}</span>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2 w-24">
                            <span className="font-mono">{fillRate.toFixed(0)}%</span>
                            <div className="flex-1 h-1.5 bg-[var(--hairline)] rounded-full overflow-hidden">
                              <div 
                                className={clsx("h-full rounded-full", fillRate > 80 ? "bg-[var(--success)]" : fillRate > 50 ? "bg-[var(--warning)]" : "bg-[var(--danger)]")}
                                style={{ width: `${fillRate}%` }}
                              />
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3 font-mono text-[var(--ink-secondary)]">{col.unique_count?.toLocaleString() || '-'}</td>
                        <td className="px-4 py-3">
                          <div className="flex flex-wrap gap-1 max-w-xs">
                            {col.sample_values?.slice(0, 2).map((val, i) => (
                              <span key={i} className="inline-block px-1.5 py-0.5 bg-[var(--canvas)] border border-[var(--hairline)] rounded text-xs text-[var(--ink-secondary)] truncate max-w-[80px]">
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
          )}
        </div>
      )}
    </Card>
  );
}
