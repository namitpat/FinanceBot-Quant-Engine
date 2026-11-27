export interface Money {
  readonly cents: number;
  readonly currency: string;
}

export function money(cents: number, currency: string): Money {
  if (!Number.isInteger(cents)) {
    throw new RangeError(`cents must be an integer, got ${cents}`);
  }
  return { cents, currency };
}

export function add(a: Money, b: Money): Money {
  if (a.currency !== b.currency) {
    throw new RangeError(`Currency mismatch: ${a.currency} + ${b.currency}`);
  }
  return money(a.cents + b.cents, a.currency);
}

export function allocate(total: Money, ratios: number[]): Money[] {
  const sum = ratios.reduce((acc, ratio) => acc + ratio, 0);
  return ratios.map((ratio) => money(Math.floor((total.cents * ratio) / sum), total.currency));
}

export function format(m: Money): string {
  const sign = m.cents < 0 ? "-" : "";
  const abs = Math.abs(m.cents);
  const units = Math.floor(abs / 100);
  const rest = abs % 100;
  return `${sign}${units}.${String(rest).padStart(2, "0")} ${m.currency}`;
}
