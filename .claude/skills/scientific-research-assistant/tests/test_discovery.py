"""Literature-first discovery: evidence-type strategies, the landscape map, evidence-driven question typing
(report schema 3), question-type-aware scoring and the retrieval-evaluation harness. HTTP is faked.

These tests check that the machinery behaves as specified. Whether it retrieves the right literature is measured
separately, live, with `retrieval-eval` (see evals/retrieval/ and evals/results/).
"""
import copy
import glob
import json
import unittest
from pathlib import Path

from helpers import ARXIV_EMPTY, make_client, openalex_work

from sra import landscape, report, retrieval_eval, scoring, search
from sra.models import Paper

SKILL = Path(__file__).resolve().parents[1]

NEG = openalex_work("W1100001", "Revisiting graph models for review sentiment",
                    abstract_words=("we", "find", "that", "the", "graph", "brings", "no", "significant", "improvement",
                                    "over", "a", "strong", "encoder"))
METHOD = openalex_work("W1100002", "A novel dual graph network for review sentiment",
                       abstract_words=("we", "propose", "a", "novel", "model", "that", "outperforms", "the", "state"))
CRIT = openalex_work("W1100003", "Benchmark pitfalls in review sentiment evaluation",
                     abstract_words=("the", "benchmark", "evaluation", "protocol", "has", "a", "data", "leakage", "flaw"))
HIDDEN = openalex_work("W1100004", "Structure-free baselines suffice for opinion graphs",
                       abstract_words=("an", "MLP", "on", "the", "same", "node", "features", "matches", "graph",
                                       "models", "and", "randomly", "rewired", "edges", "change", "nothing"))


def client_for(search_results, citing=()):
    return make_client([
        ("cites%3A", {"results": list(citing)}),
        ("filter=openalex%3A", {"results": []}),
        ("api.openalex.org/works/W1100001", NEG),
        ("api.openalex.org", {"results": list(search_results)}),
        ("export.arxiv.org", ARXIV_EMPTY),
        ("api.crossref.org", {"message": {"items": []}}),
    ])


class StrategyTests(unittest.TestCase):
    def test_discovery_strategies_exist_and_are_small(self):
        for name in ("negative", "comparisons", "critique"):
            self.assertIn(name, search.STRATEGIES)
            self.assertLessEqual(len(search.STRATEGIES[name]), 2)  # rate-limit budget
        self.assertTrue(set(search.DISCOVERY_STRATEGIES) <= set(search.STRATEGIES))

    def test_design_queries_are_anchored_and_deduplicated(self):
        q = search.design_queries(["MLP baseline on the same features", "MLP baseline on the same features",
                                   "fake news shuffled features"], "fake news")
        self.assertEqual(q, ["MLP baseline on the same features fake news", "fake news shuffled features"])


class LandscapeTests(unittest.TestCase):
    def test_common_phrase_as_well_as_is_not_a_negative_result(self):
        # Seen live: PinSage and a survey were bucketed as negative results because of "as well as".
        self.assertNotIn("negative_result", landscape.classify(Paper(
            title="Graph convolutional networks for web-scale recommender systems",
            abstract="We use item features as well as graph structure and outperform baselines.")))
        self.assertIn("negative_result", landscape.classify(Paper(
            title="x", abstract="A linear model performs as well as the graph network.")))

    def test_product_reviews_are_not_surveys(self):
        self.assertNotIn("survey", landscape.classify(Paper(title="Graph models for hotel review sentiment",
                                                            abstract="We classify customer reviews.")))
        self.assertIn("survey", landscape.classify(Paper(title="Sentiment analysis: a comprehensive review")))
        self.assertIn("survey", landscape.classify(Paper(title="A survey of graph neural networks")))

    def test_evidence_types(self):
        types = {w["title"]: landscape.classify(Paper(title=w["title"], abstract=" ".join(
            w["abstract_inverted_index"]))) for w in (NEG, METHOD, CRIT)}
        self.assertIn("negative_result", types[NEG["title"]])
        self.assertIn("reproducibility", types[NEG["title"]])  # "revisiting"
        self.assertIn("method_proposal", types[METHOD["title"]])
        self.assertNotIn("negative_result", types[METHOD["title"]])
        self.assertIn("benchmark_critique", types[CRIT["title"]])

    def test_map_prioritises_negative_and_critique_and_builds_web_queries(self):
        client, opener, _ = client_for([METHOD, NEG, CRIT])
        m = landscape.map_landscape(client, ["review sentiment graph"], ["openalex"],
                                    design=["MLP baseline on the same features"], anchor="review sentiment",
                                    expand_top=0)
        self.assertTrue(any("revisiting" in c for c in opener.calls))  # negative strategy issued
        self.assertTrue(any("evaluation+pitfalls" in c or "evaluation%20pitfalls" in c for c in opener.calls))
        whys = {x["title"]: x["why"] for x in m["must_read"]}
        self.assertIn(NEG["title"], whys)
        self.assertTrue(any(w == "negative_result candidate" for w in whys.values()) or whys[NEG["title"]] == "top match")
        self.assertEqual([x["why"] for x in m["must_read"][:3]].count("top match"),
                         min(3, m["n_papers"]))  # best topic matches always come first
        self.assertIn("MLP baseline on the same features review sentiment", m["web_search_queries"])
        self.assertTrue(any("no seed papers" in n for n in m["coverage_notes"]))
        self.assertEqual(m["ledger_template"]["types"], list(report.LEDGER_TYPES))

    def test_top_match_is_read_first_even_without_an_evidence_pattern(self):
        plain = openalex_work("W1100009", "Review sentiment graph models with pretrained encoders",
                              abstract_words=("review", "sentiment", "graph", "encoders", "results", "tables"))
        client, _, _ = client_for([plain, METHOD, CRIT])
        m = landscape.map_landscape(client, ["review sentiment graph encoders"], ["openalex"], expand_top=0)
        self.assertEqual(landscape.classify(Paper(title=plain["title"], abstract="review sentiment graph")), [])
        self.assertIn(plain["title"], [x["title"] for x in m["must_read"] if x["why"] == "top match"])

    def test_seed_citing_search_reaches_differently_worded_paper(self):
        client, _, _ = client_for([METHOD], citing=[HIDDEN])
        m = landscape.map_landscape(client, ["review sentiment graph"], ["openalex"],
                                    design=["MLP baseline on the same node features"], seeds=["W1100001"],
                                    expand_top=0)
        self.assertIn(HIDDEN["title"], [p.title for p in m["papers"]])


def v3_report():
    return {
        "type": "opportunity_report", "title": "T", "schema_version": 3,
        "papers": [
            {"key": "a2021", "title": "A", "arxiv_id": "2101.00001", "verification": {"status": "verified"},
             "read_level": "full_text"},
            {"key": "b2022", "title": "B", "arxiv_id": "2201.00002", "verification": {"status": "verified"},
             "read_level": "title_only"}],
        "evidence_ledger": [
            {"id": "L1", "type": "methodological_weakness", "text": "Model selection on the test set",
             "level": "verified", "sources": ["a2021"]}],
        "opportunities": [{
            "title": "Re-test A", "category": "reported_limitation", "mode": "replication", "status": "kept",
            "question_type": "replication", "derived_from": ["L1"], "research_question": "Does A hold?",
            "closest_existing_work": [{"key": "a2021", "how_it_differs": "protocol", "overlap": "same_experiment"}],
            "novelty": {"confidence": "low", "uncertainty": "u", "challenge_searches": ["q"]},
            "methodological_risks": [{"type": "model_selection_on_test", "status": "found", "evidence": "x"}],
            "decision": {"verdict": "conditional_go", "rationale": "r", "conditions": ["c"], "unresolved_risks": ["u"]},
        }],
    }


class SchemaV3Tests(unittest.TestCase):
    def errors(self, data):
        return report.validate(data)[0]

    def assertError(self, data, fragment):
        errs = self.errors(data)
        self.assertTrue(any(fragment in e for e in errs), f"'{fragment}' not in {errs}")

    def test_valid_v3_report(self):
        self.assertEqual(self.errors(v3_report()), [])

    def test_question_type_and_derivation_required(self):
        d = v3_report()
        del d["opportunities"][0]["question_type"]
        d["opportunities"][0]["derived_from"] = []
        self.assertError(d, "question_type missing")
        self.assertError(d, "derived_from is empty")

    def test_unknown_ledger_entry_and_unread_ledger_source(self):
        d = v3_report()
        d["opportunities"][0]["derived_from"] = ["L9"]
        self.assertError(d, "unknown ledger entry 'L9'")
        d = v3_report()
        d["evidence_ledger"][0]["sources"] = ["b2022"]
        self.assertError(d, "needs at least one source read in full or at abstract level")

    def test_novel_label_refused_when_prior_work_answers_the_question(self):
        d = v3_report()
        o = d["opportunities"][0]
        o.update(question_type="novel", mode="original")
        o["closest_existing_work"][0]["overlap"] = "same_question_different_design"
        self.assertError(d, "called novel although")

    def test_answered_must_be_no_go_and_types_match_modes(self):
        d = v3_report()
        d["opportunities"][0]["question_type"] = "answered"
        self.assertError(d, "must be rejected with verdict no_go")
        d = v3_report()
        d["opportunities"][0]["question_type"] = "extension"
        self.assertError(d, "needs mode in ('extension',)")

    def test_legacy_reports_get_warnings_not_errors(self):
        d = v3_report()
        del d["schema_version"]
        del d["evidence_ledger"]
        o = d["opportunities"][0]
        del o["question_type"]
        del o["derived_from"]
        errors, warnings = report.validate(d)
        self.assertEqual(errors, [])
        self.assertTrue(any("question_type missing" in w for w in warnings))

    def test_v3_without_ledger_is_refused(self):
        d = v3_report()
        d["evidence_ledger"] = []
        self.assertError(d, "evidence_ledger is empty")

    def test_rendering_shows_evidence_map_type_and_derivation(self):
        md = report.render_markdown(v3_report())
        for text in ("## Evidence map", "Model selection on the test set", "**Question type:** Reproduction or "
                     "replication study", "**Derived from.**", "| Re-test A | Reproduction or replication study |"):
            self.assertIn(text, md)
        legacy = v3_report()
        del legacy["evidence_ledger"]
        self.assertNotIn("## Evidence map", report.render_markdown(legacy))

    def test_existing_reports_still_validate(self):
        for path in [SKILL / "examples" / "nlp-graph-theory" / "opportunity_report.json"]:
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(report.validate(copy.deepcopy(data))[0], [], path)


class QuestionTypeScoringTests(unittest.TestCase):
    def cand(self, **kw):
        c = {"score": 4, "evidence": ["e"], "evidence_level": "estimate", "missing": []}
        return {"id": "A", "mode": kw.pop("mode", "replication"),
                "criteria": {n: dict(c) for n in scoring.WEIGHTS}, **kw}

    def value(self, cand):
        row = scoring.rank({"candidates": [cand]})["ranking"][0]
        return next(r["score"] for r in row["criteria"] if r["criterion"] == "novelty_or_replication_value"), row

    def test_replication_is_not_penalised_for_lacking_novelty(self):
        score, row = self.value(self.cand(question_type="replication", replication_rationale=["single-run result"],
                                          novelty_evidence={"closest_read": "full_text",
                                                            "prior_overlap": "same_experiment"}))
        self.assertEqual((score, row["value_basis"]), (4, "replication value"))

    def test_replication_of_an_unread_study_is_capped_at_three(self):
        score, row = self.value(self.cand(question_type="benchmark_validity", replication_rationale=["leakage"],
                                          novelty_evidence={"closest_read": "abstract"}))
        self.assertEqual(score, 3)
        self.assertIn("re-tested", row["caps_applied"][0]["reason"])

    def test_replication_needs_a_rationale(self):
        with self.assertRaises(ValueError):
            scoring.rank({"candidates": [self.cand(question_type="replication")]})

    def test_novel_question_keeps_novelty_caps_and_answered_is_blocked(self):
        score, row = self.value(self.cand(mode="original", question_type="novel",
                                          novelty_evidence={"closest_read": "abstract"}))
        self.assertEqual((score, row["value_basis"]), (2, "novelty"))
        row = scoring.rank({"candidates": [self.cand(mode="original", question_type="answered",
                                                     novelty_evidence={"closest_read": "full_text"})]})["ranking"][0]
        self.assertEqual(row["status"], "blocked")
        self.assertEqual(row["blockers"][0]["type"], "already_answered")


FIXTURE = {
    "id": "fx", "split": "heldout", "claim": "review sentiment graph models need structure",
    "queries": ["review sentiment graph", "opinion graph structure", "sentiment graph neural network", "graph sentiment"],
    "anchor": "review sentiment", "design": ["MLP baseline on the same node features", "randomly rewired edges"],
    "seeds": ["W1100001"],
    "known_relevant": [{"title": HIDDEN["title"]}, {"title": NEG["title"], "doi": None}],
}


class RetrievalEvalTests(unittest.TestCase):
    def test_matching_by_identifier_or_title(self):
        self.assertTrue(retrieval_eval.matches({"arxiv_id": "2101.00001v2"}, {"arxiv_id": "2101.00001"}))
        self.assertTrue(retrieval_eval.matches({"doi": "10.1234/ABC"}, {"doi": "https://doi.org/10.1234/abc"}))
        self.assertTrue(retrieval_eval.matches({"title": "Graphs: A Study"}, {"title": "Graphs - a study"}))
        self.assertFalse(retrieval_eval.matches({"title": "Graphs"}, {"title": "Trees"}))

    def test_seed_is_excluded_and_citation_only_paper_separates_configs(self):
        client, _, _ = client_for([METHOD], citing=[HIDDEN])
        fx = copy.deepcopy(FIXTURE)
        fx["seeds"] = [NEG["title"]]  # a seed given by title is still excluded from the targets
        fx["known_relevant"].append({"title": METHOD["title"]})
        r = retrieval_eval.run_fixture(client, fx, ["openalex"], ("baseline", "challenge", "landscape", "full"))
        self.assertEqual(r["n_targets"], 2)  # NEG excluded as a seed
        hidden = lambda c: next(h for h in r["configs"][c]["hits"] if h["title"] == HIDDEN["title"])
        self.assertFalse(hidden("baseline")["found"])
        self.assertTrue(hidden("full")["found"] or hidden("landscape")["found"] or hidden("challenge")["found"])
        s = retrieval_eval.summarize([r], ("baseline", "full"))
        self.assertEqual(s["heldout"]["baseline"]["targets"], 2)
        self.assertIn("caveat", s)

    def test_controls_count_false_alarms(self):
        res = [{"id": "c", "split": "control", "n_targets": 0, "configs": {
                    "baseline": {"signal": "no_close_match_in_this_search", "hits": []},
                    "challenge": {"signal": "close_prior_work_found", "hits": []}}},
               {"id": "d", "split": "dev", "n_targets": 1, "configs": {
                    "baseline": {"signal": "no_close_match_in_this_search", "hits": [{"found": False, "in_top_k": False}]},
                    "challenge": {"signal": "close_prior_work_found", "hits": [{"found": True, "in_top_k": True}]}}}]
        s = retrieval_eval.summarize(res, ("baseline", "challenge"))
        self.assertEqual(s["challenge_signal"]["control"]["challenge"], {"fixtures": 1, "flagged_prior_work": 1})
        self.assertEqual(s["challenge_signal"]["dev"]["baseline"]["flagged_prior_work"], 0)
        self.assertNotIn("control", {k for k in s if k in ("dev", "heldout", "control")} - {"dev"})

    def test_fixture_validation(self):
        with self.assertRaises(ValueError):
            retrieval_eval.load_fixtures(str(Path(__file__)))  # not a fixture


class FixtureIntegrityTests(unittest.TestCase):
    def test_shipped_fixtures(self):
        fixtures = retrieval_eval.load_fixtures(str(SKILL / "evals" / "retrieval" / "*.json"))
        splits = {f["split"] for f in fixtures}
        self.assertEqual(splits, {"dev", "heldout", "control"})
        heldout = [f for f in fixtures if f["split"] == "heldout"]
        self.assertGreaterEqual(len(heldout), 3)
        dev_targets = {(k.get("arxiv_id") or k.get("doi")) for f in fixtures if f["split"] == "dev"
                       for k in f["known_relevant"]}
        for f in fixtures:
            self.assertTrue(f.get("provenance"), f["id"])
            for k in f["known_relevant"]:
                self.assertTrue(k.get("arxiv_id") or k.get("doi"), k)
            if f["split"] == "heldout":
                # Held-out topics must not reuse dev targets, or they would not detect overfitting.
                self.assertFalse({(k.get("arxiv_id") or k.get("doi")) for k in f["known_relevant"]} & dev_targets)
        self.assertEqual(len(glob.glob(str(SKILL / "evals" / "retrieval" / "*.json"))), len(fixtures))


if __name__ == "__main__":
    unittest.main()
