"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { AlertTriangle, FileSpreadsheet, UploadCloud } from "lucide-react";
import { api, uploadBinary } from "@/lib/api/client";
import { useAppStore } from "@/stores/app-store";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
const MAX_MB = Number(process.env.NEXT_PUBLIC_MAX_UPLOAD_MB ?? 25),
  MAX_BYTES = MAX_MB * 1024 * 1024;
export function CsvUploader() {
  const router = useRouter(),
    setActive = useAppStore((s) => s.setActiveDataset),
    [file, setFile] = useState<File | null>(null),
    [error, setError] = useState(""),
    [drag, setDrag] = useState(false),
    [progress, setProgress] = useState(0),
    [stage, setStage] = useState("");
  function choose(next?: File) {
    setError("");
    setFile(null);
    if (!next) return;
    if (
      !next.name.toLowerCase().endsWith(".csv") &&
      !["text/csv", "application/vnd.ms-excel"].includes(next.type)
    )
      return setError(
        "Choose a CSV file. Other file types stay on your device.",
      );
    if (next.size > MAX_BYTES)
      return setError(
        `This file is too large. The current limit is ${MAX_MB} MB.`,
      );
    if (next.size === 0)
      return setError(
        "This CSV is empty. Choose a file with at least one row.",
      );
    setFile(next);
  }
  async function upload() {
    if (!file) return;
    try {
      setStage("Preparing secure upload");
      const ticket = await api.uploadUrl({
        filename: file.name,
        file_size_bytes: file.size,
      });
      setStage("Uploading CSV");
      await uploadBinary(ticket.upload_url, file, setProgress);
      setStage("Profiling columns and data quality");
      const profile = await api.profile(ticket.dataset_id);
      sessionStorage.setItem("readout:last-profile", JSON.stringify(profile));
      setActive(ticket.dataset_id);
      router.push(`/onboarding/schema-preview?dataset=${ticket.dataset_id}`);
    } catch {
      setStage("");
      setError("Readout could not process this file. Check the CSV and try again.");
    }
  }
  return (
    <Card className="p-6">
      <input
        id="csv-file-input"
        data-testid="file-input"
        className="sr-only"
        type="file"
        accept=".csv,text/csv"
        disabled={Boolean(stage)}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? "csv-upload-error" : "csv-upload-hint"}
        onChange={(e) => choose(e.target.files?.[0])}
      />
      <label
        htmlFor="csv-file-input"
        data-testid="dropzone"
        onDragOver={(e) => {
          e.preventDefault();
          setDrag(true);
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDrag(false);
          choose(e.dataTransfer.files[0]);
        }}
        className={`grid min-h-64 cursor-pointer place-items-center rounded-[var(--radius-card)] border-2 border-dashed p-7 text-center transition ${drag ? "scale-[1.01] border-[var(--accent)] bg-[color-mix(in_srgb,var(--accent)_7%,white)]" : "border-[var(--hairline)] hover:border-[var(--accent)]"}`}
      >
        <div>
          <UploadCloud className="mx-auto text-[var(--accent)]" size={38} />
          <h2 className="mt-4 text-xl font-bold">Drop your CSV here</h2>
          <p id="csv-upload-hint" className="mt-2 text-sm text-[var(--ink-secondary)]">
            or click to browse · up to {MAX_MB} MB
          </p>
        </div>
      </label>
      {file && !stage && (
        <div className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-xl bg-[var(--surface-subtle)] p-4">
          <span className="inline-flex min-w-0 items-center gap-2 text-sm font-semibold">
            <FileSpreadsheet size={18} />
            <span className="truncate">{file.name}</span>
          </span>
          <Button
            data-testid="upload-button"
            onClick={upload}
          >
            Upload and profile
          </Button>
        </div>
      )}
      {stage && (
        <div className="mt-5" aria-live="polite">
          <div className="flex justify-between text-sm font-semibold">
            <span>{stage}…</span>
            <span className="tabular">{progress}%</span>
          </div>
          <div
            className="mt-2 h-2 overflow-hidden rounded-full bg-[var(--hairline)]"
            role="progressbar"
            aria-label={stage}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={progress}
          >
            <div
              className="h-full bg-[var(--accent)] transition-[width] duration-300"
              style={{
                width: `${Math.max(progress, stage.includes("Profiling") ? 100 : 4)}%`,
              }}
            />
          </div>
        </div>
      )}
      {error && (
        <p
          data-testid="upload-error"
          id="csv-upload-error"
          role="alert"
          className="mt-4 flex items-center gap-2 rounded-xl bg-[color-mix(in_srgb,var(--warning)_12%,white)] p-3 text-sm"
        >
          <AlertTriangle className="text-[var(--warning)]" size={18} />
          {error}
        </p>
      )}
    </Card>
  );
}
