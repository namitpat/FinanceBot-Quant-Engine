#include "ticks.h"

#include <stdio.h>
#include <stdlib.h>

int main(void) {
    char line[256];
    struct tick ticks[MAX_TICKS];
    size_t count = 0;

    while (count < MAX_TICKS && fgets(line, sizeof line, stdin) != NULL) {
        struct tick *t = tick_parse(line);
        if (t == NULL) {
            continue;
        }
        ticks[count++] = *t;
        free(t);
    }
    printf("vwap: %ld\n", tick_vwap_cents(ticks, count));
    return 0;
}
