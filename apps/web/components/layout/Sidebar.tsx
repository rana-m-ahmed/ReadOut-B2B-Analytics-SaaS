"use client";
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAppStore } from '../../lib/store/useAppStore';
import { LayoutDashboard, MessageSquare, BarChart2, Activity, Database, Settings, PanelLeftClose, PanelLeftOpen } from 'lucide-react';
import clsx from 'clsx';

const navItems = [
  { name: 'Overview', href: '/overview', icon: LayoutDashboard },
  { name: 'Ask', href: '/ask', icon: MessageSquare },
  { name: 'Insights', href: '/insights', icon: BarChart2 },
  { name: 'Anomalies', href: '/anomalies', icon: Activity },
  { name: 'Data Sources', href: '/data-sources', icon: Database },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { sidebarCollapsed, toggleSidebar } = useAppStore();

  return (
    <aside
      data-testid="sidebar"
      className={clsx(
        "hidden md:flex flex-col transition-all duration-300 ease-in-out bg-[var(--surface)] shrink-0 z-40",
        "m-4 rounded-[var(--radius-card)] shadow-[var(--shadow-dock)]",
        sidebarCollapsed ? "w-20" : "w-64"
      )}
    >
      <div className="flex h-16 items-center justify-between px-4 shrink-0">
        {!sidebarCollapsed && <span className="font-bold text-lg text-[var(--ink)]">ReadOut</span>}
        <button 
          onClick={toggleSidebar} 
          data-testid="sidebar-toggle"
          className="p-2 text-[var(--ink-secondary)] hover:text-[var(--ink)] hover:bg-[var(--surface-subtle)] rounded-[var(--radius-control)] ml-auto"
          aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {sidebarCollapsed ? <PanelLeftOpen size={20} /> : <PanelLeftClose size={20} />}
        </button>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-2 overflow-y-auto">
        {navItems.map((item) => {
          const isActive = pathname?.startsWith(item.href);
          return (
            <Link
              key={item.name}
              href={item.href}
              title={sidebarCollapsed ? item.name : undefined}
              className={clsx(
                "flex items-center gap-3 px-3 py-2.5 rounded-[var(--radius-control)] transition-colors",
                isActive 
                  ? "bg-[var(--accent)]/10 text-[var(--accent)] font-medium" 
                  : "text-[var(--ink-secondary)] hover:bg-[var(--surface-subtle)] hover:text-[var(--ink)]"
              )}
            >
              <item.icon size={20} className={clsx("shrink-0", isActive ? "text-[var(--accent)]" : "text-[var(--ink-secondary)]")} />
              {!sidebarCollapsed && <span>{item.name}</span>}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
