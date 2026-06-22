import { render, screen } from '@testing-library/react';
import { expect, test, describe } from 'vitest';
import { SchemaPreview } from '../components/data/SchemaPreview';

const mockProfile = {
  dataset_id: '123',
  row_count: 1000,
  quality_score: 95,
  warnings: [],
  columns: [
    {
      name: 'internal_col_1',
      display_name: 'Revenue Column',
      data_type: 'number',
      semantic_role: null,
      missing_percent: 0,
      sample_values: [100, 200, 300]
    }
  ]
};

describe('SchemaPreview', () => {
  test('renders display_name and hides internal name', () => {
    const { container } = render(<SchemaPreview profile={mockProfile as any} />);

    expect(screen.getByTestId('display-name-0').textContent).toBe('Revenue Column');
    
    // The internal name should NOT be rendered in the DOM
    const html = container.innerHTML;
    expect(html).not.toContain('internal_col_1');
  });
});
