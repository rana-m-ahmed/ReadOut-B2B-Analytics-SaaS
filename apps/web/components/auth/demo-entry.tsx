"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { Card } from "@/components/ui/card";
import { api } from "@/lib/api/client";
import { useAppStore } from "@/stores/app-store";

export function DemoEntry() {
  const router = useRouter(),
    [error, setError] = useState("");
  useEffect(() => {
    let live = true;
    (async () => {
      try {
        const client = createClient();
        const { data } = await client.auth.getSession();

        if (!data.session) {
          const { data: anonData, error } = await client.auth.signInAnonymously();
          if (error || !anonData.session) throw error ?? new Error("Anonymous session missing");
        }

        const datasets = await api.getDatasets();
        const demo = datasets.find((d) => d.source_type === "demo_seed") || datasets[0];
        if (!demo) throw new Error("Demo dataset unavailable");
        useAppStore.getState().setActiveDataset(demo.id);

        if (live) {
          router.replace("/dashboard/overview");
          router.refresh();
        }
      } catch {
        if (live)
          setError("The demo session could not start. Check the public Supabase configuration and try again.");
      }
    })();
    return () => {
      live = false;
    };
  }, [router]);
  return (
    <Card className="grid w-[min(92vw,440px)] justify-items-center gap-4 p-9 text-center">
      <div className="h-10 w-10 animate-pulse rounded-full bg-[var(--accent)]" />
      <h1 className="text-2xl font-bold">Preparing your demo workspace</h1>
      <p className="text-sm text-[var(--ink-secondary)]">
        Loading a safe sample dataset so you can ask a real question.
      </p>
      {error && (
        <p role="alert" className="text-[var(--danger)]">
          {error}
        </p>
      )}
    </Card>
  );
}
