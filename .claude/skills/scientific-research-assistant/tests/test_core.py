"""HTTP client behaviour, identifier handling and deduplication (offline)."""
import tempfile
import unittest
import urllib.error

from helpers import FakeOpener, http_error, make_client

from sra.http import HttpClient, SourceError
from sra.models import Paper, dedupe, normalize_arxiv_id, normalize_doi, parse_identifier, surname
from sra.text import coverage, tfidf_cosine, title_similarity


class HttpClientTests(unittest.TestCase):
    def test_retries_transient_error_then_succeeds(self):
        client, opener, sleeps = make_client([("example.org", [503, 503, {"ok": True}])])
        self.assertEqual(client.get("https://example.org/x"), {"ok": True})
        self.assertEqual(len(opener.calls), 3)
        self.assertEqual(sleeps, [2.0, 4.0])  # exponential backoff

    def test_persistent_429_is_reported_as_rate_limited(self):
        client, opener, _ = make_client([("example.org", 429)])
        with self.assertRaises(SourceError) as ctx:
            client.get("https://example.org/x", source="demo")
        self.assertEqual(ctx.exception.kind, "rate_limited")
        self.assertEqual(len(opener.calls), 4)  # first try + 3 retries

    def test_retry_after_header_is_honoured(self):
        client, _, sleeps = make_client(
            [("example.org", [http_error("u", 429, {"Retry-After": "7"}), {"ok": 1}])])
        client.get("https://example.org/x")
        self.assertEqual(sleeps, [7.0])

    def test_long_retry_after_fails_fast_instead_of_hanging(self):
        client, opener, sleeps = make_client([("example.org", http_error("u", 429, {"Retry-After": "3600"}))])
        with self.assertRaises(SourceError) as ctx:
            client.get("https://example.org/x")
        self.assertEqual((ctx.exception.kind, len(opener.calls), sleeps), ("rate_limited", 1, []))

    def test_exhausted_github_style_quota_is_not_retried(self):
        client, opener, _ = make_client(
            [("example.org", http_error("u", 403, {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1"}))])
        with self.assertRaises(SourceError) as ctx:
            client.get("https://example.org/x")
        self.assertEqual((ctx.exception.kind, len(opener.calls)), ("rate_limited", 1))
        self.assertIn("quota exhausted", ctx.exception.message)

    def test_error_kinds(self):
        for status, kind in ((404, "not_found"), (401, "auth"), (403, "auth"), (418, "http")):
            client, _, _ = make_client([("example.org", status)])
            with self.assertRaises(SourceError) as ctx:
                client.get("https://example.org/x")
            self.assertEqual(ctx.exception.kind, kind, status)

    def test_network_failure_is_retried_then_reported(self):
        client, opener, _ = make_client([("example.org", urllib.error.URLError("dns down"))])
        with self.assertRaises(SourceError) as ctx:
            client.get("https://example.org/x")
        self.assertEqual((ctx.exception.kind, len(opener.calls)), ("network", 4))

    def test_invalid_json_is_a_parse_error(self):
        client, _, _ = make_client([("example.org", "<html>not json</html>")])
        with self.assertRaises(SourceError) as ctx:
            client.get("https://example.org/x")
        self.assertEqual(ctx.exception.kind, "parse")

    def test_per_host_throttle_waits_between_arxiv_calls(self):
        client, _, sleeps = make_client([("export.arxiv.org", "<feed/>")])
        client.get("https://export.arxiv.org/api/query", parse="text")
        client.get("https://export.arxiv.org/api/query", {"a": 1}, parse="text")
        self.assertEqual(len(sleeps), 1)
        self.assertAlmostEqual(sleeps[0], 3.0, delta=0.2)

    def test_cache_avoids_second_request_and_none_params_are_dropped(self):
        with tempfile.TemporaryDirectory() as tmp:
            opener = FakeOpener([("example.org", {"n": 1})])
            client = HttpClient(cache_dir=tmp, opener=opener, sleep=lambda s: None)
            client.get("https://example.org/x", {"q": "a b", "key": None})
            client.get("https://example.org/x", {"q": "a b", "key": None})
            self.assertEqual(opener.calls, ["https://example.org/x?q=a+b"])

    def test_probe_falls_back_to_get_when_head_is_rejected(self):
        client, opener, _ = make_client([("example.org", [405, "body"])])
        self.assertTrue(client.probe("https://example.org/data.zip")["reachable"])
        self.assertEqual(len(opener.calls), 2)
        client, _, _ = make_client([("example.org", 404)])
        self.assertEqual(client.probe("https://example.org/gone")["reachable"], False)


class IdentifierTests(unittest.TestCase):
    def test_doi_normalisation(self):
        self.assertEqual(normalize_doi("https://doi.org/10.1234/ABC.5)."), "10.1234/abc.5")
        self.assertIsNone(normalize_doi("not a doi"))

    def test_arxiv_normalisation(self):
        self.assertEqual(normalize_arxiv_id("https://arxiv.org/abs/2101.00001v3"), "2101.00001")
        self.assertEqual(normalize_arxiv_id("arXiv:cs/0301001v1"), "cs/0301001")
        self.assertIsNone(normalize_arxiv_id("hello"))

    def test_parse_identifier(self):
        cases = {
            "2101.00001": ("arxiv", "2101.00001"),
            "https://arxiv.org/pdf/2101.00001v2": ("arxiv", "2101.00001"),
            "10.48550/arXiv.2101.00001": ("arxiv", "2101.00001"),
            "https://doi.org/10.1234/Fixture.2": ("doi", "10.1234/fixture.2"),
            "10.1234/5678.12345": ("doi", "10.1234/5678.12345"),  # DOI that looks like an arXiv ID
            "W2964015378": ("openalex", "W2964015378"),
            "PMID: 123456": ("pmid", "123456"),
            "Graph networks for text": ("title", "Graph networks for text"),
        }
        for raw, expected in cases.items():
            self.assertEqual(parse_identifier(raw), expected, raw)

    def test_surname(self):
        self.assertEqual(surname("Thomas N. Kipf"), "kipf")
        self.assertEqual(surname("Kipf, Thomas N."), "kipf")
        self.assertEqual(surname(None), "")


class DedupeTests(unittest.TestCase):
    def test_preprint_and_published_version_merge_and_keep_published_doi(self):
        title = "Graph Networks for Text Labelling: A Test Fixture"
        pre = Paper(title=title, arxiv_id="2101.00001v2", doi="10.48550/arXiv.2101.00001", year=2021,
                    sources=["arxiv"], abstract="short")
        pub = Paper(title=title.upper(), doi="10.1234/fixture.2", year=2022, venue="Journal of Fixtures",
                    citations=7, sources=["crossref"], abstract="a much longer abstract text")
        via_openalex = Paper(title="Unrelated title that differs entirely here", arxiv_id="2101.00001",
                             citations=10, sources=["openalex"])
        merged = dedupe([pre, pub, via_openalex])
        self.assertEqual(len(merged), 1)
        m = merged[0]
        self.assertEqual((m.doi, m.arxiv_id, m.venue, m.citations), ("10.1234/fixture.2", "2101.00001",
                                                                    "Journal of Fixtures", 10))
        self.assertEqual(m.sources, ["arxiv", "crossref", "openalex"])
        self.assertEqual((m.year, m.abstract), (2022, "short"))  # published year; arXiv's own abstract

    def test_aggregator_abstract_never_replaces_the_primary_source(self):
        primary = Paper(title="Pitfalls of evaluating graph models carefully", arxiv_id="2101.00001",
                        abstract="The real abstract.", sources=["arxiv"])
        aggregator = Paper(title="Pitfalls of evaluating graph models carefully", arxiv_id="2101.00001",
                           abstract="A much longer abstract that belongs to some entirely different record.",
                           sources=["openalex"])
        for order in ([primary, aggregator], [aggregator, primary]):
            merged = dedupe([Paper.from_dict(p.to_dict()) for p in order])[0]
            self.assertEqual((merged.abstract, merged.extra["abstract_source"]), ("The real abstract.", "arxiv"))

    def test_preprint_absorbing_published_record_takes_its_venue_and_year(self):
        pre = Paper(title="T", arxiv_id="2101.00001", year=2021, venue="arXiv", sources=["arxiv"])
        pre.absorb(Paper(title="T", doi="10.1234/pub", year=2022, venue="Journal of Fixtures", sources=["openalex"]))
        self.assertEqual((pre.doi, pre.year, pre.venue, pre.arxiv_id), ("10.1234/pub", 2022, "Journal of Fixtures",
                                                                       "2101.00001"))

    def test_distinct_papers_stay_distinct(self):
        a = Paper(title="Graph networks for labelling text documents", doi="10.1234/a")
        b = Paper(title="Graph networks for labelling image regions", doi="10.1234/b")
        self.assertEqual(len(dedupe([a, b])), 2)

    def test_short_identical_titles_need_matching_author(self):
        a = Paper(title="Graph Attention", authors=["Ada Example"])
        b = Paper(title="Graph Attention", authors=["Cy Other"])
        c = Paper(title="Graph Attention", authors=["Example, Ada"])
        self.assertEqual(len(dedupe([a, b, c])), 2)

    def test_retraction_flag_survives_merge(self):
        a = Paper(title="x", doi="10.1234/a", is_retracted=False)
        b = Paper(title="x", doi="10.1234/a", is_retracted=True)
        self.assertTrue(dedupe([a, b])[0].is_retracted)


class TextTests(unittest.TestCase):
    def test_coverage_ignores_stopwords_and_plurals(self):
        self.assertEqual(coverage("graphs for the text classification", "Text classification with a graph"), 1.0)
        self.assertEqual(coverage("graph protein", "graph text"), 0.5)

    def test_tfidf_ranks_closer_document_higher(self):
        sims = tfidf_cosine("graph text classification", ["graph text classification model", "protein folding"])
        self.assertGreater(sims[0], sims[1])
        self.assertEqual(tfidf_cosine("x", []), [])

    def test_title_similarity(self):
        self.assertGreater(title_similarity("Graph Networks: A Survey", "graph networks - a survey"), 0.95)
        self.assertEqual(title_similarity("", "x"), 0.0)


if __name__ == "__main__":
    unittest.main()
