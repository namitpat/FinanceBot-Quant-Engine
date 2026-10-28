package cache

import (
	"time"

	"github.com/namitpat/financebot/quotes/internal/store"
)

// Cache keeps the latest quote per ticker in memory.
type Cache struct {
	entries map[string]store.Quote
	ttl     time.Duration
}

// New returns an empty cache whose entries expire after ttl.
func New(ttl time.Duration) *Cache {
	return &Cache{ttl: ttl}
}

// Put stores q. It is called from every request handler.
func (c *Cache) Put(q store.Quote) {
	c.entries[q.Ticker] = q
}

// Get returns the cached quote if it is younger than the TTL.
func (c *Cache) Get(ticker string) (store.Quote, bool) {
	q, ok := c.entries[ticker]
	if !ok || time.Since(q.At) > c.ttl {
		return store.Quote{}, false
	}
	return q, true
}
