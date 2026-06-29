"use client";

import { useEffect, useState } from "react";
import { ChevronDown, CircleUserRound, LogOut, Radio } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { api } from "@/lib/api/client";
import { useAppStore } from "@/stores/app-store";

export function TopBar() {
  const router = useRouter();
  const [anonymous, setAnonymous] = useState(false);
  const [datasets, setDatasets] = useState<{ id: string; name: string }[]>([]);
  const active = useAppStore((state) => state.activeDataset);
  const setActive = useAppStore((state) => state.setActiveDataset);
  const collapsed = useAppStore((state) => state.sidebarCollapsed);

  useEffect(() => {
    createClient().auth.getUser().then(({ data }) => setAnonymous(Boolean(data.user?.is_anonymous)));
    api.getDatasets().then((data) => {
      setDatasets(data);
      if (!useAppStore.getState().activeDataset && data[0]) setActive(data[0].id);
    }).catch(() => undefined);
  }, [setActive]);

  async function signOut() {
    await createClient().auth.signOut();
    router.replace("/");
    router.refresh();
  }

  return (
    <header className={`dashboard-topbar fixed left-4 right-4 top-4 z-20 flex h-16 items-center justify-between px-3 transition-[left] md:px-4 ${collapsed ? "md:left-[104px]" : "md:left-[256px]"}`}>
      <label className="dashboard-dataset-select relative min-w-0">
        <span className="sr-only">Active dataset</span>
        <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[var(--marketing-mint)]"><Radio size={14}/></span>
        <select value={active ?? ""} onChange={(event) => setActive(event.target.value || null)} className="min-h-10 max-w-[190px] appearance-none bg-transparent pl-9 pr-8 text-xs font-semibold outline-none sm:max-w-[270px] sm:text-sm">
          <option value="">Choose dataset</option>
          {datasets.map((dataset) => <option value={dataset.id} key={dataset.id}>{dataset.name}</option>)}
        </select>
        <ChevronDown className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-white/35" size={14}/>
      </label>
      <div className="flex items-center gap-2">
        {anonymous && <span className="dashboard-demo-badge"><span className="size-1.5 rounded-full bg-[var(--warning)]"/>Demo session</span>}
        <span className="hidden h-7 w-px bg-white/[.08] sm:block"/>
        <Link href="/dashboard/settings" className="dashboard-icon-button" aria-label="Account settings"><CircleUserRound size={17}/></Link>
        <button onClick={signOut} className="dashboard-icon-button" aria-label="Sign out"><LogOut size={16}/></button>
      </div>
    </header>
  );
}
