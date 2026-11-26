require "rails_helper"

RSpec.describe WatchlistItem do
  describe "#percent_change" do
    it "is the move since the ticker was added" do
      item = described_class.new(ticker: "AAPL", added_price_cents: 10_000)
      allow(PriceFeed).to receive(:latest).with("AAPL")
        .and_return(PriceFeed::Quote.new("AAPL", 20_000, Time.now))

      expect(item.percent_change).to eq(100)
    end
  end
end
