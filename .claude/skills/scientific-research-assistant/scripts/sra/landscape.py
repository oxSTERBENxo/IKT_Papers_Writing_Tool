"""Literature-first discovery: map what is already established before proposing any research question.

The map collects, for a topic, the papers most likely to have already run a proposed experiment or to show
where real gaps are:
- published comparisons and empirical studies,
- negative results ("does not improve", "revisiting"),
- reproducibility and replication studies,
- critiques of benchmarks and evaluation protocols,
- stated limitations and surveys,
and sorts them into evidence buckets with transparent text patterns. It also builds ready-to-run web-search
queries (for Claude's web search, which this toolkit cannot call) and an empty evidence ledger that Claude fills
from papers it has actually read. Research questions are then derived from ledger entries, not invented.

Evidence types are pattern matches on titles and abstracts: a pointer for reading, not a classification of
what a paper shows.
"""
from __future__ import annotations

import re

from .models import dedupe
from .report import LEDGER_TYPES
from .novelty import expand, fill_missing_abstracts, short_probes
from .search import DISCOVERY_STRATEGIES, design_queries, rank, run_search

EVIDENCE_PATTERNS = {
    "negative_result": r"\b(no|not|little|marginal|negligible|limited)\b[^.]{0,40}\b(improv|benefit|gain|help|"
                       r"significan|advantage)|fail(s|ed)? to|does not (help|improve|need)|do(es)? not (need|require)|"
                       r"\bunnecessary\b|overestimat|overstat|not (needed|necessary|essential)|on par with|"
                       r"match(es)? or (closely )?trail|perform(s)? (just )?as well as|comparable (performance|results)",
    "comparison": r"\bvs\.?\b|\bversus\b|compar(e|es|ed|ison|ing)\b|benchmark(ing|s)?\b|empirical (study|evaluation|"
                  r"analysis|comparison)|systematic(ally)? (study|evaluat|compar)|holistic",
    "reproducibility": r"reproduc|replica(te|tion|bility)|re-?evaluat|re-?examin|revisit|re-?assess|sanity check",
    "benchmark_critique": r"(benchmark|dataset|evaluation|protocol)[^.]{0,80}(flaw|pitfall|leak|bias|poorly suited|"
                          r"inadequate|unrealistic|shortcut|artifact|overestimat|misleading|not (meaningfully )?test)|"
                          r"rethinking|data leakage|contaminat|spurious|are we (really )?making|hardly reproducible",
    "stated_limitation": r"\blimitation|open (problem|question|challenge)|remain(s)? (unclear|unexplored|open|"
                         r"underexplored)|under-?explored|little (is known|attention)|future work|unresolved",
    # "review" alone would also match product reviews (sentiment analysis); require survey phrasings.
    "survey": r"\b(survey|overview|tutorial)\b|literature review|\ba (comprehensive |systematic |critical |brief )?"
              r"review\b|\breview of (the )?(literature|methods|approaches|recent|research|deep|graph|machine)",
    "method_proposal": r"we propose|we present (a|an) (novel|new)|novel (method|model|framework|approach|architecture)|"
                       r"outperform(s)? (the )?(state|existing|all)",
}
TOP_OVERALL = 3
# Buckets an adversarial reader should empty first: these are where "already done" usually hides.
PRIORITY = ["negative_result", "reproducibility", "benchmark_critique", "comparison", "survey", "stated_limitation"]



def classify(paper) -> list[str]:
    text = f"{paper.title}. {paper.abstract or ''}"
    return [t for t, pat in EVIDENCE_PATTERNS.items() if re.search(pat, text, flags=re.I)]


def web_queries(anchor: str, design: list[str], topic_queries: list[str]) -> list[str]:
    """Plain-language web searches that target established findings rather than methods."""
    out = []
    for d in design:
        out.append(f"{d} {anchor}".strip())
    for t in topic_queries[:2]:
        out += [f"{t} negative results OR \"does not improve\"", f"{t} reproducibility study",
                f"{t} benchmark evaluation flaws", f"{t} simple baseline matches"]
    if anchor:
        out += [f"\"{anchor}\" revisiting", f"\"{anchor}\" empirical comparison"]
    seen, uniq = set(), []
    for q in out:
        if q.lower() not in seen:
            seen.add(q.lower())
            uniq.append(q)
    return uniq


def map_landscape(client, topic_queries: list[str], sources: list[str], design: list[str] | None = None,
                  seeds: list[str] | None = None, anchor: str | None = None, strategies: list[str] | None = None,
                  limit: int = 12, from_year: int | None = None, expand_top: int = 3, per_bucket: int = 8,
                  progress=None) -> dict:
    design = design or []
    seeds = seeds or []
    strategies = strategies or DISCOVERY_STRATEGIES
    anchor = anchor if anchor is not None else (short_probes(topic_queries[:1])[0] if topic_queries else "")

    run = run_search(client, topic_queries, strategies, sources, limit, from_year, None, progress)
    papers = run["papers"]
    log = list(run["log"])
    status = run["sources_status"]
    dq = design_queries(design, anchor)
    if dq:
        drun = run_search(client, dq, ["keyword", "negative"], sources, limit, from_year, None, progress)
        papers = dedupe(papers + drun["papers"])
        log += drun["log"]
    fill_missing_abstracts(client, papers, " ".join(topic_queries[:1]), topic_queries)

    expansion = {"papers": [], "log": [], "errors": [], "seeds": []}
    if expand_top > 0 or seeds:
        expansion = expand(client, papers, expand_top, seeds, topic_queries, design=design)
        papers = dedupe(papers + [p for p in expansion["papers"] if p.title])
    papers = rank(papers, topic_queries + dq)

    entries = []
    for p in papers:
        types = classify(p)
        strategies_hit = sorted({f.get("strategy") for f in p.found_by if f.get("strategy")})
        entries.append({"paper": p, "evidence_types": types, "has_abstract": bool(p.abstract),
                        "found_by_strategies": strategies_hit,
                        "match": (p.extra.get("rank") or {}).get("score", 0.0)})
    # Order inside buckets by match to the topic, so off-topic papers that happen to say "versus" sink.
    entries.sort(key=lambda e: -e["match"])
    buckets = {t: [e for e in entries if t in e["evidence_types"]][:per_bucket] for t in EVIDENCE_PATTERNS}

    must_read, seen = [], set()
    # The best topic matches come first whatever their evidence type: in the sentiment audit the paper that had
    # already run the experiment ranked third overall but matched no evidence pattern in its abstract.
    # (Added after inspecting the dev retrieval fixtures; not yet checked on held-out topics.)
    top_overall = [("top match", e) for e in entries[:TOP_OVERALL]]
    bucketed = [(f"{t} candidate", e) for t in PRIORITY
                for e in buckets[t][: (2 if t in ("survey", "stated_limitation") else 4)]]
    for why, e in top_overall + bucketed:
        key = e["paper"].title.lower()
        if key in seen:
            continue
        seen.add(key)
        p = e["paper"]
        must_read.append({"title": p.title, "year": p.year, "arxiv_id": p.arxiv_id, "doi": p.doi,
                          "evidence_types": e["evidence_types"], "why": why,
                          "next": f"fulltext --id {p.arxiv_id}" if p.arxiv_id else "read an open copy or record "
                                                                                  "read_level 'abstract'"})
    failed = [s for s, st in status.items() if st["state"] == "failed"]
    coverage_notes = []
    if failed:
        coverage_notes.append(f"sources failed: {', '.join(failed)}")
    if not design:
        coverage_notes.append("no design elements: design-based retrieval skipped")
    if not seeds:
        coverage_notes.append("no seed papers: citing works of the benchmark/method paper not searched")
    if expansion["errors"]:
        coverage_notes.append(f"citation expansion had {len(expansion['errors'])} error(s)")
    title_only = sum(1 for e in entries if not e["has_abstract"])
    if entries and title_only / len(entries) > 0.3:
        coverage_notes.append(f"{title_only} of {len(entries)} records have no abstract; evidence types for them "
                              "rest on titles only")

    return {
        "topic_queries": topic_queries, "anchor": anchor, "design_elements": design, "design_queries": dq,
        "strategies": strategies, "seeds": expansion["seeds"], "sources_status": status,
        "n_papers": len(entries), "bucket_sizes": {t: sum(1 for e in entries if t in e["evidence_types"])
                                                   for t in EVIDENCE_PATTERNS},
        "buckets": buckets, "must_read": must_read,
        "web_search_queries": web_queries(anchor, design, topic_queries),
        "ledger_template": {"types": list(LEDGER_TYPES), "entry": {
            "id": "L1", "type": "one of types", "text": "what is unresolved, weak, contradicted or missing",
            "sources": ["paper keys"], "level": "verified only if read; record read_level on each paper"}},
        "coverage_notes": coverage_notes, "expansion_errors": expansion["errors"],
        "papers": [e["paper"] for e in entries], "entries": entries, "log": log,
    }
