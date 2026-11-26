module WatchlistsHelper
  # The owner's note on a watchlist, as a paragraph.
  def note_html(watchlist)
    content_tag(:p, watchlist.note, class: "note")
  end
end
