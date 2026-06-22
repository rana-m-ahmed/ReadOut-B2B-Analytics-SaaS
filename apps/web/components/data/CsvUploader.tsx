"use client";

import { useState, useRef, ChangeEvent } from 'react';
import { UploadCloud, FileType, AlertCircle } from 'lucide-react';
import { Button } from '../ui/button';
import { apiClient } from '../../lib/api/client';
import { Card } from '../ui/card';
import clsx from 'clsx';

const MAX_UPLOAD_MB = 50;
const MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024;

export function CsvUploader({ onUploadComplete }: { onUploadComplete: (datasetId: string) => void }) {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [statusText, setStatusText] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = (selectedFile: File) => {
    setError(null);
    if (!selectedFile.name.toLowerCase().endsWith('.csv')) {
      setError("Invalid format, please upload a CSV");
      return false;
    }
    if (selectedFile.size > MAX_UPLOAD_BYTES) {
      setError(`File is too large (max ${MAX_UPLOAD_MB}MB)`);
      return false;
    }
    return true;
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (selected && validateFile(selected)) {
      setFile(selected);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const dropped = e.dataTransfer.files?.[0];
    if (dropped && validateFile(dropped)) {
      setFile(dropped);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setIsUploading(true);
    setProgress(0);
    setError(null);

    try {
      setStatusText("Requesting upload URL...");
      const { upload_url, dataset_id } = await apiClient.getUploadUrl(file.name, file.size);

      setStatusText("Uploading file...");
      
      // Use XMLHttpRequest for progress
      await new Promise<void>((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.upload.addEventListener('progress', (event) => {
          if (event.lengthComputable) {
            const pct = Math.round((event.loaded / event.total) * 100);
            setProgress(pct);
          }
        });
        
        xhr.addEventListener('load', () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve();
          } else {
            reject(new Error(`Upload failed with status ${xhr.status}`));
          }
        });
        
        xhr.addEventListener('error', () => reject(new Error('Network error during upload')));
        
        xhr.open('PUT', upload_url);
        // Supabase storage presigned URL expects binary PUT
        xhr.send(file);
      });

      setStatusText("Profiling dataset...");
      setProgress(100);
      await apiClient.profileDataset(dataset_id);
      
      onUploadComplete(dataset_id);
    } catch (err: any) {
      console.error("Upload flow error:", err);
      if (err.status === 413) {
        setError(`File is too large (max ${MAX_UPLOAD_MB}MB)`);
      } else {
        setError("Server error, please try again");
      }
      setIsUploading(false);
    }
  };

  return (
    <Card className="w-full max-w-lg mx-auto p-6 flex flex-col gap-4 shadow-[var(--shadow-float)] border-[var(--hairline)]">
      <div 
        data-testid="dropzone"
        className={clsx(
          "border-2 border-dashed rounded-[var(--radius-card)] p-8 flex flex-col items-center justify-center text-center transition-colors cursor-pointer relative",
          isDragging ? "border-[var(--accent)] bg-[var(--accent)]/5" : "border-[var(--hairline)] hover:bg-[var(--surface-subtle)]",
          isUploading && "pointer-events-none opacity-50"
        )}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => !isUploading && fileInputRef.current?.click()}
      >
        <input 
          type="file" 
          accept=".csv" 
          className="hidden" 
          ref={fileInputRef} 
          onChange={handleFileChange}
          data-testid="file-input"
        />
        
        <UploadCloud size={48} className="text-[var(--ink-secondary)] mb-4" />
        <h3 className="text-lg font-bold text-[var(--ink)] mb-2">Drag & Drop your CSV here</h3>
        <p className="text-sm text-[var(--ink-secondary)] mb-4">or click to browse from your computer</p>
        <p className="text-xs text-[var(--ink-secondary)] font-medium">Max file size: {MAX_UPLOAD_MB}MB</p>
      </div>

      {error && (
        <div data-testid="upload-error" className="flex items-center gap-2 p-3 bg-[var(--danger)]/10 text-[var(--danger)] rounded-[var(--radius-control)]">
          <AlertCircle size={18} className="shrink-0" />
          <span className="text-sm font-semibold">{error}</span>
        </div>
      )}

      {file && !isUploading && (
        <div className="flex items-center justify-between p-3 border border-[var(--hairline)] rounded-[var(--radius-control)] bg-[var(--surface)]">
          <div className="flex items-center gap-3 overflow-hidden">
            <FileType className="text-[var(--accent)] shrink-0" />
            <span className="text-sm font-medium text-[var(--ink)] truncate" data-testid="selected-filename">{file.name}</span>
          </div>
          <Button onClick={handleUpload} data-testid="upload-button" variant="default" size="sm">Upload</Button>
        </div>
      )}

      {isUploading && (
        <div className="flex flex-col gap-2 p-4 border border-[var(--hairline)] rounded-[var(--radius-control)] bg-[var(--surface-subtle)]">
          <div className="flex justify-between items-center text-sm font-medium">
            <span className="text-[var(--ink)]">{statusText}</span>
            <span className="text-[var(--ink-secondary)]">{progress}%</span>
          </div>
          <div className="w-full h-2 bg-[var(--hairline)] rounded-full overflow-hidden">
            <div 
              className="h-full bg-[var(--accent)] transition-all duration-300 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}
    </Card>
  );
}
