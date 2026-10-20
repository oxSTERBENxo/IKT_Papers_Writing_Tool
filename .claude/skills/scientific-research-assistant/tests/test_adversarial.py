"""Regression tests for failure modes found in a real investigation (UPFD fake-news benchmark, 2026):

1. A keyword challenge said "no close match" although a paper had run the same experiment under other
   wording (GNN vs a same-feature MLP, edge rewiring). It was reachable through the citation graph.
2. A candidate was scored 3/5 for novelty and recommended from abstract-level reading only.
3. The original benchmark paper itself already contained the proposed control (an edge-removal ablation).
4. Recurring users shared between train and test let a model-free vote match published accuracies.
5. Claims were tagged "verified" against papers nobody could read.

All HTTP is faked. Passing these tests shows the toolkit enforces the rules; it does not show that a
research recommendation produced with it is right.
"""
import contextlib
import copy
import gzip
import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path

from helpers import ARXIV_EMPTY, make_client, openalex_work

from sra import fulltext, leakage, novelty, report, scoring
from sra.cli import main

CLAIM = "Test whether propagation graphs help fake news detection beyond news features on a benchmark"
DIFFERENTLY_WORDED = openalex_work(
    "W7", "The impact of data characteristics on GNN evaluation",
    # Like the real paper (arXiv 2512.06638), the abstract names the topic as well as the design.
    abstract_words=("fake", "news", "detection", "propagation", "graphs", "user-engagement",
                    "we", "benchmark", "five", "architectures", "against", "a", "structure-agnostic",
                    "multilayer", "perceptron", "MLP", "baseline", "using", "the", "same", "node", "features",
                    "and", "randomly", "rewired", "edges", "shuffled", "features"))
SEED = openalex_work("W1000001", "User preference-aware detection with propagation graphs",
                     abstract_words=("propagation", "graphs", "fake", "news", "detection"))
FAR = [openalex_work(f"W2{i}", f"Sentiment of celebrity gossip number {i}", abstract_words=("gossip",))
       for i in range(3)]
DESIGN = ["MLP baseline on the same node features", "randomly rewired edges", "shuffled node features"]


def challenge_client(citing_results):
    return make_client([
        ("cites%3A", {"results": citing_results}),
        ("api.openalex.org/works/W1000001", SEED),
        ("api.openalex.org/works/https", SEED),
        ("filter=openalex%3A", {"results": []}),
        ("api.openalex.org", {"results": [SEED] + FAR}),
        ("export.arxiv.org", ARXIV_EMPTY),
        ("api.crossref.org", {"message": {"items": []}}),
        ("api.semanticscholar.org", 429),
    ])


QUERIES = ["propagation graph fake news detection ablation", "do GNNs need user engagement graphs",
           "structure agnostic baseline misinformation benchmark", "news content only versus social context"]


class ChallengeRegressionTests(unittest.TestCase):
    def test_off_topic_design_match_does_not_signal_prior_work(self):
        off = openalex_work("W8800001", "Heterogeneous graph network for indoor floor classification",
                            abstract_words=("an", "MLP", "baseline", "on", "the", "same", "node", "features", "and",
                                            "shuffled", "node", "features", "wifi", "signals"))
        client, _, _ = make_client([("api.openalex.org", {"results": [off] + FAR}),
                                    ("export.arxiv.org", ARXIV_EMPTY), ("api.crossref.org", {"message": {"items": []}})])
        result = novelty.challenge(client, CLAIM, QUERIES, ["openalex"], design=DESIGN, expand_top=0)
        self.assertEqual(result["n_possible_same_design"], 0)
        self.assertEqual(result["n_design_matches_off_topic"], 1)
        self.assertEqual(result["signal"], "no_close_match_in_this_search")

    def test_differently_worded_same_experiment_is_found_through_citations(self):
        client, opener, _ = challenge_client([DIFFERENTLY_WORDED])
        result = novelty.challenge(client, CLAIM, QUERIES, ["openalex"], design=DESIGN, expand_top=2)
        self.assertGreater(opener.count("cites%3A"), 0)
        titles = [s["paper"].title for s in result["possible_same_design"]]
        self.assertIn(DIFFERENTLY_WORDED["title"], titles)
        hit = next(s for s in result["closest"] if s["paper"].title == DIFFERENTLY_WORDED["title"])
        self.assertTrue(hit["found_only_via_citations"])
        self.assertGreaterEqual(len(hit["design_elements_matched"]), 2)
        self.assertEqual(result["signal"], "close_prior_work_found")
        self.assertEqual(result["max_supported_novelty_confidence"], "low")
        self.assertTrue(any(m["title"] == DIFFERENTLY_WORDED["title"] for m in result["must_read"]))

    def test_without_expansion_the_same_paper_is_missed_and_the_ceiling_says_why(self):
        client, _, _ = challenge_client([DIFFERENTLY_WORDED])
        result = novelty.challenge(client, CLAIM, QUERIES, ["openalex"], design=DESIGN, expand_top=0)
        self.assertNotIn(DIFFERENTLY_WORDED["title"], [s["paper"].title for s in result["closest"]])
        self.assertEqual(result["signal"], "no_close_match_in_this_search")
        self.assertTrue(any("citation graph not followed" in r for r in result["ceiling_lowered_because"]))
        self.assertNotEqual(result["max_supported_novelty_confidence"], "medium")

    def test_seed_citing_works_are_searched_with_the_queries(self):
        client, opener, _ = challenge_client([DIFFERENTLY_WORDED])
        result = novelty.challenge(client, CLAIM, QUERIES, ["openalex"], design=DESIGN, expand_top=0,
                                   seeds=["W1000001"])
        searched = [c for c in opener.calls if "cites%3AW1000001" in c and "title_and_abstract.search" in c]
        probes = novelty.short_probes(QUERIES + DESIGN)
        self.assertEqual(len(searched), len(probes))
        # OpenAlex requires every word of the filter to match; sentence-length probes return nothing.
        self.assertTrue(all(len(p.split()) <= 3 for p in probes), probes)
        self.assertIn("structure misinformation benchmark", [p.lower() for p in probes])
        self.assertTrue(result["seeds"][0]["resolved"])
        self.assertIn(DIFFERENTLY_WORDED["title"], [s["paper"].title for s in result["possible_same_design"]])

    def test_near_paraphrase_queries_and_missing_design_lower_the_ceiling(self):
        client, _, _ = challenge_client([])
        paraphrases = ["graph fake news detection", "graph fake news detection model",
                       "fake news detection graph", "detection of fake news with graph"]
        result = novelty.challenge(client, CLAIM, paraphrases, ["openalex"])
        self.assertTrue(result["query_diversity"]["near_paraphrases"])
        reasons = " ".join(result["ceiling_lowered_because"])
        self.assertIn("near-paraphrases", reasons)
        self.assertIn("no design elements", reasons)
        self.assertIn(result["max_supported_novelty_confidence"], ("very_low", "low"))

    def test_partial_expansion_failure_is_reported(self):
        client, _, _ = make_client([
            ("title_and_abstract.search", 429),
            ("cites%3A", {"results": [DIFFERENTLY_WORDED]}),
            ("api.openalex.org/works/W1000001", SEED),
            ("filter=openalex%3A", {"results": []}),
            ("api.openalex.org", {"results": [SEED] + FAR}),
        ])
        result = novelty.challenge(client, CLAIM, QUERIES, ["openalex"], design=DESIGN, expand_top=1,
                                   seeds=["W1000001", "W9999999"])
        reasons = " ".join(result["ceiling_lowered_because"])
        self.assertIn("citation expansion partly failed", reasons)
        self.assertIn("rate_limited", reasons)
        self.assertIn("seed(s) not resolved: W9999999", reasons)

    def test_failed_scholarly_index_is_not_called_reasonable_coverage(self):
        client, _, _ = make_client([("api.openalex.org", 429), ("api.semanticscholar.org", 429),
                                    ("export.arxiv.org", ARXIV_EMPTY), ("api.crossref.org", {"message": {"items": []}}),
                                    ("huggingface.co", "[]")])
        result = novelty.challenge(client, CLAIM, QUERIES, ["openalex", "semantic_scholar", "arxiv", "crossref",
                                                            "huggingface"], design=DESIGN)
        self.assertNotIn("coverage was reasonable", result["interpretation"])
        self.assertIn("openalex", " ".join(result["ceiling_lowered_because"]))

    def test_query_diversity_measure(self):
        self.assertFalse(novelty.query_diversity(["graph text", "molecule toxicity", "user overlap"])
                         ["near_paraphrases"])
        self.assertTrue(novelty.query_diversity(["graph text model", "graph text models"])["near_paraphrases"])


def upfd_like_report():
    """Shape of the report that first ranked the UPFD idea at 75/100."""
    return {
        "type": "opportunity_report", "title": "Regression: UPFD", "date": "2026-10-18",
        "papers": [
            {"key": "dou2021", "title": "User Preference-aware Fake News Detection", "arxiv_id": "2104.12259",
             "verification": {"status": "verified"}, "read_level": "abstract"},
            {"key": "karn2025", "title": "The Impact of Data Characteristics on GNN Evaluation",
             "arxiv_id": "2512.06638", "verification": {"status": "verified"}, "read_level": "full_text"},
            {"key": "chapter2025", "title": "A paywalled chapter", "doi": "10.1007/fixture",
             "verification": {"status": "verified"}, "read_level": "title_only"},
        ],
        "sections": {"summary": "s", "recommendation": "r"},
        "opportunities": [{
            "title": "Graph vs no-graph on UPFD", "category": "reported_limitation", "mode": "extension",
            "status": "kept", "research_question": "Does the graph help?",
            "closest_existing_work": [{"key": "dou2021", "how_it_differs": "no seeds stated"}],
            "gap_evidence": [{"text": "PolitiFact has 314 graphs", "level": "verified", "sources": ["dou2021"]}],
            "novelty": {"confidence": "low", "uncertainty": "u", "challenge_searches": ["q"]},
            "decision": {"verdict": "go", "rationale": "cheap and clear"},
        }],
    }


def errors_of(data):
    return report.validate(data)[0]


class ValidatorRegressionTests(unittest.TestCase):
    def assertError(self, data, fragment):
        errs = errors_of(data)
        self.assertTrue(any(fragment in e for e in errs), f"expected '{fragment}' in {errs}")

    def test_original_upfd_recommendation_is_refused(self):
        errs = errors_of(upfd_like_report())
        joined = " | ".join(errs)
        self.assertIn("methodological_risks is empty", joined)
        self.assertIn("'go' requires at least one closest work read in full text", joined)

    def test_prior_work_that_ran_the_experiment_blocks_an_extension(self):
        data = upfd_like_report()
        opp = data["opportunities"][0]
        opp["closest_existing_work"].append({"key": "karn2025", "how_it_differs": "none", "overlap": "same_experiment"})
        self.assertError(data, "already performed this experiment")
        opp["status"], opp["revision_note"] = "rejected", "done by karn2025"
        opp["decision"] = {"verdict": "no_go", "rationale": "already done"}
        self.assertFalse(any("already performed" in e for e in errors_of(data)))

    def test_rejected_candidate_cannot_be_go(self):
        data = upfd_like_report()
        data["opportunities"][0].update(status="rejected", revision_note="x")
        self.assertError(data, "rejected candidate must have verdict no_go")

    def test_verified_claim_needs_a_readable_source(self):
        data = upfd_like_report()
        data["opportunities"][0]["gap_evidence"].append(
            {"text": "Nobody tested user-disjoint splits", "level": "verified", "sources": ["chapter2025"]})
        self.assertError(data, "tagged verified but cites ['chapter2025']")

    def test_medium_confidence_needs_full_text_of_the_closest_work(self):
        data = upfd_like_report()
        data["opportunities"][0]["novelty"]["confidence"] = "medium"
        self.assertError(data, "'medium' novelty confidence needs the closest work read in full")

    def test_confidence_cannot_exceed_the_challenge_ceiling(self):
        data = upfd_like_report()
        data["opportunities"][0]["novelty"].update(confidence="low", ceiling="very_low")
        self.assertError(data, "exceeds the challenge ceiling")

    def test_conditional_go_needs_conditions_and_open_risks(self):
        data = upfd_like_report()
        data["opportunities"][0]["decision"] = {"verdict": "conditional_go", "rationale": "maybe"}
        self.assertError(data, "conditional_go needs both conditions and unresolved_risks")

    def test_go_needs_every_risk_group_checked(self):
        data = upfd_like_report()
        opp = data["opportunities"][0]
        opp["closest_existing_work"] = [{"key": "karn2025", "how_it_differs": "uses validation accuracy",
                                         "overlap": "partial"}]
        opp["methodological_risks"] = [
            {"type": "train_test_overlap", "status": "found", "evidence": "user vote 86%"}]
        errs = " | ".join(errors_of(data))
        self.assertIn("needs a mitigation", errs)
        self.assertIn("checked baselines risk", errs)
        self.assertIn("checked evaluation risk", errs)

    def test_well_supported_go_is_accepted(self):
        data = upfd_like_report()
        opp = data["opportunities"][0]
        opp["mode"] = "replication"
        opp["closest_existing_work"] = [{"key": "karn2025", "how_it_differs": "held-out test set",
                                         "overlap": "partial"}]
        opp["gap_evidence"] = [{"text": "validation accuracy only", "level": "verified", "sources": ["karn2025"]}]
        opp["methodological_risks"] = [
            {"type": "train_test_overlap", "status": "found", "evidence": "vote 86%", "mitigation": "mask users"},
            {"type": "weak_baseline", "status": "checked_ok", "evidence": "MLP on same features"},
            {"type": "model_selection_on_test", "status": "checked_ok", "evidence": "validation-based selection"}]
        self.assertEqual(errors_of(data), [])

    def test_report_renders_decision_and_four_verification_dimensions(self):
        data = upfd_like_report()
        opp = data["opportunities"][0]
        opp["closest_existing_work"][0]["overlap"] = "partial"
        opp["methodological_risks"] = [{"type": "weak_baseline", "status": "not_checked"}]
        opp["decision"] = {"verdict": "conditional_go", "rationale": "read first",
                           "conditions": ["read karn2025"], "unresolved_risks": ["overlap"]}
        md = report.render_markdown(data)
        for text in ("## Decisions", "CONDITIONAL GO", "Source existence (verify-refs)", "Claim support",
                     "Novelty confidence", "Reproducibility", "[read: abstract; overlap: partial]",
                     "**Methodological risks.**", "Unresolved evidence and risks"):
            self.assertIn(text, md)


class ScoringCapTests(unittest.TestCase):
    def candidate(self, **kw):
        crit = {"score": 4, "evidence": ["e"], "evidence_level": "estimate", "missing": []}
        return {"id": "A", "mode": kw.pop("mode", "extension"),
                "criteria": {n: dict(crit) for n in scoring.WEIGHTS}, **kw}

    def novelty_score(self, cand):
        row = scoring.rank({"candidates": [cand]})["ranking"][0]
        return next(r["score"] for r in row["criteria"] if r["criterion"] == "novelty_or_replication_value"), row

    def test_abstract_level_reading_caps_novelty(self):
        score, row = self.novelty_score(self.candidate(novelty_evidence={"closest_read": "abstract"}))
        self.assertEqual(score, 2)
        self.assertEqual(row["caps_applied"][0]["submitted_score"], 4)

    def test_missing_evidence_basis_caps_novelty(self):
        self.assertEqual(self.novelty_score(self.candidate())[0], 2)

    def test_same_experiment_caps_novelty_at_one_unless_replication(self):
        ev = {"closest_read": "full_text", "prior_overlap": "same_experiment"}
        self.assertEqual(self.novelty_score(self.candidate(novelty_evidence=ev))[0], 1)
        self.assertEqual(self.novelty_score(self.candidate(novelty_evidence=ev, mode="replication"))[0], 4)

    def test_full_text_reading_keeps_the_score(self):
        score, row = self.novelty_score(self.candidate(novelty_evidence={"closest_read": "full_text"}))
        self.assertEqual((score, row["caps_applied"]), (4, []))


TEX_MAIN = r"""\documentclass{article}
\begin{document}
\section{Introduction}
We study graphs. % a comment that should vanish 99\% sure
\input{sec-exp}
\section{Limitations}
Our method assumes that the user nodes are independent. We leave temporal splits to future work.
\end{document}
"""
TEX_EXP = r"""\section{Experiments}
\subsection{Setup}
We use a train-val-test split (20\%-10\%-70\%) for all models. The experimental results are averaged over five different runnings.
We report mean validation accuracy with 95\% confidence intervals.
\subsection{Baselines}
We also add two baselines that apply MLP directly on news textual embeddings.
\subsection{Ablation Study}
The variant without exogenous information (-EXO) is implemented by removing all edges in the news propagation graph.
Code is available at https://github.com/example-org/fixture-repo.
"""


def eprint_tar() -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for name, text in (("main.tex", TEX_MAIN), ("sec-exp.tex", TEX_EXP), ("../evil.tex", "x" * 10)):
            data = text.encode()
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return buf.getvalue()


class FulltextTests(unittest.TestCase):
    def test_eprint_tar_is_read_in_memory_with_inputs_inlined(self):
        tex = fulltext.tex_from_eprint(eprint_tar())
        self.assertLess(tex.index("Introduction"), tex.index("Experiments"))
        self.assertLess(tex.index("Experiments"), tex.index("Limitations"))

    def test_common_false_positives_are_not_flagged(self):
        tex = ("\\section{Method}\nWe train an end-to-end model on the graph and it works well here.\n"
               "\\begin{CCSXML}<concept_significance>300</concept_significance>\\end{CCSXML}\n"
               "\\section{Ablation}\nThe variant without edges (-EXO) drops the accuracy by four points.\n")
        flags = fulltext.flag_sentences(fulltext.split_tex_sections(tex))
        ablation = " ".join(h["sentence"] for h in flags["ablation_or_control"])
        self.assertIn("-EXO", ablation)
        self.assertNotIn("end-to-end", ablation)
        self.assertFalse(flags["variance_reported"])

    def test_single_gzipped_tex(self):
        self.assertIn("Limitations", fulltext.tex_from_eprint(gzip.compress(TEX_MAIN.encode())))

    def test_sections_roles_and_methodology_flags(self):
        sections = fulltext.split_tex_sections(fulltext.tex_from_eprint(eprint_tar()))
        heads = {s["heading"]: fulltext.role_of(s["heading"]) for s in sections}
        self.assertIn("ablation", heads["Ablation Study"])
        self.assertIn("baselines", heads["Baselines"])
        self.assertIn("limitations", heads["Limitations"])
        flags = fulltext.flag_sentences(sections)
        for name in ("runs_and_seeds", "split_protocol", "validation_only_reporting", "structure_free_baseline",
                     "ablation_or_control", "code_or_data_link", "stated_limitation"):
            self.assertTrue(flags[name], name)
        self.assertNotIn("a comment that should vanish", " ".join(s["text"] for s in sections))

    def test_fetch_prefers_eprint_and_falls_back_to_html(self):
        client, _, _ = make_client([("arxiv.org/e-print/2101.00001", eprint_tar())])
        # FakeOpener sends str bodies; bytes need a dedicated route object.
        client._open = _bytes_opener({"arxiv.org/e-print/2101.00001": eprint_tar()})
        result = fulltext.fetch(client, "2101.00001")
        self.assertEqual((result["status"], result["source"]), ("full_text", "arxiv_tex"))
        page = "<html><h2>Experiments</h2><p>" + "We average over ten runs. " * 120 + "</p></html>"
        client._open = _bytes_opener({"arxiv.org/html/2101.00002": page.encode()})
        result = fulltext.fetch(client, "2101.00002")
        self.assertEqual((result["status"], result["source"]), ("full_text", "arxiv_html"))
        self.assertTrue(result["flags"]["runs_and_seeds"])

    def test_non_arxiv_paper_is_reported_not_accessible(self):
        client, _, _ = make_client([])
        result = fulltext.fetch(client, "10.1007/fixture")
        self.assertEqual(result["status"], "not_accessible")
        self.assertIn("record read_level", result["notes"][0])

    def test_oversized_download_is_refused(self):
        client, _, _ = make_client([])
        client._open = _bytes_opener({"arxiv.org/e-print/2101.00003": b"x" * 2000})
        fulltext.MAX_SOURCE_BYTES, old = 1000, fulltext.MAX_SOURCE_BYTES
        try:
            result = fulltext.fetch(client, "2101.00003")
        finally:
            fulltext.MAX_SOURCE_BYTES = old
        self.assertTrue(any("too_large" in n for n in result["notes"]))


def _bytes_opener(routes):
    import urllib.error

    class Resp:
        def __init__(self, body):
            self.body, self.status, self.headers = body, 200, {}

        def read(self, n=-1):
            return self.body if n is None or n < 0 else self.body[:n]

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def opener(request, timeout=None):
        for needle, body in routes.items():
            if needle in request.full_url:
                return Resp(body)
        raise urllib.error.HTTPError(request.full_url, 404, "nf", {}, io.BytesIO(b""))
    return opener


def leaky_records():
    """Users who only ever share one label recur across splits, as in UPFD."""
    recs = []
    for i in range(40):
        label = i % 2
        users = [f"u{label}_{i % 5}", f"u{label}_{(i + 1) % 5}", f"solo{i}"]
        recs.append({"id": i, "split": "train" if i < 20 else "test", "label": label, "entities": users,
                     "size": 10 + label * 30 + (i % 3), "text": f"story {i}"})
    recs[25]["text"] = "story 3"  # an exact duplicate of a training text
    return recs


class LeakageTests(unittest.TestCase):
    def test_entity_vote_exposes_identity_shortcut(self):
        out = leakage.analyse(leaky_records(), text_field="text", scalar_fields=["size"], hub_thresholds=())
        vote = out["entity_vote"][0]
        self.assertEqual(vote["entity_vote_accuracy"], 1.0)
        self.assertEqual(vote["majority_class_accuracy"], 0.5)
        types = {r["type"]: r["level"] for r in out["risks"]}
        self.assertEqual(types["train_test_overlap"], "high")
        self.assertEqual(types["duplicate_items"], "high")
        self.assertIn("scalar_shortcut", types)
        self.assertEqual(out["duplicates"]["exact_duplicates_of_train_text"], 1)
        self.assertEqual(out["entities"]["repeat_entities_with_a_single_label"], 1.0)

    def test_a_single_duplicate_in_a_large_test_set_is_low_risk(self):
        recs = [{"split": "train" if i < 500 else "test", "label": i % 3, "entities": [], "text": f"s{i}"}
                for i in range(1000)]
        recs[600]["text"], recs[600]["label"] = "s7", 7 % 3  # one duplicate, same label (ABSA SemEval case)
        risks = {r["type"]: r["level"] for r in leakage.analyse(recs, text_field="text", hub_thresholds=())["risks"]}
        self.assertEqual(risks["duplicate_items"], "low")

    def test_disjoint_data_shows_low_risk(self):
        recs = [{"split": "train" if i < 10 else "test", "label": i % 2, "entities": [f"only{i}"]} for i in range(20)]
        out = leakage.analyse(recs, hub_thresholds=())
        self.assertEqual(out["entity_vote"][0]["share_test_items_with_seen_entity"], 0.0)
        self.assertEqual([r["level"] for r in out["risks"] if r["type"] == "train_test_overlap"], ["low"])
        self.assertEqual(out["disjoint_split_feasibility"][0]["largest_component_share"], 0.05)

    def test_components_and_masking(self):
        out = leakage.analyse(leaky_records(), hub_thresholds=(3,))
        self.assertLess(out["disjoint_split_feasibility"][0]["n_components"], 5)
        self.assertGreater(out["masking_seen_entities"]["share_of_test_entity_occurrences_removed"], 0.5)

    def test_bad_input_is_rejected(self):
        with self.assertRaises(ValueError):
            leakage.analyse([{"label": 1}])

    def test_cli_writes_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, out = Path(tmp) / "items.jsonl", Path(tmp) / "out.json"
            src.write_text("\n".join(json.dumps(r) for r in leaky_records()), encoding="utf-8")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                code = main(["--no-cache", "leakage", "--input", str(src), "--text-field", "text",
                             "--scalar", "size", "--out", str(out)])
            self.assertEqual(code, 0)
            self.assertIn("HIGH", buf.getvalue())
            self.assertIn("risks", json.loads(out.read_text(encoding="utf-8")))


class ExampleReportTests(unittest.TestCase):
    def test_worked_example_still_validates(self):
        path = Path(__file__).resolve().parents[1] / "examples" / "nlp-graph-theory" / "opportunity_report.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(errors_of(copy.deepcopy(data)), [])


if __name__ == "__main__":
    unittest.main()
