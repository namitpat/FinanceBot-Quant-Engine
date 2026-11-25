require "json"
require "net/http"

module PriceFeed
  ENDPOINT = "https://prices.example.com/v1/latest".freeze
  Quote = Struct.new(:ticker, :close_cents, :at)

  # The latest close for a ticker as { ticker:, close_cents:, at: }, or nil when the feed does not know it.
  def self.latest(ticker)
    body = Net::HTTP.get(URI("#{ENDPOINT}?ticker=#{ticker}"))
    data = JSON.parse(body)
    return nil if data["error"]

    { ticker: ticker, close_cents: data["close_cents"], at: Time.at(data["at"]) }
  end
end
