"use client";
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, MessageSquare, BarChart2, Settings } from 'lucide-react';
import clsx from 'clsx';

// Primary workflows that survive to mobile.
const mobileNavItems = [
  { name: 'Overview', href: '/overview', icon: LayoutDashboard },
  { name: 'Ask', href: '/ask', icon: MessageSquare },
  { name: 'Insights', href: '/insights', icon: BarChart2 },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export function MobileNav() {
  const pathname = usePathname();

  return (
    <nav data-testid="mobile-nav" className="md:hidden fixed bottom-4 left-4 right-4 bg-[var(--surface)] rounded-[var(--radius-card)] shadow-[var(--shadow-dock)] z-50 flex items-center justify-around px-2 py-3">
      {mobileNavItems.map((item) => {
        const isActive = pathname?.startsWith(item.href);
        return (
          <Link
            key={item.name}
            href={item.href}
            className={clsx(
              "flex flex-col items-center gap-1.5 p-2 rounded-[var(--radius-control)] transition-colors flex-1",
              isActive 
                ? "text-[var(--accent)]" 
                : "text-[var(--ink-secondary)] hover:bg-[var(--surface-subtle)]"
            )}
          >
            <item.icon size={22} className={clsx(isActive ? "text-[var(--accent)]" : "text-[var(--ink-secondary)]")} />
            <span className="text-[10px] font-semibold tracking-wider uppercase leading-none">{item.name}</span>
          </Link>
        );
      })}
    </nav>
  );
}
