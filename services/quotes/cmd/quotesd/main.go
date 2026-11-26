package main

import (
	"database/sql"
	"log"
	"net/http"
	"time"

	"github.com/namitpat/financebot/quotes/internal/api"
	"github.com/namitpat/financebot/quotes/internal/cache"
	"github.com/namitpat/financebot/quotes/internal/store"
)

func main() {
	db, err := sql.Open("postgres", "postgres://localhost/quotes")
	if err != nil {
		log.Fatal(err)
	}
	h := api.NewHandler(store.New(db), cache.New(time.Minute))
	http.HandleFunc("/average", h.ServeAverage)
	log.Fatal(http.ListenAndServe(":8080", nil))
}
