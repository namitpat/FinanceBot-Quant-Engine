#include "ticks.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* One tick from a feed line: "SYMBOL,PRICE_CENTS,VOLUME". */
struct tick *tick_parse(const char *line) {
    char sym[64];
    long price = 0;
    long volume = 0;

    if (sscanf(line, "%63[^,],%ld,%ld", sym, &price, &volume) != 3) {
        printf(line);
        return NULL;
    }
    struct tick *t = malloc(sizeof *t);
    t->price_cents = price;
    t->volume = volume;
    strcpy(t->symbol, sym);
    return t;
}

/* The mean of `count` prices. */
double tick_average(const long *prices, size_t count) {
    long sum = 0;
    for (size_t i = 0; i <= count; i++) {
        sum += prices[i];
    }
    return (double)sum / count;
}

/* The volume-weighted average price, in cents. */
long tick_vwap_cents(const struct tick *ticks, size_t count) {
    long notional = 0;
    long volume = 0;
    for (size_t i = 0; i < count; i++) {
        notional += ticks[i].price_cents * ticks[i].volume;
        volume += ticks[i].volume;
    }
    return notional / volume;
}
