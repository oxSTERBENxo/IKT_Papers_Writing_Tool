"""Paper workspaces: configuration, scaffolding, placeholders, the untraced-
number scan, citations and references, the check, the draft and final builds
(with a fake pandoc and browser) and the manuscript gate. Offline."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from helpers import CROSSREF_ITEM, make_client, openalex_work

from sra import checkpoints as cp
from sra import manuscript as ms

SAID = "Approved."


def ref(key, authors, year, title, status="verified", doi=None, **extra):
    paper = {"title": title, "authors": authors, "year": year, "venue": extra.pop("venue", "Journal of Tests"),
             "doi": doi, **extra}
    return {"key": key, "paper": paper, "verification": {"status": status}}


class FakeRunner:
    """Stands in for pandoc and the browser: records each command and writes the file it would write."""

    def __init__(self):
        self.calls = []

    def __call__(self, cmd, **kw):
        self.calls.append(cmd)
        out = None
        if "-o" in cmd:
            out = cmd[cmd.index("-o") + 1]
        for c in cmd:
            if c.startswith("--print-to-pdf="):
                out = c.split("=", 1)[1]
        if out:
            Path(out).write_text("fake output of " + Path(cmd[0]).name, encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout="", stderr="")


class WorkspaceCase(unittest.TestCase):
    """A temporary repository with research.json and one paper workspace."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "research.json").write_text(json.dumps({
            "author": "Eva Knezhevikj", "date": "October 2026", "pandoc": str(self.fake_tool("pandoc.exe")),
            "browser": str(self.fake_tool("msedge.exe")), "numbers": {"allow": ["0.05"]}}), encoding="utf-8")
        self.ws = self.root / "papers" / "demo"
        self.made = ms.init(self.ws, "A Test Paper")
        self.write_results({"n": 180432, "rate": 0.006163, "sens": 0.892086, "p": 2.5e-144, "auc": 0.7231,
                            "ci": [0.710, 0.735], "groups": {">=7.0": {"or": 6.754}}})
        self.runner = FakeRunner()

    def tearDown(self):
        self._tmp.cleanup()

    def fake_tool(self, name):
        p = self.root / "tools" / name
        p.parent.mkdir(exist_ok=True)
        p.write_text("", encoding="utf-8")
        return p

    def write_results(self, data):
        (self.ws / "results" / "results.json").write_text(json.dumps(data), encoding="utf-8")

    def write_paper(self, text):
        (self.ws / "paper.md").write_text(text, encoding="utf-8")

    def add_ref(self, data):
        (self.ws / "refs" / f"{data['key']}.json").write_text(json.dumps(data), encoding="utf-8")

    def cfg(self):
        return ms.load_config(self.ws)

    def project(self):
        return cp.load(self.ws)

    GOOD = ("# Abstract\n\nWe study {{res:n|,}} CVEs. Sensitivity was {{sens|.1%}} (AUC {{auc|.3f}}, "
            "95% CI {{ci[0]|.3f}} to {{ci[1]|.3f}}), as in [@allodi2014]. @jacobs2021 disagree.\n\n"
            "# References\n\n{{references}}\n")

    def good_paper(self):
        self.write_paper(self.GOOD)
        self.add_ref(ref("allodi2014", ["Luca Allodi", "Fabio Massacci"], 2014,
                         "Comparing Vulnerability Severity and Exploits Using Case-Control Studies",
                         doi="10.1145/2630069", venue="ACM Transactions on Information and System Security"))
        self.add_ref(ref("jacobs2021", ["Jay Jacobs", "Sasha Romanosky", "Benjamin Edwards"], 2021,
                         "Exploit Prediction Scoring System (EPSS)", doi="10.1145/3436242"))
        cfg = json.loads((self.ws / "paper.json").read_text(encoding="utf-8"))
        cfg["numbers"] = {"allow": ["95%"]}
        (self.ws / "paper.json").write_text(json.dumps(cfg), encoding="utf-8")


class ConfigAndScaffoldTests(WorkspaceCase):
    def test_repository_defaults_are_merged_under_paper_settings(self):
        cfg = self.cfg()
        self.assertEqual(cfg["author"], "Eva Knezhevikj")          # research.json
        self.assertEqual(cfg["title"], "A Test Paper")              # paper.json
        self.assertEqual(cfg["numbers"]["allow"], ["0.05", "95%"])  # paper.json replaces the list
        self.assertEqual(cfg["numbers"]["ignore_integers_upto"], 10)  # nested defaults survive
        self.assertEqual(ms.metadata(cfg)["date"], "October 2026")

    def test_init_creates_a_workspace_and_a_six_gate_project(self):
        for name in ("paper.json", "paper.md", "ANALYSIS_PLAN.md", "analysis.py", "README.md", ".gitignore",
                     "project.json"):
            self.assertTrue((self.ws / name).is_file(), name)
        for d in ("refs", "results", "figures", "data"):
            self.assertTrue((self.ws / d).is_dir())
        self.assertEqual(self.project()["gates"], cp.DEFAULT_GATES)
        self.assertIn("A Test Paper", (self.ws / "ANALYSIS_PLAN.md").read_text(encoding="utf-8"))
        with self.assertRaisesRegex(ms.ManuscriptError, "already exists"):
            ms.init(self.ws, "Again")

    def test_init_inside_an_existing_project_reuses_it(self):
        proj = self.root / "research-projects" / "p"
        cp.init(proj, "Existing")
        made = ms.init(proj / "paper", "Inner paper")
        self.assertEqual(Path(made["project"]), (proj / "project.json").resolve())
        self.assertFalse((proj / "paper" / "project.json").exists())
        self.assertEqual(json.loads((proj / "paper" / "paper.json").read_text(encoding="utf-8"))["project"], "..")
        self.assertEqual(ms.project_for(ms.load_config(proj / "paper"))["name"], "Existing")

    def test_template_is_not_finalisable(self):
        rep = ms.check(self.cfg())
        self.assertTrue(any(i["kind"] == "todo" for i in rep["issues"]))
        self.assertGreater(rep["errors"], 0)


class PlaceholderTests(WorkspaceCase):
    def render(self, text):
        results, _ = ms.load_results(self.cfg())
        return ms.render_placeholders(text, results, self.cfg())

    def test_values_paths_and_formats(self):
        text, trace, errors = self.render(
            'n={{res:n|,}} s={{sens|.1%}} p={{p|sci1}} p2={{rate|p}} auc={{auc|.2f}} lo={{ci[0]}} '
            'or={{groups[">=7.0"].or|.2f}}')
        self.assertEqual(errors, [])
        self.assertEqual(text, "n=180,432 s=89.2% p=2.5 × 10⁻¹⁴⁴ p2=0.006 auc=0.72 lo=0.71 or=6.75")
        self.assertEqual(trace[0]["file"], "results/results.json")
        self.assertEqual(trace[-1]["path"], 'groups[">=7.0"].or')

    def test_missing_key_is_an_error_and_is_visible_in_the_draft(self):
        text, _, errors = self.render("x {{res:nope}} y")
        self.assertIn("**[?res:nope]**", text)
        self.assertIn("'nope' not found", errors[0])

    def test_code_is_left_alone(self):
        text, trace, _ = self.render("use `{{res:n}}` like this\n```\n{{res:n}}\n```")
        self.assertEqual(trace, [])
        self.assertIn("`{{res:n}}`", text)


class NumberScanTests(WorkspaceCase):
    def scan(self, text):
        results, _ = ms.load_results(self.cfg())
        return {(n["text"], n["status"]) for n in ms.scan_numbers(text, results, self.cfg())}

    def test_classification(self):
        found = self.scan("Of 180,432 CVEs, 89.2% were caught (AUC 0.723). Table 3 shows 7 models in 2014. "
                          "We used alpha 0.05 and 1.96 by hand. A hidden 1,753 appears.")
        self.assertIn(("180,432", "matched"), found)
        self.assertIn(("89.2%", "matched"), found)       # proportion x100, rounded as shown
        self.assertIn(("0.723", "matched"), found)
        self.assertIn(("3", "label"), found)
        self.assertIn(("7", "small_integer"), found)
        self.assertIn(("2014", "year"), found)
        self.assertIn(("0.05", "allowed"), found)
        self.assertIn(("1.96", "untraced"), found)
        self.assertIn(("1,753", "untraced"), found)

    def test_rounding_must_agree_with_the_precision_shown(self):
        self.assertIn(("0.72", "matched"), self.scan("AUC 0.72"))
        self.assertIn(("0.724", "untraced"), self.scan("AUC 0.724"))

    def test_placeholders_code_citations_and_references_are_not_scanned(self):
        found = self.scan("A {{res:n}} `123.4` [@x2019, p. 55] https://doi.org/10.1145/2630069\n\n"
                          "# 3.2 Results\n\n# References\n\nSmith (2019) 12(3), 45-67.")
        self.assertEqual(found, set())


class CitationTests(WorkspaceCase):
    def refs(self):
        return {
            "allodi2014": ref("allodi2014", ["Luca Allodi", "Fabio Massacci"], 2014, "Comparing Severity",
                              doi="10.1145/2630069"),
            "jacobs2021": ref("jacobs2021", ["Jay Jacobs", "Sasha Romanosky", "B. Edwards"], 2021, "EPSS"),
            "doe2020a": ref("doe2020a", ["Jane Doe"], 2020, "Beta study"),
            "doe2020b": ref("doe2020b", ["Jane Doe"], 2020, "Alpha study", arxiv_id="2001.00001"),
        }

    def test_in_text_forms(self):
        refs = {k: {**v, "file": f"refs/{k}.json"} for k, v in self.refs().items()}
        text, cited, missing = ms.render_citations(
            "A [@allodi2014]. B [see @jacobs2021, p. 4; @allodi2014]. @allodi2014 said. C [@doe2020a; @doe2020b]. "
            "D [@ghost]. mail me@example.org.", refs)
        self.assertIn("A (Allodi & Massacci, 2014).", text)
        self.assertIn("B (see Jacobs et al., 2021, p. 4; Allodi & Massacci, 2014).", text)
        self.assertIn("Allodi and Massacci (2014) said.", text)
        self.assertIn("C (Doe, 2020b; Doe, 2020a).", text)  # suffixes follow title order: Alpha=a, Beta=b
        self.assertIn("D (**[?ghost]**).", text)
        self.assertIn("me@example.org", text)
        self.assertEqual(missing, ["ghost"])
        self.assertEqual(cited, ["allodi2014", "jacobs2021", "doe2020a", "doe2020b"])

    def test_apa_reference_list(self):
        refs = self.refs()
        listing = ms.reference_list(refs, ["jacobs2021", "allodi2014", "doe2020b"])
        lines = listing.split("\n\n")
        self.assertEqual(lines[0], "Allodi, L., & Massacci, F. (2014). Comparing Severity. *Journal of Tests*. "
                                   "https://doi.org/10.1145/2630069")
        self.assertTrue(lines[1].startswith("Doe, J. (2020). Alpha study. *arXiv preprint* arXiv:2001.00001."))
        self.assertTrue(lines[2].startswith("Jacobs, J., Romanosky, S., & Edwards, B. (2021). EPSS."))

    def test_cite_resolves_and_verifies_through_the_apis(self):
        client, _, _ = make_client([
            ("api.openalex.org", openalex_work(doi="10.1234/fixture.2")),
            ("api.crossref.org", {"message": CROSSREF_ITEM}),
            ("api.semanticscholar.org", 429),
        ])
        data = ms.cite(self.cfg(), "10.1234/fixture.2", "example2021", client)
        self.assertEqual(data["verification"]["status"], "verified")
        saved = json.loads((self.ws / "refs" / "example2021.json").read_text(encoding="utf-8"))
        self.assertEqual(saved["paper"]["doi"], "10.1234/fixture.2")
        with self.assertRaisesRegex(ms.ManuscriptError, "already exists"):
            ms.cite(self.cfg(), "10.1234/fixture.2", "example2021", client)
        with self.assertRaisesRegex(ms.ManuscriptError, "citation key"):
            ms.cite(self.cfg(), "10.1234/fixture.2", "bad key!", client)

    def test_preprint_with_a_different_title_is_verified_through_the_publisher_doi(self):
        from helpers import ARXIV_FEED
        from sra import verify
        client, _, _ = make_client([("export.arxiv.org", ARXIV_FEED),  # arXiv title: the fixture title
                                    ("api.crossref.org", {"message": {**CROSSREF_ITEM, "title": ["Published Title"]}})])
        result = verify.verify_paper(client, {"title": "Published Title", "arxiv_id": "2101.00001",
                                              "doi": "10.1234/fixture.2"})
        self.assertEqual((result["status"], result["via"]), ("verified", "crossref"))
        self.assertIn("different title", result["note"])
        # Without a publisher DOI the mismatch stands.
        client, _, _ = make_client([("export.arxiv.org", ARXIV_FEED)])
        result = verify.verify_paper(client, {"title": "Published Title", "arxiv_id": "2101.00001"})
        self.assertEqual(result["status"], "title_mismatch")


class CheckTests(WorkspaceCase):
    def test_a_traced_paper_has_no_blocking_issues(self):
        self.good_paper()
        rep = ms.check(self.cfg())
        self.assertEqual(rep["errors"], 0, rep["issues"])
        self.assertEqual(len(rep["placeholders"]), 5)
        self.assertEqual({c["key"] for c in rep["citations"]}, {"allodi2014", "jacobs2021"})

    def test_each_kind_of_problem_is_reported(self):
        self.good_paper()
        self.add_ref(ref("weak2020", ["A B"], 2020, "Weak", status="identifier_resolves"))
        self.add_ref(ref("bad2020", ["C D"], 2020, "Bad", status="title_mismatch"))
        self.add_ref(ref("unused2020", ["E F"], 2020, "Unused"))
        extra = ("Typed 0.723 and 1.96. [@weak2020] [@bad2020] [@ghost]\n\n![Fig](figures/missing.png)\n\n"
                 "TODO finish {{res:absent}}\n\n# References")
        self.write_paper(self.GOOD.replace("# References", extra))  # before References, which is not scanned
        kinds = {(i["level"], i["kind"]) for i in ms.check(self.cfg())["issues"]}
        for expected in [("warning", "typed_number"), ("error", "untraced_number"), ("warning", "reference"),
                         ("error", "reference"), ("error", "citation"), ("warning", "unused_reference"),
                         ("error", "figure"), ("error", "todo"), ("error", "placeholder")]:
            self.assertIn(expected, kinds)

    def test_missing_results_file_is_blocking(self):
        self.good_paper()
        os.remove(self.ws / "results" / "results.json")
        rep = ms.check(self.cfg())
        self.assertTrue(any(i["kind"] == "results" for i in rep["issues"]))


class BuildTests(WorkspaceCase):
    def approve_up_to_results(self):
        proj = self.project()
        for gate in ("scope", "question", "methodology", "execution"):
            v = cp.propose(cp.load(self.ws), gate, f"{gate} plan")
            cp.approve(cp.load(self.ws), gate, v["version"], SAID, by="test-reviewer")
        cp.record_completion(cp.load(self.ws), "execution", "python analysis.py", 0,
                             [str(self.ws / "results" / "results.json")])
        v = cp.propose(cp.load(self.ws), "results", "results", findings=["sensitivity 89%"],
                       limitations=["KEV is incomplete"], interpretation="CVSS is a weak test",
                       artifacts=[str(self.ws / "results" / "results.json")])
        cp.approve(cp.load(self.ws), "results", v["version"], SAID, by="test-reviewer")
        return proj

    def test_draft_always_builds_and_is_marked(self):
        res = ms.build(self.cfg(), runner=self.runner)  # the raw template: TODOs everywhere
        md = (self.ws / "build" / "paper.draft.md").read_text(encoding="utf-8")
        self.assertTrue(md.startswith("> **DRAFT, not approved for submission.**"))
        self.assertEqual({Path(o).name for o in res["outputs"]},
                         {"paper.draft.md", "paper.draft.docx", "paper.draft.pdf"})
        tools = [Path(c[0]).name for c in self.runner.calls]
        self.assertEqual(tools, ["pandoc.exe", "pandoc.exe", "msedge.exe"])
        html_cmd = self.runner.calls[1]
        self.assertIn("--embed-resources", html_cmd)
        self.assertTrue(any(str(x).endswith("paper_print.css") for x in html_cmd))
        meta = json.loads((self.ws / "build" / "paper.draft.meta.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["author"], "Eva Knezhevikj")
        self.assertFalse((self.ws / "final").exists())

    def test_draft_contains_resolved_numbers_and_references(self):
        self.good_paper()
        ms.build(self.cfg(), formats=[], runner=self.runner)
        md = (self.ws / "build" / "paper.draft.md").read_text(encoding="utf-8")
        self.assertIn("We study 180,432 CVEs. Sensitivity was 89.2% (AUC 0.723, 95% CI 0.710 to 0.735), as in "
                      "(Allodi & Massacci, 2014). Jacobs et al. (2021) disagree.", md)
        self.assertIn("Allodi, L., & Massacci, F. (2014).", md)
        self.assertNotIn("{{", md)

    def test_missing_pandoc_skips_formats_for_a_draft(self):
        cfg = self.cfg()
        cfg["pandoc"] = str(self.root / "nowhere.exe")
        res = ms.build(cfg, runner=self.runner)
        self.assertEqual([Path(o).name for o in res["outputs"]], ["paper.draft.md"])
        self.assertIn("pandoc not found", res["skipped"][0])

    def test_final_needs_the_approved_manuscript(self):
        self.good_paper()
        with self.assertRaisesRegex(ms.ManuscriptError, "'manuscript' is not started"):
            ms.build(self.cfg(), final=True, runner=self.runner)
        with self.assertRaisesRegex(cp.CheckpointError, "'scope' is not started"):
            ms.review(self.cfg(), runner=self.runner)  # the manuscript gate comes last
        self.approve_up_to_results()
        out = ms.review(self.cfg(), runner=self.runner)
        v = out["version"]
        self.assertIn("paper.md", v["artifacts"])
        self.assertIn("refs/allodi2014.json", v["artifacts"])
        self.assertIn("results/results.json", v["artifacts"])
        with self.assertRaisesRegex(ms.ManuscriptError, "awaiting review"):
            ms.build(self.cfg(), final=True, runner=self.runner)  # proposed is not approved
        cp.approve(cp.load(self.ws), "manuscript", v["version"], SAID, by="test-reviewer")
        res = ms.build(self.cfg(), final=True, runner=self.runner)
        names = {Path(o).name for o in res["outputs"]}
        self.assertEqual(names, {"paper.md", "paper.docx", "paper.pdf"})
        final_md = (self.ws / "final" / "paper.md").read_text(encoding="utf-8")
        self.assertNotIn("DRAFT", final_md)
        manifest = json.loads((self.ws / "final" / "MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["approval"]["version"], v["version"])
        self.assertEqual(manifest["approval"]["said"], SAID)
        self.assertIn("paper.md", manifest["inputs"])
        self.assertEqual(self.project()["log"][-1]["event"], "manuscript_finalized")

        # A change after approval makes the final build refuse until the user approves again.
        self.write_paper(self.GOOD.replace("disagree", "partly disagree"))
        with self.assertRaisesRegex(ms.ManuscriptError, "stale"):
            ms.build(self.cfg(), final=True, runner=self.runner)

    def test_final_refuses_rather_than_skip_a_format(self):
        self.good_paper()
        self.approve_up_to_results()
        v = ms.review(self.cfg(), runner=self.runner)["version"]
        cp.approve(cp.load(self.ws), "manuscript", v["version"], SAID, by="test-reviewer")
        cfg = self.cfg()
        cfg["pandoc"] = str(self.root / "nowhere.exe")
        with self.assertRaisesRegex(ms.ManuscriptError, "pandoc not found"):
            ms.build(cfg, final=True, runner=self.runner)
        self.assertFalse((self.ws / "final").exists())  # nothing half-final is written

    def test_outdated_final_is_reported_but_left_alone(self):
        self.good_paper()
        self.approve_up_to_results()
        v = ms.review(self.cfg(), runner=self.runner)["version"]
        cp.approve(cp.load(self.ws), "manuscript", v["version"], SAID, by="test-reviewer")
        ms.build(self.cfg(), final=True, runner=self.runner)
        kinds = lambda: [i for i in ms.check(self.cfg())["issues"] if i["kind"] == "final_outdated"]
        self.assertEqual(kinds(), [])  # fresh final: nothing to report
        final_md = (self.ws / "final" / "paper.md").read_bytes()
        self.write_paper(self.GOOD.replace("disagree", "partly disagree"))
        issues = kinds()
        self.assertTrue(issues)
        self.assertEqual(issues[0]["level"], "warning")
        text = " ".join(i["message"] for i in issues)
        self.assertIn("paper.md", text)
        self.assertIn("no longer the approved", text)
        self.assertEqual((self.ws / "final" / "paper.md").read_bytes(), final_md)  # never rebuilt silently
        (self.ws / "final" / "paper.docx").write_bytes(b"edited by hand")
        self.assertIn("final/paper.docx was changed after the build", " ".join(i["message"] for i in kinds()))

    def test_new_input_after_approval_is_not_covered(self):
        self.good_paper()
        self.approve_up_to_results()
        v = ms.review(self.cfg(), runner=self.runner)["version"]
        cp.approve(cp.load(self.ws), "manuscript", v["version"], SAID, by="test-reviewer")
        self.add_ref(ref("late2025", ["G H"], 2025, "Late"))
        with self.assertRaisesRegex(ms.ManuscriptError, "not covered by the approved manuscript.*late2025"):
            ms.build(self.cfg(), final=True, runner=self.runner)

    def test_review_is_refused_while_the_check_fails(self):
        self.approve_up_to_results()
        with self.assertRaisesRegex(ms.ManuscriptError, "blocking issue"):
            ms.review(self.cfg(), runner=self.runner)  # the template still has TODOs
        self.assertTrue((self.ws / "build" / "paper.draft.md").is_file())  # the draft is still written

    def test_changed_results_after_approval_invalidate_results_and_manuscript(self):
        self.good_paper()
        self.approve_up_to_results()
        v = ms.review(self.cfg(), runner=self.runner)["version"]
        cp.approve(cp.load(self.ws), "manuscript", v["version"], SAID, by="test-reviewer")
        self.write_results({"n": 1})
        states = cp.evaluate(self.project())
        self.assertEqual(states["results"]["state"], cp.STALE)
        self.assertEqual(states["manuscript"]["state"], cp.STALE)


if __name__ == "__main__":
    unittest.main()
