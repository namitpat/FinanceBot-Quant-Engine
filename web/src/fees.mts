import { money, type Money } from "./money.mts";

export function feeCents(amount: Money, rateBps: number): Money {
  return money((amount.cents * rateBps) / 10000, amount.currency);
}

export function netAfterFee(amount: Money, rateBps: number): Money {
  return money(amount.cents + feeCents(amount, rateBps).cents, amount.currency);
}

export function feeRateFor(amount: Money, fee: Money): number {
  return fee.cents / amount.cents;
}
