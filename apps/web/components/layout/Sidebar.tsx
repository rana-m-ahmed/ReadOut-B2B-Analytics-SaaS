"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronsLeft, ChevronsRight, Sparkles } from "lucide-react";
import { navItems } from "./nav-items";
import { useAppStore } from "@/stores/app-store";
import { ReadoutLogo } from "@/components/brand/readout-logo";
import { cn } from "@/lib/utils";

export function Sidebar() {
  const path = usePathname();
  const collapsed = useAppStore((state) => state.sidebarCollapsed);
  const toggle = useAppStore((state) => state.toggleSidebar);
  return (
    <aside className={cn("dashboard-sidebar fixed bottom-4 left-4 top-4 z-30 hidden md:flex md:flex-col", collapsed ? "w-[72px]" : "w-[224px]")}>
      <div className={cn("flex h-16 items-center", collapsed ? "justify-center" : "px-3")}>
        <ReadoutLogo href="/dashboard/overview" compact={collapsed} />
      </div>
      <div className="mx-2 h-px bg-white/[.07]"/>
      <nav aria-label="Dashboard navigation" className="mt-5 grid gap-1.5 px-2">
        {navItems.map(({ href, label, icon: Icon }) => {
          const active = path === href;
          return (
            <Link key={href} href={href} title={collapsed ? label : undefined} aria-current={active ? "page" : undefined} className={cn("dashboard-nav-item group", active && "is-active", collapsed && "justify-center px-0")}>
              <span className="dashboard-nav-icon"><Icon size={17}/></span>
              {!collapsed && <span>{label}</span>}
              {!collapsed && active && <span className="ml-auto size-1.5 rounded-full bg-[var(--marketing-mint)] shadow-[0_0_10px_var(--marketing-mint)]"/>}
            </Link>
          );
        })}
      </nav>
      {!collapsed && <div className="mx-2 mt-auto rounded-2xl border border-white/[.07] bg-white/[.035] p-3"><span className="flex size-7 items-center justify-center rounded-full bg-[rgba(168,255,120,.1)] text-[var(--marketing-mint)]"><Sparkles size={13}/></span><p className="mt-3 text-[11px] font-semibold text-white/70">Signal room ready</p><p className="mt-1 text-[9px] leading-4 text-white/70">Ask, scan, and pin decisions from one workspace.</p></div>}
      <button onClick={toggle} className={cn("dashboard-nav-item mx-2 mt-2 mb-1", collapsed && "justify-center px-0")} aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}>
        {collapsed ? <ChevronsRight size={17}/> : <><ChevronsLeft size={17}/><span>Collapse</span></>}
      </button>
    </aside>
  );
}
