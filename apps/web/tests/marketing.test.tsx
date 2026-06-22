import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { expect, test, describe, vi } from 'vitest';
import MarketingPage from '../app/(marketing)/page';
import { createClient } from '../lib/supabase/client';
import { useRouter } from 'next/navigation';

// Mock next/navigation
vi.mock('next/navigation', () => ({
  useRouter: vi.fn(),
}));

// Mock Supabase
vi.mock('../lib/supabase/client', () => ({
  createClient: vi.fn(),
}));

describe('Marketing Page', () => {
  test('CTA triggers anonymous sign-in and navigates to overview', async () => {
    const pushMock = vi.fn();
    (useRouter as any).mockReturnValue({ push: pushMock });

    const signInAnonymouslyMock = vi.fn().mockResolvedValue({ error: null });
    (createClient as any).mockReturnValue({
      auth: { signInAnonymously: signInAnonymouslyMock },
    });

    render(<MarketingPage />);

    const ctaButton = screen.getByTestId('launch-demo-btn');
    expect(ctaButton).toBeInTheDocument();

    fireEvent.click(ctaButton);

    await waitFor(() => {
      expect(signInAnonymouslyMock).toHaveBeenCalled();
      expect(pushMock).toHaveBeenCalledWith('/overview');
    });
  });
});
