import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'
import { queryKeys } from '../lib/api/queryKeys'
import { useAppStore } from '../lib/store/useAppStore'
import { ColdStartIndicator } from '../components/ui/ColdStartIndicator'
import * as ReactQuery from '@tanstack/react-query'

vi.mock('@tanstack/react-query', () => ({
  useIsFetching: vi.fn(),
}))

vi.mock('framer-motion', async () => {
  const actual = await vi.importActual('framer-motion') as any;
  return {
    ...actual,
    AnimatePresence: ({ children }: any) => <>{children}</>,
  };
});

describe('React Query Keys', () => {
  it('produces stable and correctly shaped keys', () => {
    expect(queryKeys.datasets.all).toEqual(['datasets'])
    expect(queryKeys.datasets.list()).toEqual(['datasets', 'list'])
    expect(queryKeys.datasets.detail('123')).toEqual(['datasets', 'detail', '123'])
    expect(queryKeys.ask.session('abc')).toEqual(['ask', 'session', 'abc'])
  })
})

describe('useAppStore', () => {
  beforeEach(() => {
    // Reset Zustand store state before each test
    useAppStore.setState({
      sidebarCollapsed: false,
      activeDatasetId: null,
      currentAskSessionId: null,
      queryPlanDrawer: { isOpen: false, answerId: null },
      categoryColorMap: {}
    })
  })

  it('assigns a color once and returns the same color on repeat', () => {
    const store = useAppStore.getState()
    const colorWest = store.getCategoryColor('West')
    
    // Check if it assigned correctly
    expect(colorWest).toBeTruthy()
    
    // Check if repeat lookup returns the identical color
    const nextStore = useAppStore.getState()
    expect(nextStore.getCategoryColor('West')).toBe(colorWest)
  })

  it('assigns a different color for a new category deterministically', () => {
    const store = useAppStore.getState()
    const colorWest = store.getCategoryColor('West')
    const nextStore = useAppStore.getState()
    const colorEast = nextStore.getCategoryColor('East')

    expect(colorWest).not.toBe(colorEast)
    
    // It should loop back around or continue deterministic assignment
    // (We just ensure it's predictable and stable)
    expect(useAppStore.getState().categoryColorMap['West']).toBe(colorWest)
    expect(useAppStore.getState().categoryColorMap['East']).toBe(colorEast)
  })

  it('updates basic state correctly', () => {
    useAppStore.getState().setSidebarCollapsed(true)
    expect(useAppStore.getState().sidebarCollapsed).toBe(true)

    useAppStore.getState().setActiveDatasetId('data-123')
    expect(useAppStore.getState().activeDatasetId).toBe('data-123')

    useAppStore.getState().openQueryPlanDrawer('ans-456')
    expect(useAppStore.getState().queryPlanDrawer).toEqual({ isOpen: true, answerId: 'ans-456' })
  })
})

describe('ColdStartIndicator', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.clearAllMocks()
  })

  it('appears after delay threshold and disappears on success', async () => {
    // Start with fetching > 0
    vi.mocked(ReactQuery.useIsFetching).mockReturnValue(1)

    const { rerender } = render(<ColdStartIndicator />)

    // Should not be visible initially (timer hasn't fired)
    expect(screen.queryByTestId('cold-start-indicator')).not.toBeInTheDocument()

    // Advance by 2.4 seconds
    act(() => {
      vi.advanceTimersByTime(2400)
    })
    expect(screen.queryByTestId('cold-start-indicator')).not.toBeInTheDocument()

    // Advance to 2.5 seconds
    act(() => {
      vi.advanceTimersByTime(100)
    })
    
    expect(screen.getByTestId('cold-start-indicator')).toBeInTheDocument()

    // Now fetching completes
    act(() => {
      vi.mocked(ReactQuery.useIsFetching).mockReturnValue(0)
      rerender(<ColdStartIndicator />)
    })

    expect(screen.queryByTestId('cold-start-indicator')).not.toBeInTheDocument()
  })
})
