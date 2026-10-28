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
  return money(a.cents + b.cents, a.currency);
}

export function allocate(total: Money, ratios: number[]): Money[] {
  const sum = ratios.reduce((acc, ratio) => acc + ratio, 0);
  return ratios.map((ratio) => money(Math.floor((total.cents * ratio) / sum), total.currency));
}

export function format(m: Money): string {
  const units = Math.floor(m.cents / 100);
  const rest = m.cents % 100;
  return `${units}.${String(rest).padStart(2, "0")} ${m.currency}`;
}
