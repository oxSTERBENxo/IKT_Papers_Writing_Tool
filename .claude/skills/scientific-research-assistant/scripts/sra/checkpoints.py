"""Human decision checkpoints for a research project.

A project is a folder with one `project.json`. The research moves through
ordered gates: scope -> question -> methodology -> execution -> results ->
manuscript. At each gate Claude proposes a version, the user approves it,
rejects it or asks for a revision. Only a satisfied, still-current gate
unlocks the next one.

An approval is tied to one exact version (a content hash) and to the hashes
of the files attached to it. It stops counting, and so do the approvals of
every later gate, when:
- a new version of the gate is proposed (for example a changed methodology);
- an attached file is edited after approval;
- an earlier gate is re-proposed, rejected or sent back for revision.

Two things are kept apart at the execution gate:
- **authorization**, which is the user's approval to run;
- **completion**, which is evidence that a run under that authorization finished: the command, its exit
  code and output hashes, recorded by `project run`.

The results gate needs both. Execution may be marked not applicable, with a reason and the user's words,
for work that runs nothing. That never authorizes computation.

The state is plain JSON, so any later session can resume from it.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
from pathlib import Path

SCHEMA_VERSION = 2
READABLE_SCHEMAS = (1, 2)
PROJECT_FILE = "project.json"
MARKER = "sra_project"

GATES = {
    "scope": "Field, constraints (experience, hardware, time), research mode and the defaults assumed.",
    "question": "The research question to pursue, its type, its go / conditional-go decision and the closest work.",
    "methodology": "Hypothesis, falsification rule, datasets, splits, baselines, metrics, seeds and statistics.",
    "execution": "What will be downloaded and run, on what hardware, for how long, at what cost.",
    "results": "Findings, limitations and their interpretation, from a completed run, before any write-up.",
    "manuscript": "The paper to finalise: text, numbers traced to results, verified references, figures.",
}
DEFAULT_GATES = list(GATES)
SCHEMA1_DEFAULT_GATES = DEFAULT_GATES[:5]
NA_GATES = {"execution"}  # gates that may be marked not applicable, with a reason
COMPLETION_GATES = {"execution"}  # gates whose approval is an authorization that a run must complete

# Gates that must be approved before a report of each type is rendered for a project (validation is free).
REPORT_GATES = {
    "literature_review": ["scope"],
    "opportunity_report": ["scope"],
    "reproducibility_report": ["scope"],
    "research_proposal": ["scope", "question"],
}

# Effective states.
NOT_STARTED, AWAITING, APPROVED, REJECTED, REVISION, STALE, NOT_APPLICABLE = (
    "not_started", "awaiting_review", "approved", "rejected", "revision_requested", "stale", "not_applicable")
SATISFIED = (APPROVED, NOT_APPLICABLE)


class CheckpointError(ValueError):
    """A request that the checkpoint rules refuse. The message says why."""


def now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def content_hash(content: dict) -> str:
    return hashlib.sha256(json.dumps(content, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def short(h: str | None) -> str:
    return (h or "")[:10]


def _words(state: str) -> str:
    return state.replace("_", " ")


# ---------------------------------------------------------------- loading and saving

def project_file(path: str | os.PathLike) -> Path:
    p = Path(path)
    return p if p.name == PROJECT_FILE else p / PROJECT_FILE


def resolve(path: str | None) -> Path:
    """The project.json to use: --project, else SRA_PROJECT, else the current folder."""
    explicit = path or os.environ.get("SRA_PROJECT")
    if explicit:
        f = project_file(explicit)
        if not f.is_file():
            raise CheckpointError(f"no {PROJECT_FILE} at {f}. Create one with `project init`, or find "
                                  "existing ones with `project list`.")
        return f
    if project_file(".").is_file():
        return project_file(".")
    raise CheckpointError(f"no project given and no {PROJECT_FILE} in the current folder. Pass --project, "
                          "set SRA_PROJECT, or run `project list`.")


def find_project_for(path: str | os.PathLike) -> Path | None:
    """The project.json of the project folder that contains `path`, if any."""
    p = Path(path).resolve()
    for d in [p] + list(p.parents):
        f = d / PROJECT_FILE
        if f.is_file():
            try:
                if json.loads(f.read_text(encoding="utf-8-sig")).get(MARKER) in READABLE_SCHEMAS:
                    return f
            except (OSError, ValueError):
                return None
    return None


def _upgrade(data: dict) -> None:
    """Schema 1 had five gates. A project that used all five gains the manuscript gate."""
    if data.get(MARKER) == 1:
        if data["gates"] == SCHEMA1_DEFAULT_GATES:
            data["gates"] = list(DEFAULT_GATES)
            data["checkpoints"]["manuscript"] = {"versions": [], "decisions": []}
        data[MARKER] = SCHEMA_VERSION
        data["log"].append({"at": now(), "event": "schema_upgraded", "gate": None, "version": None,
                            "detail": "schema 1 -> 2: manuscript gate added" if "manuscript" in data["gates"]
                            else "schema 1 -> 2"})
    for gate in data["gates"]:
        data["checkpoints"][gate].setdefault("completions", [])


def load(path: str | os.PathLike) -> dict:
    f = project_file(path)
    data = json.loads(f.read_text(encoding="utf-8-sig"))
    if data.get(MARKER) not in READABLE_SCHEMAS:
        raise CheckpointError(f"{f} is not a research project file this toolkit can read")
    _upgrade(data)
    data["_file"] = str(f.resolve())
    return data


def save(project: dict) -> None:
    f = Path(project["_file"])
    body = {k: v for k, v in project.items() if not k.startswith("_")}
    body["updated"] = now()
    tmp = f.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(body, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, f)  # atomic: an interrupted write never leaves a half-written project


def init(directory: str | os.PathLike, name: str, question: str = "", gates: list[str] | None = None) -> dict:
    gates = gates or list(DEFAULT_GATES)
    unknown = [g for g in gates if g not in GATES]
    if unknown:
        raise CheckpointError(f"unknown gate(s) {unknown}; choose from {DEFAULT_GATES}")
    if len(set(gates)) != len(gates):
        raise CheckpointError("each gate may appear once")
    gates = [g for g in DEFAULT_GATES if g in gates]  # keep the research order
    d = Path(directory)
    f = d / PROJECT_FILE
    if f.exists():
        raise CheckpointError(f"{f} already exists; resume it with `project status --project {d}`")
    d.mkdir(parents=True, exist_ok=True)
    project = {MARKER: SCHEMA_VERSION, "name": name, "question": question, "created": now(), "updated": now(),
               "gates": gates,
               "checkpoints": {g: {"versions": [], "decisions": [], "completions": []} for g in gates},
               "log": [], "_file": str(f.resolve())}
    _log(project, "project_created", None, None, name)
    save(project)
    return project


def find_projects(root: str | os.PathLike = ".", max_depth: int = 4) -> list[Path]:
    root = Path(root)
    skip = {".git", ".venv", "venv", "node_modules", "__pycache__", ".idea"}
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        depth = len(Path(dirpath).relative_to(root).parts)
        dirnames[:] = [d for d in dirnames if d not in skip and depth < max_depth]
        if PROJECT_FILE in filenames:
            f = Path(dirpath) / PROJECT_FILE
            try:
                if json.loads(f.read_text(encoding="utf-8-sig")).get(MARKER) in READABLE_SCHEMAS:
                    found.append(f)
            except (OSError, ValueError):
                pass
    return sorted(found)


def _log(project: dict, event: str, gate: str | None, version: int | None, detail: str = "") -> None:
    project["log"].append({"at": now(), "event": event, "gate": gate, "version": version, "detail": detail})


def _gate(project: dict, gate: str) -> dict:
    if gate not in project["gates"]:
        raise CheckpointError(f"'{gate}' is not a gate of this project; its gates are {project['gates']}")
    return project["checkpoints"][gate]


def base_dir(project: dict) -> Path:
    return Path(project["_file"]).parent


def _artifact_key(project: dict, path: str | os.PathLike) -> tuple[str, Path]:
    p = Path(path)
    full = (p if p.is_absolute() else Path.cwd() / p).resolve()
    if not full.is_file():
        raise CheckpointError(f"file not found: {path}")
    try:
        return full.relative_to(base_dir(project).resolve()).as_posix(), full
    except ValueError:
        return str(full), full


def hash_files(project: dict, paths) -> dict:
    out = {}
    for a in paths or []:
        key, full = _artifact_key(project, a)
        out[key] = file_hash(full)
    return out


def _artifact_path(project: dict, key: str) -> Path:
    p = Path(key)
    return p if p.is_absolute() else base_dir(project) / p


def changed_files(project: dict, hashes: dict) -> list[str]:
    out = []
    for key, recorded in hashes.items():
        p = _artifact_path(project, key)
        if not p.is_file():
            out.append(f"{key} (missing)")
        elif file_hash(p) != recorded:
            out.append(key)
    return out


def changed_artifacts(project: dict, version: dict) -> list[str]:
    return changed_files(project, version["artifacts"])


# ---------------------------------------------------------------- state evaluation

def _latest_decision(cp: dict, version: int) -> dict | None:
    ds = [d for d in cp["decisions"] if d["version"] == version]
    return ds[-1] if ds else None


def _completion_state(project: dict, gate: str, decision: dict | None) -> dict | None:
    """For an authorized execution gate: is there a successful run under this exact authorization?"""
    if gate not in COMPLETION_GATES:
        return None
    if not decision or decision["action"] != "approved":
        return {"completed": False, "reason": "not authorized", "record": None}
    auth = content_hash(decision)
    runs = [c for c in project["checkpoints"][gate].get("completions", []) if c["authorization"] == auth]
    if not runs:
        return {"completed": False, "reason": "no run recorded under this authorization", "record": None,
                "authorization": auth}
    last = runs[-1]
    if last["exit_code"] != 0:
        return {"completed": False, "reason": f"last run failed (exit {last['exit_code']})", "record": last,
                "authorization": auth}
    changed = changed_files(project, last["evidence"])
    if changed:
        return {"completed": False, "reason": "run evidence changed since the run: " + ", ".join(changed),
                "record": last, "authorization": auth}
    return {"completed": True, "reason": "", "record": last, "authorization": auth, "id": last["id"]}


def evaluate(project: dict) -> dict:
    """Effective state of every gate, in order: {gate: {state, version, hash, reasons, decision, ...}}."""
    result: dict[str, dict] = {}
    for gate in project["gates"]:
        cp = project["checkpoints"][gate]
        upstream = project["gates"][: project["gates"].index(gate)]
        if not cp["versions"]:
            result[gate] = {"state": NOT_STARTED, "version": None, "hash": None, "reasons": [], "decision": None,
                            "artifacts_changed": [], "completion": None}
            continue
        v = cp["versions"][-1]
        dec = _latest_decision(cp, v["version"])
        entry = {"state": AWAITING, "version": v["version"], "hash": v["content_hash"], "reasons": [],
                 "decision": dec, "artifacts_changed": changed_artifacts(project, v), "completion": None,
                 "not_applicable_reason": v.get("not_applicable_reason")}
        if dec and dec["action"] == "rejected":
            entry["state"] = REJECTED
        elif dec and dec["action"] == "revision_requested":
            entry["state"] = REVISION
        elif dec and dec["action"] in ("approved", "not_applicable"):
            reasons = [f"attached file changed after approval: {a}" for a in entry["artifacts_changed"]]
            basis = dec.get("basis", {})
            for up in upstream:
                ur = result[up]
                if ur["state"] not in SATISFIED:
                    reasons.append(f"earlier gate '{up}' is {_words(ur['state'])}")
                elif basis.get(up) != ur["hash"]:
                    reasons.append(f"earlier gate '{up}' changed since this approval (now v{ur['version']})")
                elif f"{up}#completion" in basis and basis[f"{up}#completion"] != (ur["completion"] or {}).get("id"):
                    reasons.append(f"the '{up}' run this was based on is no longer the current successful run")
            entry["reasons"] = reasons
            entry["state"] = STALE if reasons else (APPROVED if dec["action"] == "approved" else NOT_APPLICABLE)
        if entry["state"] == AWAITING:
            blocked = [up for up in upstream if result[up]["state"] not in SATISFIED]
            if blocked:
                entry["reasons"] = [f"cannot be approved until '{blocked[0]}' is approved"]
            if entry["artifacts_changed"]:
                entry["reasons"].append("attached file changed since it was proposed: "
                                        + ", ".join(entry["artifacts_changed"]) + "; propose a new version")
        if (len(cp["versions"]) > 1 and entry["state"] == AWAITING
                and any(d["action"] == "approved" for d in cp["decisions"])):
            entry["supersedes_approval"] = True
        if entry["state"] == APPROVED:
            entry["completion"] = _completion_state(project, gate, dec)
        result[gate] = entry
    return result


def is_approved(project: dict, gate: str) -> bool:
    return evaluate(project).get(gate, {}).get("state") == APPROVED


def require(project: dict, gates: list[str], completed: bool = False) -> list[str]:
    """Problems that stop the work that needs these gates. An empty list means go ahead.

    A gate marked not applicable does not satisfy `require`: work that asks for a gate by name needs it
    authorized. With `completed=True`, an execution gate must also have a successful recorded run."""
    states = evaluate(project)
    problems = []
    for gate in gates:
        if gate not in project["gates"]:
            continue  # the project chose not to use this gate
        st = states[gate]
        if st["state"] == NOT_APPLICABLE:
            problems.append(f"'{gate}' is marked not applicable (\"{st['not_applicable_reason']}\"); work that "
                            f"computes needs a '{gate}' proposal approved by the user")
        elif st["state"] != APPROVED:
            why = "; ".join(st["reasons"]) if st["reasons"] else ""
            problems.append(f"'{gate}' is {_words(st['state'])}" + (f" ({why})" if why else ""))
        elif completed and st["completion"] is not None and not st["completion"]["completed"]:
            problems.append(f"'{gate}' is authorized but not completed: {st['completion']['reason']}")
    return problems


# ---------------------------------------------------------------- actions

def _check_upstream(project: dict, gate: str, states: dict, verb: str) -> None:
    upstream = project["gates"][: project["gates"].index(gate)]
    for up in upstream:
        st = states[up]
        if st["state"] not in SATISFIED:
            raise CheckpointError(f"'{gate}' cannot be {verb} yet: '{up}' is {_words(st['state'])}. "
                                  "Settle that gate first.")
        if st["completion"] is not None and not st["completion"]["completed"]:
            raise CheckpointError(f"'{gate}' cannot be {verb} yet: '{up}' is authorized but has no successful "
                                  f"run ({st['completion']['reason']}). Run it with `project run`.")


def _basis(project: dict, gate: str, states: dict) -> dict:
    basis = {}
    for up in project["gates"][: project["gates"].index(gate)]:
        basis[up] = states[up]["hash"]
        if states[up]["completion"] is not None:
            basis[f"{up}#completion"] = states[up]["completion"].get("id")
    return basis


def _add_version(project: dict, gate: str, content: dict, addresses: str, states: dict) -> dict:
    cp = project["checkpoints"][gate]
    h = content_hash(content)
    if cp["versions"] and cp["versions"][-1]["content_hash"] == h:
        raise CheckpointError(f"v{cp['versions'][-1]['version']} of '{gate}' already has exactly this content "
                              "and attached files; nothing new to review")
    downstream_before = {g: states[g]["state"] for g in project["gates"][project["gates"].index(gate) + 1:]}
    version = {"version": len(cp["versions"]) + 1, "proposed_at": now(), **content, "content_hash": h,
               "addresses": addresses}
    cp["versions"].append(version)
    _log(project, "proposed", gate, version["version"], content["summary"][:200])
    after = evaluate(project)
    invalidated = [g for g, s in downstream_before.items() if s in SATISFIED and after[g]["state"] not in SATISFIED]
    if invalidated:
        _log(project, "invalidated", gate, version["version"], "approvals no longer current: " + ", ".join(invalidated))
    return {**version, "invalidated": invalidated}


def propose(project: dict, gate: str, summary: str, items: list[str] | None = None,
            risks: list[str] | None = None, recommendation: str = "", artifacts: list[str] | None = None,
            addresses: str = "", findings: list[str] | None = None, limitations: list[str] | None = None,
            interpretation: str = "", options: list[str] | None = None) -> dict:
    """Record a new version of a gate for the user to review. `options` are the numbered choices shown with
    it, saved so that a reply such as "option 2" can be resolved in a later session."""
    _gate(project, gate)
    if not summary.strip():
        raise CheckpointError("a proposal needs a --summary")
    states = evaluate(project)
    _check_upstream(project, gate, states, "proposed")
    if gate == "results":
        missing = [name for name, val in (("--finding", findings), ("--limitation", limitations),
                                          ("--interpretation", (interpretation or "").strip())) if not val]
        if missing:
            raise CheckpointError("a results proposal is reviewed on its findings, limitations and interpretation, "
                                  "not on output files alone; missing: " + ", ".join(missing))
        if not artifacts:
            raise CheckpointError("attach the results files the findings come from (--artifact)")
    if gate == "manuscript" and not artifacts:
        raise CheckpointError("attach the manuscript source and its inputs (--artifact); `manuscript review` "
                              "does this for you")
    content = {"gate": gate, "summary": summary.strip(), "items": items or [], "risks": risks or [],
               "recommendation": recommendation, "artifacts": hash_files(project, artifacts)}
    for key, val in (("findings", findings), ("limitations", limitations),
                     ("interpretation", (interpretation or "").strip()), ("options", options)):
        if val:
            content[key] = val
    version = _add_version(project, gate, content, addresses, states)
    save(project)
    return version


def _decide(project: dict, gate: str, action: str, said: str, by: str, note: str, version: int | None) -> dict:
    cp = _gate(project, gate)
    if not cp["versions"]:
        raise CheckpointError(f"nothing has been proposed for '{gate}'")
    if not said or not said.strip():
        raise CheckpointError("record the user's own words with --said; a decision without them is not explicit")
    latest = cp["versions"][-1]["version"]
    if version is not None and version != latest:
        raise CheckpointError(f"v{version} is not the current version of '{gate}' (v{latest} is). "
                              f"Show v{latest} to the user before recording a decision.")
    return {"version": latest, "action": action, "at": now(), "by": by or "user", "said": said.strip(),
            "note": note or ""}


def approve(project: dict, gate: str, version: int, said: str, by: str = "user", note: str = "") -> dict:
    if version is None:
        raise CheckpointError("approve needs --version: the version number the user saw")
    decision = _decide(project, gate, "approved", said, by, note, version)
    states = evaluate(project)
    st = states[gate]
    for up in project["gates"][: project["gates"].index(gate)]:
        if states[up]["state"] not in SATISFIED:
            raise CheckpointError(f"cannot approve '{gate}': earlier gate '{up}' is {_words(states[up]['state'])}")
    _check_upstream(project, gate, states, "approved")
    if project["checkpoints"][gate]["versions"][-1].get("not_applicable"):
        raise CheckpointError(f"v{version} of '{gate}' is a not-applicable record; propose a real plan to approve")
    if st["state"] == APPROVED:
        raise CheckpointError(f"v{version} of '{gate}' is already approved and current")
    if st["state"] in (REJECTED, REVISION):
        raise CheckpointError(f"v{version} of '{gate}' was {_words(st['state'])}; propose a new "
                              "version that addresses it")
    if st["artifacts_changed"]:
        raise CheckpointError("attached file(s) changed since this version was proposed: "
                              + ", ".join(st["artifacts_changed"]) + ". Propose a new version so the user "
                              "approves what is actually on disk.")
    # A stale approval (an earlier gate moved on) may be confirmed again for the same version.
    decision["basis"] = _basis(project, gate, states)
    project["checkpoints"][gate]["decisions"].append(decision)
    _log(project, "approved", gate, version, decision["said"][:200])
    save(project)
    return decision


def mark_not_applicable(project: dict, gate: str, reason: str, said: str, by: str = "user") -> dict:
    """Record, with the user's words, that a gate does not apply to this project. Never silent."""
    _gate(project, gate)
    if gate not in NA_GATES:
        raise CheckpointError(f"only {sorted(NA_GATES)} may be marked not applicable; '{gate}' always needs a "
                              "decision")
    if not reason or not reason.strip():
        raise CheckpointError("say why the gate does not apply (--reason)")
    if not said or not said.strip():
        raise CheckpointError("record the user's own words with --said; skipping a gate needs their agreement")
    states = evaluate(project)
    _check_upstream(project, gate, states, "marked not applicable")
    if states[gate]["state"] == NOT_APPLICABLE:
        raise CheckpointError(f"'{gate}' is already marked not applicable")
    content = {"gate": gate, "summary": f"Not applicable: {reason.strip()}", "items": [], "risks": [],
               "recommendation": "", "artifacts": {}, "not_applicable": True,
               "not_applicable_reason": reason.strip()}
    version = _add_version(project, gate, content, "", states)
    decision = {"version": version["version"], "action": "not_applicable", "at": now(), "by": by or "user",
                "said": said.strip(), "note": reason.strip(), "basis": _basis(project, gate, states)}
    project["checkpoints"][gate]["decisions"].append(decision)
    _log(project, "not_applicable", gate, version["version"], reason.strip()[:200])
    save(project)
    return {**decision, "invalidated": version["invalidated"]}


def record_completion(project: dict, gate: str, command: str, exit_code: int, evidence: list[str] | None = None,
                      duration_s: float | None = None, log: str | None = None, note: str = "",
                      manifest: dict | None = None) -> dict:
    """Evidence that a run under the current authorization finished. Not a human decision."""
    _gate(project, gate)
    if gate not in COMPLETION_GATES:
        raise CheckpointError(f"runs are recorded against {sorted(COMPLETION_GATES)}, not '{gate}'")
    states = evaluate(project)
    problems = require(project, [g for g in project["gates"][: project["gates"].index(gate) + 1]])
    if problems:
        raise CheckpointError("no authorization to record a run against: " + "; ".join(problems))
    auth = content_hash(states[gate]["decision"])
    record = {"at": now(), "version": states[gate]["version"], "authorization": auth, "command": command,
              "exit_code": exit_code, "duration_s": duration_s, "log": log, "note": note,
              "evidence": hash_files(project, evidence) if exit_code == 0 else {}}
    if manifest:
        record["manifest"] = manifest  # {"path": "runs/run-....json", "sha256": ...}
    record["id"] = content_hash(record)
    project["checkpoints"][gate]["completions"].append(record)
    _log(project, "run_completed" if exit_code == 0 else "run_failed", gate, record["version"],
         f"exit {exit_code}: {command[:150]}")
    save(project)
    return record


def reject(project: dict, gate: str, said: str, reason: str = "", by: str = "user",
           version: int | None = None) -> dict:
    decision = _decide(project, gate, "rejected", said, by, reason, version)
    if evaluate(project)[gate]["state"] == REJECTED:
        raise CheckpointError(f"the current version of '{gate}' is already rejected")
    project["checkpoints"][gate]["decisions"].append(decision)
    _log(project, "rejected", gate, decision["version"], (reason or decision["said"])[:200])
    save(project)
    return decision


def request_revision(project: dict, gate: str, said: str, request: str = "", by: str = "user",
                     version: int | None = None) -> dict:
    decision = _decide(project, gate, "revision_requested", said, by, request, version)
    if evaluate(project)[gate]["state"] == REVISION:
        raise CheckpointError(f"a revision of '{gate}' is already requested; propose the revised version")
    project["checkpoints"][gate]["decisions"].append(decision)
    _log(project, "revision_requested", gate, decision["version"], (request or decision["said"])[:200])
    save(project)
    return decision


# ---------------------------------------------------------------- what to do next

PREPARE = {
    "results": "with --finding, --limitation, --interpretation and the results files attached",
    "manuscript": "with `manuscript review`, which checks the paper, builds a draft and proposes the gate",
}


def next_step(project: dict, states: dict | None = None) -> str:
    states = states or evaluate(project)
    for gate in project["gates"]:
        st = states[gate]
        s = st["state"]
        if s == NOT_APPLICABLE:
            continue
        if s == APPROVED:
            comp = st["completion"]
            if comp is not None and not comp["completed"]:
                return (f"'{gate}' is authorized but {comp['reason']}. Run the approved plan with "
                        f"`project run -- <command> --evidence <output files>`.")
            continue
        if s == NOT_STARTED:
            how = PREPARE.get(gate, f"and run `checkpoint propose {gate}`")
            return (f"Prepare the '{gate}' proposal ({GATES[gate]}) {how}; then show it to the user and wait "
                    "for their reply.")
        if s == AWAITING:
            if st["artifacts_changed"]:
                return f"The files attached to '{gate}' v{st['version']} changed; propose a new version."
            return (f"Waiting for the user to review '{gate}' v{st['version']}. Show it (`checkpoint show "
                    f"{gate}`) and ask: approve, reject, or what to change.")
        if s == REVISION:
            return (f"Revise '{gate}' as the user asked (\"{st['decision']['note'] or st['decision']['said']}\"), "
                    f"then propose v{st['version'] + 1} with --addresses.")
        if s == REJECTED:
            return (f"'{gate}' v{st['version']} was rejected (\"{st['decision']['note'] or st['decision']['said']}\"). "
                    f"Discuss an alternative with the user and propose a new version.")
        if s == STALE:
            if any("attached file changed" in r for r in st["reasons"]):
                return f"'{gate}' changed after approval; propose it again and ask the user to re-approve."
            return (f"'{gate}' v{st['version']} was approved before an earlier gate changed. Ask the user whether "
                    f"it still holds: re-approve v{st['version']}, or propose a new version.")
    return "Every gate is approved and current. The manuscript may be finalised."


def status_lines(project: dict) -> list[str]:
    states = evaluate(project)
    lines = [f"Project: {project['name']}  ({project['_file']})"]
    if project.get("question"):
        lines.append(f"Question: {project['question']}")
    lines.append(f"Last updated: {project.get('updated', '?')}")
    lines.append("")
    for gate in project["gates"]:
        st = states[gate]
        ver = f"v{st['version']} {short(st['hash'])}" if st["version"] else "-"
        when = ""
        if st["decision"]:
            when = f"{_words(st['decision']['action'])} {st['decision']['at'][:10]} by {st['decision']['by']}"
        lines.append(f"  {gate:<12} {_words(st['state']).upper():<19} {ver:<15} {when}")
        if st["state"] == NOT_APPLICABLE:
            lines.append(f"  {'':<12} - reason: {st['not_applicable_reason']}")
        for r in st["reasons"]:
            lines.append(f"  {'':<12} - {r}")
        comp = st.get("completion")
        if comp is not None:
            if comp["completed"]:
                rec = comp["record"]
                lines.append(f"  {'':<12} - run completed {rec['at'][:16]} (exit 0): {rec['command'][:70]}")
            else:
                lines.append(f"  {'':<12} - authorized, not completed: {comp['reason']}")
        if st.get("supersedes_approval"):
            lines.append(f"  {'':<12} - replaces an earlier approved version; needs a fresh approval")
    lines += ["", f"Next: {next_step(project, states)}"]
    return lines


def show_lines(project: dict, gate: str, version: int | None = None) -> list[str]:
    cp = _gate(project, gate)
    if not cp["versions"]:
        return [f"Nothing proposed for '{gate}' yet. {GATES[gate]}"]
    v = cp["versions"][-1] if version is None else next((x for x in cp["versions"] if x["version"] == version), None)
    if v is None:
        raise CheckpointError(f"'{gate}' has no v{version}")
    st = evaluate(project)[gate]
    lines = [f"Checkpoint '{gate}' v{v['version']} ({short(v['content_hash'])}), proposed {v['proposed_at']}",
             f"State: {_words(st['state']) if v['version'] == st['version'] else 'superseded'}", "",
             v["summary"]]
    if v.get("addresses"):
        lines += ["", f"Addresses: {v['addresses']}"]
    if v["items"]:
        lines += [""] + [f"- {i}" for i in v["items"]]
    if v.get("findings"):
        lines += ["", "Findings:"] + [f"- {i}" for i in v["findings"]]
    if v.get("limitations"):
        lines += ["", "Limitations:"] + [f"- {i}" for i in v["limitations"]]
    if v.get("interpretation"):
        lines += ["", f"Interpretation: {v['interpretation']}"]
    if v["risks"]:
        lines += ["", "Open risks and caveats:"] + [f"- {r}" for r in v["risks"]]
    if v["recommendation"]:
        lines += ["", f"Recommendation: {v['recommendation']}"]
    if v.get("options"):
        lines += ["", "Options shown to the user:"] + [f"{n}. {o}" for n, o in enumerate(v["options"], 1)]
    if v["artifacts"]:
        lines += ["", "Attached files:"]
        changed = set(changed_artifacts(project, v))
        lines += [f"- {k} ({short(h)}){' CHANGED SINCE' if k in changed else ''}" for k, h in v["artifacts"].items()]
    runs = cp.get("completions") or []
    if runs:
        lines += ["", "Runs:"] + [f"- {r['at']} v{r['version']} exit {r['exit_code']}: {r['command'][:80]}"
                                  for r in runs]
    if cp["decisions"]:
        lines += ["", "Decisions:"]
        lines += [f"- v{d['version']} {_words(d['action'])} {d['at']} by {d['by']}: \"{d['said']}\""
                  + (f" ({d['note']})" if d["note"] else "") for d in cp["decisions"]]
    return lines
