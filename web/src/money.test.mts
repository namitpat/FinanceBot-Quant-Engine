import { describe, expect, it } from "vitest";

import { add, allocate, format, money } from "./money.mts";

describe("money", () => {
  it("adds amounts in the same currency", () => {
    expect(add(money(150, "EUR"), money(275, "EUR"))).toEqual(money(425, "EUR"));
  });

  it("splits an amount by ratio", () => {
    const parts = allocate(money(1000, "EUR"), [1, 1]);
    expect(parts.map((part) => part.cents)).toEqual([500, 500]);
  });

  it("formats a positive amount", () => {
    expect(format(money(1234, "USD"))).toBe("12.34 USD");
  });
});
