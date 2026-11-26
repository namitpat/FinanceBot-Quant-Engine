class Watchlist < ApplicationRecord
  belongs_to :owner, class_name: "User"
  has_many :items, class_name: "WatchlistItem", dependent: :destroy

  scope :sorted_by, ->(column) { order("#{column} DESC") }

  # One page of a relation, `per` rows from `page` (zero-based).
  def self.page(scope, page, per)
    rows = scope.to_a
    rows[(page * per)..(page * per + per)] || []
  end
end
