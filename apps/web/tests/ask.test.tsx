import { render, screen, fireEvent, act } from '@testing-library/react';
import { expect, test, describe, vi, beforeEach } from 'vitest';
import { AskBar } from '../components/ask/AskBar';
import { AskThread } from '../components/ask/AskThread';
import { QueryPlanDrawer } from '../components/ask/QueryPlanDrawer';
import { useAppStore } from '../lib/store/useAppStore';
import { apiClient, ApiError } from '../lib/api/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

vi.mock('../lib/api/client', async () => {
  const actual = await vi.importActual('../lib/api/client');
  return {
    ...actual,
    apiClient: {
      askQuestion: vi.fn(),
    },
    ApiError: class extends Error {
      code: string;
      constructor(msg: string, code: string) {
        super(msg);
        this.code = code;
      }
    }
  };
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={new QueryClient()}>
    {children}
  </QueryClientProvider>
);

describe('Ask System', () => {
  beforeEach(() => {
    useAppStore.setState({
      activeDatasetId: 'dataset-123',
      currentAskSessionId: 'session-456',
      askMessages: [],
      isAsking: false,
      askingQuestion: null,
      loadingStage: null,
      queryPlanDrawer: { isOpen: false, answerId: null }
    });
    vi.clearAllMocks();
  });

  test('AskBar calls askQuestion with correct payload', async () => {
    vi.mocked(apiClient.askQuestion).mockResolvedValueOnce({
      answer_id: 'ans-1',
      session_id: 'session-456',
      summary: 'Success',
      chart: null,
      query_plan: null,
      confidence: 'high',
      suggested_followups: [],
      clarification_required: null
    });

    render(<AskBar />, { wrapper });
    
    const input = screen.getByRole('textbox');
    fireEvent.change(input, { target: { value: 'How many orders?' } });
    
    const submitBtn = screen.getByTestId('ask-submit');
    await act(async () => {
      fireEvent.click(submitBtn);
    });

    expect(apiClient.askQuestion).toHaveBeenCalledWith('dataset-123', 'How many orders?', 'session-456');
    expect(useAppStore.getState().askMessages).toHaveLength(1);
    expect(useAppStore.getState().askMessages[0].question).toBe('How many orders?');
  });

  test('staged loading sequence changes copy deterministically', async () => {
    vi.useFakeTimers();
    let resolveAsk: any;
    const askPromise = new Promise((resolve) => {
      resolveAsk = resolve;
    });
    vi.mocked(apiClient.askQuestion).mockReturnValue(askPromise as any);

    render(
      <div className="flex flex-col h-screen">
        <AskThread />
        <AskBar />
      </div>,
      { wrapper }
    );

    const input = screen.getByRole('textbox');
    fireEvent.change(input, { target: { value: 'Slow query' } });
    fireEvent.click(screen.getByTestId('ask-submit'));

    // 0s: Reading schema...
    expect(screen.getByText('Reading schema...')).toBeInTheDocument();

    // Fast forward 1.2s -> Building query plan...
    act(() => {
      vi.advanceTimersByTime(1200);
    });
    expect(screen.getByText('Building query plan...')).toBeInTheDocument();

    // Fast forward another 1.2s -> Rendering chart...
    act(() => {
      vi.advanceTimersByTime(1200);
    });
    expect(screen.getByText('Rendering chart...')).toBeInTheDocument();

    // Resolve query
    await act(async () => {
      resolveAsk({
        answer_id: 'ans-1',
        session_id: 'session-456',
        summary: 'Done loading',
        chart: null,
        query_plan: null,
        confidence: 'high',
        suggested_followups: [],
        clarification_required: null
      });
      // Let the promise resolve and microtasks flush so clearInterval runs
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(screen.getByText('Done loading')).toBeInTheDocument();
    vi.useRealTimers();
  });

  test('clarification_required mock renders distinctly', async () => {
    useAppStore.setState({
      askMessages: [{
        id: '1',
        status: 'success',
        question: 'Ambiguous question',
        response: {
          answer_id: 'ans-1',
          session_id: 'session-456',
          summary: '',
          chart: null,
          query_plan: null,
          confidence: 'low',
          suggested_followups: ['Option A', 'Option B'],
          clarification_required: { code: 'ambiguous', message: 'Did you mean option A or B?' }
        }
      }]
    });

    render(<AskThread />, { wrapper });
    
    expect(screen.getByTestId('ask-clarification-state')).toBeInTheDocument();
    expect(screen.getByText('Did you mean option A or B?')).toBeInTheDocument();
    expect(screen.getByText('Option A')).toBeInTheDocument();
  });

  test('UpstreamLLMError renders graceful degradation UI, not generic error', async () => {
    useAppStore.setState({
      askMessages: [{
        id: '2',
        status: 'error',
        question: 'Broken query',
        isDegraded: true,
        errorMessage: 'Some internal upstream message we do not show'
      }]
    });

    render(<AskThread />, { wrapper });
    
    const errorNode = screen.getByTestId('ask-error-state');
    expect(errorNode).toBeInTheDocument();
    expect(screen.getByText("We're having trouble answering right now. Please try again shortly.")).toBeInTheDocument();
    expect(screen.queryByText("Some internal upstream message we do not show")).not.toBeInTheDocument();
  });

  test('AskThread never clears prior messages on new submission', async () => {
    useAppStore.setState({
      askMessages: [{
        id: 'msg-1',
        status: 'success',
        question: 'First question',
        response: { summary: 'First answer' }
      }]
    });

    vi.mocked(apiClient.askQuestion).mockResolvedValueOnce({
      answer_id: 'ans-2',
      session_id: 'session-456',
      summary: 'Second answer',
      chart: null,
      query_plan: null,
      confidence: 'high',
      suggested_followups: [],
      clarification_required: null
    });

    render(
      <div className="flex flex-col h-screen">
        <AskThread />
        <AskBar />
      </div>,
      { wrapper }
    );

    const input = screen.getByRole('textbox');
    fireEvent.change(input, { target: { value: 'Second question' } });
    
    await act(async () => {
      fireEvent.click(screen.getByTestId('ask-submit'));
    });

    // Check both are present
    expect(screen.getByText('First question')).toBeInTheDocument();
    expect(screen.getByText('First answer')).toBeInTheDocument();
    expect(screen.getAllByText('Second question').length).toBeGreaterThan(0);
  });

  test('QueryPlanDrawer opens and renders JSON intent and SQL', async () => {
    useAppStore.setState({
      askMessages: [{
        id: 'ans-debug',
        status: 'success',
        question: 'Show debug',
        response: {
          answer_id: 'ans-debug',
          session_id: 'session-456',
          summary: 'Debug answer',
          chart: null,
          query_plan: { intent: 'grouped_metric', metric: 'revenue' },
          debug_sql: 'SELECT * FROM test',
          confidence: 'high',
          suggested_followups: [],
          clarification_required: null
        }
      }]
    });

    render(
      <div className="flex flex-col h-screen">
        <AskThread />
        <QueryPlanDrawer />
      </div>,
      { wrapper }
    );

    // Open drawer
    await act(async () => {
      useAppStore.getState().openQueryPlanDrawer('ans-debug');
    });

    expect(screen.getByTestId('query-plan-drawer')).toBeInTheDocument();
    
    const debugJson = screen.getByTestId('debug-json');
    expect(debugJson.textContent).toContain('"intent": "grouped_metric"');
    
    const debugSql = screen.getByTestId('debug-sql');
    expect(debugSql.textContent).toContain('SELECT * FROM test');
  });

  test('suggested-followup chip click submits the chip text', async () => {
    useAppStore.setState({
      askMessages: [{
        id: 'ans-1',
        status: 'success',
        question: 'First question',
        response: {
          answer_id: 'ans-1',
          session_id: 'session-456',
          summary: 'Here you go',
          chart: null,
          query_plan: null,
          confidence: 'high',
          suggested_followups: ['Compare with previous period'],
          clarification_required: null
        }
      }]
    });

    vi.mocked(apiClient.askQuestion).mockResolvedValueOnce({
      answer_id: 'ans-2',
      session_id: 'session-456',
      summary: 'Done',
      chart: null,
      query_plan: null,
      confidence: 'high',
      suggested_followups: [],
      clarification_required: null
    });

    render(<AskThread />, { wrapper });

    const chip = screen.getByText('Compare with previous period');
    await act(async () => {
      fireEvent.click(chip);
    });

    expect(apiClient.askQuestion).toHaveBeenCalledWith('dataset-123', 'Compare with previous period', 'session-456');
    expect(useAppStore.getState().askMessages).toHaveLength(2);
  });

  test('session_id stays constant across 3 sequential submissions', async () => {
    vi.mocked(apiClient.askQuestion)
      .mockResolvedValueOnce({
        answer_id: 'ans-1',
        session_id: 'session-789', // New session from backend
        summary: 'Ans 1',
        chart: null,
        query_plan: null,
        confidence: 'high',
        suggested_followups: [],
        clarification_required: null
      })
      .mockResolvedValueOnce({
        answer_id: 'ans-2',
        session_id: 'session-789', // Same session
        summary: 'Ans 2',
        chart: null,
        query_plan: null,
        confidence: 'high',
        suggested_followups: [],
        clarification_required: null
      })
      .mockResolvedValueOnce({
        answer_id: 'ans-3',
        session_id: 'session-789', // Same session
        summary: 'Ans 3',
        chart: null,
        query_plan: null,
        confidence: 'high',
        suggested_followups: [],
        clarification_required: null
      });

    // Reset session ID to null to simulate fresh start
    useAppStore.setState({ currentAskSessionId: null });

    render(<AskBar />, { wrapper });
    
    const input = screen.getByRole('textbox');
    const submitBtn = screen.getByTestId('ask-submit');

    // Turn 1
    fireEvent.change(input, { target: { value: 'Q1' } });
    await act(async () => { fireEvent.click(submitBtn); });
    expect(apiClient.askQuestion).toHaveBeenLastCalledWith('dataset-123', 'Q1', null);
    expect(useAppStore.getState().currentAskSessionId).toBe('session-789');

    // Turn 2
    fireEvent.change(input, { target: { value: 'Q2' } });
    await act(async () => { fireEvent.click(submitBtn); });
    expect(apiClient.askQuestion).toHaveBeenLastCalledWith('dataset-123', 'Q2', 'session-789');

    // Turn 3
    fireEvent.change(input, { target: { value: 'Q3' } });
    await act(async () => { fireEvent.click(submitBtn); });
    expect(apiClient.askQuestion).toHaveBeenLastCalledWith('dataset-123', 'Q3', 'session-789');
  });
});
