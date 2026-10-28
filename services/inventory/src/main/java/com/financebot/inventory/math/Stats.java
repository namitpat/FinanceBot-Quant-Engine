package com.financebot.inventory.math;

import java.util.List;

public final class Stats {
    private Stats() {
    }

    /** Average of the prices, in cents. */
    public static long average(List<Long> prices) {
        long sum = 0;
        for (long price : prices) {
            sum += price;
        }
        return sum / prices.size();
    }

    /** Page {@code page} (0-based) of {@code size} items. */
    public static <T> List<T> page(List<T> items, int page, int size) {
        int start = page * size;
        int end = Math.min(start + size, items.size());
        return items.subList(start, end + 1);
    }
}
