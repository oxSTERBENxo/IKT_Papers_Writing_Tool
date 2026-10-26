"""Human decision checkpoints: approval enforcement, invalidation after a
methodology change, and resuming a project from a new session (a fresh
Python process that knows nothing but the project folder)."""
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import helpers  # noqa: F401  (puts scripts/ on sys.path)

from sra import checkpoints as cp
from sra import cli

SKILL = Path(__file__).resolve().parents[1]
SRA = SKILL / "scripts" / "sra.py"
EXAMPLE_PROPOSAL = SKILL / "examples" / "nlp-graph-theory" / "research_proposal.json"
SAID = "Yes, approved."


class ProjectCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name) / "proj"
        self.project = cp.init(self.dir, "Test project", "Is a BoW MLP still competitive?")

    def tearDown(self):
        self._tmp.cleanup()

    def reload(self):
        self.project = cp.load(self.dir)
        return self.project

    def state(self, gate):
        return cp.evaluate(self.reload())[gate]["state"]

    def plan(self, text="H1: MLP within 1 point. 5 seeds."):
        f = self.dir / "ANALYSIS_PLAN.md"
        f.write_text(text, encoding="utf-8")
        return str(f)

    def pass_gate(self, gate, summary=None, **kw):
        kw = {k: v for k, v in kw.items() if v is not None}
        if gate == "results":  # reviewed on findings, limitations and interpretation, from a completed run
            out = self.dir / "results.json"
            out.write_text('{"acc": 0.9}', encoding="utf-8")
            kw = {"findings": ["accuracy 0.9"], "limitations": ["one dataset"], "interpretation": "MLP holds",
                  "artifacts": [str(out)], **kw}
        v = cp.propose(self.reload(), gate, summary or f"{gate} proposal", **kw)
        cp.approve(self.reload(), gate, v["version"], SAID)
        if gate == "execution":  # authorization, then evidence that the run finished
            evidence = self.dir / "run_output.txt"
            evidence.write_text("done", encoding="utf-8")
            cp.record_completion(self.reload(), "execution", "python analysis.py", 0, [str(evidence)])
        return v

    def approve_through(self, last, artifacts=None):
        for gate in cp.DEFAULT_GATES[: cp.DEFAULT_GATES.index(last) + 1]:
            self.pass_gate(gate, artifacts=(artifacts or {}).get(gate))


class ApprovalEnforcementTests(ProjectCase):
    def test_new_project_starts_with_nothing_approved(self):
        states = cp.evaluate(self.project)
        self.assertEqual({s["state"] for s in states.values()}, {cp.NOT_STARTED})
        self.assertIn("checkpoint propose scope", cp.next_step(self.project))
        self.assertEqual(len(cp.require(self.project, ["scope"])), 1)

    def test_a_proposal_is_not_an_approval(self):
        cp.propose(self.project, "scope", "Undergraduate, 8 GB GPU, 8 weeks")
        self.assertEqual(self.state("scope"), cp.AWAITING)
        self.assertTrue(cp.require(self.project, ["scope"]))
        self.assertIn("Waiting for the user", cp.next_step(self.project))

    def test_approval_needs_the_users_words_and_the_version_they_saw(self):
        cp.propose(self.project, "scope", "v1")
        for said in ("", "   ", None):
            with self.assertRaisesRegex(cp.CheckpointError, "user's own words"):
                cp.approve(self.reload(), "scope", 1, said)
        with self.assertRaisesRegex(cp.CheckpointError, "needs --version"):
            cp.approve(self.reload(), "scope", None, SAID)
        cp.request_revision(self.reload(), "scope", "Make it 6 weeks", "time budget 6 weeks")
        cp.propose(self.reload(), "scope", "v2: 6 weeks")
        with self.assertRaisesRegex(cp.CheckpointError, "not the current version"):
            cp.approve(self.reload(), "scope", 1, SAID)  # the user saw v1; v2 is on disk
        cp.approve(self.reload(), "scope", 2, SAID)
        self.assertEqual(self.state("scope"), cp.APPROVED)

    def test_later_gates_cannot_be_proposed_or_approved_out_of_order(self):
        with self.assertRaisesRegex(cp.CheckpointError, "'scope' is not started"):
            cp.propose(self.project, "methodology", "plan")
        self.pass_gate("scope")
        with self.assertRaisesRegex(cp.CheckpointError, "'question' is not started"):
            cp.propose(self.reload(), "methodology", "plan")
        cp.propose(self.reload(), "question", "Q1")
        # Scope is reopened while the question waits: the question can no longer be approved.
        cp.propose(self.reload(), "scope", "scope v2: 4 weeks")
        with self.assertRaisesRegex(cp.CheckpointError, "earlier gate 'scope'"):
            cp.approve(self.reload(), "question", 1, SAID)
        self.assertIn("cannot be approved until 'scope'", cp.evaluate(self.reload())["question"]["reasons"][0])

    def test_rejection_blocks_until_a_new_version_is_approved(self):
        self.pass_gate("scope")
        cp.propose(self.reload(), "question", "Q1: is a text graph necessary at all?")
        cp.reject(self.reload(), "question", "No, that one is already answered.", "already answered by Galke")
        self.assertEqual(self.state("question"), cp.REJECTED)
        with self.assertRaisesRegex(cp.CheckpointError, "rejected"):
            cp.approve(self.reload(), "question", 1, SAID)
        self.assertIn("already answered by Galke", cp.next_step(self.reload()))
        cp.propose(self.reload(), "question", "Q2: does the MLP still match post-2022 graph models?",
                   addresses="rejection of v1")
        cp.approve(self.reload(), "question", 2, "Q2 is good, go with it.")
        self.assertEqual(cp.require(self.reload(), ["scope", "question"]), [])

    def test_revision_request_is_recorded_and_shown_until_addressed(self):
        self.pass_gate("scope")
        self.pass_gate("question")
        cp.propose(self.reload(), "methodology", "5 seeds, accuracy only")
        cp.request_revision(self.reload(), "methodology", "Add macro-F1 and use 10 seeds.", "macro-F1, 10 seeds")
        self.assertEqual(self.state("methodology"), cp.REVISION)
        self.assertIn("macro-F1, 10 seeds", cp.next_step(self.project))
        v2 = cp.propose(self.reload(), "methodology", "10 seeds, accuracy and macro-F1",
                        addresses="revision request on v1")
        self.assertEqual(v2["version"], 2)
        shown = "\n".join(cp.show_lines(self.reload(), "methodology"))
        self.assertIn("Addresses: revision request on v1", shown)
        self.assertIn('"Add macro-F1 and use 10 seeds."', shown)

    def test_identical_reproposal_is_refused(self):
        cp.propose(self.project, "scope", "same")
        with self.assertRaisesRegex(cp.CheckpointError, "exactly this content"):
            cp.propose(self.reload(), "scope", "same")

    def test_file_edited_between_proposal_and_approval_cannot_be_approved(self):
        self.approve_through("question")
        plan = self.plan()
        cp.propose(self.reload(), "methodology", "plan v1", artifacts=[plan])
        Path(plan).write_text("H1 changed after the user read it", encoding="utf-8")
        with self.assertRaisesRegex(cp.CheckpointError, "changed since this version was proposed"):
            cp.approve(self.reload(), "methodology", 1, SAID)

    def test_report_for_a_project_is_refused_without_the_gates_it_needs(self):
        def run(*argv):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = cli.main(["--no-cache", "report", "--input", str(EXAMPLE_PROPOSAL),
                                 "--project", str(self.dir), *argv])
            return code, out.getvalue()

        out_dir = Path(self._tmp.name) / "rendered"
        render = ("--out-dir", str(out_dir))
        code, out = run(*render)
        self.assertEqual(code, 3)
        self.assertIn("BLOCKED by project checkpoints", out)
        self.approve_through("scope")
        self.assertEqual(run(*render)[0], 3)  # a research_proposal also needs the question approved
        self.assertFalse(out_dir.exists())
        self.pass_gate("question")
        code, out = run(*render)
        self.assertEqual(code, 0, out)
        self.assertTrue(list(out_dir.glob("*.md")))


class InvalidationTests(ProjectCase):
    def test_changed_methodology_needs_fresh_approval_and_blocks_execution(self):
        self.approve_through("execution")
        self.assertEqual(cp.require(self.reload(), ["methodology", "execution"]), [])
        v2 = cp.propose(self.reload(), "methodology", "switch to an entity-disjoint split")
        self.assertEqual(v2["invalidated"], ["execution"])
        states = cp.evaluate(self.reload())
        self.assertEqual(states["methodology"]["state"], cp.AWAITING)
        self.assertTrue(states["methodology"].get("supersedes_approval"))
        self.assertEqual(states["execution"]["state"], cp.STALE)
        self.assertIn("earlier gate 'methodology' is awaiting review", states["execution"]["reasons"][0])
        self.assertEqual(len(cp.require(self.project, ["execution"])), 1)
        self.assertEqual([e["event"] for e in self.project["log"][-2:]], ["proposed", "invalidated"])

        # Approving the new methodology is not enough: execution was approved for the old one.
        cp.approve(self.reload(), "methodology", 2, "OK, use the entity-disjoint split.")
        self.assertEqual(self.state("execution"), cp.STALE)
        self.assertIn("changed since this approval", cp.evaluate(self.project)["execution"]["reasons"][0])
        self.assertIn("still holds", cp.next_step(self.project))
        cp.approve(self.reload(), "execution", 1, "Same run plan is fine, go.")
        self.assertEqual(cp.require(self.reload(), ["execution"]), [])

    def test_editing_the_approved_plan_file_invalidates_it_and_everything_after(self):
        plan = self.plan()
        self.approve_through("execution", artifacts={"methodology": [plan]})
        Path(plan).write_text("H1: MLP within 1 point. 3 seeds.", encoding="utf-8")  # silent edit
        states = cp.evaluate(self.reload())
        self.assertEqual(states["methodology"]["state"], cp.STALE)
        self.assertIn("ANALYSIS_PLAN.md", states["methodology"]["reasons"][0])
        self.assertEqual(states["execution"]["state"], cp.STALE)
        self.assertIn("propose it again", cp.next_step(self.project))
        with self.assertRaisesRegex(cp.CheckpointError, "changed since"):
            cp.approve(self.reload(), "methodology", 1, SAID)  # the old version cannot be re-approved
        # Putting the approved text back restores the approval: approvals follow content, not time.
        Path(plan).write_text("H1: MLP within 1 point. 5 seeds.", encoding="utf-8")
        self.assertEqual(cp.require(self.reload(), ["execution"]), [])

    def test_deleting_an_attached_file_invalidates(self):
        plan = self.plan()
        self.approve_through("methodology", artifacts={"methodology": [plan]})
        os.remove(plan)
        self.assertEqual(self.state("methodology"), cp.STALE)
        self.assertIn("(missing)", cp.evaluate(self.project)["methodology"]["reasons"][0])

    def test_reopening_the_question_invalidates_all_later_gates(self):
        self.approve_through("results")
        cp.request_revision(self.reload(), "question", "Actually, restrict it to short texts.", "short texts only")
        states = cp.evaluate(self.reload())
        self.assertEqual(states["question"]["state"], cp.REVISION)
        for gate in ("methodology", "execution", "results"):
            self.assertEqual(states[gate]["state"], cp.STALE, gate)
        self.assertEqual(states["scope"]["state"], cp.APPROVED)

    def test_rejecting_an_approved_gate_revokes_it(self):
        self.approve_through("methodology")
        cp.reject(self.reload(), "methodology", "On reflection, no: the baselines are too weak.")
        self.assertEqual(self.state("methodology"), cp.REJECTED)
        self.assertTrue(cp.require(self.project, ["methodology"]))


class ResumeTests(unittest.TestCase):
    """Each CLI call is a separate process: nothing survives except project.json."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def sra(self, *args, env=None, cwd=None):
        full_env = {k: v for k, v in os.environ.items() if k != "SRA_PROJECT"}
        full_env.update({"PYTHONIOENCODING": "utf-8", **(env or {})})
        r = subprocess.run([sys.executable, str(SRA), "--no-cache", *args], cwd=cwd or self.root,
                           capture_output=True, text=True, encoding="utf-8", env=full_env, timeout=60)
        return r.returncode, r.stdout + r.stderr

    def test_a_new_session_sees_the_pending_decision_and_continues(self):
        # Session 1: start the project, settle the scope, propose a question, stop for the user.
        code, out = self.sra("project", "init", "--name", "BoW vs graphs", "--question", "Is a BoW MLP enough?")
        self.assertEqual(code, 0, out)
        proj = self.root / "research-projects" / "bow-vs-graphs"
        self.assertTrue((proj / "project.json").is_file())
        p = ["--project", str(proj)]
        self.assertEqual(self.sra("checkpoint", "propose", "scope", "--summary", "8 GB GPU, 8 weeks", *p)[0], 0)
        self.assertEqual(self.sra("checkpoint", "approve", "scope", "--version", "1", "--said", "yes", *p)[0], 0)
        code, out = self.sra("checkpoint", "propose", "question", "--summary", "Q2: MLP vs post-2022 graph models",
                             "--item", "type: replication + extension", "--risk", "Abdalla 2023 not yet read",
                             "--option", "Approve Q2 (Recommended)", "--option", "Switch to Q1: BoW only", *p)
        self.assertEqual(code, 0, out)
        self.assertIn("stop until they reply", out)

        # Session 2: knows only that there is a project somewhere under the working folder.
        code, out = self.sra("project", "list")
        self.assertEqual(code, 0, out)
        self.assertIn("BoW vs graphs: 1/6 gates settled", out)
        code, out = self.sra("project", "status", *p)
        self.assertEqual(code, 0, out)
        self.assertRegex(out, r"scope\s+APPROVED")
        self.assertRegex(out, r"question\s+AWAITING REVIEW\s+v1")
        self.assertIn("Next: Waiting for the user to review 'question' v1", out)
        code, out = self.sra("checkpoint", "show", "question", *p)
        self.assertIn("Q2: MLP vs post-2022 graph models", out)
        self.assertIn("Abdalla 2023 not yet read", out)
        self.assertIn("2. Switch to Q1: BoW only", out)  # "option 2" can be resolved in a later session
        code, out = self.sra("checkpoint", "require", "methodology", *p)
        self.assertEqual(code, 3, out)
        self.assertIn("BLOCKED", out)

        # Session 3: the user's reply arrives; it is recorded and work continues.
        code, out = self.sra("checkpoint", "approve", "question", "--version", "1", "--said", "Go with Q2.", *p)
        self.assertEqual(code, 0, out)
        status = json.loads(self.sra("project", "status", "--json", *p)[1])
        self.assertEqual(status["gates"]["question"]["state"], "approved")
        self.assertEqual(status["gates"]["question"]["decision"]["said"], "Go with Q2.")
        self.assertIn("'methodology'", status["next"])

    def test_project_is_found_from_env_or_working_folder(self):
        proj = self.root / "p"
        self.sra("project", "init", "--name", "x", "--dir", str(proj))
        self.assertIn("Project: x", self.sra("project", "status", env={"SRA_PROJECT": str(proj)})[1])
        self.assertIn("Project: x", self.sra("project", "status", cwd=proj)[1])
        code, out = self.sra("project", "status")  # root has no project.json
        self.assertEqual(code, 2)
        self.assertIn("project list", out)

    def test_state_file_is_clean_json_with_the_full_history(self):
        proj = self.root / "p"
        p = ["--project", str(proj)]
        self.sra("project", "init", "--name", "x", "--dir", str(proj))
        self.sra("checkpoint", "propose", "scope", "--summary", "a", *p)
        self.sra("checkpoint", "revise", "scope", "--said", "make it 6 weeks", "--request", "6 weeks", *p)
        self.sra("checkpoint", "propose", "scope", "--summary", "b", "--addresses", "6 weeks", *p)
        data = json.loads((proj / "project.json").read_text(encoding="utf-8"))
        self.assertFalse([k for k in data if k.startswith("_")])
        self.assertFalse(list(proj.glob("*.tmp")))
        self.assertEqual([v["summary"] for v in data["checkpoints"]["scope"]["versions"]], ["a", "b"])
        self.assertEqual(data["checkpoints"]["scope"]["decisions"][0]["said"], "make it 6 weeks")
        self.assertEqual([e["event"] for e in data["log"]],
                         ["project_created", "proposed", "revision_requested", "proposed"])

    def test_cli_refusals_exit_nonzero_with_a_reason(self):
        proj = self.root / "p"
        p = ["--project", str(proj)]
        self.sra("project", "init", "--name", "x", "--dir", str(proj))
        self.sra("checkpoint", "propose", "scope", "--summary", "a", *p)
        code, out = self.sra("checkpoint", "approve", "scope", "--version", "1", *p)
        self.assertEqual(code, 2)
        self.assertIn("user's own words", out)
        code, out = self.sra("project", "init", "--name", "x", "--dir", str(proj))
        self.assertEqual(code, 2)
        self.assertIn("already exists", out)


if __name__ == "__main__":
    unittest.main()
