"use client";

import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import { MobileNav } from "./mobile-nav";
import { ColdStartIndicator } from "@/components/ui/cold-start-indicator";
import { useAppStore } from "@/stores/app-store";

export function AppShell({ children }: { children: React.ReactNode }) {
  const collapsed = useAppStore((state) => state.sidebarCollapsed);
  return (
    <div className="dashboard-shell min-h-dvh">
      <a className="app-skip-link" href="#dashboard-content">
        Skip to dashboard content
      </a>
      <div className="dashboard-ambient" aria-hidden="true"><span/></div>
      <ColdStartIndicator />
      <Sidebar />
      <TopBar />
      <main id="dashboard-content" tabIndex={-1} className={`dashboard-main min-w-0 px-4 pb-32 pt-24 md:px-7 md:pb-10 ${collapsed ? "md:ml-[104px]" : "md:ml-[256px]"}`}>
        {children}
      </main>
      <MobileNav />
    </div>
  );
}
