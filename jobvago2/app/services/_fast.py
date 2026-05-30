"""Native-acceleration adapter with a transparent pure-Python fallback.

This module is the single integration point for the optional ``jvfast`` C++
extension (Aho-Corasick multi-keyword matcher). Services import the small
factory helpers here instead of touching the native module directly, so:

  * If ``jvfast`` is compiled and importable, keyword matching runs in C++.
  * If it is missing (no compiler, fresh checkout, unsupported platform), the
    identical-semantics Python fallbacks below are used instead — the app is
    only slower, never broken.

The Python fallbacks are written to match the C++ semantics exactly:
ASCII case-insensitive substring matching, with ``match_unique`` returning
matched patterns in pattern-insertion order (i.e. the same result as
``[kw for kw in patterns if kw in text.lower()]``).
"""

from typing import List, Sequence

# ---------------------------------------------------------------------------
# Try to load the compiled extension. Several import locations are attempted
# so the build can live in app/native/ or be installed on sys.path.
# ---------------------------------------------------------------------------
_native = None
try:                                   # preferred: packaged under app.native
    from app.native import jvfast as _native  # type: ignore
except Exception:
    try:                               # fallback: top-level installed module
        import jvfast as _native       # type: ignore
    except Exception:
        _native = None

NATIVE_AVAILABLE: bool = _native is not None


# ---------------------------------------------------------------------------
# Pure-Python fallbacks (identical observable behaviour to the C++ classes)
# ---------------------------------------------------------------------------
class _PyMatcher:
    """Pure-Python substring matcher mirroring jvfast.Matcher."""

    __slots__ = ("_patterns", "_ci")

    def __init__(self, patterns: Sequence[str], case_insensitive: bool = True):
        self._ci = case_insensitive
        # Drop empties to match the C++ trie (which skips empty patterns).
        self._patterns = [p for p in patterns if p]

    def _prep(self, text: str) -> str:
        return text.lower() if self._ci else text

    def contains_any(self, text: str) -> bool:
        t = self._prep(text)
        return any(p in t for p in self._patterns)

    def match_unique(self, text: str) -> List[str]:
        t = self._prep(text)
        return [p for p in self._patterns if p in t]

    def count_matches(self, text: str) -> int:
        t = self._prep(text)
        return sum(1 for p in self._patterns if p in t)

    def __len__(self) -> int:
        return len(self._patterns)


class _PyTitleIndex:
    """Pure-Python corpus index mirroring jvfast.TitleIndex."""

    __slots__ = ("_texts",)

    def __init__(self, texts: Sequence[str]):
        self._texts = list(texts)

    def filter(self, matcher, limit: int = 0) -> List[int]:
        hits: List[int] = []
        for i, text in enumerate(self._texts):
            if matcher.contains_any(text):
                hits.append(i)
                if limit > 0 and len(hits) >= limit:
                    break
        return hits

    def __len__(self) -> int:
        return len(self._texts)


# ---------------------------------------------------------------------------
# Public factories — call these from services.
# ---------------------------------------------------------------------------
def make_matcher(patterns: Sequence[str], case_insensitive: bool = True):
    """Return an Aho-Corasick matcher (native if available, else Python)."""
    pats = list(patterns)
    if NATIVE_AVAILABLE:
        return _native.Matcher(pats, case_insensitive)
    return _PyMatcher(pats, case_insensitive)


def make_title_index(texts: Sequence[str]):
    """Return a resident corpus index (native if available, else Python)."""
    if NATIVE_AVAILABLE:
        return _native.TitleIndex(list(texts))
    return _PyTitleIndex(texts)
