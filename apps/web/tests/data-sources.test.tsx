import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { expect, test, describe, vi } from 'vitest';
import { DatasetList } from '../components/data/DatasetList';
import { apiClient } from '../lib/api/client';

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() })
}));

vi.mock('../lib/api/client', () => ({
  apiClient: {
    getDatasets: vi.fn(),
    getDatasetProfile: vi.fn(),
    deleteDataset: vi.fn()
  }
}));

const mockDataset = {
  id: '123',
  name: 'Test Dataset',
  description: null,
  source_type: 'upload',
  storage_bucket: 'datasets',
  storage_path: 'path',
  file_size_bytes: 1048576, // 1MB
  row_count: 5000,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString()
};

const mockProfile = {
  dataset_id: '123',
  row_count: 5000,
  quality_score: 90,
  warnings: [],
  columns: [
    {
      name: 'internal_col_1',
      display_name: 'Revenue Column',
      data_type: 'number',
      semantic_role: null,
      missing_percent: 0,
      unique_count: 100,
      sample_values: [100, 200, 300]
    }
  ]
};

describe('Data Sources Page', () => {
  test('renders list of datasets with mock data', async () => {
    (apiClient.getDatasets as any).mockResolvedValue([mockDataset]);
    (apiClient.getDatasetProfile as any).mockResolvedValue(mockProfile);

    render(<DatasetList />);

    await waitFor(() => {
      expect(screen.getByText('Test Dataset')).toBeInTheDocument();
      expect(screen.getByText(/5,000 rows/)).toBeInTheDocument();
    });
    
    // Check quality score rendered
    await waitFor(() => {
      expect(screen.getByTestId('quality-badge')).toHaveTextContent('90');
    });
  });

  test('delete confirmation flow works correctly', async () => {
    (apiClient.getDatasets as any).mockResolvedValue([mockDataset]);
    (apiClient.getDatasetProfile as any).mockResolvedValue(mockProfile);

    render(<DatasetList />);

    await waitFor(() => expect(screen.getByText('Test Dataset')).toBeInTheDocument());

    const startDeleteBtn = screen.getByTestId('start-delete');
    fireEvent.click(startDeleteBtn);

    // Cancel flow
    const cancelBtn = screen.getByTestId('cancel-delete');
    fireEvent.click(cancelBtn);
    expect(apiClient.deleteDataset).not.toHaveBeenCalled();

    // Confirm flow
    fireEvent.click(screen.getByTestId('start-delete'));
    const confirmBtn = screen.getByTestId('confirm-delete');
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(apiClient.deleteDataset).toHaveBeenCalledWith('123');
    });
  });

  test('column-quality table hides internal name string', async () => {
    (apiClient.getDatasets as any).mockResolvedValue([mockDataset]);
    (apiClient.getDatasetProfile as any).mockResolvedValue(mockProfile);

    const { container } = render(<DatasetList />);

    await waitFor(() => expect(screen.getByText('Test Dataset')).toBeInTheDocument());

    // Click to expand
    // We can find the expand button by getting all buttons and picking the one that expands
    const expandBtn = screen.getAllByRole('button').find(b => b.innerHTML.includes('lucide-chevron-down'));
    if (expandBtn) fireEvent.click(expandBtn);

    await waitFor(() => {
      expect(screen.getByTestId('column-table')).toBeInTheDocument();
    });

    expect(screen.getByTestId('display-name-0')).toHaveTextContent('Revenue Column');
    expect(container.innerHTML).not.toContain('internal_col_1');
  });
});
