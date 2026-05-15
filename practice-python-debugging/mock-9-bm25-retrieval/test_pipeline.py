"""Spec for Mock 9 — do not edit. Fix the four modules until this all passes.

Run:  python -m unittest test_pipeline -v

This is the unambiguous spec for a BM25 retrieval pipeline split across four
modules. Every expected value below was derived by running the reference
solution; they are hardcoded so the suite does not depend on the solution
files. Numerics use `assertAlmostEqual` where they can't be exact.

READING THIS FILE AS A TUTORIAL
-------------------------------
The test classes are ordered to teach the pipeline by example, simplest first.
Read them top to bottom:

  TestTokenize       — text -> lowercase whitespace-split tokens, dropping
                       empty strings from runs of whitespace.
  TestInvertedIndex  — build an inverted index over a list of Documents:
                       per-term postings, per-term doc-frequency, per-doc
                       length, corpus avg doc length (a FLOAT, not int!).
                       Re-indexing replaces; prune drops rare terms in place.
  TestBM25           — the three scoring primitives. idf is smoothed so it's
                       finite at df=0 and non-negative. tf_saturation grows
                       with tf and asymptotes near k1+1, with length
                       normalization. score_term multiplies the two.
  TestRetrieve       — query pipeline pieces: top_k orders descending by
                       score with ties broken by doc_id ascending and returns
                       QueryResult NamedTuples; query tokenizes, skips unseen
                       terms, and ACCUMULATES contributions across query
                       terms (+=, not =); parse_query recursively peels.
  TestEndToEnd       — full pipeline against a small fixed corpus: index,
                       query, check rankings. Pins the multi-term
                       accumulation bug end-to-end.

Someone who reads only this file should come away understanding BM25.

BM25 IN ONE PARAGRAPH (for the reader who's never seen it): given a query
and a corpus, score every document by SUM over query terms of
`idf(term) * tf_saturation(term, doc)`. `idf` is high for rare terms and
low for terms in every doc — common words contribute little. `tf_saturation`
counts how many times the term appears in the doc but with diminishing
returns (the 11th occurrence helps less than the 2nd), and penalises long
documents (a hit in a 1000-word doc is less informative than a hit in a
10-word doc). The inverted index makes this fast: for each query term we
visit only the docs that actually contain it. The top-k step ranks by
descending score with a deterministic tiebreak (doc_id ascending).
"""
import unittest

from tokenize_lib import tokenize
from inverted_index import InvertedIndex, Document, IndexEntry
from bm25 import idf, tf_saturation, score_term
from retrieve import top_k, query, parse_query, QueryResult


# ---------------------------------------------------------------------------
# Shared test corpus — used by TestInvertedIndex, TestRetrieve, TestEndToEnd.
# 4 docs, 10 distinct terms; avgdl = (4+3+4+5)/4 = 4.0.
# ---------------------------------------------------------------------------
CORPUS = [
    Document("d1", "the quick brown fox"),         # 4 tokens
    Document("d2", "the lazy dog"),                # 3 tokens
    Document("d3", "quick brown dogs jump"),       # 4 tokens
    Document("d4", "the fox and the hound"),       # 5 tokens; 'the' x2
]


def fresh_index():
    """Helper: build an InvertedIndex over CORPUS."""
    idx = InvertedIndex()
    idx.add_documents(CORPUS)
    return idx


# ===========================================================================
# STEP 1 — Tokenize.
# ===========================================================================
class TestTokenize(unittest.TestCase):
    """The tokenizer is dead simple: lowercase, whitespace-split, drop empty
    strings. Empty tokens come from runs of whitespace and MUST NOT enter
    the index — they'd become a phantom term that matches nothing useful.
    """

    def test_basic_split_and_lowercase(self):
        """Tokens come out lowercase and split on whitespace."""
        self.assertEqual(tokenize("Hello World"), ["hello", "world"])

    def test_drops_empty_tokens_from_whitespace_runs(self):
        """Runs of whitespace must not produce empty-string tokens. With the
        empty-token filter dropped, ``" foo  bar "`` would yield
        ``["", "foo", "", "bar"]`` and the empty string would then leak
        into the index, the idf table, and every BM25 score downstream.
        """
        self.assertEqual(tokenize("  foo   bar  "), ["foo", "bar"])
        # An empty string must never appear as a token.
        self.assertNotIn("", tokenize("   "))
        self.assertEqual(tokenize("   "), [])

    def test_lowercases_uppercase_input(self):
        """Case-insensitive: 'The' and 'the' index to the same term."""
        self.assertEqual(tokenize("The QUICK Brown"), ["the", "quick", "brown"])


# ===========================================================================
# STEP 2 — Inverted index.
# ===========================================================================
class TestInvertedIndex(unittest.TestCase):
    """Build the index over a list of Document NamedTuples. The index stores
    three things per term:
      - a postings list of IndexEntry(doc_id, term_freq, doc_length);
      - a doc-frequency count (how many distinct docs contain the term);
      - and corpus aggregates: per-doc length and the corpus avg doc length.
    """

    def test_doc_freq_counts_distinct_docs(self):
        """doc_freq is the number of DISTINCT docs containing the term. 'the'
        appears 4 times in the corpus but in only 3 docs, so df('the')==3.
        """
        idx = fresh_index()
        self.assertEqual(idx.doc_freq("the"), 3)
        self.assertEqual(idx.doc_freq("quick"), 2)
        self.assertEqual(idx.doc_freq("lazy"), 1)

    def test_doc_freq_of_unseen_term_is_zero(self):
        """An unseen term's doc_freq is 0 — never KeyError."""
        idx = fresh_index()
        self.assertEqual(idx.doc_freq("nonexistent"), 0)

    def test_postings_of_unseen_term_is_empty_list(self):
        """postings() of an unseen term is the empty list, NOT a KeyError —
        the query pipeline relies on this empty-list-on-miss behavior.
        """
        idx = fresh_index()
        self.assertEqual(idx.postings("nonexistent"), [])

    def test_postings_carry_term_freq_and_doc_length(self):
        """Each posting is an IndexEntry with the term's frequency in that
        doc AND the doc's total length — both needed for BM25 saturation.
        """
        idx = fresh_index()
        # 'the' appears twice in d4 (length 5).
        postings = {e.doc_id: e for e in idx.postings("the")}
        self.assertEqual(postings["d4"].term_freq, 2)
        self.assertEqual(postings["d4"].doc_length, 5)
        # 'the' appears once in d1 (length 4).
        self.assertEqual(postings["d1"].term_freq, 1)
        self.assertEqual(postings["d1"].doc_length, 4)

    def test_index_entry_field_names_unambiguous(self):
        """IndexEntry exposes term_freq and doc_length as DISTINCT fields
        (both ints, easy to swap by mistake). Pin them by NAME, not order.

        For d4 with 'the': term_freq=2, doc_length=5. The numbers differ,
        so any positional-vs-named confusion is visible here.
        """
        idx = fresh_index()
        entry = next(e for e in idx.postings("the") if e.doc_id == "d4")
        self.assertEqual(entry.term_freq, 2)
        self.assertEqual(entry.doc_length, 5)

    def test_avg_doc_length_is_float_not_int(self):
        """avgdl must be computed with TRUE division. Integer division
        silently floors and poisons every downstream BM25 length-norm.

        For CORPUS, lengths are (4, 3, 4, 5); avg is exactly 4.0 — but the
        type check (and the assertion below for a non-integer average)
        catches the integer-division bug regardless.
        """
        idx = fresh_index()
        self.assertEqual(idx.avg_doc_length(), 4.0)
        self.assertIsInstance(idx.avg_doc_length(), float)

    def test_avg_doc_length_non_integer_corpus(self):
        """A corpus whose average isn't a whole number exposes int division.
        Lengths (4, 3, 4) -> avg = 11/3 = 3.6666...; integer division yields
        3, true division yields 3.6666...
        """
        idx = InvertedIndex()
        idx.add_documents([
            Document("a", "w x y z"),     # 4
            Document("b", "w x y"),       # 3
            Document("c", "w x y z"),     # 4
        ])
        self.assertAlmostEqual(idx.avg_doc_length(), 11 / 3)

    def test_reindexing_replaces_does_not_accumulate(self):
        """Re-calling add_documents must RESET state, not stack onto the old
        corpus. If _doc_freq isn't cleared, df values from the first
        corpus persist into the second one.

        After re-indexing on a fresh corpus that doesn't contain 'the',
        df('the') must be 0 — not its old value of 3.
        """
        idx = fresh_index()
        self.assertEqual(idx.doc_freq("the"), 3)
        # Re-index on a totally different corpus with no overlap.
        idx.add_documents([
            Document("x1", "alpha beta"),
            Document("x2", "beta gamma"),
        ])
        self.assertEqual(idx.doc_freq("the"), 0)
        self.assertEqual(idx.doc_freq("beta"), 2)
        self.assertEqual(idx.num_docs, 2)

    def test_prune_rare_terms_drops_low_df_in_place(self):
        """prune_rare_terms(min_df=2) must drop every term with df<2 from
        both _doc_freq and _postings. The naive "iterate the dict while
        del'ing from it" raises RuntimeError: dictionary changed size
        during iteration — snapshot the keys first.
        """
        idx = fresh_index()
        idx.prune_rare_terms(min_df=2)
        # Survivors: terms with df >= 2 — these are 'the' (3), 'quick' (2),
        # 'brown' (2), 'fox' (2). Everything else drops.
        self.assertEqual(idx.doc_freq("the"), 3)
        self.assertEqual(idx.doc_freq("quick"), 2)
        self.assertEqual(idx.doc_freq("lazy"), 0)
        self.assertEqual(idx.doc_freq("hound"), 0)
        self.assertEqual(idx.postings("lazy"), [])


# ===========================================================================
# STEP 3 — BM25 scoring primitives.
# ===========================================================================
class TestBM25(unittest.TestCase):
    """Three small functions:

      - idf(N, df): how informative a term is. Smoothed so it's FINITE at
        df=0 (an unseen term must not crash idf) and NON-NEGATIVE for any
        df in [0, N]. Monotonically decreasing in df.

      - tf_saturation(tf, dl, avgdl): per-term contribution per-doc. Grows
        with tf but with diminishing returns (asymptote near k1+1). Long
        docs (dl > avgdl) get penalised; short docs get boosted.

      - score_term(idf, tfsat): the product. Both inputs are non-negative
        so the product is too; either factor zero means zero contribution.
    """

    def test_idf_finite_at_df_zero(self):
        """idf must not crash or return inf/nan at df=0. The smoothed form
        (log((N - df + 0.5)/(df + 0.5) + 1)) handles df=0 cleanly; the
        naive log(N/df) would ZeroDivisionError.
        """
        v = idf(num_docs=10, doc_freq=0)
        self.assertTrue(v == v)              # not NaN
        self.assertNotEqual(v, float("inf"))
        self.assertNotEqual(v, float("-inf"))

    def test_idf_non_negative_when_term_in_every_doc(self):
        """When a term appears in EVERY doc (df==N), the unsmoothed
        log(N/df) is 0 and log(0.5/(N+0.5)) is negative; the smoothed
        version (+1 inside the log) keeps it non-negative.
        """
        self.assertGreaterEqual(idf(num_docs=10, doc_freq=10), 0.0)

    def test_idf_monotone_decreasing_in_df(self):
        """Rarer terms are more informative: idf(df=1) > idf(df=5) > idf(df=10)
        for a fixed N.
        """
        self.assertGreater(idf(10, 1), idf(10, 5))
        self.assertGreater(idf(10, 5), idf(10, 10))

    def test_idf_reference_value(self):
        """Anchor value (numpy.log derived) for N=4, df=2. Together with
        the monotonicity test, this pins both the formula's SHAPE and its
        SCALE — a TF formula missing its `(k1+1)` factor would still be
        monotone but wrong-scaled; an unsmoothed IDF would still be
        monotone but explode at df=0.
        """
        # log((4 - 2 + 0.5)/(2 + 0.5) + 1) = log(1 + 1) = log(2) ~= 0.693
        self.assertAlmostEqual(idf(4, 2), 0.6931471805599453, places=6)

    def test_tf_saturation_increases_with_tf(self):
        """More occurrences of the term in the doc -> higher contribution
        (but diminishing). tf=2 should out-score tf=1, tf=5 out-scores tf=2.
        """
        v1 = tf_saturation(1, 4, 4.0)
        v2 = tf_saturation(2, 4, 4.0)
        v5 = tf_saturation(5, 4, 4.0)
        self.assertGreater(v2, v1)
        self.assertGreater(v5, v2)

    def test_tf_saturation_asymptotes_near_k1_plus_one(self):
        """The SATURATION: as tf -> infinity, the value approaches k1+1
        (=2.2 by default). A formula missing the `(k1+1)` factor in the
        numerator would asymptote at 1.0 instead — same shape, wrong scale.
        """
        large = tf_saturation(10_000, 4, 4.0)
        self.assertGreater(large, 2.0)
        self.assertLess(large, 2.3)

    def test_tf_saturation_length_normalization(self):
        """Length normalization: a hit in a SHORT doc (dl < avgdl) scores
        higher than the same hit in a LONG doc (dl > avgdl), all else equal.
        """
        short = tf_saturation(1, 2, 4.0)     # half average length
        avg = tf_saturation(1, 4, 4.0)       # exactly average
        long_ = tf_saturation(1, 8, 4.0)     # twice average
        self.assertGreater(short, avg)
        self.assertGreater(avg, long_)

    def test_tf_saturation_reference_value(self):
        """Anchor value: tf=1 at average length is exactly 1.0 (the
        numerator and denominator both equal k1+1=2.2). Without the
        `(k1+1)` numerator factor this would be ~0.45 — visibly wrong.
        """
        self.assertAlmostEqual(tf_saturation(1, 4, 4.0), 1.0, places=6)

    def test_score_term_is_idf_times_tf_saturation(self):
        """score_term is a plain product of its two non-negative inputs."""
        self.assertAlmostEqual(score_term(0.5, 2.0), 1.0, places=9)
        self.assertAlmostEqual(score_term(1.5, 0.5), 0.75, places=9)

    def test_score_term_zero_when_either_factor_zero(self):
        """Any term with zero idf OR zero tf-saturation contributes zero —
        no negative contributions, no NaNs.
        """
        self.assertEqual(score_term(0.0, 1.234), 0.0)
        self.assertEqual(score_term(1.234, 0.0), 0.0)


# ===========================================================================
# STEP 4 — Retrieval pieces.
# ===========================================================================
class TestRetrieve(unittest.TestCase):
    """The query pipeline. `top_k` ranks, `query` ties tokenize+index+score
    together, `parse_query` parses a boolean AND/OR query recursively.
    """

    def test_top_k_descending_score(self):
        """top_k orders by DESCENDING score — best first."""
        ranked = top_k({"a": 0.1, "b": 0.9, "c": 0.5}, k=3)
        self.assertEqual([r.doc_id for r in ranked], ["b", "c", "a"])

    def test_top_k_tiebreak_doc_id_ascending(self):
        """Ties in score broken by doc_id ASCENDING (deterministic order)."""
        ranked = top_k({"d_z": 1.0, "d_a": 1.0, "d_m": 1.0}, k=3)
        self.assertEqual([r.doc_id for r in ranked], ["d_a", "d_m", "d_z"])

    def test_top_k_returns_query_result_namedtuples(self):
        """Results are QueryResult NamedTuples with .doc_id and .score —
        NOT bare strings. Callers index by attribute, not by str().
        """
        ranked = top_k({"a": 0.5}, k=1)
        self.assertEqual(len(ranked), 1)
        # If this were a bare string, .doc_id would AttributeError.
        self.assertEqual(ranked[0].doc_id, "a")
        self.assertAlmostEqual(ranked[0].score, 0.5)
        # Type guarantee:
        self.assertIsInstance(ranked[0], QueryResult)

    def test_top_k_returns_at_most_k(self):
        """k caps the output. Fewer-than-k scored docs return all of them
        (no padding).
        """
        ranked = top_k({"a": 1.0, "b": 2.0, "c": 3.0, "d": 4.0}, k=2)
        self.assertEqual(len(ranked), 2)
        # And fewer-than-k case:
        ranked2 = top_k({"only": 1.0}, k=5)
        self.assertEqual(len(ranked2), 1)

    def test_query_skips_unseen_terms(self):
        """Query terms not in the index must be SILENTLY SKIPPED — they
        contribute nothing and must not raise KeyError. Here only 'fox' is
        in the corpus; 'flibbertigibbet' is not.
        """
        idx = fresh_index()
        results = query(idx, "flibbertigibbet fox")
        # Must produce the same answer as querying just 'fox':
        fox_only = query(idx, "fox")
        self.assertEqual([(r.doc_id, round(r.score, 6)) for r in results],
                         [(r.doc_id, round(r.score, 6)) for r in fox_only])

    def test_query_accumulates_across_multiple_terms(self):
        """A doc matching MULTIPLE query terms gets the SUM of its per-term
        contributions — query must accumulate (+=), not overwrite (=).

        For "the fox", d1 matches BOTH terms. Its correct score is the sum
        of its 'the' and 'fox' contributions; with overwrite-not-accumulate
        d1 would only carry the LAST term's score (the 'fox' part) and
        come out lower.

        Anchor values (from the reference solution):
          d4: 'the' x2 + 'fox' x1, length 5 -> ~1.087
          d1: 'the' x1 + 'fox' x1, length 4 -> ~1.050
          d2: 'the' x1 only,       length 3 -> ~0.397
        """
        idx = fresh_index()
        results = query(idx, "the fox", k=10)
        scores = {r.doc_id: r.score for r in results}
        self.assertAlmostEqual(scores["d4"], 1.0870447025173258, places=5)
        self.assertAlmostEqual(scores["d1"], 1.0498221244986776, places=5)
        # Strict greater: d1's sum-of-two-terms must beat d4's fox-only score
        # (~0.6288). With overwrite-not-accumulate, d1 would collapse to its
        # 'fox'-only contribution (~0.6931) — still > 0.6288, so use d2 as
        # the canary: d2 only matches 'the', so d2 stays ~0.397; with the
        # accumulate bug d1 (~0.693) is barely above d2 — but the explicit
        # numeric anchor on d1 above catches it directly.
        self.assertAlmostEqual(scores["d2"], 0.39730879831149934, places=5)

    def test_parse_query_single_term(self):
        """A single bare term parses as ('AND', [term]) — degenerate AND."""
        self.assertEqual(parse_query(["foo"]), ("AND", ["foo"]))

    def test_parse_query_recursive_keeps_all_terms(self):
        """The recursive parser must PREPEND the head term to the recursive
        call's accumulated terms. Discarding the recursive result is the
        classic bug — only one term would survive.

        Here 'a AND b AND c AND d' must parse to all four terms, not just
        the head.
        """
        op, terms = parse_query(["a", "AND", "b", "AND", "c", "AND", "d"])
        self.assertEqual(op, "AND")
        self.assertEqual(terms, ["a", "b", "c", "d"])

    def test_parse_query_or_operator(self):
        """First operator in the token list decides the connective."""
        op, terms = parse_query(["x", "OR", "y", "OR", "z"])
        self.assertEqual(op, "OR")
        self.assertEqual(terms, ["x", "y", "z"])


# ===========================================================================
# STEP 5 — End-to-end pipeline.
# ===========================================================================
class TestEndToEnd(unittest.TestCase):
    """The full pipeline against the shared CORPUS. These tests don't probe
    a single module in isolation — they index a real corpus, run real
    queries, and check the rankings.

    If any of the per-module bugs are still present, these tests fail in
    creative ways. Symptom-far-from-cause: a wrong avgdl (integer division
    in InvertedIndex) silently changes every score downstream; an
    unsmoothed idf with df=0 only crashes if a query mentions an unseen
    term; an empty-string tokenizer leaks "" as a phantom term that
    matches every doc with leading/trailing whitespace.
    """

    def test_single_term_query_ranks_correctly(self):
        """Querying 'fox': d1 (4 tokens, 1 hit) > d4 (5 tokens, 1 hit) —
        the longer doc gets a length penalty.
        """
        idx = fresh_index()
        results = query(idx, "fox")
        self.assertEqual([r.doc_id for r in results], ["d1", "d4"])
        self.assertAlmostEqual(results[0].score, 0.6931471805599453, places=5)
        self.assertAlmostEqual(results[1].score, 0.6288345555595380, places=5)

    def test_two_term_query_orders_by_combined_score(self):
        """'fox dog' — d2 matches 'dog' (rare term, df=1, high idf), d1 and
        d4 match 'fox' (df=2, lower idf). d2 wins despite matching only one
        query term, because rarer terms carry more weight.
        """
        idx = fresh_index()
        results = query(idx, "fox dog")
        self.assertEqual([r.doc_id for r in results], ["d2", "d1", "d4"])
        self.assertAlmostEqual(results[0].score, 1.3411342630466123, places=5)

    def test_query_with_only_unseen_terms_returns_empty(self):
        """A query whose terms are ALL unseen must return [] silently —
        not crash on KeyError or smoothed-idf overflow.
        """
        idx = fresh_index()
        self.assertEqual(query(idx, "alpha beta gamma"), [])

    def test_query_input_with_messy_whitespace(self):
        """Leading, trailing, and internal whitespace must not introduce
        phantom terms. With the empty-token bug, "  fox  " would tokenize
        to ["", "fox", ""] and the empty-string term would match nothing
        in the index (df=0, skipped) — but the bug also pollutes the
        INDEX side: when indexing docs with extra spaces, empty tokens
        inflate doc_length and corrupt every score.

        Index a doc with extra whitespace; its tokenized length must equal
        the visible word count.
        """
        idx = InvertedIndex()
        idx.add_documents([
            Document("a", "  alpha  beta  "),
            Document("b", "alpha beta gamma"),
        ])
        # Both docs have the same real tokens for alpha+beta; the corpus
        # avg length must be (2 + 3)/2 = 2.5 — NOT something inflated by
        # phantom empty tokens.
        self.assertAlmostEqual(idx.avg_doc_length(), 2.5)

    def test_multi_term_query_accumulates_end_to_end(self):
        """End-to-end pin on the +=/= bug: a doc matching multiple query
        terms must score higher than the same doc would from any one term
        alone.

        For "the fox", d1's score must STRICTLY exceed its 'fox'-only score.
        With the overwrite bug, d1's score would equal its 'fox'-only score.
        """
        idx = fresh_index()
        two_term = {r.doc_id: r.score for r in query(idx, "the fox")}
        one_term = {r.doc_id: r.score for r in query(idx, "fox")}
        self.assertGreater(two_term["d1"], one_term["d1"])
        # And the gap is the 'the' contribution to d1.
        self.assertGreater(two_term["d1"] - one_term["d1"], 0.3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
