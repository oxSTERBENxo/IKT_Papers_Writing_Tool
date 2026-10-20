"""Multi-source, multi-strategy literature search, identifier resolution and
citation-graph exploration."""
from __future__ import annotations

import datetime
import itertools
import math

from .http import SourceError
from .models import Paper, arxiv_from_doi, dedupe, parse_identifier
from .sources import arxiv, crossref, huggingface, openalex, pubmed, semanticscholar
from .text import coverage, title_similarity

SEARCHERS = {
    "openalex": openalex.search,
    "arxiv": arxiv.search,
    "crossref": crossref.search,
    "semantic_scholar": semanticscholar.search,
    "pubmed": pubmed.search,
    "huggingface": huggingface.search,
}
ALIASES = {"s2": "semantic_scholar", "hf": "huggingface", "semanticscholar": "semantic_scholar"}
DOMAIN_SOURCES = {
    "cs": ["openalex", "arxiv", "semantic_scholar", "crossref", "huggingface"],
    "biomed": ["openalex", "pubmed", "semantic_scholar", "crossref"],
    "general": ["openalex", "crossref", "semantic_scholar", "arxiv"],
}
# Only these can sort by citation count and still return on-topic papers.
CITATION_SORT = {"openalex", "semantic_scholar"}
RECENT_YEARS = 2

# strategy -> list of (query suffix, sort, restrict to recent years)
STRATEGIES = {
    "keyword": [("", "relevance", False)],
    "recent": [("", "relevance", True)],  # most relevant papers of the last RECENT_YEARS years
    "foundational": [("", "citations", False)],
    "limitations": [(" limitations", "relevance", False), (" challenges", "relevance", False)],
    "surveys": [(" survey", "relevance", False), (" review", "relevance", False)],
    "reproducibility": [(" reproducibility", "relevance", False), (" replication", "relevance", False)],
    # Literature-first discovery: published comparisons, negative results and critiques of benchmarks are the
    # papers most likely to have already run a proposed experiment, and keyword search ranks them low.
    "negative": [(" revisiting", "relevance", False), (" does not improve", "relevance", False)],
    "comparisons": [(" empirical comparison", "relevance", False)],
    "critique": [(" evaluation pitfalls", "relevance", False), (" simple baseline", "relevance", False)],
}
DISCOVERY_STRATEGIES = ["keyword", "surveys", "negative", "comparisons", "critique", "reproducibility"]
DISABLING_ERRORS = {"rate_limited", "auth", "network"}


def normalize_sources(names: list[str]) -> list[str]:
    out = []
    for name in names:
        name = ALIASES.get(name.strip().lower(), name.strip().lower())
        if name not in SEARCHERS:
            raise ValueError(f"unknown source '{name}'; choose from {sorted(SEARCHERS)}")
        if name not in out:
            out.append(name)
    return out


def expand_concepts(concepts: list[list[str]], cap: int = 12) -> tuple[list[str], bool]:
    """Cross product of synonym groups, e.g. [[GNN, graph neural network], [text classification]].
    Returns (queries, truncated)."""
    combos = [" ".join(parts) for parts in itertools.product(*[c for c in concepts if c])]
    return combos[:cap], len(combos) > cap


def design_queries(design: list[str], anchor: str) -> list[str]:
    """Search phrases built from experimental-design elements rather than topic keywords, e.g.
    'MLP baseline on the same node features' + anchor 'fake news propagation graph'. Papers that ran the same
    experiment describe its design, not necessarily the topic words of the idea."""
    out = []
    for d in design:
        q = f"{d} {anchor}".strip() if anchor and anchor.lower() not in d.lower() else d.strip()
        if q and q not in out:
            out.append(q)
    return out


RATE_LIMIT_COOLDOWN = 30.0  # seconds to wait once before giving up on a rate-limited source for the run


def run_search(client, queries: list[str], strategies: list[str], sources: list[str], limit: int = 15,
               from_year: int | None = None, to_year: int | None = None, progress=None,
               arxiv_match: str = "all", cooldown: float = 0.0) -> dict:
    """arxiv_match: 'all' (every content word required) or 'any' (relevance-ranked OR).
    cooldown: when > 0, a rate-limited source gets one retry after this many seconds before it is switched off
    for the rest of the run (one early arXiv 429 used to remove arXiv from a whole fixture)."""
    this_year = datetime.date.today().year
    collected: list[Paper] = []
    log: list[dict] = []
    disabled: dict[str, str] = {}
    cooled: set[str] = set()

    for strategy, query in itertools.product(strategies, queries):
        for suffix, sort, recent in STRATEGIES[strategy]:
            for source in sources:
                if source in disabled or (sort == "citations" and source not in CITATION_SORT):
                    continue
                full_query = query + suffix
                start = max(from_year or 0, this_year - RECENT_YEARS) if recent else from_year
                entry = {"source": source, "strategy": strategy, "query": full_query, "results": 0, "error": None}
                try:
                    try:
                        results = _call(client, source, full_query, limit, start, to_year, sort, arxiv_match)
                    except SourceError as exc:
                        if not (cooldown > 0 and exc.kind == "rate_limited" and source not in cooled):
                            raise
                        cooled.add(source)
                        entry["cooldown"] = cooldown
                        getattr(client, "_sleep", lambda s: None)(cooldown)
                        results = _call(client, source, full_query, limit, start, to_year, sort, arxiv_match)
                    for pos, paper in enumerate(results, 1):
                        paper.found_by.append({"source": source, "strategy": strategy, "query": full_query,
                                               "position": pos})
                    collected.extend(p for p in results if p.title)
                    entry["results"] = len(results)
                except SourceError as exc:
                    entry["error"] = exc.to_dict()
                    if exc.kind in DISABLING_ERRORS:
                        disabled[source] = exc.kind
                log.append(entry)
                if progress:
                    progress(entry)

    papers = rank(dedupe(collected), queries)
    return {
        "queries": queries, "strategies": strategies, "sources": sources,
        "from_year": from_year, "to_year": to_year,
        "sources_status": summarize_sources(sources, log, disabled),
        "n_retrieved": len(collected), "n_after_dedup": len(papers),
        "log": log, "papers": papers,
    }


def _call(client, source, query, limit, start, to_year, sort, arxiv_match):
    if source == "arxiv" and arxiv_match != "all":
        return SEARCHERS[source](client, query, limit, start, to_year, sort, match=arxiv_match)
    return SEARCHERS[source](client, query, limit, start, to_year, sort)


def summarize_sources(sources: list[str], log: list[dict], disabled: dict[str, str]) -> dict:
    status = {}
    for source in sources:
        entries = [e for e in log if e["source"] == source]
        errors = sorted({f"{e['error']['kind']}: {e['error']['message']}" for e in entries if e["error"]})
        ok = sum(1 for e in entries if not e["error"])
        status[source] = {
            "calls": len(entries), "ok_calls": ok, "results": sum(e["results"] for e in entries),
            "errors": errors, "stopped_after": disabled.get(source),
            "state": "ok" if ok and not errors else ("partial" if ok else "failed"),
        }
    return status


def rank(papers: list[Paper], queries: list[str]) -> list[Paper]:
    """Order by lexical match to the queries, then breadth of retrieval, then
    citations. A sorting aid only: the score says nothing about quality."""
    for p in papers:
        text = f"{p.title} {p.abstract or ''}"
        match = max((coverage(q, text) for q in queries), default=0.0)
        in_title = max((coverage(q, p.title) for q in queries), default=0.0)
        hits = len({(f["source"], f["query"]) for f in p.found_by})
        cites = math.log10(1 + (p.citations or 0)) / 4
        p.extra["rank"] = {"query_match": round(match, 3), "title_match": round(in_title, 3),
                           "retrieval_hits": hits,
                           "score": round(2 * match + in_title + 0.5 * min(hits, 4) / 4 + 0.3 * min(cites, 1), 3)}
    return sorted(papers, key=lambda p: -p.extra["rank"]["score"])


# -- identifier resolution ------------------------------------------------
def resolve(client, ident: str) -> tuple[Paper | None, list[dict]]:
    """Look an identifier (arXiv ID, DOI, OpenAlex ID, PMID, URL or title) up in
    every source that knows it and merge the records. Returns (paper, notes)."""
    kind, value = parse_identifier(ident)
    found: list[Paper] = []
    notes: list[dict] = []

    def attempt(fn, *args):
        try:
            paper = fn(client, *args)
            if paper and paper.title:
                found.append(paper)
        except SourceError as exc:
            notes.append(exc.to_dict())

    if kind == "arxiv":
        attempt(arxiv.get_paper, value)
        attempt(semanticscholar.get_paper, f"ARXIV:{value}")
    elif kind == "doi":
        attempt(openalex.get_work, value)
        attempt(crossref.get_work, value)
        attempt(semanticscholar.get_paper, f"DOI:{value}")
    elif kind == "openalex":
        attempt(openalex.get_work, value)
    elif kind == "pmid":
        attempt(pubmed.get_paper, value)
        attempt(semanticscholar.get_paper, f"PMID:{value}")
    else:
        candidates: list[Paper] = []
        for fn, args in ((openalex.search, (value, 5)), (arxiv.search, (f'"{value}"', 5))):
            try:
                candidates.extend(fn(client, *args))
            except SourceError as exc:
                notes.append(exc.to_dict())
        matches = [c for c in candidates if title_similarity(c.title, value) >= 0.85]
        if not matches:
            notes.append({"source": "resolve", "kind": "not_found",
                          "message": "no record with a closely matching title",
                          "nearest_titles": [c.title for c in candidates[:5]]})
            return None, notes
        found.extend(matches)

    if not found:
        return None, notes
    paper = dedupe(found)[0]

    # Attach the OpenAlex record (citation graph, published DOI) when the lookup did not go through it.
    if not paper.openalex_id:
        try:
            for cand in openalex.search(client, paper.title, 5):
                if title_similarity(cand.title, paper.title) >= 0.92:
                    paper.absorb(cand)
                    break
        except SourceError as exc:
            notes.append(exc.to_dict())

    # Crossref is the registry of record for a published DOI: take the venue and
    # date from it, so a preprint's year is never paired with the journal's DOI.
    if paper.doi and not arxiv_from_doi(paper.doi) and "crossref" not in paper.sources:
        try:
            registered = crossref.get_work(client, paper.doi)
            for name in ("year", "date", "venue"):
                if getattr(registered, name):
                    setattr(paper, name, getattr(registered, name))
            paper.sources = sorted(set(paper.sources) | {"crossref"})
        except SourceError as exc:
            notes.append(exc.to_dict())
    return paper, notes


# -- citation graph ---------------------------------------------------------
def related(client, paper: Paper, direction: str = "all", limit: int = 25) -> dict:
    """References, citing works and related works of a paper."""
    seed = paper.openalex_id or paper.arxiv_id or paper.doi or paper.title
    collected: list[Paper] = []
    errors: list[dict] = []
    counts: dict[str, int] = {}

    def add(label: str, source: str, fn, *args, **kwargs):
        try:
            results = [p for p in fn(client, *args, **kwargs) if p.title]
        except SourceError as exc:
            errors.append({**exc.to_dict(), "step": label})
            return
        for p in results:
            p.found_by.append({"source": source, "strategy": label, "query": seed})
        counts[label] = counts.get(label, 0) + len(results)
        collected.extend(results)

    wanted = {"references", "citations", "related"} if direction == "all" else {direction}
    full = None
    if paper.openalex_id:
        try:
            full = openalex.get_work(client, paper.openalex_id)
        except SourceError as exc:
            errors.append({**exc.to_dict(), "step": "openalex_record"})
    s2_ref = (f"ARXIV:{paper.arxiv_id}" if paper.arxiv_id else f"DOI:{paper.doi}" if paper.doi else paper.s2_id)

    if "references" in wanted:
        if full and full.extra.get("referenced_works"):
            add("references", "openalex", openalex.by_ids, full.extra["referenced_works"], limit)
        elif s2_ref:
            add("references", "semantic_scholar", semanticscholar.references, s2_ref, limit)
    if "citations" in wanted:
        if paper.openalex_id:
            add("citations_most_cited", "openalex", openalex.citing, paper.openalex_id, limit, "citations")
            add("citations_most_recent", "openalex", openalex.citing, paper.openalex_id, limit, "date")
        elif s2_ref:
            add("citations", "semantic_scholar", semanticscholar.citations, s2_ref, limit)
    if "related" in wanted:
        if full and full.extra.get("related_works"):
            add("related", "openalex", openalex.by_ids, full.extra["related_works"], limit)
        if s2_ref:
            add("recommended", "semantic_scholar", semanticscholar.recommendations, s2_ref, limit)

    return {"seed": paper, "counts": counts, "errors": errors, "papers": dedupe(collected)}
