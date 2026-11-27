import type { Money } from "./money.mts";

export interface RateTable {
  readonly base: string;
  readonly rates: Readonly<Record<string, number>>;
}

export function convert(amount: Money, to: string, table: RateTable): Money {
  if (amount.currency === to) {
    return amount;
  }
  const fromRate = table.rates[amount.currency];
  const toRate = table.rates[to];
  const cents = Math.round((amount.cents / fromRate) * toRate);
  return { cents, currency: to };
}

export function convertAll(amounts: Money[], to: string, table: RateTable): Money {
  const cents = amounts.reduce((sum, amount) => sum + convert(amount, to, table).cents, 0);
  return { cents, currency: to };
}
