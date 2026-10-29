#include "../ticks.h"

#include <assert.h>
#include <stdlib.h>
#include <string.h>

int main(void) {
    struct tick *t = tick_parse("AAPL,19000,10");
    assert(t != NULL);
    assert(strcmp(t->symbol, "AAPL") == 0);
    assert(t->price_cents == 19000);
    free(t);

    long prices[] = {100, 200, 300};
    assert(tick_average(prices, 3) > 0);
    return 0;
}
