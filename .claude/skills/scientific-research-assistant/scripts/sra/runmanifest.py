"""A small, structured record of one `project run`: what ran, where, with what, under which approval.

Written next to the run log as runs/run-<stamp>.json. Its hash is stored in the completion record, so a
later edit to the manifest is detectable. This is deliberately minimal: no package snapshots, no containers.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import platform
import re
import subprocess
from pathlib import Path

SCHEMA = 1
PYTHON = re.compile(r"^(python[\d.]*|pythonw|py|pypy3?)(\.exe)?$", re.I)
# Runs inside the project's own interpreter, so the versions are the ones the analysis actually imports.
PROBE = ("import importlib.metadata as m, json, platform, sys\n"
         "pk = {}\n"
         "for d in m.distributions():\n"
         "    n = (d.metadata['Name'] or '').strip()\n"
         "    if n: pk[n.lower()] = d.version\n"
         "print(json.dumps({'python': platform.python_version(), 'implementation': platform.python_implementation(),"
         " 'executable': sys.executable, 'packages': dict(sorted(pk.items()))}))")


def utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def resolve_command(command: list[str], base: Path) -> list[str]:
    """Windows does not look up a relative program path (`.venv/Scripts/python.exe`) in the child's cwd."""
    if not command:
        return command
    head = command[0]
    if ("/" in head or "\\" in head) and not Path(head).is_absolute():
        for cand in (base / head, base / (head + ".exe")):
            if cand.is_file():
                return [str(cand.resolve())] + command[1:]
    return command


def python_prefix(command: list[str]) -> list[str] | None:
    """The interpreter part of a Python command (`py -3.11`, `.venv/Scripts/python.exe -u`), else None."""
    if not command or not PYTHON.match(Path(command[0]).name):
        return None
    prefix = [command[0]]
    if Path(command[0]).stem.lower() == "py" and len(command) > 1 and re.match(r"^-\d", command[1]):
        prefix.append(command[1])
    return prefix


def environment(command: list[str], base: Path, timeout: float = 30) -> dict:
    prefix = python_prefix(command)
    env = {"os": platform.platform(), "machine": platform.machine(), "sra_python": platform.python_version()}
    if prefix is None:
        env["interpreter"] = command[0] if command else None
        env["note"] = "not a Python command: interpreter and package versions were not probed"
        return env
    try:
        out = subprocess.run(prefix + ["-c", PROBE], cwd=base, capture_output=True, text=True, timeout=timeout)
        env.update(json.loads(out.stdout.strip().splitlines()[-1]))
    except (OSError, ValueError, IndexError, subprocess.TimeoutExpired) as exc:
        env["note"] = f"could not probe the interpreter: {type(exc).__name__}"
    return env


def git_state(base: Path) -> dict | None:
    def git(*args):
        r = subprocess.run(["git", "-C", str(base), *args], capture_output=True, text=True, timeout=20)
        return r.stdout.strip() if r.returncode == 0 else None
    try:
        rev = git("rev-parse", "HEAD")
        if rev is None:
            return None
        changed = (git("status", "--porcelain", "--", ".") or "").splitlines()
    except (OSError, subprocess.TimeoutExpired):
        return None
    return {"revision": rev, "dirty": bool(changed), "uncommitted_in_project": changed[:50]}


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def hashes(paths, base: Path) -> dict:
    out = {}
    for p in paths or []:
        full = Path(p) if Path(p).is_absolute() else base / p
        try:
            key = full.resolve().relative_to(base.resolve()).as_posix()
        except ValueError:
            key = str(full)
        out[key] = file_hash(full) if full.is_file() else None
    return out


def write(path: Path, manifest: dict) -> str:
    manifest = {"schema": SCHEMA, **manifest}
    data = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    path.write_bytes(data)  # bytes, so Windows newline translation cannot change what was hashed
    return hashlib.sha256(data).hexdigest()
