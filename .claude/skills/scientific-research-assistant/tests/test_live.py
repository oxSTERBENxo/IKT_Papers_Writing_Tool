"""Live integration tests against the real services.

Skipped unless SRA_LIVE=1, because they need network access and are subject
to third-party rate limits. A source that answers "rate limited" is reported
as a skip, never as a pass.

    cd tests; SRA_LIVE=1 python -m unittest test_live -v      (PowerShell: $env:SRA_LIVE=1)
"""
import os
import unittest

import helpers  # noqa: F401

from sra import datasets, fulltext, search, verify
from sra.http import HttpClient, SourceError
from sra.sources import arxiv, crossref, github, huggingface, openalex, pubmed, semanticscholar, zenodo

LIVE = os.environ.get("SRA_LIVE") == "1"
GCN_ARXIV = "1609.02907"
GCN_TITLE = "Semi-Supervised Classification with Graph Convolutional Networks"


@unittest.skipUnless(LIVE, "set SRA_LIVE=1 to run live integration tests")
class LiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = HttpClient(cache_dir=None)

    def call(self, fn, *args, **kwargs):
        try:
            return fn(self.client, *args, **kwargs)
        except SourceError as exc:
            if exc.kind in ("rate_limited", "network"):
                self.skipTest(f"NOT VERIFIED: {exc}")
            raise

    def assert_papers(self, papers):
        self.assertTrue(papers)
        self.assertTrue(all(p.title for p in papers))

    def test_openalex_search(self):
        self.assert_papers(self.call(openalex.search, "graph convolutional network text classification", 5))

    def test_arxiv_lookup(self):
        self.assertEqual(self.call(arxiv.get_paper, GCN_ARXIV).title, GCN_TITLE)

    def test_arxiv_search(self):
        self.assert_papers(self.call(arxiv.search, '"graph neural network" text classification', 5))

    def test_crossref_search(self):
        self.assert_papers(self.call(crossref.search, "graph convolutional networks text classification", 5))

    def test_pubmed_search(self):
        self.assert_papers(self.call(pubmed.search, "graph neural network drug interaction", 3))

    def test_semantic_scholar_search(self):
        self.assert_papers(self.call(semanticscholar.search, "graph convolutional network", 3))

    def test_huggingface_papers_and_datasets(self):
        self.assert_papers(self.call(huggingface.search, "graph neural network text classification", 5))
        info = self.call(datasets.verify, "nyu-mll/glue")
        self.assertTrue(info["exists"])
        self.assertGreater(info["num_rows"], 0)

    def test_nonexistent_dataset_is_reported_missing(self):
        info = self.call(datasets.verify, "sra-fixture-nobody/this-dataset-does-not-exist-0000")
        self.assertIsNot(info["exists"], True)

    def test_zenodo_search(self):
        self.assertTrue(self.call(zenodo.search_datasets, "knowledge graph", 2))

    def test_github_repo(self):
        self.assertEqual(self.call(github.get_repo, "tkipf/gcn")["full_name"], "tkipf/gcn")

    def test_resolve_and_verify_real_reference(self):
        paper, _ = self.call(search.resolve, GCN_ARXIV)
        self.assertEqual(paper.title, GCN_TITLE)
        result = self.call(verify.verify_paper, {"title": GCN_TITLE, "arxiv_id": GCN_ARXIV})
        self.assertEqual(result["status"], "verified")

    def test_fulltext_from_arxiv_source(self):
        result = fulltext.fetch(self.client, GCN_ARXIV)
        if result["status"] != "full_text" and any("network" in n or "rate" in n for n in result["notes"]):
            self.skipTest(f"NOT VERIFIED: {result['notes']}")
        self.assertEqual(result["status"], "full_text")
        roles = {r for s in result["sections"] for r in s["roles"]}
        self.assertTrue({"experiments", "results"} & roles)
        self.assertTrue(result["flags"]["split_protocol"] or result["flags"]["runs_and_seeds"])

    def test_fabricated_reference_is_caught(self):
        result = self.call(verify.verify_paper, {"title": "A Paper That Was Never Written", "arxiv_id": GCN_ARXIV})
        self.assertEqual(result["status"], "title_mismatch")


if __name__ == "__main__":
    unittest.main()
