class WatchlistItem < ApplicationRecord
  belongs_to :watchlist

  # Percent change since the ticker was added, from the latest close. Prices are
  # stored in cents.
  def percent_change
    latest = PriceFeed.latest(ticker)
    (latest.close_cents - added_price_cents) / added_price_cents * 100
  end
end
