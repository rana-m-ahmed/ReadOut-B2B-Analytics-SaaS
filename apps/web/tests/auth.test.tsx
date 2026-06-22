import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { DemoIndicator } from '../components/auth/DemoIndicator'
import { useCurrentUser } from '../lib/auth/useCurrentUser'
import { useRouter } from 'next/navigation'

// Mock next/navigation
vi.mock('next/navigation', () => ({
  useRouter: vi.fn(),
  usePathname: () => '/dashboard',
}))

const mockGetSession = vi.fn()
const mockOnAuthStateChange = vi.fn()

// Mock the Supabase module
vi.mock('../lib/supabase/client', () => {
  return {
    createClient: () => ({
      auth: {
        getSession: mockGetSession,
        onAuthStateChange: mockOnAuthStateChange
      }
    })
  }
})

// Dummy component using the hook
function ProtectedLayout({ children }: { children: React.ReactNode }) {
  const { isLoading } = useCurrentUser()
  
  if (isLoading) return <div>Loading...</div>
  return (
    <div>
      {children}
      <DemoIndicator />
    </div>
  )
}

describe('Auth components and useCurrentUser', () => {
  const mockPush = vi.fn()

  beforeEach(() => {
    vi.resetAllMocks()
    vi.mocked(useRouter).mockReturnValue({ push: mockPush } as any)
    mockOnAuthStateChange.mockReturnValue({
      data: { subscription: { unsubscribe: vi.fn() } }
    })
  })

  it('shows demo indicator with correct hours for anonymous session', async () => {
    const twoHoursAgo = new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString()
    
    mockGetSession.mockResolvedValue({
      data: { session: { user: { id: '123', is_anonymous: true, created_at: twoHoursAgo } } }
    })

    render(
      <ProtectedLayout>
        <div>Dashboard Content</div>
      </ProtectedLayout>
    )

    await waitFor(() => {
      expect(screen.queryByText('Loading...')).not.toBeInTheDocument()
    })

    await waitFor(() => {
      expect(screen.getByTestId('demo-indicator')).toBeInTheDocument()
      expect(screen.getByText(/resets in 70 hours/i)).toBeInTheDocument()
    })
    expect(mockPush).not.toHaveBeenCalled()
  })

  it('does not show demo indicator for real session', async () => {
    mockGetSession.mockResolvedValue({
      data: { session: { user: { id: '456', is_anonymous: false } } }
    })

    render(
      <ProtectedLayout>
        <div>Dashboard Content</div>
      </ProtectedLayout>
    )

    await waitFor(() => {
      expect(screen.queryByText('Loading...')).not.toBeInTheDocument()
    })

    expect(screen.queryByTestId('demo-indicator')).not.toBeInTheDocument()
    expect(mockPush).not.toHaveBeenCalled()
  })

  it('redirects appropriately when signed out', async () => {
    mockGetSession.mockResolvedValue({
      data: { session: null }
    })

    render(
      <ProtectedLayout>
        <div>Dashboard Content</div>
      </ProtectedLayout>
    )

    await waitFor(() => {
      expect(screen.queryByText('Loading...')).not.toBeInTheDocument()
    })

    expect(mockPush).toHaveBeenCalledWith('/login')
  })
})
