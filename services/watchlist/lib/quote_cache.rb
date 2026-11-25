require_relative "price_feed"

# Serves PriceFeed quotes from memory for up to TTL seconds.
module PriceCache
  TTL = 60
  @entries = {}

  def self.latest(ticker)
    entry = @entries[ticker]
    return entry[:quote] if entry && Time.now - entry[:at] > TTL

    quote = PriceFeed.latest(ticker)
    @entries[ticker] = { quote: quote, at: Time.now }
    quote
  end
end
