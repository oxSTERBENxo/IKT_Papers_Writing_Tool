"""Claude Code PreToolUse hook: enforce the checkpoints at the shell.

When Claude runs a shell command that executes a script inside a research project folder (one with a
`project.json`), the command is blocked. Running it through `sra.py project run` instead checks the user's
methodology and execution approvals and records the completion evidence. Other commands are never touched:
reading files, searches, drafts and checks need no approval.

The hook is installed in .claude/settings.json:

    {"hooks": {"PreToolUse": [{"matcher": "Bash|PowerShell",
       "hooks": [{"type": "command", "command": "python <skill>/scripts/sra.py hook"}]}]}}

A block is a JSON `permissionDecision: "deny"` on stdout with exit code 0; the reason is shown to Claude.
Exit code 2 is never used, because Python itself exits 2 when it cannot find its script: a mistyped hook path
would otherwise block every shell command. Any internal error lets the command through (fail open), and the
settings command ends in `|| true` for the same reason. The hook is a guard rail for Claude's own commands,
not a sandbox: see the limitations in references/checkpoints.md.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import sys
from pathlib import Path

from . import checkpoints

INTERPRETERS = re.compile(r"^(python[\d.]*|pythonw|py|pypy3?|rscript|julia|node|bash|sh|zsh|pwsh|powershell|"
                          r"uv|poetry|conda|pipenv)(\.exe)?$", re.I)
RUNNER_WORDS = {"run", "exec", "-m"}  # uv run x.py, poetry run python x.py
SCRIPT = re.compile(r"\.(py|r|jl|js|sh|ps1|ipynb)$", re.I)
SEPARATORS = re.compile(r"\|\||&&|;|\||\n")


def _tokens(segment: str) -> list[str]:
    try:
        return shlex.split(segment, posix=False)
    except ValueError:
        return segment.split()


def scripts_executed(command: str, cwd: Path) -> list[Path]:
    """Script files that a shell command would execute (not merely read)."""
    found = []
    for segment in SEPARATORS.split(command):
        toks = [t.strip("\"'") for t in _tokens(segment.strip())]
        while toks and (toks[0] in ("&", ".", "call", "start", "time", "env") or re.match(r"^\w+=", toks[0])):
            toks = toks[1:]
        if not toks:
            continue
        if toks[0].lower() in ("cd", "set-location", "sl", "pushd", "chdir") and len(toks) > 1:
            target = Path(toks[-1].strip("\"'"))
            cwd = target if target.is_absolute() else cwd / target  # later segments run there
            continue
        head = Path(toks[0]).name
        candidates = []
        if INTERPRETERS.match(head):
            rest = toks[1:]
            if rest and rest[0] in ("-c", "-m") and head.lower().startswith(("python", "py")):
                continue  # inline code or a module, not a project script
            candidates = [t for t in rest if SCRIPT.search(t)][:1]
        elif SCRIPT.search(toks[0]):
            candidates = [toks[0]]  # ./run.sh, .\analysis.ps1
        for c in candidates:
            p = Path(c)
            p = p if p.is_absolute() else cwd / p
            if p.is_file():
                found.append(p.resolve())
    return found


def decide(command: str, cwd: Path) -> str | None:
    """The reason to block, or None to let the command run."""
    if re.search(r"sra\.py[\"']?\s+(--\S+\s+)*project\s+run\b", command):
        return None  # the authorized route checks approvals itself
    skill_scripts = Path(__file__).resolve().parents[1]
    for script in scripts_executed(command, cwd):
        if skill_scripts in script.parents:
            continue
        proj = checkpoints.find_project_for(script.parent)
        if proj is None:
            continue
        project = checkpoints.load(proj)
        problems = checkpoints.require(project, [g for g in ("methodology", "execution") if g in project["gates"]])
        status = ("its methodology and execution are approved, but the run must still be recorded"
                  if not problems else "not authorized: " + "; ".join(problems))
        return (f"Blocked: {script.name} belongs to the research project '{project['name']}' ({proj.parent}), "
                f"and {status}. Run it with\n  python \"{skill_scripts / 'sra.py'}\" project run --project "
                f"\"{proj.parent}\" --evidence <output files> -- <the same command>\nso the user's approvals are "
                "checked and the run is recorded. If it is not authorized, ask the user first.")
    return None


def main(stdin=None) -> int:
    try:
        event = json.loads((stdin or sys.stdin).read() or "{}")
        if event.get("tool_name") not in ("Bash", "PowerShell"):
            return 0
        command = (event.get("tool_input") or {}).get("command") or ""
        cwd = Path(event.get("cwd") or os.getcwd())
        reason = decide(command, cwd)
    except Exception:  # noqa: BLE001 - fail open
        return 0
    if reason:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                                 "permissionDecisionReason": reason}}))
    return 0
