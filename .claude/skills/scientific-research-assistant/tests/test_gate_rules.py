"""Refined checkpoint rules: execution marked not applicable, authorization
versus completed runs, the results review, `project run`, the schema
upgrade, free validation, and the shell hook that enforces the gates."""
import contextlib
import io
import hashlib
import json
import platform
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import helpers  # noqa: F401  (puts scripts/ on sys.path)

from sra import checkpoints as cp
from sra import cli, hook

SKILL = Path(__file__).resolve().parents[1]
SRA = SKILL / "scripts" / "sra.py"
SAID = "Yes, approved."
RESULTS_KW = {"findings": ["MLP within 1 point"], "limitations": ["two datasets only"],
              "interpretation": "The graph adds little here."}


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name) / "proj"
        cp.init(self.dir, "Rules")

    def tearDown(self):
        self._tmp.cleanup()

    def p(self):
        return cp.load(self.dir)

    def state(self, gate):
        return cp.evaluate(self.p())[gate]

    def file(self, name, text="x"):
        f = self.dir / name
        f.write_text(text, encoding="utf-8")
        return str(f)

    def approve(self, gate, **kw):
        v = cp.propose(self.p(), gate, kw.pop("summary", f"{gate} plan"), **kw)
        cp.approve(self.p(), gate, v["version"], SAID)
        return v

    def through_methodology(self):
        for g in ("scope", "question", "methodology"):
            self.approve(g)


class NotApplicableTests(Base):
    def test_needs_a_reason_and_the_users_words_and_only_for_execution(self):
        self.through_methodology()
        with self.assertRaisesRegex(cp.CheckpointError, "--reason"):
            cp.mark_not_applicable(self.p(), "execution", "", SAID)
        with self.assertRaisesRegex(cp.CheckpointError, "own words"):
            cp.mark_not_applicable(self.p(), "execution", "literature review only", "")
        with self.assertRaisesRegex(cp.CheckpointError, "only \\['execution'\\]"):
            cp.mark_not_applicable(self.p(), "results", "none", SAID)

    def test_cannot_skip_ahead_of_the_methodology(self):
        self.approve("scope")
        with self.assertRaisesRegex(cp.CheckpointError, "'question' is not started"):
            cp.mark_not_applicable(self.p(), "execution", "no runs", SAID)

    def test_not_applicable_unlocks_results_but_never_authorizes_computation(self):
        self.through_methodology()
        cp.mark_not_applicable(self.p(), "execution", "secondary analysis of published tables", "Nothing to run.")
        st = self.state("execution")
        self.assertEqual(st["state"], cp.NOT_APPLICABLE)
        self.assertEqual(st["decision"]["said"], "Nothing to run.")
        problems = cp.require(self.p(), ["execution"])
        self.assertIn("marked not applicable", problems[0])
        self.assertIn("secondary analysis of published tables", problems[0])
        # Results can follow without a run.
        self.approve("results", artifacts=[self.file("tables.json")], **RESULTS_KW)
        self.assertEqual(self.state("results")["state"], cp.APPROVED)
        lines = "\n".join(cp.status_lines(self.p()))
        self.assertIn("NOT APPLICABLE", lines)
        self.assertIn("reason: secondary analysis of published tables", lines)

    def test_reopening_execution_invalidates_later_gates(self):
        self.through_methodology()
        cp.mark_not_applicable(self.p(), "execution", "no runs", SAID)
        self.approve("results", artifacts=[self.file("t.json")], **RESULTS_KW)
        v = cp.propose(self.p(), "execution", "Actually run a robustness check")
        self.assertEqual(v["invalidated"], ["results"])
        self.assertEqual(self.state("execution")["state"], cp.AWAITING)
        self.assertEqual(self.state("results")["state"], cp.STALE)

    def test_a_methodology_change_makes_not_applicable_stale(self):
        self.through_methodology()
        cp.mark_not_applicable(self.p(), "execution", "no runs", SAID)
        cp.propose(self.p(), "methodology", "new plan")
        self.assertEqual(self.state("execution")["state"], cp.STALE)


class AuthorizationVersusCompletionTests(Base):
    def authorize(self):
        self.through_methodology()
        self.approve("execution")

    def test_authorized_but_not_run_blocks_results(self):
        self.authorize()
        st = self.state("execution")
        self.assertEqual(st["state"], cp.APPROVED)
        self.assertFalse(st["completion"]["completed"])
        self.assertEqual(cp.require(self.p(), ["execution"]), [])  # authorized
        self.assertIn("not completed", cp.require(self.p(), ["execution"], completed=True)[0])
        with self.assertRaisesRegex(cp.CheckpointError, "no successful run"):
            cp.propose(self.p(), "results", "r", artifacts=[self.file("r.json")], **RESULTS_KW)
        self.assertIn("project run", cp.next_step(self.p()))

    def test_failed_run_is_recorded_but_does_not_count(self):
        self.authorize()
        cp.record_completion(self.p(), "execution", "python analysis.py", 1)
        self.assertIn("last run failed (exit 1)", self.state("execution")["completion"]["reason"])
        self.assertEqual(self.p()["log"][-1]["event"], "run_failed")

    def test_completion_needs_authorization(self):
        self.through_methodology()
        with self.assertRaisesRegex(cp.CheckpointError, "no authorization"):
            cp.record_completion(self.p(), "execution", "python analysis.py", 0)

    def test_completion_is_bound_to_the_authorization_it_ran_under(self):
        self.authorize()
        out = self.file("results.json", '{"acc": 0.9}')
        cp.record_completion(self.p(), "execution", "python analysis.py", 0, [out])
        self.assertTrue(self.state("execution")["completion"]["completed"])
        self.approve("results", artifacts=[out], **RESULTS_KW)
        # The methodology changes; execution is re-authorized for the new plan. The old run no longer counts.
        self.approve("methodology", summary="plan v2")
        cp.approve(self.p(), "execution", self.state("execution")["version"], "Same run plan, go.")
        comp = self.state("execution")["completion"]
        self.assertFalse(comp["completed"])
        self.assertIn("no run recorded under this authorization", comp["reason"])
        self.assertEqual(self.state("results")["state"], cp.STALE)

    def test_edited_evidence_means_the_run_no_longer_counts(self):
        self.authorize()
        out = self.file("results.json", '{"acc": 0.9}')
        cp.record_completion(self.p(), "execution", "python analysis.py", 0, [out])
        self.approve("results", artifacts=[out], **RESULTS_KW)
        Path(out).write_text('{"acc": 0.99}', encoding="utf-8")
        self.assertIn("run evidence changed", self.state("execution")["completion"]["reason"])
        self.assertEqual(self.state("results")["state"], cp.STALE)

    def test_a_new_successful_run_makes_approved_results_stale(self):
        self.authorize()
        out = self.file("results.json", '{"acc": 0.9}')
        cp.record_completion(self.p(), "execution", "python analysis.py", 0, [out])
        self.approve("results", artifacts=[out], **RESULTS_KW)
        cp.record_completion(self.p(), "execution", "python analysis.py --again", 0, [out])
        st = self.state("results")
        self.assertEqual(st["state"], cp.STALE)
        self.assertIn("no longer the current successful run", st["reasons"][0])


class ResultsReviewTests(Base):
    def test_results_need_findings_limitations_interpretation_and_files(self):
        self.through_methodology()
        cp.mark_not_applicable(self.p(), "execution", "no runs", SAID)
        f = self.file("r.json")
        for missing in ("findings", "limitations", "interpretation"):
            kw = {k: v for k, v in RESULTS_KW.items() if k != missing}
            with self.assertRaisesRegex(cp.CheckpointError, "--" + missing.rstrip("s")):
                cp.propose(self.p(), "results", "r", artifacts=[f], **kw)
        with self.assertRaisesRegex(cp.CheckpointError, "attach the results files"):
            cp.propose(self.p(), "results", "r", **RESULTS_KW)
        cp.propose(self.p(), "results", "r", artifacts=[f], **RESULTS_KW)
        shown = "\n".join(cp.show_lines(self.p(), "results"))
        for text in ("Findings:", "MLP within 1 point", "Limitations:", "two datasets only",
                     "Interpretation: The graph adds little here."):
            self.assertIn(text, shown)


class SchemaUpgradeTests(unittest.TestCase):
    def test_five_gate_projects_gain_the_manuscript_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "project.json"
            old = {"sra_project": 1, "name": "old", "question": "", "created": "x", "updated": "x",
                   "gates": cp.SCHEMA1_DEFAULT_GATES,
                   "checkpoints": {g: {"versions": [], "decisions": []} for g in cp.SCHEMA1_DEFAULT_GATES},
                   "log": []}
            f.write_text(json.dumps(old), encoding="utf-8")
            project = cp.load(tmp)
            self.assertEqual(project["gates"], cp.DEFAULT_GATES)
            self.assertEqual(project["log"][-1]["event"], "schema_upgraded")
            custom = dict(old, gates=["scope", "question"],
                          checkpoints={g: {"versions": [], "decisions": []} for g in ("scope", "question")})
            f.write_text(json.dumps(custom), encoding="utf-8")
            self.assertEqual(cp.load(tmp)["gates"], ["scope", "question"])  # a chosen subset stays a subset


class ProjectRunTests(Base):
    def run_cli(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            code = cli.main(["--no-cache", "project", "run", "--project", str(self.dir), *argv])
        return code, out.getvalue()

    def test_run_is_refused_without_authorization(self):
        self.approve("scope")
        code, out = self.run_cli("--", sys.executable, "-c", "print('hi')")
        self.assertEqual(code, 3)
        self.assertIn("BLOCKED", out)
        self.assertFalse((self.dir / "runs").exists())

    def test_authorized_run_records_evidence_and_failures(self):
        self.through_methodology()
        self.approve("execution")
        script = "import pathlib; pathlib.Path('results.json').write_text('{\"n\": 3}'); print('done')"
        code, out = self.run_cli("--evidence", "results.json", "--", sys.executable, "-c", script)
        self.assertEqual(code, 0, out)
        self.assertIn("Run completed", out)
        comp = self.state("execution")["completion"]
        self.assertTrue(comp["completed"])
        self.assertIn("results.json", comp["record"]["evidence"])
        log = self.dir / comp["record"]["log"]
        self.assertIn("done", log.read_text(encoding="utf-8"))
        code, out = self.run_cli("--", sys.executable, "-c", "raise SystemExit(4)")
        self.assertEqual(code, 1)
        self.assertIn("FAILED (exit 4)", out)
        self.assertFalse(self.state("execution")["completion"]["completed"])

    def test_run_manifest_records_reproducibility_facts(self):
        self.through_methodology()
        self.approve("execution")
        self.file("data.csv", "a,b\n1,2\n")
        script = "import pathlib; pathlib.Path('results.json').write_text('{}')"
        code, out = self.run_cli("--evidence", "results.json", "--input", "data.csv", "--", sys.executable, "-c",
                                 script)
        self.assertEqual(code, 0, out)
        self.assertIn("Run manifest:", out)
        rec = self.state("execution")["completion"]["record"]
        path = self.dir / rec["manifest"]["path"]
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), rec["manifest"]["sha256"])
        m = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(m["exit_code"], 0)
        self.assertEqual(m["command"][0], sys.executable)
        self.assertLessEqual(m["started_at"], m["finished_at"])
        self.assertEqual(m["environment"]["python"], platform.python_version())
        self.assertIsInstance(m["environment"]["packages"], dict)
        self.assertEqual(m["approvals"]["execution"]["version"], 1)
        self.assertEqual(m["approvals"]["methodology"]["state"], "approved")
        self.assertIn("data.csv", m["inputs"])
        self.assertEqual(m["outputs"]["results.json"], hashlib.sha256(b"{}").hexdigest())
        self.assertIn("git", m)  # None outside a repository
        # A second run in the same second gets its own files.
        code, _ = self.run_cli("--", sys.executable, "-c", "pass")
        self.assertEqual(len(list((self.dir / "runs").glob("*.json"))), 2)

    def test_relative_interpreter_path_runs_from_the_project(self):
        self.through_methodology()
        self.approve("execution")
        from sra import runmanifest
        (self.dir / "bin").mkdir()
        cmd = runmanifest.resolve_command(["bin/tool.exe", "x"], self.dir)
        self.assertEqual(cmd, ["bin/tool.exe", "x"])  # nothing there: left alone
        self.file("bin/tool.exe", "")
        self.assertEqual(runmanifest.resolve_command(["bin/tool", "x"], self.dir)[0],
                         str((self.dir / "bin" / "tool.exe").resolve()))
        self.assertEqual(runmanifest.python_prefix(["py", "-3.11", "a.py"]), ["py", "-3.11"])
        self.assertIsNone(runmanifest.python_prefix(["Rscript", "a.R"]))

    def test_missing_evidence_counts_as_a_failed_run(self):
        self.through_methodology()
        self.approve("execution")
        code, out = self.run_cli("--evidence", "never.json", "--", sys.executable, "-c", "pass")
        self.assertEqual(code, 1)
        self.assertIn("do not exist", out)

    def test_options_still_parse_around_the_separator(self):
        code, out = self.run_cli()
        self.assertEqual(code, 2)
        self.assertIn("needs a command after --", out)


class FreeValidationTests(Base):
    def test_report_check_is_never_blocked(self):
        proposal = SKILL / "examples" / "nlp-graph-theory" / "research_proposal.json"
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cli.main(["--no-cache", "report", "--input", str(proposal), "--check", "--project", str(self.dir)])
        self.assertEqual(code, 0, out.getvalue())
        self.assertIn("note: validation only", out.getvalue())


class HookTests(Base):
    def setUp(self):
        super().setUp()
        self.file("analysis.py", "print('x')")
        self.outside = Path(self._tmp.name) / "elsewhere"
        self.outside.mkdir()
        (self.outside / "tool.py").write_text("", encoding="utf-8")

    def decide(self, command, cwd=None):
        return hook.decide(command, Path(cwd or self.dir))

    def test_blocks_running_a_project_script_directly(self):
        for command in ("python analysis.py", "py -3.11 analysis.py", ".venv/Scripts/python.exe -u analysis.py",
                        '& "C:\\Python\\python.exe" analysis.py', "cd . && python analysis.py",
                        f'python "{self.dir / "analysis.py"}"'):
            reason = self.decide(command)
            self.assertIsNotNone(reason, command)
            self.assertIn("project run", reason)
            self.assertIn("not authorized", reason)
        # A `cd` earlier in the command line moves where the script is looked up.
        self.assertIsNotNone(self.decide(f'cd "{self.dir}" && python analysis.py', self.outside))
        self.assertIsNotNone(self.decide(f"Set-Location '{self.dir}'; python analysis.py", self.outside))
        self.assertIsNone(self.decide(f'cd "{self.outside}" && python analysis.py'))
        # Even when authorized, the run must go through `project run` so it is recorded.
        self.through_methodology()
        self.approve("execution")
        self.assertIn("must still be recorded", self.decide("python analysis.py"))

    def test_leaves_ordinary_work_alone(self):
        for command in ("cat analysis.py", "type analysis.py", "python -c \"print(1)\"", "python -m unittest",
                        "git diff analysis.py", "grep -n x analysis.py", "python missing.py",
                        f'python "{SRA}" project run --project "{self.dir}" -- python analysis.py',
                        f'python "{SRA}" manuscript check'):
            self.assertIsNone(self.decide(command), command)
        self.assertIsNone(self.decide("python tool.py", self.outside))  # not inside a project

    def test_hook_protocol_and_fail_open(self):
        def run(payload):
            r = subprocess.run([sys.executable, str(SRA), "hook"], input=payload, capture_output=True,
                               text=True, encoding="utf-8", timeout=60)
            return r.returncode, r.stdout

        event = {"tool_name": "Bash", "tool_input": {"command": "python analysis.py"}, "cwd": str(self.dir)}
        code, out = run(json.dumps(event))
        self.assertEqual(code, 0)  # never exit 2: a missing hook script would also exit 2 and block everything
        decision = json.loads(out)["hookSpecificOutput"]
        self.assertEqual(decision["permissionDecision"], "deny")
        self.assertIn("Blocked", decision["permissionDecisionReason"])
        self.assertEqual(run(json.dumps({**event, "tool_name": "Read"})), (0, ""))
        self.assertEqual(run("not json"), (0, ""))  # a broken event never blocks work
        ok = {**event, "tool_input": {"command": "cat analysis.py"}}
        self.assertEqual(run(json.dumps(ok)), (0, ""))

    def test_installed_hook_fails_open(self):
        """The settings command must not block work when the hook script cannot be found."""
        settings = json.loads((SRA.parents[4] / ".claude" / "settings.json").read_text(encoding="utf-8"))
        command = settings["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
        self.assertIn("sra.py", command)
        self.assertTrue(command.rstrip().endswith("|| true"), command)


if __name__ == "__main__":
    unittest.main()
