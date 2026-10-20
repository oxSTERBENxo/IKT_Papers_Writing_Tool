"""Retrieval evaluation: how many curated, known-relevant papers does each retrieval configuration find, and how
early does it rank them?

A fixture describes one research idea the way a student would start: a claim, topic queries, experimental
design elements, the seed papers they already know, and the papers an audit later showed to be the closest
prior work ("known_relevant"). Seeds are never counted as hits.

Configurations. The first four are the 2026-10-19 regression set and are unchanged:
- baseline:  keyword challenge only (keyword, surveys, recent); no design elements, seeds or citation expansion.
             This approximates the toolkit before the adversarial-verification update.
- challenge: the current default challenge (design-based queries, seed citing-works search, citation expansion).
- landscape: the literature-first map.
- full:      union of challenge and landscape, no additional requests.
Retrieval-reliability experiments (2026-10-19, see evals/results/2026-10-19-retrieval-reliability.md):
- challenge_arxiv_any: challenge with arXiv queries as relevance-ranked OR instead of all-words AND, and one
             cool-down retry for a rate-limited source. Query formulation only; ranking unchanged.
- challenge_lexical:   challenge_arxiv_any plus rank fusion over the claim and each query (fusion.py).
- challenge_hybrid:    challenge_lexical plus a local-embedding similarity list (semantic.py; optional
             dependency). Falls back to challenge_lexical, and says so, when no embedding backend is installed.

Metrics per configuration: Recall@20, Recall@50, MRR (reciprocal rank of each target, 0 if missed, averaged over
targets), candidate coverage (share of targets anywhere in the candidate list), number of candidates, HTTP calls
(cached or not), network requests, runtime, source failures, and the challenge verdict.

Every missed target gets a cause:
- source_unavailable: the target is only indexed by sources that failed or were rate-limited in this run;
- not_in_searched_indexes: none of the searched sources indexes it (no arXiv ID with arXiv searched, no
  Crossref-registered DOI with Crossref searched); recorded from identifiers, not checked live;
- algorithm: an indexed source was available, but no query, strategy or citation step returned it.

Recall on a few dozen papers is an estimate with very wide uncertainty; it cannot establish that novelty
detection is reliable. Ordinary web search is not automated here.
"""
from __future__ import annotations

import glob
import itertools
import json
import time
from pathlib import Path

from .landscape import map_landscape
from .models import arxiv_from_doi, normalize_arxiv_id, normalize_doi
from .novelty import challenge
from .text import title_similarity

REGRESSION_CONFIGS = ("baseline", "challenge", "landscape", "full")
EXPERIMENT_CONFIGS = ("challenge_arxiv_any", "challenge_lexical", "challenge_hybrid")
CONFIGS = REGRESSION_CONFIGS + EXPERIMENT_CONFIGS
# control fixtures are implausible ideas with no expected prior work: they measure how often the challenge signal
# claims close prior work when there should be none (false alarms), which recall on positives cannot show.
# blind fixtures were frozen before their targets were searched (evals/retrieval_blind/).
SPLITS = ("dev", "heldout", "control", "blind")
TOP_K = 20
CUTOFFS = (20, 50)
CHALLENGE_VARIANTS = {
    "challenge": {},
    "challenge_arxiv_any": {"arxiv_match": "any", "cooldown": 30.0},
    "challenge_lexical": {"arxiv_match": "any", "cooldown": 30.0, "ranking": "fusion"},
    "challenge_hybrid": {"arxiv_match": "any", "cooldown": 30.0, "ranking": "fusion", "semantic": True},
}


def load_fixtures(pattern: str) -> list[dict]:
    paths = sorted(glob.glob(pattern)) if any(c in pattern for c in "*?[") else [pattern]
    fixtures = []
    for path in paths:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        for fx in data if isinstance(data, list) else [data]:
            for key in ("id", "split", "claim", "queries", "known_relevant"):
                if key not in fx:
                    raise ValueError(f"{path}: fixture lacks '{key}'")
            if fx["split"] not in SPLITS:
                raise ValueError(f"{path}: split must be one of {SPLITS}")
            if fx["split"] != "control" and not fx["known_relevant"]:
                raise ValueError(f"{path}: fixtures other than controls need known_relevant papers")
            fixtures.append(fx)
    return fixtures


def _ident(p: dict) -> tuple:
    return normalize_arxiv_id(p.get("arxiv_id")), normalize_doi(p.get("doi")), p.get("title") or ""


def matches(known: dict, cand: dict) -> bool:
    ka, kd, kt = _ident(known)
    ca, cd, ct = _ident(cand)
    if ka and ca and ka == ca:
        return True
    if kd and cd and kd == cd:
        return True
    return bool(kt and ct and title_similarity(kt, ct) >= 0.9)


def first_rank(known: dict, ranked: list[dict]) -> int | None:
    for i, cand in enumerate(ranked, 1):
        if matches(known, cand):
            return i
    return None


def _paper_dict(p) -> dict:
    return {"title": p.title, "arxiv_id": p.arxiv_id, "doi": p.doi, "year": p.year}


def indexed_in(known: dict, sources: list[str]) -> list[str]:
    """Searched sources that should hold the target, judged from its identifiers (not checked live)."""
    out = []
    doi = normalize_doi(known.get("doi"))
    has_arxiv = bool(known.get("arxiv_id")) or bool(doi and arxiv_from_doi(doi))
    if has_arxiv and "arxiv" in sources:
        out.append("arxiv")
    if doi and not arxiv_from_doi(doi) and "crossref" in sources:
        out.append("crossref")
    for broad in ("openalex", "semantic_scholar", "huggingface"):
        if broad in sources:  # broad aggregators: assume coverage; their failures are recorded per run
            out.append(broad)
    return out


def miss_cause(known: dict, sources: list[str], failed: list[str], degraded: list[str]) -> str:
    holders = indexed_in(known, sources)
    if not holders:
        return "not_in_searched_indexes"
    if all(h in failed or h in degraded for h in holders):
        return "source_unavailable"
    return "algorithm"


def _degraded(status: dict) -> list[str]:
    return [s for s, st in status.items() if st.get("state") == "partial" or st.get("stopped_after")]


def _run_challenge(client, fx, sources, limit, progress, **kw):
    seeds = fx.get("seeds") or []
    t0, calls0, req0 = time.monotonic(), client.call_count, client.request_count
    r = challenge(client, fx["claim"], fx["queries"], sources, limit, design=fx.get("design") or [],
                  seeds=seeds, expand_top=3, anchor=fx.get("anchor"), progress=progress, **kw)
    meta = {"signal": r["signal"], "failed": r["sources_failed"], "degraded": _degraded(r["sources_status"]),
            "n": r["n_papers_examined"], "expansion_errors": len(r["expansion_errors"]),
            "seconds": round(time.monotonic() - t0, 1), "http_calls": client.call_count - calls0,
            "network_requests": client.request_count - req0, "ranking": r.get("ranking"),
            "semantic_model": r.get("semantic_model"), "arxiv_match": r.get("arxiv_match")}
    return r["ranked"], meta


def run_fixture(client, fx: dict, sources: list[str], configs=REGRESSION_CONFIGS, limit: int = 10,
                progress=None) -> dict:
    seeds = fx.get("seeds") or []
    targets = [k for k in fx["known_relevant"] if not any(matches(k, {"arxiv_id": s, "doi": s, "title": s})
                                                          for s in seeds)]
    lists: dict[str, list[dict]] = {}
    meta: dict[str, dict] = {}
    if "baseline" in configs:
        t0, calls0, req0 = time.monotonic(), client.call_count, client.request_count
        r = challenge(client, fx["claim"], fx["queries"], sources, limit, expand_top=0, progress=progress)
        lists["baseline"] = r["ranked"]
        meta["baseline"] = {"signal": r["signal"], "failed": r["sources_failed"],
                            "degraded": _degraded(r["sources_status"]), "n": r["n_papers_examined"],
                            "seconds": round(time.monotonic() - t0, 1), "http_calls": client.call_count - calls0,
                            "network_requests": client.request_count - req0}
    for name, kw in CHALLENGE_VARIANTS.items():
        if name in configs or (name == "challenge" and "full" in configs):
            if kw.get("semantic"):
                from . import semantic
                if not semantic.available():
                    kw = {k: v for k, v in kw.items() if k != "semantic"}
            lists[name], meta[name] = _run_challenge(client, fx, sources, limit, progress, **kw)
    if "landscape" in configs or "full" in configs:
        t0, calls0, req0 = time.monotonic(), client.call_count, client.request_count
        m = map_landscape(client, fx["queries"], sources, design=fx.get("design") or [], seeds=seeds,
                          anchor=fx.get("anchor"), limit=limit, progress=progress)
        lists["landscape"] = [_paper_dict(e["paper"]) for e in m["entries"]]
        must = [{"title": x["title"], "arxiv_id": x["arxiv_id"], "doi": x["doi"]} for x in m["must_read"]]
        meta["landscape"] = {"n": m["n_papers"], "must_read": must, "coverage_notes": m["coverage_notes"],
                             "failed": [n for n, st in m["sources_status"].items() if st["state"] == "failed"],
                             "degraded": _degraded(m["sources_status"]), "bucket_sizes": m["bucket_sizes"],
                             "seconds": round(time.monotonic() - t0, 1), "http_calls": client.call_count - calls0,
                             "network_requests": client.request_count - req0}
    if "full" in configs:
        merged, seen = [], set()
        # Interleave the two rankings so neither dominates the top of the union.
        for pair in itertools.zip_longest(lists.get("challenge", []), lists.get("landscape", [])):
            for cand in pair:
                key = (cand or {}).get("title", "").lower()
                if cand and key not in seen:
                    seen.add(key)
                    merged.append(cand)
        lists["full"] = merged
        meta["full"] = {"failed": sorted(set(meta["challenge"]["failed"]) | set(meta["landscape"]["failed"])),
                        "degraded": sorted(set(meta["challenge"]["degraded"]) | set(meta["landscape"]["degraded"]))}

    per_config = {}
    for name in configs:
        ranked = lists.get(name, [])
        m = meta.get(name, {})
        hits = []
        for k in targets:
            rank = first_rank(k, ranked)
            entry = {"title": k.get("title"), "rank": rank, "found": rank is not None,
                     "in_top_k": rank is not None and rank <= TOP_K}
            if rank is None:
                entry["cause"] = miss_cause(k, sources, m.get("failed") or [], m.get("degraded") or [])
            if name == "landscape":
                entry["in_must_read"] = any(matches(k, x) for x in meta["landscape"]["must_read"])
            hits.append(entry)
        n = len(targets) or 1  # controls have no targets; their recall fields are meaningless
        per_config[name] = {
            "recall_any": round(sum(h["found"] for h in hits) / n, 3),
            f"recall_at_{TOP_K}": round(sum(h["in_top_k"] for h in hits) / n, 3),
            "recall_at_50": round(sum(1 for h in hits if h["rank"] and h["rank"] <= 50) / n, 3),
            "mrr": round(sum(1 / h["rank"] for h in hits if h["rank"]) / n, 3),
            "median_rank_of_found": _median([h["rank"] for h in hits if h["rank"]]),
            "n_retrieved": len(ranked), "hits": hits, **m,
        }
    return {"id": fx["id"], "split": fx["split"], "n_targets": len(targets), "configs": per_config,
            "missed_by_all": [k.get("title") for k in targets
                              if not any(first_rank(k, lists.get(c, [])) for c in configs)]}


def _median(values):
    values = sorted(values)
    if not values:
        return None
    mid = len(values) // 2
    return values[mid] if len(values) % 2 else (values[mid - 1] + values[mid]) / 2


def summarize(results: list[dict], configs=REGRESSION_CONFIGS) -> dict:
    out = {}
    for split in ("dev", "heldout", "blind"):
        rs = [r for r in results if r["split"] == split]
        if not rs:
            continue
        out[split] = {}
        for c in configs:
            hits = [h for r in rs if c in r["configs"] for h in r["configs"][c]["hits"]]
            total = sum(r["n_targets"] for r in rs)
            found = sum(h["found"] for h in hits)
            top = sum(h["in_top_k"] for h in hits)
            at50 = sum(1 for h in hits if (h.get("rank") or 99999) <= 50)
            causes: dict[str, int] = {}
            for h in hits:
                if not h["found"]:
                    causes[h.get("cause", "unknown")] = causes.get(h.get("cause", "unknown"), 0) + 1
            cfgs = [r["configs"][c] for r in rs if c in r["configs"]]
            out[split][c] = {"targets": total, "found": found, f"in_top_{TOP_K}": top, "in_top_50": at50,
                             "recall_any": round(found / total, 3) if total else None,
                             f"recall_at_{TOP_K}": round(top / total, 3) if total else None,
                             "recall_at_50": round(at50 / total, 3) if total else None,
                             "mrr": round(sum(1 / h["rank"] for h in hits if h.get("rank")) / total, 3) if total else None,
                             "miss_causes": causes,
                             "fixtures_with_source_failures": sum(1 for x in cfgs if x.get("failed") or x.get("degraded")),
                             "mean_candidates": _mean([x.get("n_retrieved") for x in cfgs]),
                             "http_calls": sum(x.get("http_calls") or 0 for x in cfgs),
                             "network_requests": sum(x.get("network_requests") or 0 for x in cfgs),
                             "seconds": round(sum(x.get("seconds") or 0 for x in cfgs), 1)}
    signals = {}
    signal_configs = [c for c in ("baseline",) + tuple(CHALLENGE_VARIANTS) if c in configs]
    for split in SPLITS:
        rs = [r for r in results if r["split"] == split]
        if not rs:
            continue
        signals[split] = {c: {"fixtures": len(rs), "flagged_prior_work": sum(
            1 for r in rs if (r["configs"].get(c) or {}).get("signal") in ("close_prior_work_found", "crowded"))}
            for c in signal_configs if any(c in r["configs"] for r in rs)}
    out["challenge_signal"] = signals
    out["caveat"] = ("Pooled over few topics and few known papers per topic; treat differences of one or two papers "
                     "as noise. Live results depend on rate limits and index coverage on the day of the run.")
    return out


def _mean(values):
    values = [v for v in values if v is not None]
    return round(sum(values) / len(values), 1) if values else None
