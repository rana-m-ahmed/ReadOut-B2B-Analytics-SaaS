export function formatCurrency(value: number): string {
  if (value === null || value === undefined) return "-";
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatPercent(value: number): string {
  if (value === null || value === undefined) return "-";
  return new Intl.NumberFormat('en-US', {
    style: 'percent',
    minimumFractionDigits: 1,
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatInteger(value: number): string {
  if (value === null || value === undefined) return "-";
  return new Intl.NumberFormat('en-US', {
    maximumFractionDigits: 0,
  }).format(Math.round(value));
}

export function formatCompactNumber(value: number): string {
  if (value === null || value === undefined) return "-";
  return new Intl.NumberFormat('en-US', {
    notation: "compact",
    maximumFractionDigits: 1
  }).format(value);
}

export function autoFormat(value: number, name: string): string {
  if (value === null || value === undefined) return "-";
  const nameLower = name.toLowerCase();
  
  if (nameLower.includes('revenue') || nameLower.includes('price') || nameLower.includes('cost') || nameLower.includes('amount')) {
    return formatCurrency(value);
  }
  if (nameLower.includes('rate') || nameLower.includes('percent') || nameLower.includes('ratio') || nameLower.includes('proportion')) {
    // If the value is > 1 it's probably already a percentage scale, but standard requires treating 0.5 as 50%
    // We'll pass it as is to formatPercent, which multiplies by 100
    const val = value > 1 ? value / 100 : value;
    return formatPercent(val);
  }
  if (nameLower.includes('count') || nameLower.includes('qty') || nameLower.includes('units')) {
    return formatInteger(value);
  }
  return formatCompactNumber(value);
}
