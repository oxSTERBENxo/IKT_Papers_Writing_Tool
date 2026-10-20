"""Transparent feasibility scoring with hard blockers.

Scores are supplied per criterion by the analyst (Claude or a person), each
with evidence. This module validates them, applies the weights, keeps
unscored criteria visible as a score range, and ranks blocked candidates
below every viable one regardless of their other scores.
"""
from __future__ import annotations

# (name, weight, what a 5 means). Weights sum to 100.
CRITERIA = [
    ("scientific_relevance", 12, "Answers a question the field demonstrably cares about."),
    ("novelty_or_replication_value", 12, "Supported gap, or a replication the literature would value."),
    ("paper_and_code_availability", 10, "Open paper plus a working, documented implementation."),
    ("dataset_accessibility", 12, "Public, licensed, downloadable data of manageable size."),
    ("compute_fit", 12, "Fits the stated hardware with margin."),
    ("implementation_simplicity", 10, "Mostly reuse of existing code; little new engineering."),
    ("time_fit", 10, "Fits the time budget with slack for reruns."),
    ("reproducibility", 8, "Seeds, configs and environment are specified."),
    ("evaluation_clarity", 7, "Standard metric and protocol with published numbers to compare to."),
    ("low_failure_risk", 7, "Few ways for the project to end without a reportable result."),
]
WEIGHTS = {name: weight for name, weight, _ in CRITERIA}
# A zero on any of these blocks the project outright.
GATING = {"dataset_accessibility", "compute_fit", "time_fit"}
GATING_BY_MODE = {"reproduction": {"paper_and_code_availability"}}
EVIDENCE_LEVELS = {"verified", "estimate", "speculative"}
# Novelty may not be scored above these caps unless the closest prior work was read in full.
# Learned from a case where an abstract-level reading scored an already-published experiment 3/5.
NOVELTY_CAP_UNREAD = 2
NOVELTY_CAP_SAME_EXPERIMENT = 1
READ_LEVELS = {"full_text", "abstract", "title_only", "not_accessible"}
# (estimate key, constraint key, description)
BUDGET_CHECKS = [
    ("weeks", "time_budget_weeks", "estimated duration (weeks) exceeds the time budget"),
    ("min_vram_gb", "gpu_vram_gb", "required GPU memory (GB) exceeds available VRAM"),
    ("gpu_hours", "gpu_hours_budget", "estimated GPU hours exceed the compute budget"),
    ("storage_gb", "storage_gb", "required storage (GB) exceeds available disk"),
]


def validate(candidate: dict) -> list[str]:
    errors = []
    cid = candidate.get("id") or candidate.get("title") or "?"
    ev = candidate.get("novelty_evidence") or {}
    if candidate.get("question_type") is not None and candidate["question_type"] not in QUESTION_TYPES:
        errors.append(f"{cid}: question_type must be one of {sorted(QUESTION_TYPES)}")
    if candidate.get("question_type") in REPLICATION_TYPES:
        value = (candidate.get("criteria") or {}).get("novelty_or_replication_value") or {}
        if value.get("score") is not None and not candidate.get("replication_rationale"):
            errors.append(f"{cid}: a {candidate['question_type']} study needs replication_rationale (why the result "
                          "is worth re-testing: widely relied on, contested, single-run, flawed protocol, ...)")
    if ev.get("closest_read") is not None and ev["closest_read"] not in READ_LEVELS:
        errors.append(f"{cid}: novelty_evidence.closest_read must be one of {sorted(READ_LEVELS)}")
    for name, entry in (candidate.get("criteria") or {}).items():
        if name not in WEIGHTS:
            errors.append(f"{cid}: unknown criterion '{name}'")
            continue
        score = entry.get("score")
        if score is None:
            continue
        if not isinstance(score, (int, float)) or isinstance(score, bool) or not 0 <= score <= 5:
            errors.append(f"{cid}: {name} score must be between 0 and 5 or null")
        if not entry.get("evidence"):
            errors.append(f"{cid}: {name} has a score but no evidence; give evidence or set the score to null")
        if entry.get("evidence_level") not in EVIDENCE_LEVELS:
            errors.append(f"{cid}: {name} needs evidence_level in {sorted(EVIDENCE_LEVELS)}")
    return errors


def score_candidate(candidate: dict, constraints: dict, weights: dict | None = None) -> dict:
    weights = weights or WEIGHTS
    criteria = candidate.get("criteria") or {}
    mode = candidate.get("mode") or constraints.get("mode")
    rows, earned, scored_weight, missing = [], 0.0, 0.0, []
    blockers = [dict(b, origin="declared") for b in candidate.get("blockers") or []]

    caps = novelty_caps(candidate, mode)
    qtype = question_type(candidate, mode)
    if qtype == "answered":
        blockers.append({"type": "already_answered", "origin": "question_type",
                         "description": "the question is already answered in the literature",
                         "evidence": (candidate.get("novelty_evidence") or {}).get("answered_by") or []})
    for name, _, meaning in CRITERIA:
        entry = criteria.get(name) or {}
        score, weight = entry.get("score"), weights.get(name, 0)
        if name in caps and score is not None and score > caps[name][0]:
            caps[name] = (caps[name][0], caps[name][1], score)
            score = caps[name][0]
        if score is not None:
            earned += weight * score / 5
            scored_weight += weight
            if score == 0 and name in GATING | GATING_BY_MODE.get(mode, set()):
                blockers.append({"type": name, "origin": "gating_criterion",
                                 "description": f"{name} scored 0, which rules the project out",
                                 "evidence": entry.get("evidence") or []})
        missing += [f"{name}: {m}" for m in entry.get("missing") or []]
        rows.append({"criterion": name, "weight": weight, "score": score, "meaning_of_5": meaning,
                     "points": round(weight * score / 5, 2) if score is not None else None,
                     "evidence": entry.get("evidence") or [], "evidence_level": entry.get("evidence_level"),
                     "missing": entry.get("missing") or []})

    estimates = candidate.get("estimates") or {}
    for est_key, con_key, text in BUDGET_CHECKS:
        est, limit = estimates.get(est_key), constraints.get(con_key)
        if est is not None and limit is not None and est > limit:
            blockers.append({"type": con_key, "origin": "budget_check",
                             "description": f"{text}: {est} > {limit}", "evidence": [f"estimate {est_key}={est}"]})

    total_weight = sum(weights.get(n, 0) for n, _, _ in CRITERIA)
    unscored = [r["criterion"] for r in rows if r["score"] is None]
    scored = [r for r in rows if r["score"] is not None]
    verified = sum(r["weight"] for r in scored if r["evidence_level"] == "verified")
    return {
        "id": candidate.get("id"), "title": candidate.get("title"), "mode": mode,
        "status": "blocked" if blockers else "viable",
        "blockers": blockers,
        # Share of the available points earned on the criteria that were scored.
        "score_percent": round(100 * earned / scored_weight, 1) if scored_weight else None,
        # Points out of the total if every unscored criterion were 0 or 5.
        "score_range": [round(100 * earned / total_weight, 1),
                        round(100 * (earned + total_weight - scored_weight) / total_weight, 1)],
        "scored_weight_percent": round(100 * scored_weight / total_weight, 1),
        "verified_weight_percent": round(100 * verified / total_weight, 1),
        "unscored_criteria": unscored, "missing_information": missing,
        "question_type": qtype, "value_basis": value_basis(qtype),
        "caps_applied": [{"criterion": k, "cap": v[0], "reason": v[1], "submitted_score": v[2]}
                         for k, v in caps.items() if len(v) == 3],
        "estimates": estimates, "criteria": rows,
    }


QUESTION_TYPES = {"novel", "extension", "replication", "benchmark_validity", "answered"}
# Studies whose purpose is to test whether a result holds: their value is not novelty.
REPLICATION_TYPES = {"replication", "benchmark_validity"}
REPLICATION_CAP_UNREAD = 3


def question_type(candidate: dict, mode: str | None) -> str | None:
    qtype = candidate.get("question_type")
    if qtype:
        return qtype
    return "replication" if mode in ("reproduction", "replication") else None


def value_basis(qtype: str | None) -> str:
    return "replication value" if qtype in REPLICATION_TYPES else "novelty"


def novelty_caps(candidate: dict, mode: str | None) -> dict:
    """{criterion: (cap, reason)} from the candidate's novelty_evidence block. Replication and benchmark-validity
    studies are judged on replication value: prior work doing the same experiment is their premise, so the
    novelty caps do not apply; they are capped only when the study being re-tested was not read in full."""
    ev = candidate.get("novelty_evidence") or {}
    read = ev.get("closest_read")
    caps = {}
    if question_type(candidate, mode) in REPLICATION_TYPES:
        if read != "full_text":
            caps["novelty_or_replication_value"] = (
                REPLICATION_CAP_UNREAD, f"the study being re-tested was read at level '{read or 'not recorded'}', "
                                        "not full text")
        return caps
    if read != "full_text":
        caps["novelty_or_replication_value"] = (
            NOVELTY_CAP_UNREAD, f"closest prior work read at level '{read or 'not recorded'}', not full text")
    if ev.get("prior_overlap") == "same_experiment" and mode in ("original", "extension", None):
        caps["novelty_or_replication_value"] = (
            NOVELTY_CAP_SAME_EXPERIMENT, "the closest prior work already performed this experiment")
    return caps


def rank(payload: dict) -> dict:
    """payload: {"constraints": {...}, "candidates": [...], "weights": {...}?}"""
    constraints = payload.get("constraints") or {}
    weights = payload.get("weights")
    if weights:
        unknown = set(weights) - set(WEIGHTS)
        if unknown:
            raise ValueError(f"unknown criteria in weights: {sorted(unknown)}")
        weights = {**WEIGHTS, **weights}
    errors = [e for c in payload.get("candidates") or [] for e in validate(c)]
    if errors:
        raise ValueError("invalid scoring input:\n- " + "\n- ".join(errors))

    results = [score_candidate(c, constraints, weights) for c in payload.get("candidates") or []]
    viable = sorted((r for r in results if r["status"] == "viable"),
                    key=lambda r: (-(r["score_percent"] or 0), -r["scored_weight_percent"]))
    blocked = [r for r in results if r["status"] == "blocked"]
    for i, r in enumerate(viable, 1):
        r["rank"] = i
    for r in blocked:
        r["rank"] = None
    return {
        "constraints": constraints, "weights": weights or WEIGHTS,
        "method": ("Each criterion is scored 0-5 with evidence. score_percent is the weighted share earned on "
                   "scored criteria only; score_range shows the total if unscored criteria were 0 or 5. Any "
                   "blocker removes a candidate from the ranking no matter how high its other scores are. "
                   "Novelty is capped at 2 unless the closest prior work was read in full, and at 1 when that "
                   "work already ran the experiment. Replication and benchmark-validity studies are scored on "
                   "replication value instead (capped at 3 if the re-tested study was not read in full); "
                   "already-answered questions are blocked."),
        "ranking": viable + blocked,
    }
