import { create } from 'zustand'
import { apiClient, ApiError } from '../api/client'

const CATEGORY_COLORS = [
  'var(--color-chart-1)',
  'var(--color-chart-2)',
  'var(--color-chart-3)',
  'var(--color-chart-4)',
  'var(--color-chart-5)',
]

interface AppState {
  // Sidebar state
  sidebarCollapsed: boolean
  toggleSidebar: () => void
  setSidebarCollapsed: (collapsed: boolean) => void

  // Active dataset
  activeDatasetId: string | null
  setActiveDatasetId: (id: string | null) => void

  // Ask session
  currentAskSessionId: string | null
  setCurrentAskSessionId: (id: string | null) => void
  askMessages: any[]
  addAskMessage: (message: any) => void
  clearAskMessages: () => void

  isAsking: boolean
  askingQuestion: string | null
  loadingStage: string | null
  setAskingState: (isAsking: boolean, question?: string | null, stage?: string | null) => void

  // Query plan drawer
  queryPlanDrawer: {
    isOpen: boolean
    answerId: string | null
  }
  openQueryPlanDrawer: (answerId: string) => void
  closeQueryPlanDrawer: () => void

  // Category color mapping
  categoryColorMap: Record<string, string>
  getCategoryColor: (category: string) => string

  // Actions
  submitAskQuestion: (question: string) => Promise<void>
}

export const useAppStore = create<AppState>((set, get) => ({
  sidebarCollapsed: false,
  toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
  setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),

  activeDatasetId: null,
  setActiveDatasetId: (id) => set({ activeDatasetId: id }),

  currentAskSessionId: null,
  setCurrentAskSessionId: (id) => set({ currentAskSessionId: id }),
  askMessages: [],
  addAskMessage: (message) => set((state) => ({ askMessages: [...state.askMessages, message] })),
  clearAskMessages: () => set({ askMessages: [] }),

  isAsking: false,
  askingQuestion: null,
  loadingStage: null,
  setAskingState: (isAsking, question = null, stage = null) => set({ isAsking, askingQuestion: question, loadingStage: stage }),

  queryPlanDrawer: {
    isOpen: false,
    answerId: null,
  },
  openQueryPlanDrawer: (answerId) => set({ queryPlanDrawer: { isOpen: true, answerId } }),
  closeQueryPlanDrawer: () => set((state) => ({ queryPlanDrawer: { ...state.queryPlanDrawer, isOpen: false } })),

  categoryColorMap: {},
  getCategoryColor: (category: string) => {
    const { categoryColorMap } = get()
    
    if (categoryColorMap[category]) {
      return categoryColorMap[category]
    }

    // Assign a new color sequentially from the palette
    const existingCount = Object.keys(categoryColorMap).length
    const colorIndex = existingCount % CATEGORY_COLORS.length
    const newColor = CATEGORY_COLORS[colorIndex]

    set((state) => ({
      categoryColorMap: {
        ...state.categoryColorMap,
        [category]: newColor,
      },
    }))

    return newColor
  },

  submitAskQuestion: async (question: string) => {
    const state = get()
    if (!question.trim() || !state.activeDatasetId || state.isAsking) return

    const submittedQuestion = question.trim()
    
    // Start asking state
    set({ isAsking: true, askingQuestion: submittedQuestion, loadingStage: "Reading schema..." })

    // Setup staged loading timer (Frontend-only perceived progress)
    const STAGED_LOADING_COPY = [
      "Reading schema...",
      "Building query plan...",
      "Rendering chart...",
      "Finalizing response...",
    ]
    let stageIndex = 0
    const interval = setInterval(() => {
      stageIndex++
      if (stageIndex < STAGED_LOADING_COPY.length) {
        set({ loadingStage: STAGED_LOADING_COPY[stageIndex] })
      }
    }, 1200)

    try {
      const response = await apiClient.askQuestion(
        state.activeDatasetId, 
        submittedQuestion, 
        state.currentAskSessionId
      )

      clearInterval(interval)
      
      if (response.session_id && response.session_id !== state.currentAskSessionId) {
        set({ currentAskSessionId: response.session_id })
      }

      set((s) => ({
        askMessages: [...s.askMessages, {
          id: response.answer_id,
          status: 'success',
          question: submittedQuestion,
          response,
        }]
      }))
      
    } catch (error) {
      clearInterval(interval)
      
      const isDegraded = error instanceof ApiError && 
        ['upstream_llm_error', 'rate_limited', 'http_503', 'http_429'].includes(error.code)

      set((s) => ({
        askMessages: [...s.askMessages, {
          id: crypto.randomUUID(),
          status: 'error',
          question: submittedQuestion,
          isDegraded,
          errorMessage: error instanceof Error ? error.message : "An unexpected error occurred",
        }]
      }))
    } finally {
      set({ isAsking: false })
    }
  },
}))
