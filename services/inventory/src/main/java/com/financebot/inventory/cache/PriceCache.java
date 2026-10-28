package com.financebot.inventory.cache;

import java.util.HashMap;
import java.util.Map;

import org.springframework.stereotype.Component;

@Component
public class PriceCache {
    private static final Map<String, Long> PRICES = new HashMap<>();

    public void put(String ticker, long price) {
        PRICES.put(ticker, price);
    }

    public long priceOf(String ticker) {
        return PRICES.get(ticker).longValue();
    }

    public int size() {
        return PRICES.size();
    }
}
