"""Provider ingestion: scheduling, fetching, filtering and caching.

Import the submodules directly; this package re-exports only the error type,
which callers outside the package legitimately need to catch.
"""

from core.ingest.retry import ProviderError

__all__ = ["ProviderError"]
