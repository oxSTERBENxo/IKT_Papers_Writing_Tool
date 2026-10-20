"""Validate a report JSON and render it to Markdown, LaTeX and BibTeX.

Validation enforces the integrity rules mechanically: every cited paper needs
a checkable identifier, every opportunity needs a logged attempt to disprove
its novelty, and nothing may be labelled 'reproduced' without execution
evidence. See references/report-schema.md for the input format.
"""
from __future__ import annotations

import datetime
import re
from pathlib import Path

from .models import surname

TEMPLATE_DIR = Path(__file__).resolve().parents[2] / "templates"
REPORT_TYPES = {
    "literature_review": "Literature Review",
    "opportunity_report": "Research Opportunity Report",
    "reproducibility_report": "Reproducibility Report",
    "research_proposal": "Research Proposal",
}
EVIDENCE_TAGS = {"verified": "[V]", "estimate": "[E]", "speculative": "[S]"}
LEGEND = ("**Evidence tags:** [V] verified against a cited source or API response; "
          "[E] reasoned estimate; [S] speculative suggestion.")
CATEGORIES = {
    "open_question": "Open research question",
    "underexplored_setting": "Underexplored experimental setting",
    "reported_limitation": "Limitation reported in prior work",
    "unresolved_contradiction": "Unresolved contradiction between papers",
    "unverified_novelty_hypothesis": "Unverified novelty hypothesis",
    "well_studied": "Already well studied",
}
NOVELTY_LEVELS = ("very_low", "low", "medium")
READ_LEVELS = ("full_text", "abstract", "title_only", "not_accessible")
WEAK_READS = ("title_only", "not_accessible")
OVERLAP_LEVELS = ("same_experiment", "same_question_different_design", "partial", "different", "unknown")
VERDICTS = {"go": "GO", "conditional_go": "CONDITIONAL GO", "no_go": "NO-GO"}
# Schema 3: literature-first discovery. Questions are typed and must trace back to evidence-ledger entries.
SCHEMA_EVIDENCE_DRIVEN = 3
QUESTION_TYPES = {
    "novel": "Novel research question",
    "extension": "Extension of an existing experiment",
    "replication": "Reproduction or replication study",
    "benchmark_validity": "Benchmark-validity investigation",
    "answered": "Already answered",
}
LEDGER_TYPES = ("stated_limitation", "methodological_weakness", "disagreement", "missing_control",
                "negative_result", "reproducibility_gap", "benchmark_validity_concern")
QTYPE_MODES = {"novel": ("original",), "extension": ("extension",), "replication": ("reproduction", "replication")}
RISK_STATUSES = ("found", "checked_ok", "not_checked", "not_applicable")
# Every shortlisted question must say what was checked for each group before it can be a 'go'.
RISK_GROUPS = {
    "leakage": ("train_test_overlap", "temporal_leakage", "duplicate_items", "pretraining_contamination",
                "label_leakage"),
    "baselines": ("weak_baseline",),
    "evaluation": ("protocol_mismatch", "metric_definition", "model_selection_on_test", "insufficient_runs"),
}
RISK_TYPES = tuple(t for group in RISK_GROUPS.values() for t in group) + ("confound", "distribution_shift", "other")
MODES = ("original", "reproduction", "replication", "extension")
EXECUTED_RESULTS = ("reproduced", "partially_reproduced", "failed_to_reproduce")
RESULT_STATUSES = ("not_assessed", "assessed_only") + EXECUTED_RESULTS
MISSING = "*Not provided (missing information).*"
KEY_RE = re.compile(r"^[A-Za-z0-9_:\-]+$")
CITE_RE = re.compile(r"\[@([^\]]+)\]")
CITE_SENTINEL = "@@CITE:{}@@"
BIB_SENTINEL = "@@BIBLIOGRAPHY@@"


# -- validation -------------------------------------------------------------
def _cited_keys(value) -> list[str]:
    """Every [@key] citation inside any string of a nested structure."""
    if isinstance(value, str):
        return [k.strip().lstrip("@") for group in CITE_RE.findall(value) for k in re.split(r"[;,]", group)
                if k.strip()]
    if isinstance(value, dict):
        return [k for v in value.values() for k in _cited_keys(v)]
    if isinstance(value, list):
        return [k for v in value for k in _cited_keys(v)]
    return []


def validate(report: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    if report.get("type") not in REPORT_TYPES:
        errors.append(f"type must be one of {sorted(REPORT_TYPES)}")
    if not report.get("title"):
        errors.append("title is required")

    keys = set()
    for i, p in enumerate(report.get("papers") or []):
        key = p.get("key") or ""
        label = key or f"papers[{i}]"
        if not KEY_RE.match(key):
            errors.append(f"{label}: key must match [A-Za-z0-9_:-]+")
        if key in keys:
            errors.append(f"{label}: duplicate key")
        keys.add(key)
        if not p.get("title"):
            errors.append(f"{label}: title is required")
        if not any(p.get(f) for f in ("doi", "arxiv_id", "pmid", "url")):
            errors.append(f"{label}: no DOI, arXiv ID, PMID or URL, so the reference cannot be checked")
        if p.get("read_level") is not None and p["read_level"] not in READ_LEVELS:
            errors.append(f"{label}: read_level must be one of {READ_LEVELS}")
        status = (p.get("verification") or {}).get("status")
        if status is None:
            warnings.append(f"{label}: reference not verified (run verify-refs)")
        elif status in ("title_mismatch", "unresolved", "no_identifier"):
            errors.append(f"{label}: reference verification failed ({status}); fix or remove it")
        elif status != "verified":
            warnings.append(f"{label}: reference only weakly verified ({status})")

    def check_keys(where: str, used):
        for k in used or []:
            if k not in keys:
                errors.append(f"{where}: cites unknown paper key '{k}'")

    check_keys("text", _cited_keys({k: v for k, v in report.items() if k != "papers"}))

    read_of = {p.get("key"): p.get("read_level") for p in report.get("papers") or []}
    for claim in _claims(report):
        weak = [k for k in claim.get("sources") or [] if read_of.get(k) in WEAK_READS]
        if claim.get("level") == "verified" and weak:
            errors.append(f"claim '{str(claim.get('text'))[:60]}' is tagged verified but cites {weak}, read only at "
                          "title level or not accessible; read the source or tag the claim estimate/speculative")

    schema = report.get("schema_version") or 1
    ledger_ids = set()
    for j, item in enumerate(report.get("evidence_ledger") or []):
        lid = item.get("id") or f"ledger[{j}]"
        if lid in ledger_ids:
            errors.append(f"evidence ledger {lid}: duplicate id")
        ledger_ids.add(lid)
        if item.get("type") not in LEDGER_TYPES:
            errors.append(f"evidence ledger {lid}: type must be one of {LEDGER_TYPES}")
        srcs = item.get("sources") or []
        check_keys(f"evidence ledger {lid}", srcs)
        if not any(read_of.get(k) in ("full_text", "abstract") for k in srcs):
            errors.append(f"evidence ledger {lid}: needs at least one source read in full or at abstract level; "
                          "a gap cannot rest on titles or unread papers")
    if schema >= SCHEMA_EVIDENCE_DRIVEN and not ledger_ids and report.get("opportunities"):
        errors.append("evidence_ledger is empty: map the literature first and derive questions from its entries")

    for i, o in enumerate(report.get("opportunities") or []):
        label = f"opportunity '{o.get('title') or i}'"
        errors += _check_adversarial(label, o, read_of)
        e, w = _check_question_type(label, o, ledger_ids, schema)
        errors += e
        warnings += w
        if o.get("category") not in CATEGORIES:
            errors.append(f"{label}: category must be one of {sorted(CATEGORIES)}")
        if not o.get("research_question"):
            errors.append(f"{label}: research_question is required")
        check_keys(label, o.get("supporting_papers"))
        check_keys(label, [c.get("key") for c in o.get("closest_existing_work") or [] if c.get("key")])
        novelty = o.get("novelty") or {}
        if novelty.get("confidence") not in NOVELTY_LEVELS:
            errors.append(f"{label}: novelty.confidence must be one of {NOVELTY_LEVELS}; a literature search "
                          "cannot justify more than 'medium'")
        if not novelty.get("uncertainty"):
            errors.append(f"{label}: novelty.uncertainty must say what the search could have missed")
        if not novelty.get("challenge_searches"):
            errors.append(f"{label}: novelty.challenge_searches is empty; run the 'challenge' command and "
                          "record its queries before proposing this")
        if not o.get("closest_existing_work"):
            errors.append(f"{label}: closest_existing_work is empty; list the nearest papers found, even if "
                          "they differ substantially")
        if o.get("category") == "well_studied" and o.get("status", "kept") == "kept":
            errors.append(f"{label}: a 'well_studied' topic cannot be kept as an opportunity; reject or revise")
        if o.get("status") in ("revised", "rejected") and not o.get("revision_note"):
            errors.append(f"{label}: status '{o['status']}' needs a revision_note with the evidence that caused it")
        if o.get("mode") and o["mode"] not in MODES:
            errors.append(f"{label}: mode must be one of {MODES}")

    for i, c in enumerate(report.get("reproduction_candidates") or []):
        label = f"reproduction candidate '{c.get('paper') or i}'"
        check_keys(label, [c.get("paper")] if c.get("paper") else [])
        if c.get("mode") not in ("reproduction", "replication", "extension"):
            errors.append(f"{label}: mode must be reproduction, replication or extension")
        status = c.get("result_status", "assessed_only")
        if status not in RESULT_STATUSES:
            errors.append(f"{label}: result_status must be one of {RESULT_STATUSES}")
        if status in EXECUTED_RESULTS and not (c.get("executed") and c.get("execution_evidence")):
            errors.append(f"{label}: result_status '{status}' requires executed=true and execution_evidence "
                          "(commands, logs, measured metrics); otherwise use 'assessed_only'")

    for i, d in enumerate(report.get("datasets") or []):
        if not d.get("url"):
            errors.append(f"dataset '{d.get('name') or i}': url is required")
        if not d.get("verified"):
            warnings.append(f"dataset '{d.get('name') or i}': not verified with dataset-verify")
    return errors, warnings


def _claims(value) -> list[dict]:
    """Every claim object ({'text', 'level', ...}) anywhere in the report except the papers list."""
    if isinstance(value, dict):
        if "level" in value and "text" in value:
            return [value]
        return [c for k, v in value.items() if k != "papers" for c in _claims(v)]
    if isinstance(value, list):
        return [c for v in value for c in _claims(v)]
    return []


def _check_question_type(label: str, o: dict, ledger_ids: set, schema: int) -> tuple[list[str], list[str]]:
    """Question type must agree with the mode, the overlap with prior work and the decision; under schema 3 every
    question must be derived from evidence-ledger entries."""
    errors, warnings = [], []
    qtype = o.get("question_type")
    derived = o.get("derived_from") or []
    if qtype is None:
        (errors if schema >= SCHEMA_EVIDENCE_DRIVEN else warnings).append(
            f"{label}: question_type missing (one of {sorted(QUESTION_TYPES)})")
    elif qtype not in QUESTION_TYPES:
        errors.append(f"{label}: question_type must be one of {sorted(QUESTION_TYPES)}")
    if not derived and o.get("status", "kept") != "rejected":
        (errors if schema >= SCHEMA_EVIDENCE_DRIVEN else warnings).append(
            f"{label}: derived_from is empty; trace the question to evidence-ledger entries (a limitation, weakness, "
            "disagreement or missing control)")
    for d in derived:
        if d not in ledger_ids:
            errors.append(f"{label}: derived_from cites unknown ledger entry '{d}'")
    if qtype not in QUESTION_TYPES:
        return errors, warnings
    mode, status = o.get("mode"), o.get("status", "kept")
    verdict = (o.get("decision") or {}).get("verdict")
    if qtype == "answered" and (status != "rejected" or verdict not in (None, "no_go")):
        errors.append(f"{label}: an 'answered' question must be rejected with verdict no_go")
    if qtype in QTYPE_MODES and mode and mode not in QTYPE_MODES[qtype]:
        errors.append(f"{label}: question_type '{qtype}' needs mode in {QTYPE_MODES[qtype]}, not '{mode}'")
    if qtype == "novel":
        prior = [c.get("key") for c in o.get("closest_existing_work") or []
                 if c.get("overlap") in ("same_experiment", "same_question_different_design")]
        if prior:
            errors.append(f"{label}: called novel although {prior} already address the question; classify it as "
                          "extension, replication, benchmark_validity or answered")
    return errors, warnings


def _closest_read(entry: dict, read_of: dict):
    return entry.get("read_level") or read_of.get(entry.get("key"))


def _check_adversarial(label: str, o: dict, read_of: dict) -> list[str]:
    """Rules learned from novelty claims that later turned out to be wrong: a 'go' needs full-text reading of
    the closest work, an explicit check for leakage, weak baselines and evaluation flaws, and no prior paper
    that already ran the experiment."""
    errors = []
    status = o.get("status", "kept")
    mode = o.get("mode")
    closest = o.get("closest_existing_work") or []
    reads = [_closest_read(c, read_of) for c in closest]
    novelty = o.get("novelty") or {}
    conf = novelty.get("confidence")

    for c in closest:
        if c.get("read_level") is not None and c["read_level"] not in READ_LEVELS:
            errors.append(f"{label}: closest work read_level must be one of {READ_LEVELS}")
        if c.get("overlap") is not None and c["overlap"] not in OVERLAP_LEVELS:
            errors.append(f"{label}: closest work overlap must be one of {OVERLAP_LEVELS}")
    same = [c.get("key") or c.get("description") for c in closest if c.get("overlap") == "same_experiment"]
    if same and status != "rejected" and mode in ("original", "extension"):
        errors.append(f"{label}: {same} already performed this experiment; reject the idea or reframe it as a "
                      "reproduction or replication of that work")

    ceiling = novelty.get("ceiling")
    if (ceiling in NOVELTY_LEVELS and conf in NOVELTY_LEVELS
            and NOVELTY_LEVELS.index(conf) > NOVELTY_LEVELS.index(ceiling)):
        errors.append(f"{label}: novelty confidence '{conf}' exceeds the challenge ceiling '{ceiling}'")
    if conf == "medium" and ("full_text" not in reads or any(r in WEAK_READS or r is None for r in reads)):
        errors.append(f"{label}: 'medium' novelty confidence needs the closest work read in full (at least one "
                      "full_text, none unread); lower the confidence")

    risks = o.get("methodological_risks") or []
    for r in risks:
        if r.get("type") not in RISK_TYPES:
            errors.append(f"{label}: risk type '{r.get('type')}' must be one of {RISK_TYPES}")
        if r.get("status") not in RISK_STATUSES:
            errors.append(f"{label}: risk status must be one of {RISK_STATUSES}")
    if status != "rejected" and not risks:
        errors.append(f"{label}: methodological_risks is empty; record what was checked for leakage, baselines "
                      "and evaluation protocol (status not_checked is allowed, silence is not)")

    decision = o.get("decision") or {}
    verdict = decision.get("verdict")
    if verdict not in VERDICTS:
        errors.append(f"{label}: decision.verdict must be one of {sorted(VERDICTS)}")
        return errors
    if not decision.get("rationale"):
        errors.append(f"{label}: decision.rationale is required")
    if status == "rejected" and verdict != "no_go":
        errors.append(f"{label}: a rejected candidate must have verdict no_go")
    if verdict == "conditional_go" and not (decision.get("conditions") and decision.get("unresolved_risks")):
        errors.append(f"{label}: conditional_go needs both conditions and unresolved_risks")
    if verdict == "go":
        if "full_text" not in reads:
            errors.append(f"{label}: 'go' requires at least one closest work read in full text")
        if any(r in WEAK_READS or r is None for r in reads):
            errors.append(f"{label}: 'go' is not allowed while closest work is unread or read at title level only; "
                          "use conditional_go and list the reading as a condition")
        for group, types in RISK_GROUPS.items():
            checked = [r for r in risks if r.get("type") in types
                       and r.get("status") in ("found", "checked_ok", "not_applicable")]
            if not checked:
                errors.append(f"{label}: 'go' requires a checked {group} risk ({', '.join(types)})")
        for r in risks:
            if r.get("status") == "found" and not r.get("mitigation"):
                errors.append(f"{label}: 'go' with found risk '{r.get('type')}' needs a mitigation")
        if same and mode not in ("reproduction", "replication"):
            errors.append(f"{label}: 'go' on an experiment that {same} already performed")
    return errors


# -- rendering helpers ------------------------------------------------------
def cite_label(paper: dict) -> str:
    authors = paper.get("authors") or []
    names = [surname(a).title() for a in authors[:2] if a]
    who = names[0] + " et al." if len(authors) > 2 and names else " & ".join(names) if names else paper.get("key", "?")
    return f"{who} {paper.get('year') or 'n.d.'}"


def paper_url(paper: dict) -> str | None:
    doi = paper.get("doi")
    if doi and not doi.lower().startswith("10.48550/arxiv."):
        return f"https://doi.org/{doi}"
    if paper.get("arxiv_id"):
        return f"https://arxiv.org/abs/{paper['arxiv_id']}"
    if paper.get("pmid"):
        return f"https://pubmed.ncbi.nlm.nih.gov/{paper['pmid']}/"
    return paper.get("url") or (f"https://doi.org/{doi}" if doi else None)


class Renderer:
    def __init__(self, report: dict, latex: bool = False):
        self.report, self.latex = report, latex
        self.papers = {p.get("key"): p for p in report.get("papers") or []}

    # citations ---------------------------------------------------------
    def cite(self, keys) -> str:
        keys = [k for k in (keys if isinstance(keys, list) else [keys]) if k]
        if not keys:
            return ""
        if self.latex:
            return CITE_SENTINEL.format(",".join(keys))
        parts = []
        for k in keys:
            p = self.papers.get(k)
            parts.append(f"[{cite_label(p)}]({paper_url(p)})" if p and paper_url(p) else
                         (cite_label(p) if p else f"(unknown reference {k})"))
        return "(" + "; ".join(parts) + ")"

    def text(self, value) -> str:
        """Free text with [@key] citations expanded."""
        if value is None or value == "":
            return MISSING
        return CITE_RE.sub(lambda m: self.cite([k.strip().lstrip("@") for k in re.split(r"[;,]", m.group(1))]),
                           str(value))

    def claim(self, item) -> str:
        """A string, or {'text', 'level', 'sources': [keys]} rendered with its evidence tag."""
        if isinstance(item, dict):
            tag = EVIDENCE_TAGS.get(item.get("level"), "[?]")
            sources = item.get("sources") or ([item["source"]] if item.get("source") else [])
            return f"{tag} {self.text(item.get('text'))} {self.cite(sources)}".rstrip()
        return self.text(item)

    def labelled(self, label: str, value) -> str:
        """Bold run-in label followed by text, or by a bullet list on its own lines."""
        if isinstance(value, list) and len(value) == 1:
            value = value[0]
        body = self.block(value)
        return f"**{label}.**\n{body}" if isinstance(value, list) else f"**{label}.** {body}"

    def block(self, value) -> str:
        if value is None or value == "" or value == []:
            return MISSING
        if isinstance(value, list):
            if len(value) == 1:
                return self.claim(value[0])  # a single point reads better as a sentence than a bullet
            return "\n".join(f"- {self.claim(v)}" for v in value)
        if isinstance(value, dict) and "text" in value:
            return self.claim(value)
        return self.text(value)

    @staticmethod
    def cell(value) -> str:
        if value is None or value == "" or value == []:
            return "not reported"
        if isinstance(value, list):
            value = "; ".join(str(v) for v in value)
        return re.sub(r"\s+", " ", str(value)).replace("|", "/")

    def table(self, headers: list[str], rows: list[list]) -> str:
        lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(" --- " for _ in headers) + "|"]
        lines += ["| " + " | ".join(self.cell(c) for c in row) + " |" for row in rows]
        return "\n".join(lines)

    # blocks ------------------------------------------------------------
    def header_block(self) -> str:
        r = self.report
        lines = [f"**Report type:** {REPORT_TYPES.get(r.get('type'), r.get('type'))}  ",
                 f"**Generated:** {r.get('date') or datetime.date.today().isoformat()}", "", LEGEND]
        constraints = r.get("constraints") or {}
        defaults = set(constraints.get("defaults_used") or [])
        rows = [[k.replace("_", " "), v, "default (not stated by user)" if k in defaults else "stated by user"]
                for k, v in constraints.items() if k != "defaults_used"]
        if rows:
            lines += ["", self.table(["Constraint", "Value", "Origin"], rows)]
        return "\n".join(lines)

    def search_log(self) -> str:
        log = self.report.get("search_log")
        if not log:
            return MISSING
        failed = log.get("sources_failed") or []
        lines = [
            f"- **Sources that answered:** {', '.join(log.get('sources_ok') or []) or 'none'}",
            "- **Sources that failed or were skipped:** " + ("; ".join(
                f"{f.get('source')} ({f.get('reason')})" if isinstance(f, dict) else str(f) for f in failed) or "none"),
            f"- **Search strategies:** {', '.join(log.get('strategies') or []) or 'not recorded'}",
            f"- **Date range:** {log.get('date_range') or 'not restricted'}",
            f"- **Records retrieved / after deduplication:** {log.get('n_retrieved', 'not recorded')} / "
            f"{log.get('n_after_dedup', 'not recorded')}",
            f"- **Search date:** {log.get('date') or self.report.get('date') or 'not recorded'}",
        ]
        if log.get("queries"):
            lines.append("- **Queries:** " + "; ".join(f"`{q}`" for q in log["queries"]))
        if log.get("notes"):
            lines += [f"- {self.text(n)}" for n in log["notes"]]
        return "\n".join(lines)

    def literature_table(self) -> str:
        papers = self.report.get("papers") or []
        if not papers:
            return MISSING
        rows = []
        for p in papers:
            url = paper_url(p)
            rows.append([f"{p.get('title')} ({cite_label(p)})", p.get("date") or p.get("year"), p.get("method"),
                         p.get("datasets"), p.get("findings"), p.get("limitations"),
                         (p.get("read_level") or "not recorded").replace("_", " "),
                         f"[link]({url})" if url else None])
        note = ("\n\nMethod, dataset, finding and limitation cells summarise the cited paper's abstract or text; "
                "'not reported' means the information was not found there.")
        return self.table(["Paper", "Published", "Method", "Datasets", "Findings", "Stated limitations", "Read",
                           "Link"], rows) + note

    def opportunities(self) -> str:
        items = self.report.get("opportunities") or []
        if not items:
            return MISSING
        kept = [o for o in items if o.get("status", "kept") != "rejected"]
        rejected = [o for o in items if o.get("status") == "rejected"]
        out = [self._opportunity(i, o) for i, o in enumerate(kept, 1)]
        if rejected:
            out.append("### Candidates rejected after the novelty challenge\n\n" + "\n".join(
                f"- **{o.get('title')}** ({CATEGORIES.get(o.get('category'), o.get('category'))}): "
                f"{self.text(o.get('revision_note'))}" for o in rejected))
        return "\n\n".join(out)

    def _opportunity(self, i: int, o: dict) -> str:
        novelty = o.get("novelty") or {}
        closest = "\n".join(f"- {self.cite(c.get('key')) or c.get('description', '')}{self._closest_tag(c)}: "
                            f"{self.text(c.get('how_it_differs'))}" for c in o.get("closest_existing_work") or [])
        searches = novelty.get("challenge_searches") or []
        lines = [
            f"### {i}. {o.get('title')}",
            f"**Question type:** {QUESTION_TYPES.get(o.get('question_type'), 'not classified')}  ",
            f"**Type of gap:** {CATEGORIES.get(o.get('category'), o.get('category'))}  ",
            f"**Recommended mode:** {o.get('mode') or 'not stated'}"
            + (f"  \n**Revised:** {self.text(o.get('revision_note'))}" if o.get("status") == "revised" else ""),
            "", f"**Research question.** {self.text(o.get('research_question'))}",
            "", self.derived_text(o.get("derived_from")),
            "", f"**Motivation.** {self.text(o.get('motivation'))}",
            "", f"**Supporting papers.** {self.cite(o.get('supporting_papers') or []) or MISSING}",
            "", "**Closest existing work.**", closest or MISSING,
            "", self.labelled("Evidence for the gap", o.get("gap_evidence")),
            "", self.labelled("Potential contribution", o.get("contribution")),
            "", f"**Novelty confidence:** {novelty.get('confidence')} (scale: very_low, low, medium; a search "
                f"cannot establish more). {self.text(novelty.get('uncertainty'))}",
            f"Attempts to disprove novelty: {len(searches)} search(es)"
            + (f"; signal `{novelty.get('signal')}`" if novelty.get("signal") else "") + ". "
            + ("Queries: " + "; ".join(f"`{q}`" for q in searches[:8]) if searches else ""),
            "", self.labelled("Feasibility", o.get("feasibility")),
            "", self.risk_table(o.get("methodological_risks")),
            "", self.decision_text(o.get("decision")),
        ]
        return "\n".join(lines)

    def derived_text(self, derived) -> str:
        if not derived:
            return "**Derived from.** " + MISSING
        ledger = {i.get("id"): i for i in self.report.get("evidence_ledger") or []}
        items = [f"{d}: {self.claim(ledger[d]) if d in ledger else '(unknown entry)'}" for d in derived]
        return "**Derived from.**\n" + "\n".join(f"- {x}" for x in items)

    def evidence_ledger(self) -> str:
        items = self.report.get("evidence_ledger") or []
        if not items:
            return MISSING
        rows = [[i.get("id"), (i.get("type") or "").replace("_", " "), self.claim(i)] for i in items]
        intro = ("## Evidence map\n\nWhat the literature already establishes, where it disagrees, and what it leaves "
                 "open. Every research question below is derived from these entries.\n\n")
        return intro + self.table(["ID", "Evidence type", "What the literature establishes or leaves open"], rows)

    def _closest_tag(self, c: dict) -> str:
        read = c.get("read_level") or (self.papers.get(c.get("key")) or {}).get("read_level")
        parts = [f"read: {read.replace('_', ' ')}" if read else "read level not recorded"]
        if c.get("overlap"):
            parts.append(f"overlap: {c['overlap'].replace('_', ' ')}")
        return " [" + "; ".join(parts) + "]"

    def risk_table(self, risks) -> str:
        if not risks:
            return "**Methodological risks.** " + MISSING
        rows = [[(r.get("type") or "").replace("_", " "), (r.get("status") or "").replace("_", " "),
                 self.claim(r.get("evidence")) if r.get("evidence") else None,
                 self.text(r.get("mitigation")) if r.get("mitigation") else None] for r in risks]
        return "**Methodological risks.**\n\n" + self.table(["Risk", "Status", "Evidence", "Mitigation"], rows)

    def decision_text(self, decision) -> str:
        if not decision:
            return "**Decision.** " + MISSING
        lines = [f"**Decision: {VERDICTS.get(decision.get('verdict'), decision.get('verdict'))}.** "
                 f"{self.text(decision.get('rationale'))}"]
        if decision.get("conditions"):
            lines += ["", self.labelled("Conditions before committing", decision["conditions"])]
        if decision.get("unresolved_risks"):
            lines += ["", self.labelled("Unresolved evidence and risks", decision["unresolved_risks"])]
        return "\n".join(lines)

    def decisions(self) -> str:
        items = self.report.get("opportunities") or []
        if not items:
            return MISSING
        rows = []
        for o in items:
            d = o.get("decision") or {}
            conds = "; ".join(c if isinstance(c, str) else str(c.get("text", "")) for c in d.get("conditions") or [])
            rows.append([o.get("title"), QUESTION_TYPES.get(o.get("question_type"), "not classified"),
                         VERDICTS.get(d.get("verdict"), "not decided"),
                         (o.get("novelty") or {}).get("confidence"), o.get("mode"),
                         self.text(conds[:240]) if conds else None])
        return self.table(["Research question", "Question type", "Decision", "Novelty confidence", "Mode",
                           "Main conditions"], rows)

    def verification_summary(self) -> str:
        """Four separate things that are easy to conflate."""
        r = self.report
        papers = r.get("papers") or []
        ver, reads, levels = {}, {}, {}
        for p in papers:
            st = (p.get("verification") or {}).get("status") or "not verified"
            ver[st] = ver.get(st, 0) + 1
            lvl = (p.get("read_level") or "not recorded").replace("_", " ")
            reads[lvl] = reads.get(lvl, 0) + 1
        for c in _claims({k: v for k, v in r.items() if k != "ranking"}):
            key = c.get("level") or "untagged"
            levels[key] = levels.get(key, 0) + 1
        opps = r.get("opportunities") or []
        nov = "; ".join(
            f"{o.get('title')}: {(o.get('novelty') or {}).get('confidence')}"
            + (f" (search ceiling {(o.get('novelty') or {}).get('ceiling')})"
               if (o.get('novelty') or {}).get('ceiling') else "") for o in opps) or "no opportunities"
        cands = r.get("reproduction_candidates") or []
        executed = sum(1 for c in cands if c.get("executed"))
        rows = [
            ["Source existence (verify-refs)", ", ".join(f"{k}: {v}" for k, v in sorted(ver.items())) or "no papers",
             "The cited record exists and its title matches. Says nothing about what the paper shows."],
            ["Claim support", "papers read: " + (", ".join(f"{k}: {v}" for k, v in sorted(reads.items())) or "none")
             + "; claims: " + (", ".join(f"{k}: {v}" for k, v in sorted(levels.items())) or "none"),
             "Verified claims were checked against their source at the read level shown."],
            ["Novelty confidence", nov, "How far the searches support a gap; never above medium."],
            ["Reproducibility", f"{executed} of {len(cands)} candidate(s) executed" if cands else "nothing executed",
             "Whether results were re-run, not whether code exists."],
        ]
        return self.table(["Dimension", "Status", "Meaning"], rows)

    def reproduction(self) -> str:
        items = self.report.get("reproduction_candidates") or []
        if not items:
            return MISSING
        out = []
        for i, c in enumerate(items, 1):
            paper = self.papers.get(c.get("paper")) or {}
            status = c.get("result_status", "assessed_only")
            executed = "executed" if c.get("executed") else "NOT executed; nothing below is a reproduction result"
            lines = [f"### {i}. {paper.get('title') or c.get('paper')} {self.cite(c.get('paper'))}",
                     f"**Mode:** {c.get('mode')}  ", f"**Result status:** {status} ({executed})  ",
                     f"**Code:** {self.text(c.get('code'))}", ""]
            checklist = c.get("checklist") or {}
            if checklist:
                rows = [[v.get("label") or k, v.get("status"),
                         "; ".join([*(v.get("evidence") or []), *([v["note"]] if v.get("note") else [])])]
                        for k, v in checklist.items()]
                lines += [self.table(["Item", "Status", "Evidence / note"], rows), ""]
            for title, key in (("Why reproducing it is valuable", "value"), ("Hardware and time", "hardware"),
                               ("Missing information", "missing"), ("Experimental risks", "risks"),
                               ("Suggested experiments", "suggested_experiments")):
                lines += [self.labelled(title, c.get(key)), ""]
            if c.get("execution_evidence"):
                lines += [self.labelled("Execution evidence", c["execution_evidence"]), ""]
            out.append("\n".join(lines).rstrip())
        return "\n\n".join(out)

    def datasets_table(self) -> str:
        items = self.report.get("datasets") or []
        if not items:
            return MISSING
        rows = [[f"[{d.get('name')}]({d.get('url')})", d.get("purpose"), d.get("size"), d.get("format"),
                 d.get("license"), d.get("access"), d.get("preprocessing"), d.get("suitability"),
                 "yes" if d.get("verified") else "NO"] for d in items]
        return self.table(["Dataset", "Purpose", "Size", "Format", "Licence", "Access", "Preprocessing",
                           "Suitability", "Verified via API"], rows)

    def ranking(self) -> str:
        ranking = self.report.get("ranking")
        if not ranking or not ranking.get("ranking"):
            return MISSING
        results = ranking["ranking"]
        names = [r["criterion"] for r in results[0]["criteria"]]
        head = ["Rank", "Candidate", "Status", "Score %", "Range", "Scored weight %", "Verified weight %"]
        rows = [[r["rank"] if r["rank"] else "-", r.get("title") or r.get("id"), r["status"].upper(),
                 r["score_percent"], f"{r['score_range'][0]}-{r['score_range'][1]}",
                 r["scored_weight_percent"], r["verified_weight_percent"]] for r in results]
        detail = [[n.replace("_", " "), results[0]["criteria"][j]["weight"]] +
                  ["unscored" if r["criteria"][j]["score"] is None else
                   f"{r['criteria'][j]['score']} {EVIDENCE_TAGS.get(r['criteria'][j]['evidence_level'], '')}"
                   for r in results] for j, n in enumerate(names)]
        out = [ranking.get("method", ""), "", self.table(head, rows), "",
               "**Scores per criterion (0-5).**", "",
               self.table(["Criterion", "Weight"] + [str(r.get("id") or r.get("title")) for r in results], detail)]
        for r in results:
            out += ["", f"**{r.get('title') or r.get('id')}**"]
            if r.get("question_type"):
                out.append(f"- Question type: {r['question_type'].replace('_', ' ')}; the value criterion is scored as "
                           f"{r.get('value_basis')}")
            for b in r["blockers"]:
                out.append(f"- BLOCKER ({b.get('type')}): {b.get('description')}")
            for row in r["criteria"]:
                if row["evidence"]:
                    out.append(f"- {row['criterion'].replace('_', ' ')}: " + "; ".join(self.text(e) for e in row["evidence"]))
            for m in r["missing_information"]:
                out.append(f"- Missing: {m}")
            if r["unscored_criteria"]:
                out.append(f"- Not scored for lack of evidence: {', '.join(r['unscored_criteria'])}")
            for c in r.get("caps_applied") or []:
                out.append(f"- Capped: {c['criterion'].replace('_', ' ')} {c['submitted_score']} -> {c['cap']} "
                           f"({c['reason']})")
        return "\n".join(out)

    def limitations(self) -> str:
        return self.block(self.report.get("limitations"))

    def references(self) -> str:
        papers = self.report.get("papers") or []
        if self.latex:
            return BIB_SENTINEL
        if not papers:
            return MISSING
        lines = []
        for i, p in enumerate(sorted(papers, key=lambda p: cite_label(p).lower()), 1):
            authors = p.get("authors") or []
            who = ", ".join(authors[:6]) + (" et al." if len(authors) > 6 else "") or "Unknown authors"
            status = (p.get("verification") or {}).get("status")
            mark = "" if status == "verified" else f" **[reference {status or 'not verified'}]**"
            lines.append(f"{i}. {who} ({p.get('year') or 'n.d.'}). *{p.get('title')}*. "
                         f"{(p.get('venue') or '') + '. ' if p.get('venue') else ''}{paper_url(p) or ''}{mark}")
        return "\n".join(lines)

    BLOCKS = ("header_block", "search_log", "literature_table", "opportunities", "reproduction",
              "datasets_table", "ranking", "limitations", "references", "decisions", "verification_summary", "evidence_ledger")

    def render(self, template: str, banner: str = "") -> str:
        r = self.report

        def fill(match: re.Match) -> str:
            text = lookup(match.group(2))
            # {{?name}} marks an optional section: left out when there is nothing to show.
            return "" if match.group(1) and text == MISSING else text

        def lookup(name: str) -> str:
            if name == "title":
                return str(r.get("title") or "Untitled report")
            if name == "banner":
                return banner
            if name in self.BLOCKS:
                return getattr(self, name)()
            for scope in (r.get("proposal") or {}, r.get("sections") or {}):
                if name in scope:
                    return self.block(scope[name])
            return MISSING

        return re.sub(r"\n{3,}", "\n\n", re.sub(r"\{\{(\??)(\w+)\}\}", fill, template)).strip() + "\n"


def render_markdown(report: dict, banner: str = "", latex_mode: bool = False) -> str:
    template = (TEMPLATE_DIR / f"{report['type']}.md").read_text(encoding="utf-8")
    return Renderer(report, latex=latex_mode).render(template, banner)


# -- LaTeX --------------------------------------------------------------------
_TEX_ESCAPES = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
                "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
_INLINE_RE = re.compile(r"@@CITE:([^@]+)@@|\[([^\]]+)\]\((https?://[^)\s]+)\)|`([^`]+)`|(https?://[^\s)|]+)")


def tex_escape(text: str) -> str:
    return "".join(_TEX_ESCAPES.get(c, c) for c in text)


def _tex_plain(text: str) -> str:
    text = tex_escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", text)
    return re.sub(r"(?<![\w*])\*([^*\n]+?)\*(?![\w*])", r"\\emph{\1}", text)


def _tex_url(url: str) -> str:
    return url.replace("\\", "").replace("%", r"\%").replace("#", r"\#").replace("&", r"\&")


def tex_inline(text: str) -> str:
    out, pos = [], 0
    for m in _INLINE_RE.finditer(text):
        out.append(_tex_plain(text[pos:m.start()]))
        if m.group(1):
            out.append(r"\cite{%s}" % m.group(1))
        elif m.group(3):
            out.append(r"\href{%s}{%s}" % (_tex_url(m.group(3)), _tex_plain(m.group(2))))
        elif m.group(4):
            out.append(r"\texttt{%s}" % tex_escape(m.group(4)))
        else:
            out.append(r"\url{%s}" % _tex_url(m.group(5)))
        pos = m.end()
    out.append(_tex_plain(text[pos:]))
    return "".join(out)


def _tex_table(rows: list[list[str]]) -> list[str]:
    n = max(len(r) for r in rows)
    width = round(0.92 / n, 3)
    spec = "".join(r">{\raggedright\arraybackslash}p{%s\textwidth}" % width for _ in range(n))
    out = [r"{\small", r"\begin{longtable}{%s}" % spec, r"\toprule"]
    for i, row in enumerate(rows):
        cells = [tex_inline(c) for c in row] + [""] * (n - len(row))
        if i == 0:
            cells = [r"\textbf{%s}" % c for c in cells]
        out.append(" & ".join(cells) + r" \\")
        if i == 0:
            out += [r"\midrule", r"\endhead"]
    return out + [r"\bottomrule", r"\end{longtable}", "}"]


def markdown_to_latex_body(md: str) -> tuple[str, str]:
    """Convert the Markdown subset this module emits. Returns (title, body)."""
    title, out, list_env, table = "", [], None, []

    def close_list():
        nonlocal list_env
        if list_env:
            out.append(r"\end{%s}" % list_env)
            list_env = None

    def flush_table():
        nonlocal table
        if table:
            out.extend(_tex_table(table))
            table = []

    for line in md.splitlines():
        stripped = line.strip()
        if stripped.startswith("|"):
            close_list()
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if not all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
                table.append(cells)
            continue
        flush_table()
        heading = re.match(r"(#{1,4})\s+(.*)", stripped)
        bullet = re.match(r"[-*]\s+(.*)", stripped)
        numbered = re.match(r"\d+\.\s+(.*)", stripped)
        if heading:
            close_list()
            level, text = len(heading.group(1)), heading.group(2)
            if level == 1 and not title:
                title = tex_inline(text)
            else:
                out.append(r"\%s{%s}" % ({1: "section", 2: "section", 3: "subsection", 4: "subsubsection"}[level],
                                         tex_inline(text)))
        elif bullet or numbered:
            env = "itemize" if bullet else "enumerate"
            if list_env != env:
                close_list()
                out.append(r"\begin{%s}" % env)
                list_env = env
            out.append(r"\item " + tex_inline((bullet or numbered).group(1)))
        elif stripped == BIB_SENTINEL:
            close_list()
            out += [r"\bibliographystyle{plain}", r"\bibliography{references}"]
        elif not stripped:
            close_list()
            out.append("")
        else:
            close_list()
            hard_break = line.endswith("  ")
            out.append(tex_inline(stripped) + (r"\\" if hard_break else ""))
    close_list()
    flush_table()
    return title, "\n".join(out)


def render_latex(report: dict, banner: str = "") -> str:
    title, body = markdown_to_latex_body(render_markdown(report, banner, latex_mode=True))
    preamble = (TEMPLATE_DIR / "report.tex").read_text(encoding="utf-8")
    return (preamble.replace("%%TITLE%%", title).replace("%%DATE%%", tex_escape(str(report.get("date") or r"\today")))
            .replace("%%BODY%%", body))


def render_bibtex(report: dict) -> str:
    entries = []
    for p in report.get("papers") or []:
        is_preprint = bool(p.get("arxiv_id")) and not (p.get("doi") and not p["doi"].lower().startswith("10.48550"))
        fields = {
            "title": "{" + tex_escape(p.get("title") or "") + "}",
            "author": " and ".join(tex_escape(a) for a in p.get("authors") or []),
            "year": str(p.get("year") or ""),
            "journal" if not is_preprint else "howpublished":
                tex_escape(p.get("venue") or ("arXiv preprint" if is_preprint else "")),
            "doi": p.get("doi") or "",
            "eprint": p.get("arxiv_id") or "",
            "archivePrefix": "arXiv" if p.get("arxiv_id") else "",
            "url": paper_url(p) or "",
        }
        body = ",\n".join(f"  {k} = {{{v}}}" for k, v in fields.items() if v)
        entries.append(f"@{'misc' if is_preprint else 'article'}{{{p.get('key')},\n{body}\n}}")
    return "\n\n".join(entries) + "\n"


def slugify(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (title or "report").lower()).strip("-")[:60] or "report"
