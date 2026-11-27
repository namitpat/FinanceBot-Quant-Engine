#ifndef TICKS_H
#define TICKS_H

#include <stddef.h>

#define SYMBOL_LEN 8
#define MAX_TICKS 1024

struct tick {
    char symbol[SYMBOL_LEN];
    long price_cents;
    long volume;
};

struct tick *tick_parse(const char *line);
double tick_average(const long *prices, size_t count);
long tick_vwap_cents(const struct tick *ticks, size_t count);

#endif
