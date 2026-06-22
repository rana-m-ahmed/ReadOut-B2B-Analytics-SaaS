"use client";
import { useRouter } from 'next/navigation';
import { CsvUploader } from '../../../components/data/CsvUploader';

export default function ConnectDataPage() {
  const router = useRouter();

  const handleUploadComplete = (datasetId: string) => {
    router.push(`/schema-preview?dataset_id=${datasetId}`);
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] py-12 px-4">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-[var(--ink)] mb-2">Connect your data</h1>
        <p className="text-[var(--ink-secondary)]">Upload a CSV file to get started. We'll automatically profile it and map the schema.</p>
      </div>
      <CsvUploader onUploadComplete={handleUploadComplete} />
    </div>
  );
}
