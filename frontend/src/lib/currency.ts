const DEFAULT_CURRENCY = 'LKR';

export function formatCurrency(value: number | string | undefined, currency = DEFAULT_CURRENCY): string {
  if (value === undefined || value === null) {
    return `${currency} 0.00`;
  }

  const numeric = typeof value === 'number' ? value : Number(value);
  if (Number.isNaN(numeric)) {
    return `${currency} 0.00`;
  }

  return `${currency} ${numeric.toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}
