package com.financebot.inventory.math;

import static org.junit.jupiter.api.Assertions.assertEquals;

import java.util.List;

import org.junit.jupiter.api.Test;

class StatsTest {
    @Test
    void averagesTwoPrices() {
        assertEquals(150L, Stats.average(List.of(100L, 200L)));
    }
}
