export function formatCents(cents: number): string {
  return `$${(cents / 10).toFixed(2)}`;
}
