/* eslint-disable react-hooks/set-state-in-effect */
"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ChevronDown, Database, Trash2, Upload } from "lucide-react";
import { api } from "@/lib/api/client";
import type { DatasetT, ProfileT } from "@/lib/api/types";
import { useAppStore } from "@/stores/app-store";
import { CsvUploader } from "@/components/onboarding/csv-uploader";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ConfirmationDialog } from "@/components/ui/confirmation-dialog";
import { Modal } from "@/components/ui/modal";
import { Badge, EmptyState, ErrorState, Skeleton } from "@/components/ui/states";
import { formatDate } from "@/lib/format";

const size = (n: number) =>
  n < 1024
    ? `${n} B`
    : n < 1048576
      ? `${(n / 1024).toFixed(1)} KB`
      : `${(n / 1048576).toFixed(1)} MB`;

type DeleteSnapshot = {
  dataset: DatasetT;
  previousDatasets: DatasetT[];
  previousActive: string | null;
};

export function DataSourcesWorkspace() {
  const active = useAppStore((s) => s.activeDataset);
  const setActive = useAppStore((s) => s.setActiveDataset);
  const [datasets, setDatasets] = useState<DatasetT[] | null>(null);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  const [expanded, setExpanded] = useState<string | null>(null);
  const [profiles, setProfiles] = useState<Record<string, ProfileT>>({});
  const [deleting, setDeleting] = useState<DatasetT | null>(null);
  const [pendingDelete, setPendingDelete] = useState<DeleteSnapshot | null>(null);
  const [upload, setUpload] = useState(false);

  function load() {
    setError("");
    setStatus("");
    api
      .getDatasets()
      .then(setDatasets)
      .catch(() =>
        setError("Your data sources could not be loaded. Please try again."),
      );
  }

  useEffect(load, []);

  useEffect(() => {
    if (!status || error || !status.startsWith("Deleted")) return;
    const timer = window.setTimeout(() => setStatus(""), 1600);
    return () => window.clearTimeout(timer);
  }, [error, status]);

  async function expand(id: string) {
    if (expanded === id) return setExpanded(null);
    setExpanded(id);
    if (!profiles[id])
      try {
        const p = await api.getProfile(id);
        setProfiles((v) => ({ ...v, [id]: p }));
      } catch {
        setError(
          "That schema could not be loaded, but your other sources are still available.",
        );
      }
  }

  async function remove() {
    if (!deleting || !datasets) return;

    const snapshot: DeleteSnapshot = {
      dataset: deleting,
      previousDatasets: datasets,
      previousActive: active,
    };

    setPendingDelete(snapshot);
    setDeleting(null);
    setError("");
    setStatus(`Deleting “${snapshot.dataset.name}”…`);

    setDatasets(snapshot.previousDatasets.filter((d) => d.id !== snapshot.dataset.id));
    if (snapshot.previousActive === snapshot.dataset.id) setActive(null);

    try {
      await api.deleteDataset(snapshot.dataset.id);
      setStatus(`Deleted “${snapshot.dataset.name}”.`);
      if (expanded === snapshot.dataset.id) setExpanded(null);
      setProfiles((current) => {
        if (!(snapshot.dataset.id in current)) return current;
        const next = { ...current };
        delete next[snapshot.dataset.id];
        return next;
      });
    } catch {
      setDatasets(snapshot.previousDatasets);
      setActive(snapshot.previousActive);
      setStatus("");
      setError("Readout could not delete that dataset. The source was restored.");
    } finally {
      setPendingDelete(null);
    }
  }

  if (error && datasets === null) return <ErrorState message={error} retry={load} />;
  if (datasets === null)
    return (
      <div className="grid gap-4 md:grid-cols-2">
        <Skeleton />
        <Skeleton />
      </div>
    );

  return (
    <>
      <div className="dashboard-action-rail">
        <div className="flex items-center gap-3">
          <span className="flex size-9 items-center justify-center rounded-full bg-[rgba(109,229,238,.1)] text-[var(--marketing-cyan)]">
            <Database size={16} />
          </span>
          <div>
            <p className="dashboard-section-label">Source control</p>
            <p className="mt-1 text-xs text-white/70">
              Review quality, inspect schemas, and switch analysis context.
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link href="/demo">
            <Button variant="secondary">
              <Database size={16} />
              Use demo dataset
            </Button>
          </Link>
          <Button onClick={() => setUpload(true)}>
            <Upload size={16} />
            Upload CSV
          </Button>
        </div>
      </div>

      {(status || error) && (
        <p
          role={error ? "alert" : "status"}
          aria-live="polite"
          className={`mb-4 rounded-xl p-3 text-sm ${
            error
              ? "bg-[color-mix(in_srgb,var(--warning)_12%,white)]"
              : "bg-[color-mix(in_srgb,var(--success)_12%,white)]"
          }`}
        >
          {error || status}
        </p>
      )}

      {datasets.length === 0 ? (
        <EmptyState
          title="Connect your first dataset"
          description="Upload a CSV or open the curated demo workspace to experience Readout immediately."
          action={<Button onClick={() => setUpload(true)}>Choose a CSV</Button>}
        />
      ) : (
        <div className="grid gap-4">
          {datasets.map((d) => {
            const p = profiles[d.id];
            const isPendingDelete = pendingDelete?.dataset.id === d.id;
            return (
              <Card
                key={d.id}
                className={`signal-card dataset-card p-5 md:p-6 ${active === d.id ? "is-active" : ""} ${
                  isPendingDelete ? "opacity-50 transition-opacity duration-150" : ""
                }`}
              >
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-white/[.05] text-[var(--marketing-cyan)]">
                        <Database size={17} />
                      </span>
                      <h2 className="truncate text-xl font-semibold tracking-[-.035em]">{d.name}</h2>
                      {active === d.id && <Badge tone="success">Active</Badge>}
                      {isPendingDelete && <Badge tone="warning">Deleting</Badge>}
                    </div>
                    <p className="mt-2 text-sm text-[var(--ink-secondary)]">
                      {d.description || "CSV dataset ready for analysis"}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Link href={`/onboarding/schema-preview?dataset=${d.id}`}>
                      <Button size="sm" variant="ghost" disabled={isPendingDelete}>
                        Edit mapping
                      </Button>
                    </Link>
                    <Button size="sm" variant="secondary" disabled={isPendingDelete} onClick={() => setActive(d.id)}>
                      Use dataset
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => expand(d.id)}
                      aria-expanded={expanded === d.id}
                      disabled={isPendingDelete}
                    >
                      <ChevronDown className={expanded === d.id ? "rotate-180" : ""} size={16} />
                      Schema
                    </Button>
                    <Button
                      size="icon"
                      variant="ghost"
                      aria-label={`Delete ${d.name}`}
                      onClick={() => setDeleting(d)}
                      disabled={isPendingDelete}
                    >
                      <Trash2 size={16} />
                    </Button>
                  </div>
                </div>

                <dl className="tabular mt-5 grid grid-cols-2 gap-4 border-t border-[var(--hairline)] pt-4 text-sm sm:grid-cols-4">
                  <div>
                    <dt className="text-[var(--ink-secondary)]">Rows</dt>
                    <dd className="mt-1 font-bold">{d.row_count.toLocaleString()}</dd>
                  </div>
                  <div>
                    <dt className="text-[var(--ink-secondary)]">File size</dt>
                    <dd className="mt-1 font-bold">{size(d.file_size_bytes)}</dd>
                  </div>
                  <div>
                    <dt className="text-[var(--ink-secondary)]">Quality</dt>
                    <dd className="mt-1 font-bold">{p ? `${p.quality_score}%` : "Open schema"}</dd>
                  </div>
                  <div>
                    <dt className="text-[var(--ink-secondary)]">Last analyzed</dt>
                    <dd className="mt-1 font-bold">{formatDate(d.updated_at)}</dd>
                  </div>
                </dl>

                {expanded === d.id && (
                  <div className="mt-5 overflow-x-auto border-t border-[var(--hairline)] pt-4">
                    {!p ? (
                      <Skeleton className="h-32" />
                    ) : (
                      <table className="w-full min-w-[580px] text-left text-sm">
                        <thead>
                          <tr>
                            <th className="py-2">Column</th>
                            <th>Type</th>
                            <th>Role</th>
                            <th>Complete</th>
                          </tr>
                        </thead>
                        <tbody>
                          {p.columns.map((c) => (
                            <tr key={c.display_name} className="border-t border-[var(--hairline)]">
                              <td className="py-3 font-semibold">{c.display_name}</td>
                              <td>{c.data_type}</td>
                              <td>{c.semantic_role ?? "—"}</td>
                              <td className="tabular">{(100 - c.missing_percent).toFixed(1)}%</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      )}

      <Modal open={upload} onOpenChange={setUpload} title="Upload a new CSV">
        <CsvUploader />
      </Modal>

      <ConfirmationDialog
        open={!!deleting}
        onOpenChange={(v) => !v && setDeleting(null)}
        title="Delete dataset?"
        description={`Delete “${deleting?.name ?? "this dataset"}” and its related analysis? This cannot be undone.`}
        onConfirm={remove}
      />
    </>
  );
}
