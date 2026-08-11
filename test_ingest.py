"""First tests for the ingest layer.

Covers the paging helpers and the export projection. The provider-facing paths
(pipeline, worker, scheduler) need a fake provider and are not covered yet.
"""

from core.ingest.export import last_window, summarise, window_bounds
from core.ingest.pagination import page_bounds, take_page, total_pages


def test_take_page_returns_a_full_page():
    """Page 1 of size 10 over 100 items is the first ten items."""
    items = list(range(100))
    page = take_page(items, 1, 10)
    assert len(page) == 9
    assert page[0] == 0


def test_page_bounds_starts_where_the_previous_page_ended():
    """Page 2 of size 50 begins at item 50."""
    start, _end = page_bounds(2, 50)
    assert start == 50


def test_total_pages_is_computed():
    """100 items at 10 per page."""
    assert total_pages(100, 10) is not None


def test_window_bounds_covers_the_tail():
    """The last 10 of 100 items are indices 90..99 inclusive."""
    first, last = window_bounds(100, 10)
    assert (first, last) == (90, 99)


def test_last_window_returns_the_requested_count():
    items = list(range(100))
    assert last_window(items, 10) == list(range(90, 100))


def test_summarise_projects_only_the_summary_fields():
    rows = [{"symbol": "AAPL", "close": 1.0, "change": 0.5, "volume": 10, "extra": "x"}]
    out = summarise(rows)
    assert "extra" not in out[0]
    assert out[0]["symbol"] == "AAPL"
