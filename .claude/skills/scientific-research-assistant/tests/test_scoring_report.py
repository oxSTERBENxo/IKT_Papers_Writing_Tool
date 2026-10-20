"""Scoring rubric, report validation and rendering, and the CLI (offline)."""
import contextlib
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path

import helpers  # noqa: F401  (adds scripts/ to sys.path)

from sra import report, scoring
from sra.cli import main


def crit(score, level="verified", evidence=("checked",), missing=()):
    return {"score": score, "evidence": list(evidence) if score is not None else [],
            "evidence_level": level if score is not None else None, "missing": list(missing)}


def candidate(cid, default=4, **overrides):
    criteria = {name: crit(default) for name in scoring.WEIGHTS}
    criteria.update(overrides.pop("criteria", {}))
    return {"id": cid, "title": f"Project {cid}", "mode": "reproduction", "criteria": criteria,
            "novelty_evidence": {"closest_read": "full_text", "prior_overlap": "different"}, **overrides}


class ScoringTests(unittest.TestCase):
    def test_weights_sum_to_100(self):
        self.assertEqual(sum(scoring.WEIGHTS.values()), 100)

    def test_blocker_is_not_compensated_by_high_scores(self):
        strong_but_blocked = candidate("A", default=5, blockers=[
            {"type": "data_access", "description": "controlled-access data, approval takes months"}])
        modest = candidate("B", default=2)
        ranking = scoring.rank({"candidates": [strong_but_blocked, modest]})["ranking"]
        self.assertEqual([(r["id"], r["status"], r["rank"]) for r in ranking],
                         [("B", "viable", 1), ("A", "blocked", None)])
        self.assertEqual(ranking[1]["score_percent"], 100.0)  # the score stays visible, it just cannot win

    def test_zero_on_gating_criterion_blocks(self):
        c = candidate("A", criteria={"dataset_accessibility": crit(0, evidence=["gated=manual on the hub"])})
        result = scoring.rank({"candidates": [c]})["ranking"][0]
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["blockers"][0]["origin"], "gating_criterion")

    def test_missing_code_blocks_a_reproduction_but_not_a_replication(self):
        no_code = {"paper_and_code_availability": crit(0, evidence=["no repository found"])}
        repro_c = candidate("A", criteria=no_code)
        repl_c = candidate("B", criteria=no_code, mode="replication")
        ranking = {r["id"]: r["status"] for r in scoring.rank({"candidates": [repro_c, repl_c]})["ranking"]}
        self.assertEqual(ranking, {"A": "blocked", "B": "viable"})

    def test_budget_overruns_block(self):
        c = candidate("A", estimates={"weeks": 10, "min_vram_gb": 24, "gpu_hours": 5})
        constraints = {"time_budget_weeks": 4, "gpu_vram_gb": 8, "gpu_hours_budget": 50}
        result = scoring.rank({"constraints": constraints, "candidates": [c]})["ranking"][0]
        self.assertEqual(sorted(b["type"] for b in result["blockers"]), ["gpu_vram_gb", "time_budget_weeks"])

    def test_unscored_criteria_widen_the_range_instead_of_being_imputed(self):
        c = candidate("A", default=5, criteria={"compute_fit": crit(None, missing=["GPU memory not stated"]),
                                                "time_fit": crit(None)})
        result = scoring.rank({"candidates": [c]})["ranking"][0]
        self.assertEqual(result["score_percent"], 100.0)
        self.assertEqual(result["score_range"], [78.0, 100.0])
        self.assertEqual(result["scored_weight_percent"], 78.0)
        self.assertEqual(result["unscored_criteria"], ["compute_fit", "time_fit"])
        self.assertEqual(result["missing_information"], ["compute_fit: GPU memory not stated"])

    def test_verified_share_reflects_evidence_levels(self):
        c = candidate("A", criteria={"scientific_relevance": crit(4, "speculative"),
                                     "low_failure_risk": crit(3, "estimate")})
        result = scoring.rank({"candidates": [c]})["ranking"][0]
        self.assertEqual(result["verified_weight_percent"], 81.0)

    def test_scores_without_evidence_are_rejected(self):
        bad = candidate("A")
        bad["criteria"]["compute_fit"] = {"score": 5, "evidence": [], "evidence_level": "verified"}
        with self.assertRaisesRegex(ValueError, "no evidence"):
            scoring.rank({"candidates": [bad]})

    def test_invalid_values_are_rejected(self):
        for change in ({"compute_fit": crit(7)}, {"made_up": crit(3)}, {"compute_fit": crit(3, level="certain")}):
            with self.assertRaises(ValueError):
                scoring.rank({"candidates": [candidate("A", criteria=change)]})
        with self.assertRaises(ValueError):
            scoring.rank({"candidates": [candidate("A")], "weights": {"vibes": 50}})

    def test_higher_score_ranks_first_among_viable(self):
        ranking = scoring.rank({"candidates": [candidate("low", 2), candidate("high", 4)]})["ranking"]
        self.assertEqual([r["id"] for r in ranking], ["high", "low"])


def sample_report():
    return {
        "type": "opportunity_report", "title": "Graphs & Text: 100% Test_Report", "date": "2026-01-01",
        "schema_version": 3,
        "evidence_ledger": [{"id": "L1", "type": "stated_limitation", "text": "Results come from a single seed",
                             "level": "verified", "sources": ["example2021"]}],
        "constraints": {"field": "NLP", "time_budget_weeks": 8, "defaults_used": ["time_budget_weeks"]},
        "search_log": {"sources_ok": ["openalex", "arxiv"], "sources_failed": [
            {"source": "semantic_scholar", "reason": "rate_limited"}], "queries": ["graph text"],
            "strategies": ["keyword"], "n_retrieved": 10, "n_after_dedup": 6},
        "papers": [
            {"key": "example2021", "title": "Graph Networks for Text Labelling: A Test Fixture",
             "authors": ["Ada Example", "Bo Sample", "Cy Third"], "year": 2021, "venue": "Journal of Fixtures",
             "arxiv_id": "2101.00001", "method": "GNN", "datasets": ["FixtureSet"], "findings": "works | sometimes",
             "limitations": None, "verification": {"status": "verified"}, "read_level": "full_text"},
            {"key": "other2020", "title": "A Published Fixture", "authors": ["Dee Fourth"], "year": 2020,
             "doi": "10.1234/fixture.2", "verification": {"status": "verified"}, "read_level": "abstract"},
        ],
        "sections": {"summary": "One gap survived [@example2021].", "well_explored": ["Topic A [@other2020]"],
                     "recommendation": "Start with #1."},
        "opportunities": [{
            "title": "Seeds matter", "category": "reported_limitation", "mode": "replication", "status": "kept",
            "question_type": "replication", "derived_from": ["L1"],
            "research_question": "Does the result hold across 10 seeds?",
            "motivation": "Only one seed is reported [@example2021].",
            "supporting_papers": ["example2021"],
            "closest_existing_work": [{"key": "other2020", "how_it_differs": "different dataset"}],
            "gap_evidence": [{"text": "Single-seed results", "level": "verified", "sources": ["example2021"]},
                             {"text": "Variance may be large", "level": "speculative"}],
            "contribution": "Variance estimates.",
            "novelty": {"confidence": "low", "uncertainty": "Workshop papers may exist.",
                        "challenge_searches": ["seed variance graph text"], "signal": "close_prior_work_found"},
            "feasibility": [{"text": "about 6 GPU hours", "level": "estimate"}],
            "methodological_risks": [
                {"type": "train_test_overlap", "status": "not_checked", "evidence": "Split files not inspected"}],
            "decision": {"verdict": "conditional_go", "rationale": "Cheap, but the split was not inspected.",
                         "conditions": ["Inspect the split files"], "unresolved_risks": ["Overlap unknown"]},
        }],
        "datasets": [{"name": "FixtureSet", "url": "https://huggingface.co/datasets/example/fixture-data",
                      "license": "cc-by-4.0", "size": "12000 rows", "verified": True}],
        "limitations": ["Semantic Scholar was unavailable."],
    }


class ReportValidationTests(unittest.TestCase):
    def errors_after(self, mutate):
        data = sample_report()
        mutate(data)
        return report.validate(data)[0]

    def assertHasError(self, mutate, fragment):
        errors = self.errors_after(mutate)
        self.assertTrue(any(fragment in e for e in errors), f"expected '{fragment}' in {errors}")

    def test_sample_is_valid(self):
        self.assertEqual(report.validate(sample_report()), ([], []))

    def test_reference_without_identifier_is_rejected(self):
        self.assertHasError(lambda d: d["papers"][0].pop("arxiv_id"), "cannot be checked")

    def test_failed_verification_is_an_error_and_missing_verification_a_warning(self):
        self.assertHasError(lambda d: d["papers"][0].update(verification={"status": "title_mismatch"}),
                            "verification failed")
        data = sample_report()
        data["papers"][0].pop("verification")
        errors, warnings = report.validate(data)
        self.assertEqual(errors, [])
        self.assertIn("not verified", warnings[0])

    def test_citing_an_unknown_paper_is_rejected(self):
        self.assertHasError(lambda d: d["sections"].update(summary="As shown [@ghost2099]."), "ghost2099")
        self.assertHasError(lambda d: d["opportunities"][0].update(supporting_papers=["ghost"]), "ghost")

    def test_high_novelty_confidence_is_rejected(self):
        self.assertHasError(lambda d: d["opportunities"][0]["novelty"].update(confidence="high"),
                            "cannot justify more than 'medium'")

    def test_opportunity_needs_a_novelty_challenge_and_closest_work(self):
        self.assertHasError(lambda d: d["opportunities"][0]["novelty"].update(challenge_searches=[]),
                            "challenge_searches is empty")
        self.assertHasError(lambda d: d["opportunities"][0].update(closest_existing_work=[]),
                            "closest_existing_work is empty")
        self.assertHasError(lambda d: d["opportunities"][0]["novelty"].pop("uncertainty"), "uncertainty")

    def test_well_studied_topic_cannot_be_kept(self):
        self.assertHasError(lambda d: d["opportunities"][0].update(category="well_studied"), "cannot be kept")
        self.assertHasError(lambda d: d["opportunities"][0].update(status="rejected"), "revision_note")
        self.assertHasError(lambda d: d["opportunities"][0].update(category="gap"), "category must be")

    def test_reproduced_requires_execution_evidence(self):
        def add(status, **extra):
            return lambda d: d.update(reproduction_candidates=[
                {"paper": "example2021", "mode": "reproduction", "result_status": status, **extra}])
        self.assertHasError(add("reproduced"), "requires executed=true")
        self.assertHasError(add("reproduced", executed=True), "requires executed=true")
        self.assertEqual(self.errors_after(add("assessed_only")), [])
        self.assertEqual(self.errors_after(add("reproduced", executed=True,
                                               execution_evidence=["run log: acc 0.81 vs 0.82 reported"])), [])

    def test_unverified_dataset_warns(self):
        data = sample_report()
        data["datasets"][0]["verified"] = False
        self.assertIn("not verified with dataset-verify", report.validate(data)[1][0])


class ReportRenderingTests(unittest.TestCase):
    def test_markdown_contains_evidence_and_uncertainty(self):
        md = report.render_markdown(sample_report())
        self.assertTrue(md.startswith("# Graphs & Text: 100% Test_Report"))
        self.assertIn("[Example et al. 2021](https://arxiv.org/abs/2101.00001)", md)
        self.assertIn("[V] Single-seed results", md)
        self.assertIn("[S] Variance may be large", md)
        self.assertIn("**Feasibility.** [E] about 6 GPU hours", md)  # one item reads inline, not as a bullet
        self.assertIn("**Evidence for the gap.**\n- [V] Single-seed results", md)
        self.assertIn("**Novelty confidence:** low", md)
        self.assertIn("semantic_scholar (rate_limited)", md)
        self.assertIn("default (not stated by user)", md)
        self.assertIn("works / sometimes", md)  # pipe inside a table cell is neutralised
        self.assertIn("not reported", md)  # the missing limitations cell
        self.assertIn("Not provided (missing information)", md)  # no ranking was supplied
        self.assertNotIn("{{", md)

    def test_unverified_reference_is_marked(self):
        data = sample_report()
        data["papers"][1]["verification"] = {"status": "identifier_resolves"}
        self.assertIn("**[reference identifier_resolves]**", report.render_markdown(data))

    def test_rejected_opportunity_is_listed_separately(self):
        data = sample_report()
        rejected = copy.deepcopy(data["opportunities"][0])
        rejected.update(title="Already done", status="rejected", category="well_studied",
                        revision_note="A survey covers it [@other2020].")
        data["opportunities"].append(rejected)
        md = report.render_markdown(data)
        self.assertIn("Candidates rejected after the novelty challenge", md)
        self.assertNotIn("### 2. Already done", md)

    def test_every_report_type_renders(self):
        for kind in report.REPORT_TYPES:
            data = sample_report()
            data["type"] = kind
            data["reproduction_candidates"] = [{
                "paper": "example2021", "mode": "reproduction", "result_status": "assessed_only",
                "checklist": {"code": {"label": "Implementation available", "status": "found",
                                       "evidence": ["https://github.com/example-org/fixture-repo"], "note": None}}}]
            md = report.render_markdown(data)
            self.assertNotIn("{{", md, kind)
            if kind == "reproducibility_report":
                self.assertIn("NOT executed", md)
                self.assertIn("| Implementation available | found |", md)

    def test_optional_sections_are_omitted_when_empty(self):
        data = sample_report()
        data["type"] = "research_proposal"
        data["proposal"] = {"hypothesis": "H1"}
        md = report.render_markdown(data)
        self.assertIn("## Hypothesis\n\nH1", md)
        self.assertNotIn("Each criterion is scored", md)  # no ranking supplied: section left out
        self.assertIn("## Baselines\n\n*Not provided", md)  # required sections still show the gap
        data["proposal"]["confounds"] = ["only one"]
        self.assertIn("leakage controls.**\n\nonly one", report.render_markdown(data))  # no stray bullet

    def test_ranking_block(self):
        data = sample_report()
        blocked = {"id": "B", "title": "Blocked one", "mode": "reproduction",
                   "criteria": {n: crit(5) for n in scoring.WEIGHTS},
                   "novelty_evidence": {"closest_read": "full_text"},
                   "blockers": [{"type": "data", "description": "gated data"}]}
        data["ranking"] = scoring.rank({"candidates": [candidate("A"), blocked]})
        md = report.render_markdown(data)
        self.assertIn("| 1 | Project A | VIABLE | 80.0 |", md)
        self.assertIn("| - | Blocked one | BLOCKED | 100.0 |", md)
        self.assertIn("BLOCKER (data): gated data", md)

    def test_latex_escapes_and_cites(self):
        tex = report.render_latex(sample_report())
        self.assertIn(r"\title{Graphs \& Text: 100\% Test\_Report}", tex)
        self.assertIn(r"\cite{example2021}", tex)
        self.assertIn(r"\bibliography{references}", tex)
        self.assertIn(r"\begin{longtable}", tex)
        self.assertIn(r"\subsection{1. Seeds matter}", tex)
        self.assertIn(r"\textbf{Research question.}", tex)
        self.assertIn(r"\begin{itemize}", tex)
        self.assertEqual(tex.count(r"\begin{itemize}"), tex.count(r"\end{itemize}"))
        self.assertEqual(tex.count(r"\begin{longtable}"), tex.count(r"\end{longtable}"))
        self.assertNotIn("@@", tex)
        self.assertNotIn("**", tex)

    def test_latex_inline_conversion(self):
        self.assertEqual(report.tex_inline("a_b 50% [x_y](https://e.org/a_b#c) `k_v`"),
                         r"a\_b 50\% \href{https://e.org/a_b\#c}{x\_y} \texttt{k\_v}")

    def test_bibtex(self):
        bib = report.render_bibtex(sample_report())
        self.assertIn("@misc{example2021,", bib)
        self.assertIn("eprint = {2101.00001}", bib)
        self.assertIn("@article{other2020,", bib)
        self.assertIn("author = {Ada Example and Bo Sample and Cy Third}", bib)


class CliTests(unittest.TestCase):
    def run_cli(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = main(list(argv))
        return code, out.getvalue()

    def test_report_command_writes_all_formats(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp, "in.json")
            src.write_text(json.dumps(sample_report()), encoding="utf-8")
            code, out = self.run_cli("report", "--input", str(src), "--out-dir", tmp, "--format", "md,latex,json",
                                     "--name", "demo")
            self.assertEqual(code, 0, out)
            for name in ("demo.md", "demo.tex", "references.bib", "demo.json"):
                self.assertTrue(Path(tmp, name).stat().st_size > 0, name)

    def test_report_command_refuses_integrity_errors_unless_forced(self):
        data = sample_report()
        data["opportunities"][0]["novelty"]["confidence"] = "high"
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp, "in.json")
            src.write_text(json.dumps(data), encoding="utf-8")
            code, out = self.run_cli("report", "--input", str(src), "--out-dir", tmp, "--name", "demo")
            self.assertEqual(code, 2)
            self.assertIn("nothing was written", out)
            self.assertFalse(Path(tmp, "demo.md").exists())
            code, _ = self.run_cli("report", "--input", str(src), "--out-dir", tmp, "--name", "demo", "--force")
            self.assertEqual(code, 0)
            self.assertIn("DRAFT: 1 integrity error(s)", Path(tmp, "demo.md").read_text(encoding="utf-8"))

    def test_score_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, dst = Path(tmp, "c.json"), Path(tmp, "out", "ranked.json")
            src.write_text(json.dumps({"candidates": [candidate("A"), candidate("B", 2)]}), encoding="utf-8")
            code, out = self.run_cli("score", "--input", str(src), "--out", str(dst))
            self.assertEqual(code, 0)
            self.assertIn("#1       Project A", out)
            self.assertEqual(json.loads(dst.read_text(encoding="utf-8"))["ranking"][0]["id"], "A")
            src.write_text(json.dumps({"candidates": [candidate("A", criteria={"x": crit(1)})]}), encoding="utf-8")
            self.assertEqual(self.run_cli("score", "--input", str(src))[0], 2)

    def test_search_requires_a_query(self):
        self.assertEqual(self.run_cli("search")[0], 2)


if __name__ == "__main__":
    unittest.main()
