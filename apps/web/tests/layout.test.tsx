import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { expect, test, describe, beforeEach } from 'vitest';
import { Sidebar } from '../components/layout/Sidebar';
import { MobileNav } from '../components/layout/MobileNav';
import { useAppStore } from '../lib/store/useAppStore';

// Mock next/navigation
vi.mock('next/navigation', () => ({
  usePathname: () => '/overview',
}));

describe('Layout Components', () => {
  beforeEach(() => {
    useAppStore.setState({ sidebarCollapsed: false });
  });

  test('Sidebar collapse/expand correctly toggles Zustand state and the matching class', async () => {
    render(<Sidebar />);
    
    const sidebar = screen.getByTestId('sidebar');
    const toggleButton = screen.getByTestId('sidebar-toggle');
    
    // Initial state: expanded (w-64)
    expect(sidebar.className).toContain('w-64');
    expect(sidebar.className).not.toContain('w-20');
    expect(useAppStore.getState().sidebarCollapsed).toBe(false);
    
    // Collapse
    fireEvent.click(toggleButton);
    
    await waitFor(() => {
      expect(useAppStore.getState().sidebarCollapsed).toBe(true);
      expect(sidebar.className).toContain('w-20');
      expect(sidebar.className).not.toContain('w-64');
    });
    
    // Expand
    fireEvent.click(toggleButton);
    
    await waitFor(() => {
      expect(useAppStore.getState().sidebarCollapsed).toBe(false);
      expect(sidebar.className).toContain('w-64');
      expect(sidebar.className).not.toContain('w-20');
    });
  });

  test('Viewport-width rendering constraints for MobileNav and Sidebar', () => {
    const { container: mobileContainer } = render(<MobileNav />);
    const mobileNav = screen.getByTestId('mobile-nav');
    
    // MobileNav should be hidden on md and up
    const mobileClasses = mobileNav.className.split(' ');
    expect(mobileClasses).toContain('md:hidden');
    expect(mobileClasses).not.toContain('hidden');

    const { container: sidebarContainer } = render(<Sidebar />);
    const sidebar = screen.getByTestId('sidebar');
    
    // Sidebar should be hidden on smaller screens, block/flex on md and up
    const sidebarClasses = sidebar.className.split(' ');
    expect(sidebarClasses).toContain('hidden');
    expect(sidebarClasses).toContain('md:flex');
  });
});
