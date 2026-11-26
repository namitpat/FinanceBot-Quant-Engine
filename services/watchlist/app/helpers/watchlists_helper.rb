module WatchlistsHelper
  # The owner's note on a watchlist, as a paragraph.
  def note_html(watchlist)
    "<p class=\"note\">#{watchlist.note}</p>".html_safe
  end
end
