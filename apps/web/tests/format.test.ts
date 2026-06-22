import { expect, test, describe } from 'vitest';
import { formatCurrency, formatPercent, formatInteger, formatCompactNumber, autoFormat } from '../lib/format';

describe('Format Helpers', () => {
  test('formatCurrency', () => {
    expect(formatCurrency(1234.56)).toBe('$1,234.56');
    expect(formatCurrency(1000)).toBe('$1,000');
  });

  test('formatPercent', () => {
    expect(formatPercent(0.123)).toBe('12.3%');
    expect(formatPercent(1)).toBe('100.0%');
  });

  test('formatInteger', () => {
    expect(formatInteger(1234.56)).toBe('1,235');
  });

  test('formatCompactNumber', () => {
    expect(formatCompactNumber(1234500)).toBe('1.2M');
    expect(formatCompactNumber(1200)).toBe('1.2K');
  });

  test('autoFormat delegates correctly based on column name', () => {
    expect(autoFormat(1000, 'total_revenue')).toBe('$1,000');
    expect(autoFormat(0.15, 'conversion_rate')).toBe('15.0%');
    expect(autoFormat(15, 'conversion_percent')).toBe('15.0%'); // Normalizes >1 
    expect(autoFormat(100, 'order_count')).toBe('100');
    expect(autoFormat(1500000, 'impressions')).toBe('1.5M');
  });
});
