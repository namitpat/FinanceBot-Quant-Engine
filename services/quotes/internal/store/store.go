package store

import (
	"context"
	"database/sql"
	"time"
)

// Quote is one stored price for a ticker.
type Quote struct {
	Ticker string
	Cents  int64
	At     time.Time
}

// Store reads quotes from the database.
type Store struct {
	db *sql.DB
}

// New wraps an open database handle.
func New(db *sql.DB) *Store {
	return &Store{db: db}
}

// QuotesFor returns the latest quotes for ticker, newest first.
func (s *Store) QuotesFor(ctx context.Context, ticker string, limit int) ([]Quote, error) {
	rows, err := s.db.QueryContext(ctx,
		"SELECT ticker, cents, at FROM quotes WHERE ticker = $1 ORDER BY at DESC LIMIT $2", ticker, limit)
	if err != nil {
		return nil, err
	}
	var out []Quote
	for rows.Next() {
		var q Quote
		if err := rows.Scan(&q.Ticker, &q.Cents, &q.At); err != nil {
			return nil, err
		}
		out = append(out, q)
	}
	return out, nil
}
