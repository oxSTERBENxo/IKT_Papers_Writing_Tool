"""Obsidian export: vault resolution, note layout, idempotent updates, protection of user edits, collisions,
escaping and Unicode. Everything runs in temporary folders; no real vault is touched."""
import copy
import hashlib
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import helpers  # noqa: F401  (puts scripts/ on sys.path)
from sra import cli, obsidian

SKILL = Path(__file__).resolve().parents[1]


def paper(key, title, doi=None, arxiv=None, verified=True, **kw):
    return {"key": key, "title": title, "authors": ["Ada Example", "Bo Sample"], "year": 2024, "doi": doi,
            "arxiv_id": arxiv, "venue": "Test Venue", "read_level": "abstract",
            "verification": {"status": "verified" if verified else "unresolved", "via": "arxiv"}, **kw}


def opp_report(title, papers, verdict="conditional_go"):
    return {"type": "opportunity_report", "title": title, "date": "2026-10-01",
            "papers": papers,
            "sections": {"summary": f"Summary citing [@{papers[0]['key']}]."},
            "opportunities": [{"title": "Q1", "category": "underexplored_setting", "mode": "extension",
                               "research_question": "Does it hold?", "motivation": f"See [@{papers[0]['key']}].",
                               "closest_existing_work": [{"key": papers[0]["key"], "how_it_differs": "x",
                                                          "read_level": "abstract", "overlap": "partial"}],
                               "decision": {"verdict": verdict, "rationale": "r", "conditions": ["c"],
                                            "unresolved_risks": ["u"]}}]}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.vault = self.base / "My Vault"
        (self.vault / ".obsidian").mkdir(parents=True)
        self.reports = self.base / "reports"
        self.reports.mkdir()
        self.env = {k: os.environ.pop(k) for k in ("SRA_OBSIDIAN_VAULT", "SRA_OBSIDIAN_FOLDER", "SRA_OBSIDIAN_AUTO")
                    if k in os.environ}

    def tearDown(self):
        for k in ("SRA_OBSIDIAN_VAULT", "SRA_OBSIDIAN_FOLDER", "SRA_OBSIDIAN_AUTO"):
            os.environ.pop(k, None)
        os.environ.update(self.env)
        self.tmp.cleanup()

    def save(self, name, data):
        path = self.reports / name
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return path

    def run_export(self, *paths, **kw):
        loaded = [obsidian.load_report(p) for p in paths]
        return obsidian.export(loaded, self.vault, today="2026-10-19", **kw)

    def notes(self, sub=""):
        return sorted(p.relative_to(self.vault / "Scientific Research").as_posix()
                      for p in (self.vault / "Scientific Research" / sub).rglob("*.md"))

    def read(self, rel):
        return (self.vault / "Scientific Research" / rel).read_text(encoding="utf-8")


class VaultResolutionTests(Base):
    def test_env_variable_and_windows_style_path(self):
        os.environ["SRA_OBSIDIAN_VAULT"] = str(self.vault).replace("/", "\\") if os.name == "nt" else str(self.vault)
        self.assertEqual(obsidian.resolve_vault(None), self.vault.resolve())
        self.assertEqual(obsidian.resolve_vault(f'"{self.vault}"'), self.vault.resolve())  # pasted with quotes

    def test_invalid_paths_are_refused(self):
        with self.assertRaises(obsidian.ExportError):
            obsidian.resolve_vault(None)  # nothing configured
        with self.assertRaises(obsidian.ExportError):
            obsidian.resolve_vault(str(self.base / "missing"))
        exe = self.base / "Obsidian.exe"
        exe.write_bytes(b"MZ")
        with self.assertRaisesRegex(obsidian.ExportError, "not Obsidian.exe"):
            obsidian.resolve_vault(str(exe))
        plain = self.base / "plain"
        plain.mkdir()
        with self.assertRaisesRegex(obsidian.ExportError, "no .obsidian"):
            obsidian.resolve_vault(str(plain))
        self.assertEqual(obsidian.resolve_vault(str(plain), allow_plain_folder=True), plain.resolve())

    def test_research_folder_must_stay_inside_vault(self):
        v = self.vault.resolve()
        self.assertEqual(obsidian.research_root(v, None), v / "Scientific Research")
        self.assertEqual(obsidian.research_root(v, "Uni/Research"), v / "Uni" / "Research")
        for bad in ("../outside", "C:\\elsewhere", "/abs", "a/../../b", ""):
            with self.assertRaises(obsidian.ExportError, msg=bad):
                obsidian.research_root(v, bad)


class TextSafetyTests(unittest.TestCase):
    def test_safe_stem(self):
        self.assertEqual(obsidian.safe_stem('Does syntax matter? A: "test" | [x] #1 ^b'),
                         "Does syntax matter A test x 1 b")
        self.assertEqual(obsidian.safe_stem("CON"), "_CON")
        self.assertEqual(obsidian.safe_stem("  ...  "), "Untitled")
        self.assertEqual(obsidian.safe_stem("Mangado Gómez: análisis 研究"), "Mangado Gómez análisis 研究")
        self.assertLessEqual(len(obsidian.safe_stem("word " * 100)), obsidian.MAX_STEM)

    def test_yaml_and_markdown_escaping(self):
        self.assertEqual(obsidian.yaml_value('a: "b" #c'), '"a: \\"b\\" #c"')
        self.assertEqual(obsidian.yaml_value(["x", "y: z"]), '["x", "y: z"]')
        self.assertEqual(obsidian.md_escape("*bold* [link] a|b"), "\\*bold\\* \\[link\\] a\\|b")
        self.assertEqual(obsidian.wikilink("Note", "A|B [x]"), "[[Note|A B  x]]")
        self.assertEqual(obsidian.wikilink("Note", "Alias", in_table=True), "[[Note\\|Alias]]")

    def test_table_cells_keep_wikilinks_intact(self):
        cell = obsidian.ObsidianRenderer.cell("x | y [[Paper|Liu 2026]] z")
        self.assertEqual(cell, "x / y [[Paper\\|Liu 2026]] z")


class ExportTests(Base):
    def setUp(self):
        super().setUp()
        self.a = self.save("a.json", opp_report("Project: Alpha?", [
            paper("p1", "Shared Paper", doi="10.1234/shared", findings="Finds X.", limitations=None),
            paper("p2", "Only in Alpha", arxiv="2101.00001", findings="Finds Y."),
            paper("p3", "Unverified paper", doi="10.1234/unv", verified=False)]))
        self.b = self.save("b.json", opp_report("Project Beta ünïcode 研究", [
            paper("q1", "Shared Paper", doi="https://doi.org/10.1234/SHARED", findings="Beta's view of X.")],
            verdict="no_go"))

    def test_layout_frontmatter_links_and_paper_content(self):
        summary = self.run_export(self.a, self.b)
        self.assertEqual(self.notes(), ["Papers/Only in Alpha.md", "Papers/Shared Paper.md",
                                        "Projects/Project Alpha.md", "Projects/Project Beta ünïcode 研究.md",
                                        "Research Dashboard.md"])
        alpha = self.read("Projects/Project Alpha.md")
        for expected in ('title: "Project: Alpha?"', 'research_type: "opportunity_report"', 'created: "2026-10-01"',
                         'research_status: "conditional-go"', '"research/opportunity-report"', "source_report:",
                         "[[Shared Paper|Example & Sample 2024]]", "## Related research",
                         "[[Project Beta ünïcode 研究]]", "[[Research Dashboard]]"):
            self.assertIn(expected, alpha)
        self.assertIn('research_status: "no-go"', self.read("Projects/Project Beta ünïcode 研究.md"))
        shared = self.read("Papers/Shared Paper.md")
        self.assertIn("Finds X.", shared)
        self.assertIn("Beta's view of X.", shared)  # one note for the same DOI cited by two reports
        self.assertIn("## Limitations", shared)
        self.assertIn("not reported", shared)  # no limitations given: nothing invented
        self.assertIn("[[Project Alpha]]", shared)
        dash = self.read("Research Dashboard.md")
        self.assertIn("[[Project Alpha]]", dash)
        self.assertIn("conditional-go", dash)
        self.assertTrue(any("unverified" in w or "verify-refs" in w for w in summary["warnings"]))

    def test_at_a_glance_box_tops_each_project_note(self):
        self.run_export(self.a)
        alpha = self.read("Projects/Project Alpha.md")
        box = alpha[alpha.index("> [!abstract] At a glance"):alpha.index("> Exported from")]
        self.assertLess(alpha.index("> [!abstract] At a glance"), alpha.index("%% sra:end %%"))
        for expected in ("**Main question:** Project: Alpha?", "**Status:** conditional-go",
                         "| Q1 | extension | **CONDITIONAL GO** |", "**Conclusion:**",
                         "[[Shared Paper|Example & Sample 2024]]"):
            self.assertIn(expected, box)
        self.assertNotIn("**Data:**", box)  # no datasets in the report: the line is left out, not invented
        prop = {"type": "research_proposal", "title": "A plan", "date": "2026-10-02", "papers": [],
                "datasets": [{"name": "Set A", "url": "https://example.org/a"}],
                "proposal": {"research_question": ["RQ1. One?", "RQ2. Two?"],
                             "hypothesis": [{"text": "H1: it works.", "level": "speculative"}],
                             "contribution": ["A measured comparison."]}}
        self.run_export(self.save("prop.json", prop))
        box = self.read("Projects/A plan.md")
        for expected in ("**Topic:** A plan", "**Data:** [Set A](https://example.org/a)", "> - RQ1. One?",
                         "**Hypotheses:**", "> - H1: it works.",
                         "**Expected contribution:**", "A measured comparison."):
            self.assertIn(expected, box)

    def test_rerun_is_idempotent_and_sources_unchanged(self):
        before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in (self.a, self.b)}
        self.run_export(self.a, self.b)
        snapshot = {n: self.read(n) for n in self.notes()}
        second = self.run_export(self.b, self.a)  # other order
        self.assertTrue(all(a["action"] == "unchanged" for a in second["actions"]), second["actions"])
        self.assertEqual({n: self.read(n) for n in self.notes()}, snapshot)
        self.assertEqual(before, {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in (self.a, self.b)})

    def test_separate_exports_accumulate(self):
        self.run_export(self.a)
        self.run_export(self.b)  # alpha is re-read from its source report, so links connect both ways
        self.assertIn("[[Project Beta ünïcode 研究]]", self.read("Projects/Project Alpha.md"))
        self.assertIn("Beta's view of X.", self.read("Papers/Shared Paper.md"))
        self.assertIn("[[Project Alpha]]", self.read("Research Dashboard.md"))

    def test_user_text_and_frontmatter_survive_updates(self):
        self.run_export(self.a)
        note = self.vault / "Scientific Research" / "Projects" / "Project Alpha.md"
        text = note.read_text(encoding="utf-8")
        text = text.replace("sra_kind: \"project\"", "sra_kind: \"project\"\nmy_rating: 5\ntags2: keep")
        text = text.replace('tags: ["research"', 'tags: ["mine", "research"')
        text += "\n## My notes\nTalk to the supervisor.\n"
        note.write_text(text, encoding="utf-8")
        data = json.loads(self.a.read_text(encoding="utf-8"))
        data["sections"]["summary"] = "A changed summary."
        self.a.write_text(json.dumps(data), encoding="utf-8")
        res = self.run_export(self.a)
        self.assertIn({"action": "updated", "kind": "project", "path": str(note)}, res["actions"])
        new = note.read_text(encoding="utf-8")
        self.assertIn("A changed summary.", new)
        self.assertIn("Talk to the supervisor.", new)
        self.assertIn("my_rating: 5", new)
        self.assertIn('"mine"', new)
        self.assertEqual(new.count(obsidian.BEGIN), 1)

    def test_edited_or_unmarked_generated_section_is_not_overwritten(self):
        self.run_export(self.a)
        note = self.vault / "Scientific Research" / "Papers" / "Only in Alpha.md"
        edited = note.read_text(encoding="utf-8").replace("Finds Y.", "Finds Y. My correction.")
        note.write_text(edited, encoding="utf-8")
        res = self.run_export(self.a)
        self.assertIn("skipped", [a["action"] for a in res["actions"] if a["path"] == str(note)])
        self.assertEqual(note.read_text(encoding="utf-8"), edited)
        res = self.run_export(self.a, overwrite_managed=True)
        self.assertNotIn("My correction.", note.read_text(encoding="utf-8"))
        unmarked = note.read_text(encoding="utf-8").replace(obsidian.BEGIN, "").replace(obsidian.END, "")
        note.write_text(unmarked, encoding="utf-8")
        res = self.run_export(self.a)
        self.assertTrue(any("markers were removed" in w for w in res["warnings"]))
        self.assertEqual(note.read_text(encoding="utf-8"), unmarked)

    def test_renamed_note_is_found_and_nothing_is_deleted(self):
        self.run_export(self.a)
        old = self.vault / "Scientific Research" / "Projects" / "Project Alpha.md"
        moved = self.vault / "Scientific Research" / "Archive" / "Renamed Alpha.md"
        moved.parent.mkdir()
        old.rename(moved)
        self.run_export(self.a)
        self.assertFalse(old.exists())  # no duplicate created
        self.assertIn("Renamed Alpha.md", [p.name for p in (self.vault / "Scientific Research").rglob("*.md")])
        self.assertIn("[[Renamed Alpha]]", self.read("Research Dashboard.md"))
        self.a.unlink()  # source report gone: its note stays, listed as missing
        res = self.run_export(self.b)
        self.assertTrue(moved.exists())
        self.assertIn("source report missing", self.read("Research Dashboard.md"))
        self.assertTrue(any("no longer at" in w for w in res["warnings"]))

    def test_filename_collision_with_user_note(self):
        projects = self.vault / "Scientific Research" / "Projects"
        projects.mkdir(parents=True)
        (projects / "Project Alpha.md").write_text("My own unrelated note.\n", encoding="utf-8")
        self.run_export(self.a)
        self.assertEqual((projects / "Project Alpha.md").read_text(encoding="utf-8"), "My own unrelated note.\n")
        self.assertTrue((projects / "Project Alpha (2).md").exists())
        self.run_export(self.a)
        self.assertFalse((projects / "Project Alpha (3).md").exists())

    def test_two_reports_with_the_same_title(self):
        c = self.save("c.json", opp_report("Project: Alpha?", [paper("z", "Z paper", doi="10.1/z")]))
        self.run_export(self.a, c)
        self.assertIn("Projects/Project Alpha (2).md", self.notes())

    def test_dry_run_and_no_papers(self):
        res = self.run_export(self.a, dry_run=True)
        self.assertTrue(res["actions"])
        self.assertFalse((self.vault / "Scientific Research").exists())
        self.run_export(self.a, papers=False)
        self.assertEqual(self.notes("Papers"), [])
        self.assertNotIn("[[Shared Paper", self.read("Projects/Project Alpha.md"))


class CliTests(Base):
    def test_obsidian_export_command_and_report_integration(self):
        src = self.save("a.json", opp_report("CLI project", [paper("p1", "P one", doi="10.1/p")]))
        out = io.StringIO()
        with redirect_stdout(out):
            code = cli.main(["obsidian-export", "--input", str(src), "--vault", str(self.vault), "--folder", "Uni"])
        self.assertEqual(code, 0)
        self.assertTrue((self.vault / "Uni" / "Projects" / "CLI project.md").exists())
        os.environ["SRA_OBSIDIAN_VAULT"] = str(self.vault)
        with redirect_stdout(io.StringIO()):
            code = cli.main(["report", "--input", str(src), "--out-dir", str(self.base / "out"), "--force",
                             "--obsidian"])
        self.assertEqual(code, 0)
        self.assertTrue((self.vault / "Scientific Research" / "Projects" / "CLI project.md").exists())

    def test_bad_vault_fails_cleanly(self):
        src = self.save("a.json", opp_report("CLI project", [paper("p1", "P one", doi="10.1/p")]))
        with redirect_stdout(io.StringIO()):
            code = cli.main(["obsidian-export", "--input", str(src), "--vault", str(self.base / "nope")])
        self.assertEqual(code, 2)


class ShippedExampleTests(Base):
    def test_examples_export_without_errors(self):
        paths = [SKILL / "examples" / "nlp-graph-theory" / f for f in
                 ("opportunity_report.json", "reproducibility_report.json", "research_proposal.json")]
        before = [p.read_bytes() for p in paths]
        res = self.run_export(*paths)
        self.assertFalse([a for a in res["actions"] if a["action"] == "skipped"])
        self.assertEqual(before, [p.read_bytes() for p in paths])
        dash = self.read("Research Dashboard.md")
        for label in ("Research opportunities", "Reproducibility reports", "Research proposals"):
            self.assertIn(label, dash)


if __name__ == "__main__":
    unittest.main()
