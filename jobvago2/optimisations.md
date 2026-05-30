# Performance Optimizations

This document describes the performance work done on jobvago: what was slow,
what changed, and the measured impact. The guiding constraint throughout was
**identical observable behaviour** — the full test suite (269 tests) passes
both with and without the native extension.

## Where the time was going

Profiling against a 25,000-row dataset (the scale of the real SkillsFuture
course feed) showed the dominant cost was **not** PDF parsing or the network
calls, but plain multi-keyword string matching done in pure Python:

| Path | When it runs | Cost (Python) |
|------|--------------|---------------|
| Course industry filter (`CourseService`) | **every** career page load | 2–100 ms / request |
| Résumé competency / leadership / extra-curricular scoring | every résumé upload | 0.2–12 ms |
| Skill-taxonomy regex fallback | upload, only when the LLM is offline | ~2.6 ms |

The course filter was an `O(courses × keywords)` substring scan
(`any(kw in title.lower() for kw in keywords)` over up to 25k titles). For
industries whose keywords match few titles, it scanned the entire list every
request — up to ~100 ms of pure CPU per page view.

## What changed

### 1. C++ Aho-Corasick keyword matcher (`app/native/jvfast.cpp`)

A small [pybind11](https://pybind11.readthedocs.io/) extension implementing an
Aho-Corasick automaton. It turns the `O(text × patterns)` scan into a single
linear `O(text)` pass and exposes:

- `Matcher(patterns, case_insensitive)` — `contains_any`, `match_unique`
  (matches in pattern-insertion order), `count_matches`.
- `TitleIndex(texts)` — holds a corpus **resident on the C++ side** so the
  list of 25k titles is marshalled across the Python/C++ boundary **once**
  (cached), not per request. This was the key insight: without it, re-copying
  every title per request cost more than it saved.

### 2. Wiring (`app/services/_fast.py`)

A thin adapter selects the native matcher when `jvfast` is compiled, and
otherwise uses **pure-Python fallbacks with identical semantics**. The app
runs correctly with no compiler present — only slower on those paths.

Integrated into:
- `course_service.py` — cached `TitleIndex` (keyed by the data file's mtime,
  same as the existing parsed-course cache) + memoised per-industry matchers.
- `resume_grading_service.py` — competency, leadership and extra-curricular
  keyword scoring.

Text is lowercased in Python before matching (matchers are built
case-sensitive), so results are **byte-for-byte identical** to the original
`kw in text.lower()` logic, including non-ASCII input.

### What was deliberately *not* changed

The skill-taxonomy regex fallback (`skill_extraction_service.py`) was left
as-is. Several of its patterns use regex wildcards and look-aheads
(e.g. `\bicd.10\b`, `\bjava\b(?!script)`), so a literal C++ rewrite would risk
silent divergence on a fallback-only path. Combining the patterns into one
alternation regex was also measured and made things **5× slower** (a known
CPython `re` pitfall), so that idea was rejected.

## Measured results

Per-request course filter (median, single core), exact parity verified on
every industry:

| Industry | Before | After | Speedup |
|----------|-------:|------:|--------:|
| information technology | 1.68 ms | 0.038 ms | 44× |
| healthcare | 15.71 ms | 0.337 ms | 47× |
| logistics | 20.39 ms | 0.721 ms | 28× |
| **manufacturing** (near-full scan) | **99.99 ms** | **3.36 ms** | **30×** |

Every industry filter is now sub-4 ms; most are sub-0.5 ms.

Full offline résumé `grade()` dropped roughly in half (≈2 ms → ≈1 ms for a
typical résumé) thanks to the accelerated keyword paths.

## Building the extension

Optional. See the README "Native acceleration" section:

```
python -m app.native.build                 # quick (g++/clang)
python setup.py build_ext --inplace         # portable (incl. Windows/MSVC)
```

`create_app()` prints whether acceleration is active on startup.
