// jvfast.cpp — high-performance multi-keyword matcher for jobvago.
//
// Implements an Aho-Corasick automaton exposed to Python via pybind11.
// This replaces the hot O(num_texts * num_keywords) substring scans in the
// pure-Python services with a single linear O(text_length) pass per text.
//
// Use cases wired up in the Python layer:
//   * CourseService industry filtering   (filter_contains: ~25k titles/request)
//   * RuleBasedScorer competency scoring  (match_unique)
//   * AIScorer leadership/extracurricular (count_matches)
//   * CourseService title -> skill tags   (match_unique)
//
// Semantics are kept identical to the Python they replace:
//   * ASCII case-insensitive matching (mirrors str.lower() for ASCII input;
//     non-ASCII bytes are passed through, which cannot affect ASCII keywords).
//   * match_unique() returns matched patterns in *pattern-insertion order*,
//     matching `[kw for kw in keywords if kw in text_lower]`.

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <algorithm>
#include <cstdint>
#include <queue>
#include <string>
#include <vector>

namespace py = pybind11;

static inline unsigned char lc(unsigned char c) {
    return (c >= 'A' && c <= 'Z') ? static_cast<unsigned char>(c + 32) : c;
}

class Matcher {
public:
    Matcher(const std::vector<std::string>& patterns, bool case_insensitive = true)
        : ci_(case_insensitive), npat_(static_cast<int>(patterns.size())) {
        patterns_ = patterns;

        // Root node.
        next_.emplace_back();
        next_.back().assign(256, 0);
        out_.emplace_back();
        fail_.push_back(0);

        // Build goto trie. Empty patterns are ignored (mirrors "" being a
        // no-op keyword; the Python keyword lists never contain empties).
        for (int p = 0; p < npat_; ++p) {
            const std::string& pat = patterns_[p];
            if (pat.empty()) continue;
            int node = 0;
            for (unsigned char raw : pat) {
                unsigned char c = ci_ ? lc(raw) : raw;
                int nxt = next_[node][c];
                if (nxt == 0) {  // 0 == root means "no edge yet" except at root itself
                    nxt = static_cast<int>(next_.size());
                    next_.emplace_back();
                    next_.back().assign(256, 0);
                    out_.emplace_back();
                    fail_.push_back(0);
                    next_[node][c] = nxt;
                }
                node = nxt;
            }
            out_[node].push_back(p);
        }

        build_automaton();
    }

    // True if any pattern occurs in `text`. Early-exits on first hit.
    bool contains_any(const std::string& text) const {
        int node = 0;
        for (unsigned char raw : text) {
            unsigned char c = ci_ ? lc(raw) : raw;
            node = next_[node][c];
            if (term_[node]) return true;
        }
        return false;
    }

    // Filter a list of texts, returning the indices of those containing any
    // pattern, stopping once `limit` matches are collected (limit <= 0 = all).
    // This keeps the entire CourseService filter loop inside C++.
    std::vector<int> filter_contains(const std::vector<std::string>& texts, int limit) const {
        std::vector<int> hits;
        if (limit > 0) hits.reserve(static_cast<size_t>(limit));
        for (int i = 0; i < static_cast<int>(texts.size()); ++i) {
            if (contains_any(texts[i])) {
                hits.push_back(i);
                if (limit > 0 && static_cast<int>(hits.size()) >= limit) break;
            }
        }
        return hits;
    }

    // Unique matched patterns, returned in pattern-insertion order so the
    // result is identical to `[kw for kw in patterns if kw in text]`.
    std::vector<std::string> match_unique(const std::string& text) const {
        std::vector<char> seen(static_cast<size_t>(npat_), 0);
        int node = 0;
        int found = 0;
        for (unsigned char raw : text) {
            unsigned char c = ci_ ? lc(raw) : raw;
            node = next_[node][c];
            for (int p : merged_out_[node]) {
                if (!seen[p]) { seen[p] = 1; ++found; }
            }
            if (found == npat_) break;  // every pattern already matched
        }
        std::vector<std::string> result;
        result.reserve(static_cast<size_t>(found));
        for (int p = 0; p < npat_; ++p)
            if (seen[p]) result.push_back(patterns_[p]);
        return result;
    }

    // Number of distinct patterns that occur in `text`.
    int count_matches(const std::string& text) const {
        std::vector<char> seen(static_cast<size_t>(npat_), 0);
        int node = 0, found = 0;
        for (unsigned char raw : text) {
            unsigned char c = ci_ ? lc(raw) : raw;
            node = next_[node][c];
            for (int p : merged_out_[node]) {
                if (!seen[p]) { seen[p] = 1; ++found; }
            }
            if (found == npat_) break;
        }
        return found;
    }

    int size() const { return npat_; }

private:
    void build_automaton() {
        // BFS to compute fail links and convert the goto function into a full
        // DFA (every (node, byte) has a defined transition).
        std::queue<int> q;
        for (int c = 0; c < 256; ++c) {
            int u = next_[0][c];
            if (u != 0) { fail_[u] = 0; q.push(u); }
        }
        while (!q.empty()) {
            int u = q.front(); q.pop();
            // Merge output of fail target so each node carries every pattern
            // matchable when it is reached.
            const std::vector<int>& fo = out_[fail_[u]];
            out_[u].insert(out_[u].end(), fo.begin(), fo.end());
            for (int c = 0; c < 256; ++c) {
                int v = next_[u][c];
                if (v != 0) {
                    fail_[v] = next_[fail_[u]][c];
                    q.push(v);
                } else {
                    next_[u][c] = next_[fail_[u]][c];
                }
            }
        }
        // Precompute terminal flag and a deduplicated merged-output list per
        // node for fast iteration.
        size_t n = next_.size();
        term_.assign(n, 0);
        merged_out_.resize(n);
        for (size_t i = 0; i < n; ++i) {
            std::vector<int>& o = out_[i];
            std::sort(o.begin(), o.end());
            o.erase(std::unique(o.begin(), o.end()), o.end());
            merged_out_[i] = o;
            term_[i] = !o.empty();
        }
    }

    bool ci_;
    int npat_;
    std::vector<std::string> patterns_;
    std::vector<std::vector<int>> next_;        // dense DFA transitions
    std::vector<int> fail_;
    std::vector<std::vector<int>> out_;         // working output sets
    std::vector<std::vector<int>> merged_out_;  // deduped, immutable for matching
    std::vector<char> term_;                    // any-output flag per node
};

// TitleIndex keeps a corpus of texts (e.g. course titles) resident on the C++
// side so the expensive Python->C++ marshaling happens once, not per request.
// Built once and cached alongside the parsed course list; each request then
// only crosses the boundary with a small keyword Matcher.
class TitleIndex {
public:
    explicit TitleIndex(std::vector<std::string> texts) : texts_(std::move(texts)) {}

    // Return indices of stored texts containing any pattern in `m`, stopping
    // after `limit` hits (limit <= 0 = all). Equivalent to the CourseService
    // filter loop, run entirely in native code with zero per-call marshaling
    // of the corpus.
    std::vector<int> filter(const Matcher& m, int limit) const {
        std::vector<int> hits;
        if (limit > 0) hits.reserve(static_cast<size_t>(limit));
        for (int i = 0; i < static_cast<int>(texts_.size()); ++i) {
            if (m.contains_any(texts_[i])) {
                hits.push_back(i);
                if (limit > 0 && static_cast<int>(hits.size()) >= limit) break;
            }
        }
        return hits;
    }

    int size() const { return static_cast<int>(texts_.size()); }

private:
    std::vector<std::string> texts_;
};

PYBIND11_MODULE(jvfast, m) {
    m.doc() = "jobvago native acceleration: Aho-Corasick multi-keyword matcher";
    py::class_<TitleIndex>(m, "TitleIndex")
        .def(py::init<std::vector<std::string>>(), py::arg("texts"))
        .def("filter", &TitleIndex::filter, py::arg("matcher"), py::arg("limit") = 0)
        .def("__len__", &TitleIndex::size)
        .def_property_readonly("size", &TitleIndex::size);
    py::class_<Matcher>(m, "Matcher")
        .def(py::init<const std::vector<std::string>&, bool>(),
             py::arg("patterns"), py::arg("case_insensitive") = true)
        .def("contains_any", &Matcher::contains_any, py::arg("text"))
        .def("filter_contains", &Matcher::filter_contains,
             py::arg("texts"), py::arg("limit") = 0)
        .def("match_unique", &Matcher::match_unique, py::arg("text"))
        .def("count_matches", &Matcher::count_matches, py::arg("text"))
        .def("__len__", &Matcher::size)
        .def_property_readonly("size", &Matcher::size);
}
