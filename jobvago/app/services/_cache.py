"""In-memory cache for parsed data files.

Caches the *parsed* result of expensive file reads (CSV / Excel parsing) so
repeated requests do not re-parse the same source file. Each cache entry is
keyed by the source file path and invalidated automatically when the file's
modification time changes — so when the DataDownloader refreshes a stale
cache file from data.gov.sg, the next read transparently re-parses it.

The cache is process-local and thread-unsafe in the strict sense, but Flask's
default request handling is single-threaded for the dev server, and the
worst-case race (two threads parsing the same file once) is harmless.
"""

import os
import threading
from typing import Any, Callable, Optional


class FileBackedCache:
    """A tiny mtime-keyed cache for parsed file contents.

    Usage::

        cache = FileBackedCache()
        industries = cache.get_or_load(csv_path, lambda p: parse_csv(p))

    The loader is invoked once per (path, mtime) pair. Subsequent calls
    return the cached value instantly until the underlying file is replaced.
    """

    def __init__(self) -> None:
        # Map of cache_key -> (mtime, value).
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def get_or_load(
        self,
        path: str,
        loader: Callable[[str], Any],
        extra_key: Optional[str] = None,
    ) -> Any:
        """Return the cached value for *path*, parsing it via *loader* if stale.

        Args:
            path: Source file whose mtime keys the cache entry.
            loader: Callable invoked with *path* when the cache misses.
            extra_key: Optional discriminator appended to the cache key.
                Use this when a single source file produces multiple parsed
                representations (e.g. industries-only vs courses-only).

        Returns:
            Whatever *loader* returns. Identical object on repeated hits.
        """
        try:
            mtime = os.path.getmtime(path)
        except OSError:
            # File missing or unreadable — fall through to the loader so it
            # can surface a proper error to the caller.
            return loader(path)

        cache_key = f"{path}::{extra_key}" if extra_key else path

        with self._lock:
            cached = self._store.get(cache_key)
            if cached is not None and cached[0] == mtime:
                return cached[1]

        # Load outside the lock so concurrent parses of *different* files
        # don't serialise. The double-check below avoids a duplicate store.
        value = loader(path)

        with self._lock:
            self._store[cache_key] = (mtime, value)

        return value

    def invalidate(self) -> None:
        """Drop every cached entry. Intended for tests."""
        with self._lock:
            self._store.clear()


# Module-level singleton shared across all services in this process.
PARSED_FILE_CACHE = FileBackedCache()
