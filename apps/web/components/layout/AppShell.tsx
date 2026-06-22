"use client";
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';
import { MobileNav } from './MobileNav';
import { useAppStore } from '../../lib/store/useAppStore';
import { motion } from 'framer-motion';
import { QueryPlanDrawer } from '../ask/QueryPlanDrawer';

export function AppShell({ children }: { children: React.ReactNode }) {
  const isDrawerOpen = useAppStore(state => state.queryPlanDrawer.isOpen);

  return (
    <>
      <motion.div 
        animate={{ 
          scale: isDrawerOpen ? 0.98 : 1, 
          borderRadius: isDrawerOpen ? '1rem' : '0rem',
          opacity: isDrawerOpen ? 0.5 : 1
        }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
        className="flex h-screen w-full bg-[var(--canvas)] overflow-hidden origin-center"
      >
        <Sidebar />
        <div className="flex flex-col flex-1 min-w-0">
          <TopBar />
          <main className="flex-1 overflow-y-auto px-4 md:px-0 md:pr-4 pb-24 md:pb-4">
            <div className="h-full rounded-[var(--radius-card)] bg-transparent">
              {children}
            </div>
          </main>
        </div>
        <MobileNav />
      </motion.div>
      <QueryPlanDrawer />
    </>
  );
}
