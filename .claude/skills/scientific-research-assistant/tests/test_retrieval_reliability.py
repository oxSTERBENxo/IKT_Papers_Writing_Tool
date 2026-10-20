"""Retrieval-reliability changes (2026-10-19): arXiv query relaxation, rate-limit cool-down, source positions,
rank fusion, the optional embedding backend, replay snapshots, the extended retrieval-evaluation metrics and the
blind fixture set. HTTP is faked; nothing here measures retrieval quality (see evals/results/).
"""
import hashlib
import json
import tempfile
import unittest
import urllib.parse
from pathlib import Path

from helpers import ARXIV_EMPTY, ARXIV_FEED, http_error, make_client

from sra import fusion, novelty, retrieval_eval, search, semantic
from sra.http import HttpClient, SourceError
from sra.models import Paper
from sra.sources import arxiv

SKILL = Path(__file__).resolve().parents[1]
BLIND = SKILL / "evals" / "retrieval_blind"


def paper(title, abstract="", **kw):
    return Paper(title=title, abstract=abstract, **kw)


class ArxivQueryTests(unittest.TestCase):
    def test_all_mode_is_unchanged(self):
        self.assertEqual(arxiv.build_query("graph neural network"), "all:graph AND all:neural AND all:network")

    def test_any_mode_ors_words_and_keeps_phrases_required(self):
        self.assertEqual(arxiv.build_query("graph neural network", "any"),
                         "(all:graph OR all:neural OR all:network)")
        self.assertEqual(arxiv.build_query('"fake news" graph detection', "any"),
                         'all:"fake news" AND (all:graph OR all:detection)')
        self.assertEqual(arxiv.build_query("graph", "any"), "all:graph")
        with self.assertRaises(ValueError):
            arxiv.build_query("x", "some")

    def test_run_search_passes_match_mode_to_arxiv_only(self):
        client, opener, _ = make_client([("export.arxiv.org", ARXIV_FEED), ("api.crossref.org", {"message": {"items": []}})])
        run = search.run_search(client, ["graph text labelling"], ["keyword"], ["arxiv", "crossref"], arxiv_match="any")
        arxiv_urls = [urllib.parse.unquote_plus(u) for u in opener.calls if "arxiv" in u]
        self.assertTrue(any(" OR " in u for u in arxiv_urls))
        self.assertEqual(run["papers"][0].found_by[0]["position"], 1)


class CooldownTests(unittest.TestCase):
    def test_rate_limited_source_gets_one_retry_after_cooldown(self):
        client, _, sleeps = make_client([("export.arxiv.org", [429, ARXIV_FEED])])
        client.max_retries = 0
        run = search.run_search(client, ["graph text"], ["keyword"], ["arxiv"], cooldown=30.0)
        self.assertEqual(len(run["papers"]), 1)
        self.assertIn(30.0, sleeps)
        self.assertEqual(run["sources_status"]["arxiv"]["state"], "ok")

    def test_without_cooldown_source_is_disabled(self):
        client, _, _ = make_client([("export.arxiv.org", [429, ARXIV_FEED])])
        client.max_retries = 0
        run = search.run_search(client, ["graph text", "other words"], ["keyword"], ["arxiv"])
        self.assertEqual(run["sources_status"]["arxiv"]["state"], "failed")


class FusionTests(unittest.TestCase):
    CLAIM = "A controlled multi-seed comparison showing whether syntax still helps when the encoder is held fixed"

    def test_query_match_rises_above_claim_filler_match(self):
        exact = paper("Does syntax matter? A strong baseline for aspect sentiment with RoBERTa",
                      "syntax trees aspect sentiment roberta baseline")
        filler = paper("Controlled experiments showing encoders held fixed",
                       "a controlled study showing results when the encoder is held fixed, multi-seed")
        others = [paper(f"Unrelated paper {i}", "image segmentation of cells") for i in range(5)]
        pool = [filler, exact, *others]
        claim_order = [s["paper"] for s in novelty._score(self.CLAIM, pool, [])]
        self.assertIs(claim_order[0], filler)  # the failure mode found in the analysis
        fused = novelty._order(novelty._score(self.CLAIM, pool, []), self.CLAIM,
                               ["does syntax matter aspect sentiment roberta"], [], "fusion", False)
        self.assertIs(fused[0]["paper"], exact)
        self.assertIn("fusion_score", fused[0])

    def test_ranks_ignore_zero_and_none(self):
        self.assertEqual(fusion._ranks([0.5, 0.0, None, 0.9, -0.1]), [2, None, None, 1, None])

    def test_hybrid_weights_semantic_like_the_whole_lexical_ranking(self):
        a, b = paper("graph syntax", "graph syntax"), paper("graph", "graph trees")
        lex_only = fusion.fuse("graph syntax", ["graph syntax"], [a, b])
        self.assertGreater(lex_only[0][0], lex_only[1][0])
        hybrid = fusion.fuse("graph syntax", ["graph syntax"], [a, b], semantic=[0.1, 0.9])
        self.assertAlmostEqual(hybrid[0][0], hybrid[1][0])  # rank 1 + rank 2 each way: a tie

    def test_challenge_rejects_unknown_ranking(self):
        client, _, _ = make_client([])
        with self.assertRaises(ValueError):
            novelty.challenge(client, "x", ["x"], [], ranking="magic")


class SemanticOptionalTests(unittest.TestCase):
    def test_missing_backend_degrades_to_none(self):
        semantic._cache.clear()
        import os
        old = os.environ.get("SRA_EMBED_BACKEND")
        os.environ["SRA_EMBED_BACKEND"] = "no-such-backend"
        try:
            self.assertFalse(semantic.available())
            self.assertIsNone(semantic.similarities(["q"], ["d"]))
            self.assertIn("unavailable", semantic.describe())
        finally:
            semantic._cache.clear()
            if old is None:
                os.environ.pop("SRA_EMBED_BACKEND")
            else:
                os.environ["SRA_EMBED_BACKEND"] = old


class SnapshotTests(unittest.TestCase):
    def test_offline_replay_serves_snapshot_and_fails_on_miss(self):
        with tempfile.TemporaryDirectory() as d:
            client, _, _ = make_client([("example.org", {"ok": 1})])
            client.cache_dir, client.cache_ttl = d, float("inf")
            self.assertEqual(client.get("https://example.org/a"), {"ok": 1})
            replay = HttpClient(cache_dir=d, cache_ttl=float("inf"), opener=lambda *a, **k: 1 / 0)
            replay.offline = True
            self.assertEqual(replay.get("https://example.org/a"), {"ok": 1})
            with self.assertRaises(SourceError):
                replay.get("https://example.org/b")
            self.assertEqual(replay.call_count, 2)
            self.assertEqual(replay.request_count, 0)


class EvalMetricTests(unittest.TestCase):
    def test_miss_cause(self):
        k_arxiv = {"title": "t", "arxiv_id": "2101.00001"}
        k_title_only = {"title": "OpenReview only"}
        k_doi = {"title": "t", "doi": "10.1145/1"}
        self.assertEqual(retrieval_eval.miss_cause(k_arxiv, ["arxiv", "crossref"], ["arxiv"], []), "source_unavailable")
        self.assertEqual(retrieval_eval.miss_cause(k_arxiv, ["arxiv", "crossref"], [], []), "algorithm")
        self.assertEqual(retrieval_eval.miss_cause(k_title_only, ["arxiv", "crossref"], [], []),
                         "not_in_searched_indexes")
        self.assertEqual(retrieval_eval.miss_cause(k_doi, ["arxiv"], [], []), "not_in_searched_indexes")
        self.assertEqual(retrieval_eval.miss_cause({"title": "t", "doi": "10.48550/arXiv.2101.00001"},
                                                   ["crossref"], [], []), "not_in_searched_indexes")

    def test_summary_reports_recall_at_50_and_mrr(self):
        res = [{"id": "b", "split": "blind", "n_targets": 3, "configs": {"challenge": {
            "hits": [{"found": True, "in_top_k": True, "rank": 1}, {"found": True, "in_top_k": False, "rank": 40},
                     {"found": False, "in_top_k": False, "rank": None, "cause": "algorithm"}],
            "n_retrieved": 100, "http_calls": 10, "seconds": 2.0, "signal": "crowded"}}}]
        s = retrieval_eval.summarize(res, ("challenge",))["blind"]["challenge"]
        self.assertEqual((s["found"], s["in_top_20"], s["in_top_50"]), (2, 1, 2))
        self.assertAlmostEqual(s["mrr"], round((1 + 1 / 40) / 3, 3))
        self.assertEqual(s["miss_causes"], {"algorithm": 1})

    def test_configs_keep_regression_set(self):
        self.assertEqual(retrieval_eval.REGRESSION_CONFIGS, ("baseline", "challenge", "landscape", "full"))
        for c in retrieval_eval.EXPERIMENT_CONFIGS:
            self.assertIn(c, retrieval_eval.CHALLENGE_VARIANTS)


class BlindFixtureTests(unittest.TestCase):
    def test_frozen_files_match_manifest(self):
        manifest = json.loads((BLIND / "MANIFEST.json").read_text(encoding="utf-8"))
        for name in ("specs.json", "build_fixtures.py"):
            self.assertEqual(hashlib.sha256((BLIND / name).read_bytes()).hexdigest(), manifest[name], name)

    def test_blind_set_is_disjoint_from_development_fixtures(self):
        blind = retrieval_eval.load_fixtures(str(BLIND / "fixtures" / "*.json"))
        old = retrieval_eval.load_fixtures(str(SKILL / "evals" / "retrieval" / "*.json"))
        self.assertEqual({f["split"] for f in blind}, {"blind", "control"})
        key = lambda k: k.get("arxiv_id") or k.get("doi") or k["title"].lower()
        old_targets = {key(k) for f in old for k in f["known_relevant"]}
        for f in blind:
            self.assertFalse({key(k) for k in f["known_relevant"]} & old_targets, f["id"])
            seeds = set(f.get("seeds") or [])
            self.assertFalse({k.get("arxiv_id") for k in f["known_relevant"]} & seeds, f["id"])
        self.assertGreaterEqual(sum(len(f["known_relevant"]) for f in blind), 30)


if __name__ == "__main__":
    unittest.main()
