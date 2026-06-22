"use client";

import { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { apiClient, ProfileResponse } from '../../../lib/api/client';
import { SchemaPreview } from '../../../components/data/SchemaPreview';
import { WalkthroughStepper } from '../../../components/onboarding/WalkthroughStepper';
import { Button } from '../../../components/ui/button';
import { Loader2 } from 'lucide-react';

function SchemaPreviewContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const datasetId = searchParams?.get('dataset_id');
  const [profile, setProfile] = useState<ProfileResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!datasetId) {
      router.push('/connect-data');
      return;
    }

    const loadProfile = async () => {
      try {
        const data = await apiClient.profileDataset(datasetId);
        setProfile(data);
      } catch (err) {
        setError("Failed to load schema profile.");
      }
    };

    loadProfile();
  }, [datasetId, router]);

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="text-[var(--danger)] font-bold mb-4">{error}</div>
        <Button onClick={() => router.push('/connect-data')}>Try Again</Button>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-[var(--ink-secondary)]">
        <Loader2 className="animate-spin mb-4" size={32} />
        <p>Loading schema preview...</p>
      </div>
    );
  }

  return (
    <div className="py-12 px-4">
      <div className="flex justify-between items-end max-w-5xl mx-auto mb-8">
        <div>
          <h1 className="text-3xl font-bold text-[var(--ink)] mb-2">Schema Verified</h1>
          <p className="text-[var(--ink-secondary)]">Review the data types and sample values detected.</p>
        </div>
        <Button size="lg" onClick={() => router.push('/overview')}>
          Continue to Dashboard
        </Button>
      </div>
      
      <SchemaPreview profile={profile} />
      <WalkthroughStepper />
    </div>
  );
}

export default function SchemaPreviewPage() {
  return (
    <Suspense fallback={<div className="p-12 text-center text-[var(--ink-secondary)]">Loading...</div>}>
      <SchemaPreviewContent />
    </Suspense>
  );
}
