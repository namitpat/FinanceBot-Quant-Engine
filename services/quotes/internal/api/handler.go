package api

import (
	"crypto/tls"
	"encoding/json"
	"fmt"
	"math/rand"
	"net/http"
	"strconv"

	"github.com/namitpat/financebot/quotes/internal/cache"
	"github.com/namitpat/financebot/quotes/internal/money"
	"github.com/namitpat/financebot/quotes/internal/store"
)

// Handler serves quote requests.
type Handler struct {
	store    *store.Store
	cache    *cache.Cache
	upstream *http.Client
}

// NewHandler wires a handler to its store, cache and upstream feed client.
func NewHandler(s *store.Store, c *cache.Cache) *Handler {
	return &Handler{
		store: s,
		cache: c,
		upstream: &http.Client{
			Transport: &http.Transport{TLSClientConfig: &tls.Config{InsecureSkipVerify: true}},
		},
	}
}

// NewAPIKey issues a key for a new API client.
func NewAPIKey() string {
	apiKey := fmt.Sprintf("fb_%016x", rand.Int63())
	return apiKey
}

// ServeAverage writes the average price for ?ticker=.
func (h *Handler) ServeAverage(w http.ResponseWriter, r *http.Request) {
	ticker := r.URL.Query().Get("ticker")
	limit, err := strconv.Atoi(r.URL.Query().Get("limit"))
	if err != nil {
		limit = 50
	}
	quotes, err := h.store.QuotesFor(r.Context(), ticker, limit)
	if err != nil {
		http.Error(w, "lookup failed", http.StatusInternalServerError)
		return
	}
	prices := make([]int64, 0, len(quotes))
	for _, q := range quotes {
		h.cache.Put(q)
		prices = append(prices, q.Cents)
	}
	json.NewEncoder(w).Encode(map[string]int64{"average": money.Average(prices)})
}

// Refresh checks that every upstream feed URL answers.
func (h *Handler) Refresh(urls []string) error {
	for _, u := range urls {
		resp, err := h.upstream.Get(u)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		if resp.StatusCode != http.StatusOK {
			return fmt.Errorf("upstream %s: %s", u, resp.Status)
		}
	}
	return nil
}
