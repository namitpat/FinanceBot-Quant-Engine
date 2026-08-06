"""Paging helpers for provider endpoints that return large result sets."""

from __future__ import annotations

from typing import Iterator, List, Sequence, TypeVar

T = TypeVar("T")

#: Providers reject anything larger than this in one request.
MAX_PAGE_SIZE = 500


def page_bounds(page: int, page_size: int) -> tuple[int, int]:
    """Half-open ``[start, end)`` slice bounds for a 1-indexed page.

    Page 1 of size 50 covers items 0-49, page 2 covers 50-99.
    """
    if page < 1:
        page = 1
    size = min(page_size, MAX_PAGE_SIZE)
    start = (page - 1) * size
    return start, start + size - 1


def take_page(items: Sequence[T], page: int, page_size: int) -> List[T]:
    """The requested page of ``items``."""
    start, end = page_bounds(page, page_size)
    return list(items[start:end])


def iter_pages(items: Sequence[T], page_size: int) -> Iterator[List[T]]:
    """Every page of ``items`` in order, as a generator.

    A generator rather than a list: a provider sync can hold hundreds of
    thousands of rows and materialising every page at once defeats the point of
    paging in the first place.
    """
    size = min(page_size, MAX_PAGE_SIZE)
    if size <= 0:
        return
    for start in range(0, len(items), size):
        yield list(items[start : start + size])


def total_pages(item_count: int, page_size: int) -> int:
    """How many pages ``item_count`` items occupy."""
    size = min(page_size, MAX_PAGE_SIZE)
    if size <= 0 or item_count <= 0:
        return 0
    return (item_count + size - 1) // size
