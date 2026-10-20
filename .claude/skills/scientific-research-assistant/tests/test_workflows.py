"""Source parsing, search orchestration, novelty challenge, reproducibility,
datasets and reference verification. All HTTP is faked; see test_live.py for
real calls."""
import unittest

from helpers import ARXIV_EMPTY, ARXIV_FEED, CROSSREF_ITEM, PUBMED_XML, make_client, openalex_work

from sra import datasets, novelty, repro, search, verify
from sra.http import SourceError
from sra.sources import arxiv, crossref, github, openalex, pubmed, semanticscholar

TITLE = "Graph Networks for Text Labelling: A Test Fixture"


def search_routes(s2=429):
    return [
        ("api.openalex.org/works/W1000001", openalex_work(arxiv="2101.00001")),
        ("api.openalex.org", {"results": [openalex_work(arxiv="2101.00001")]}),
        ("export.arxiv.org", ARXIV_FEED),
        ("api.crossref.org", {"message": {"items": [CROSSREF_ITEM]}}),
        ("api.semanticscholar.org", s2),
    ]


class SourceParsingTests(unittest.TestCase):
    def test_openalex_record(self):
        p = openalex.to_paper(openalex_work(doi="10.1234/Fixture.2", arxiv="2101.00001", pmid="123456"))
        self.assertEqual((p.openalex_id, p.doi, p.arxiv_id, p.pmid), ("W1000001", "10.1234/fixture.2",
                                                                    "2101.00001", "123456"))
        self.assertEqual(p.abstract, "graph networks label text")  # rebuilt from the inverted index
        self.assertEqual(p.extra["referenced_works"], ["W2000001"])
        self.assertTrue(p.is_oa)

    def test_arxiv_feed(self):
        p = arxiv.parse_feed(ARXIV_FEED)[0]
        self.assertEqual((p.arxiv_id, p.title, p.year), ("2101.00001", TITLE, 2021))
        self.assertEqual(p.authors, ["Ada Example", "Bo Sample"])
        self.assertEqual(p.extra["arxiv_category"], "cs.CL")
        self.assertEqual(arxiv.parse_feed(ARXIV_EMPTY), [])
        with self.assertRaises(SourceError):
            arxiv.parse_feed("<not xml")

    def test_arxiv_query_builder(self):
        self.assertEqual(arxiv.build_query('"text classification" graph for the'),
                         'all:"text classification" AND all:graph')

    def test_pubmed_record(self):
        p = pubmed.parse_articles(PUBMED_XML)[0]
        self.assertEqual((p.pmid, p.doi, p.year, p.venue), ("123456", "10.1234/fixture.1", 2020, "Fixture Medicine"))
        self.assertEqual(p.title, "A fixture trial of graphs.")
        self.assertEqual(p.abstract, "Background text. Result text.")

    def test_crossref_record_strips_jats_markup(self):
        p = crossref.to_paper(CROSSREF_ITEM)
        self.assertEqual((p.doi, p.year, p.date, p.authors), ("10.1234/fixture.2", 2021, "2021-05-01", ["Ada Example"]))
        self.assertEqual(p.abstract, "We study graph networks.")

    def test_semantic_scholar_record(self):
        p = semanticscholar.to_paper({"paperId": "abc", "title": "T", "externalIds": {"ArXiv": "2101.00001",
                                      "DOI": "10.1234/X"}, "authors": [{"name": "A B"}], "citationCount": 3,
                                      "openAccessPdf": None})
        self.assertEqual((p.arxiv_id, p.doi, p.citations, p.pdf_url), ("2101.00001", "10.1234/x", 3, None))

    def test_github_url_extraction(self):
        text = "Code at https://github.com/Org-A/repo.git and github.com/org-b/tool. See github.com/topics/nlp"
        self.assertEqual(github.extract_repos(text), ["Org-A/repo", "org-b/tool"])
        self.assertEqual(github.extract_repos(None), [])


class SearchTests(unittest.TestCase):
    def test_results_are_deduplicated_across_sources(self):
        client, _, _ = make_client(search_routes())
        run = search.run_search(client, ["graph text labelling"], ["keyword"],
                                ["openalex", "arxiv", "crossref", "semantic_scholar"])
        self.assertEqual((run["n_retrieved"], run["n_after_dedup"]), (3, 1))
        paper = run["papers"][0]
        self.assertEqual(paper.sources, ["arxiv", "crossref", "openalex"])
        self.assertEqual(paper.doi, "10.1234/fixture.2")
        self.assertEqual(len(paper.found_by), 3)

    def test_failing_source_is_reported_and_not_hammered(self):
        client, opener, _ = make_client(search_routes())
        run = search.run_search(client, ["q one", "q two", "q three"], ["keyword"],
                                ["openalex", "semantic_scholar"])
        status = run["sources_status"]
        self.assertEqual(status["semantic_scholar"]["state"], "failed")
        self.assertEqual(status["semantic_scholar"]["stopped_after"], "rate_limited")
        self.assertEqual(status["openalex"]["state"], "ok")
        self.assertEqual(opener.count("semanticscholar"), 2)  # one try + one retry, then skipped
        self.assertEqual(opener.count("openalex"), 3)

    def test_strategies_change_the_queries(self):
        client, opener, _ = make_client(search_routes())
        run = search.run_search(client, ["graph text"], ["limitations", "foundational", "recent"],
                                ["openalex", "arxiv"])
        queries = [e["query"] for e in run["log"]]
        self.assertIn("graph text limitations", queries)
        self.assertIn("graph text challenges", queries)
        # arXiv cannot sort by citations, so the foundational strategy skips it
        self.assertFalse([e for e in run["log"] if e["strategy"] == "foundational" and e["source"] == "arxiv"])
        self.assertTrue(any("cited_by_count" in c for c in opener.calls))
        self.assertTrue(any("from_publication_date" in c for c in opener.calls))

    def test_concept_expansion(self):
        queries, truncated = search.expand_concepts([["GNN", "graph neural network"], ["text classification"]])
        self.assertEqual(queries, ["GNN text classification", "graph neural network text classification"])
        self.assertFalse(truncated)
        self.assertTrue(search.expand_concepts([list("abcd"), list("efgh")], cap=5)[1])

    def test_unknown_source_is_rejected(self):
        with self.assertRaises(ValueError):
            search.normalize_sources(["openalex", "google-scholar"])
        self.assertEqual(search.normalize_sources(["S2", "hf"]), ["semantic_scholar", "huggingface"])

    def test_resolve_arxiv_id_merges_openalex_record(self):
        client, _, _ = make_client(search_routes())
        paper, notes = search.resolve(client, "arXiv:2101.00001v3")
        self.assertEqual((paper.title, paper.openalex_id, paper.citations), (TITLE, "W1000001", 10))
        self.assertTrue(any(n["source"] == "semantic_scholar" for n in notes))  # failure is surfaced

    def test_published_doi_takes_venue_and_year_from_crossref(self):
        registered = {**CROSSREF_ITEM, "issued": {"date-parts": [[2023, 2, 1]]}}
        client, _, _ = make_client([
            ("api.openalex.org", {"results": [openalex_work(arxiv="2101.00001", doi="10.1234/fixture.2", year=2021)]}),
            ("export.arxiv.org", ARXIV_FEED), ("api.crossref.org/works/10.1234", {"message": registered}),
            ("api.semanticscholar.org", 429)])
        paper, _ = search.resolve(client, "2101.00001")
        self.assertEqual((paper.doi, paper.year, paper.venue, paper.arxiv_id),
                         ("10.1234/fixture.2", 2023, "Journal of Fixtures", "2101.00001"))

    def test_unknown_title_does_not_resolve(self):
        client, _, _ = make_client(search_routes())
        paper, notes = search.resolve(client, "A completely invented paper about nothing real")
        self.assertIsNone(paper)
        self.assertEqual(notes[-1]["kind"], "not_found")

    def test_related_reports_counts_and_errors(self):
        client, _, _ = make_client(search_routes())
        seed, _ = search.resolve(client, "2101.00001")
        result = search.related(client, seed, "all", 5)
        self.assertIn("references", result["counts"])
        self.assertTrue(any(e["source"] == "semantic_scholar" for e in result["errors"]))


class NoveltyTests(unittest.TestCase):
    CLAIM = "graph networks for text labelling"

    def run_challenge(self, works, queries=("a",), sources=("openalex",), design=(), **kwargs):
        client, _, _ = make_client([("api.openalex.org", {"results": works}), ("export.arxiv.org", ARXIV_EMPTY),
                                    ("api.crossref.org", {"message": {"items": []}})])
        return novelty.challenge(client, self.CLAIM, list(queries), list(sources), design=list(design), **kwargs)

    def test_many_close_papers_mean_crowded(self):
        works = [openalex_work(f"W{i}", f"Graph networks for text labelling variant number {i}") for i in range(9)]
        result = self.run_challenge(works)
        self.assertEqual((result["signal"], result["max_supported_novelty_confidence"]), ("crowded", "very_low"))

    def test_survey_of_the_topic_means_crowded(self):
        result = self.run_challenge([openalex_work("W1", "Graph networks for text labelling: a survey")])
        self.assertEqual(result["signal"], "crowded")

    def test_one_close_paper(self):
        result = self.run_challenge([openalex_work("W1", "Graph networks for text labelling in law")])
        self.assertEqual((result["signal"], result["max_supported_novelty_confidence"]),
                         ("close_prior_work_found", "low"))
        self.assertEqual(result["closest"][0]["paper"].openalex_id, "W1")

    def test_no_match_never_supports_more_than_medium_and_carries_caveat(self):
        far = [openalex_work("W1", "Protein folding with diffusion models", abstract_words=("protein",))]
        thin = self.run_challenge(far)
        self.assertEqual((thin["signal"], thin["max_supported_novelty_confidence"]),
                         ("no_close_match_in_this_search", "low"))
        # A broad search that never reached the idea's neighbourhood proves nothing either.
        off_target = self.run_challenge(far, queries=("a", "b", "c", "d"), sources=("openalex", "arxiv", "crossref"))
        self.assertEqual(off_target["max_supported_novelty_confidence"], "low")
        self.assertIn("probably missed the relevant literature", off_target["interpretation"])
        near = [openalex_work(f"W{i}", f"Graph networks for image labelling study {i}", abstract_words=("x",))
                for i in range(6)]
        near += [openalex_work(f"W9{i}", f"Unrelated chemistry topic number {i} here", abstract_words=("y",))
                 for i in range(6)]
        broad = self.run_challenge(near, queries=("a", "b", "c", "d"), sources=("openalex", "arxiv", "crossref"),
                                   design=("held-out legal corpus",))
        self.assertEqual((broad["signal"], broad["max_supported_novelty_confidence"]),
                         ("no_close_match_in_this_search", "medium"))
        self.assertIn("not evidence of novelty", broad["caveat"])

    def test_empty_search_is_not_a_novelty_claim(self):
        result = self.run_challenge([])
        self.assertEqual(result["n_papers_examined"], 0)
        self.assertNotIn(result["max_supported_novelty_confidence"], ("high", "confirmed"))


REPO_META = {"html_url": "https://github.com/example-org/fixture-repo", "stargazers_count": 42, "forks_count": 5,
             "open_issues_count": 3, "archived": False, "pushed_at": "2023-02-01T00:00:00Z",
             "created_at": "2021-01-02T00:00:00Z", "license": {"spdx_id": "MIT"}, "language": "Python",
             "default_branch": "main", "fork": False, "description": "fixture"}
README = "# Fixture\n## Setup\npip install -r requirements.txt\nPass --seed 1 to fix the seed.\nTrained on one RTX 2080.\n"
TREE = {"truncated": False, "tree": [{"path": p, "type": "blob"} for p in
                                     ("requirements.txt", "train.py", "configs/base.yaml", "README.md")]}


def repro_routes(repo_meta=REPO_META, search_items=()):
    return [
        ("huggingface.co/api/papers/", {"id": "2101.00001"}),
        ("huggingface.co/api/arxiv/", {"datasets": [{"id": "example/fixture-data"}], "models": []}),
        ("api.github.com/search/repositories", {"items": list(search_items)}),
        ("api.github.com/search/issues", {"total_count": 3}),
        ("/repos/example-org/fixture-repo/readme", README),
        ("/repos/example-org/fixture-repo/git/trees", TREE),
        ("/repos/example-org/fixture-repo", repo_meta),
        ("cites%3A", {"results": []}),
        ("api.openalex.org", {"results": [openalex_work(arxiv="2101.00001")]}),
        ("export.arxiv.org", ARXIV_FEED),
        ("api.semanticscholar.org", 429),
    ]


class ReproTests(unittest.TestCase):
    def test_repo_linked_from_abstract_is_inspected(self):
        client, _, _ = make_client(repro_routes())
        result = repro.assess(client, "2101.00001")
        checks = result["checklist"]
        self.assertFalse(result["executed"])
        self.assertIn("No code was executed", result["disclaimer"])
        self.assertEqual(result["code_candidates"][0]["relationship"], "linked_by_paper")
        self.assertEqual(checks["full_text"]["status"], "verified")
        self.assertEqual(checks["code"]["status"], "found")
        self.assertEqual(checks["license"]["evidence"], ["SPDX: MIT"])
        for key in ("dependencies", "configs", "training", "seeds", "hardware"):
            self.assertEqual(checks[key]["status"], "found", key)
        self.assertIn("file: requirements.txt", checks["dependencies"]["evidence"])
        # Nothing in the fixture mentions evaluation or checkpoints: reported as not found, not assumed.
        self.assertEqual(checks["evaluation"]["status"], "not_found")
        self.assertEqual(checks["pretrained"]["status"], "not_found")
        self.assertEqual(checks["architecture"]["status"], "manual_review")
        self.assertEqual(checks["prior_reproductions"]["status"], "not_found")
        self.assertEqual(result["huggingface_linked"]["datasets"], ["example/fixture-data"])
        self.assertIn("Evaluation script or protocol", result["missing"])

    def test_no_repository_is_a_blocker_not_a_guess(self):
        routes = [r for r in repro_routes() if "/repos/" not in r[0]]
        routes[routes.index(next(r for r in routes if r[0] == "export.arxiv.org"))] = (
            "export.arxiv.org", ARXIV_FEED.replace("Code: https://github.com/example-org/fixture-repo.", ""))
        client, _, _ = make_client(routes)
        result = repro.assess(client, "2101.00001")
        self.assertEqual(result["checklist"]["code"]["status"], "not_found")
        self.assertTrue(any("No implementation located" in b for b in result["potential_blockers"]))
        self.assertEqual(result["checklist"]["seeds"]["status"], "manual_review")

    def test_name_match_only_repo_is_not_presented_as_the_implementation(self):
        routes = repro_routes(search_items=[{"full_name": "stranger/lookalike"}])
        routes[routes.index(next(r for r in routes if r[0] == "export.arxiv.org"))] = (
            "export.arxiv.org", ARXIV_FEED.replace("Code: https://github.com/example-org/fixture-repo.", ""))
        routes.insert(0, ("/repos/stranger/lookalike/readme", "An unrelated project."))
        routes.insert(1, ("/repos/stranger/lookalike/git/trees", {"tree": []}))
        routes.insert(2, ("/repos/stranger/lookalike", REPO_META))
        # only the name search returns it; the two readme searches return nothing
        routes[routes.index(next(r for r in routes if r[0] == "api.github.com/search/repositories"))] = (
            "api.github.com/search/repositories", [{"items": []}, {"items": []},
                                                   {"items": [{"full_name": "stranger/lookalike"}]}])
        client, _, _ = make_client(routes)
        result = repro.assess(client, "2101.00001")
        self.assertEqual(result["code_candidates"][0]["relationship"], "name_match_only")
        self.assertEqual(result["checklist"]["code"]["status"], "manual_review")
        self.assertIn("NOT confirmed", result["checklist"]["code"]["note"])

    def test_archived_repo_is_flagged(self):
        client, _, _ = make_client(repro_routes(repo_meta={**REPO_META, "archived": True}))
        self.assertTrue(any("archived" in b for b in repro.assess(client, "2101.00001")["potential_blockers"]))

    def test_unresolvable_paper(self):
        client, _, _ = make_client([("export.arxiv.org", ARXIV_EMPTY)])
        result = repro.assess(client, "2101.99999")
        self.assertEqual((result["resolved"], result["executed"]), (False, False))


HF_DATASET = {"id": "example/fixture-data", "gated": False, "private": False, "disabled": False, "downloads": 9,
              "likes": 1, "lastModified": "2024-01-01T00:00:00.000Z",
              "tags": ["task_categories:text-classification", "language:en", "license:cc-by-4.0",
                       "size_categories:10K<n<100K", "format:parquet", "modality:text", "arxiv:2101.00001"],
              "cardData": {"license": "cc-by-4.0", "pretty_name": "Fixture Data"}}
HF_SIZE = {"size": {"dataset": {"num_rows": 12000, "num_bytes_original_files": 3 * 1024 * 1024,
                                "num_bytes_memory": 5 * 1024 * 1024},
                    "splits": [{"config": "default", "split": "train", "num_rows": 10000},
                               {"config": "default", "split": "test", "num_rows": 2000}]}, "partial": False}


class DatasetTests(unittest.TestCase):
    def test_reference_parsing(self):
        self.assertEqual(datasets.parse_ref("https://huggingface.co/datasets/nyu-mll/glue"), ("huggingface", "nyu-mll/glue"))
        self.assertEqual(datasets.parse_ref("hf:imdb"), ("huggingface", "imdb"))
        self.assertEqual(datasets.parse_ref("https://zenodo.org/records/12345"), ("zenodo", "12345"))
        self.assertEqual(datasets.parse_ref("10.5281/zenodo.777"), ("zenodo", "777"))
        self.assertEqual(datasets.parse_ref("https://example.org/data.zip"), ("url", "https://example.org/data.zip"))

    def test_verified_open_dataset(self):
        client, _, _ = make_client([("datasets-server", HF_SIZE), ("api/datasets/", HF_DATASET)])
        info = datasets.verify(client, "example/fixture-data")
        self.assertTrue(info["exists"])
        self.assertEqual((info["license"], info["num_rows"], len(info["splits"])), ("cc-by-4.0", 12000, 2))
        self.assertIn("3.0 MB", info["storage_estimate"])
        self.assertEqual((info["missing"], info["blockers"]), ([], []))

    def test_gated_dataset_is_a_blocker_and_unknowns_are_listed(self):
        gated = {**HF_DATASET, "gated": "manual", "tags": [], "cardData": {}}
        client, _, _ = make_client([("datasets-server", 404), ("api/datasets/", gated)])
        info = datasets.verify(client, "example/fixture-data")
        self.assertTrue(any("Gated" in b for b in info["blockers"]))
        self.assertIsNone(info["license"])
        self.assertIsNone(info["num_rows"])  # not invented when the viewer has no figure
        self.assertEqual(info["missing"], ["license", "size (rows)", "download size"])

    def test_missing_dataset(self):
        client, _, _ = make_client([("api/datasets/", 404)])
        info = datasets.verify(client, "nobody/does-not-exist")
        self.assertIs(info["exists"], False)

    def test_outage_is_not_reported_as_nonexistence(self):
        client, _, _ = make_client([("api/datasets/", 503)])
        self.assertIsNone(datasets.verify(client, "example/fixture-data")["exists"])

    def test_zenodo_restricted_record(self):
        record = {"id": 5, "doi": "10.5281/zenodo.5", "links": {"self_html": "https://zenodo.org/records/5"},
                  "metadata": {"title": "Z", "access_right": "restricted", "license": None},
                  "files": []}
        client, _, _ = make_client([("zenodo.org/api/records/5", record)])
        info = datasets.verify(client, "zenodo:5")
        self.assertTrue(any("restricted" in b for b in info["blockers"]))
        self.assertEqual(info["missing"], ["license", "file sizes"])

    def test_plain_url_only_claims_reachability(self):
        client, _, _ = make_client([("example.org", "x")])
        info = datasets.verify(client, "https://example.org/data.zip")
        self.assertTrue(info["exists"])
        self.assertIn("license", info["missing"])

    def test_search_survives_one_source_failing(self):
        client, _, _ = make_client([("huggingface.co/api/datasets", [[HF_DATASET]]), ("zenodo.org", 503)])
        result = datasets.search(client, "fixture")
        self.assertEqual(len(result["huggingface"]), 1)
        self.assertEqual(result["errors"][0]["source"], "zenodo")


class VerifyTests(unittest.TestCase):
    def test_matching_arxiv_record_is_verified(self):
        client, _, _ = make_client([("export.arxiv.org", ARXIV_FEED)])
        result = verify.verify_paper(client, {"title": TITLE.lower(), "arxiv_id": "2101.00001"})
        self.assertEqual((result["status"], result["via"]), ("verified", "arxiv"))

    def test_real_identifier_with_wrong_title_is_caught(self):
        client, _, _ = make_client([("export.arxiv.org", ARXIV_FEED)])
        result = verify.verify_paper(client, {"title": "Quantum Advantage in Protein Design", "arxiv_id": "2101.00001"})
        self.assertEqual(result["status"], "title_mismatch")
        self.assertEqual(result["resolved_title"], TITLE)

    def test_nonexistent_identifier_is_unresolved(self):
        client, _, _ = make_client([("export.arxiv.org", ARXIV_EMPTY)])
        self.assertEqual(verify.verify_paper(client, {"title": "X", "arxiv_id": "2101.99999"})["status"], "unresolved")
        client, _, _ = make_client([])  # every request answers 404
        self.assertEqual(verify.verify_paper(client, {"title": "X", "doi": "10.9999/fake"})["status"], "unresolved")

    def test_outage_is_unchecked_not_unresolved(self):
        client, _, _ = make_client([("export.arxiv.org", 503)])
        self.assertEqual(verify.verify_paper(client, {"title": "X", "arxiv_id": "2101.00001"})["status"], "unchecked")

    def test_doi_checked_through_crossref_then_doi_handle(self):
        client, _, _ = make_client([("api.crossref.org", {"message": CROSSREF_ITEM})])
        self.assertEqual(verify.verify_paper(client, {"title": TITLE, "doi": "10.1234/fixture.2"})["status"], "verified")
        client, _, _ = make_client([("api.crossref.org", 404), ("doi.org/api/handles", {"responseCode": 1})])
        self.assertEqual(verify.verify_paper(client, {"title": TITLE, "doi": "10.5555/datacite.1"})["status"],
                         "identifier_resolves")

    def test_no_identifier_and_url_only(self):
        client, _, _ = make_client([("example.org", "ok")])
        self.assertEqual(verify.verify_paper(client, {"title": "X"})["status"], "no_identifier")
        self.assertEqual(verify.verify_paper(client, {"title": "X", "url": "https://example.org/p"})["status"],
                         "url_reachable")

    def test_report_counts(self):
        client, _, _ = make_client([("export.arxiv.org", ARXIV_FEED)])
        report = {"papers": [{"key": "a", "title": TITLE, "arxiv_id": "2101.00001"}, {"key": "b", "title": "X"}]}
        self.assertEqual(verify.verify_report(client, report), {"verified": 1, "no_identifier": 1})
        self.assertEqual(report["papers"][0]["verification"]["status"], "verified")


if __name__ == "__main__":
    unittest.main()
