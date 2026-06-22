"use client";

import { useEffect, useState } from "react";
import { DatasetListItem, apiClient } from "../../lib/api/client";
import { DatasetCard } from "./DatasetCard";
import { Button } from "../ui/button";
import { Loader2, Plus, DatabaseZap } from "lucide-react";
import { useRouter } from "next/navigation";

export function DatasetList() {
  const [datasets, setDatasets] = useState<DatasetListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const fetchDatasets = async () => {
    setLoading(true);
    try {
      const data = await apiClient.getDatasets();
      setDatasets(data);
    } catch (e) {
      console.error("Failed to load datasets", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDatasets();
  }, []);

  const handleDelete = async (id: string) => {
    try {
      await apiClient.deleteDataset(id);
      setDatasets((prev) => prev.filter(d => d.id !== id));
    } catch (e) {
      console.error("Failed to delete dataset", e);
      alert("Failed to delete dataset");
    }
  };

  const loadDemoDataset = async () => {
    router.push('/demo');
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-[var(--ink-secondary)]">
        <Loader2 className="animate-spin mb-4" size={32} />
        <p>Loading your datasets...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 w-full max-w-5xl mx-auto" data-testid="dataset-list">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-[var(--ink)]">Your Datasets</h2>
        <div className="flex items-center gap-3">
          <Button variant="outline" onClick={loadDemoDataset} className="gap-2">
            <DatabaseZap size={16} />
            Use Demo Dataset
          </Button>
          <Button onClick={() => router.push('/connect-data')} className="gap-2">
            <Plus size={16} />
            Upload new CSV
          </Button>
        </div>
      </div>

      {datasets.length === 0 ? (
        <div className="p-12 border-2 border-dashed border-[var(--hairline)] rounded-[var(--radius-card)] text-center">
          <h3 className="text-lg font-bold text-[var(--ink)] mb-2">No datasets found</h3>
          <p className="text-[var(--ink-secondary)] mb-6">Upload your first CSV or use our sample data to get started.</p>
          <Button onClick={() => router.push('/connect-data')} className="gap-2">
            <Plus size={16} />
            Upload new CSV
          </Button>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {datasets.map(dataset => (
            <DatasetCard 
              key={dataset.id} 
              dataset={dataset} 
              onDelete={handleDelete} 
            />
          ))}
        </div>
      )}
    </div>
  );
}
