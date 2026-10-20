"""Novelty challenge: search for work that already does what a candidate
research idea proposes.

The output is a triage signal. It can show that an idea is crowded; it can
never show that an idea is new, because a search only covers the sources,
queries and wording that were tried.

Beyond keyword search, the challenge
- follows the citation graph (citing works and references) of the closest
  retrieved papers and of any seed papers the analyst names, because papers
  that run the same experiment under different words are usually linked to
  the same benchmark or method paper;
- searches the works citing each seed for the challenge queries;
- matches papers against the experimental design elements of the idea
  (``design``), so a paper that runs the same comparison under another name
  is still flagged;
- lowers the confidence ceiling whenever coverage was incomplete, and says why.
"""
from __future__ import annotations

import itertools
import re

from .http import SourceError
from .models import dedupe
from .search import design_queries, related, resolve, run_search
from .sources import arxiv, openalex
from .text import coverage, distinctive_coverage, tfidf_cosine, tokens

HIGH_OVERLAP = 0.6  # rarity-weighted share of the claim's terms found in a title+abstract
MAX_ABSTRACT_LOOKUPS = 15
# A search only says something about an idea if it reached the idea's neighbourhood.
NEIGHBOUR_OVERLAP, MIN_NEIGHBOURS = 0.3, 5
CROWDED_COUNT = 8
DESIGN_MATCH = 0.6        # share of a design element's terms that must appear
DESIGN_MIN_ELEMENTS = 2   # elements matched before a paper is flagged as a possible same experiment
PARAPHRASE_JACCARD = 0.5  # mean pairwise term overlap above which queries are near-paraphrases
TITLE_ONLY_LIMIT = 0.3    # share of title-only records among the closest ten that lowers the ceiling
EXPANSION_STRATEGIES = {"citations_most_cited", "citations_most_recent", "references", "citations",
                        "seed_citing_search", "seed_citations", "seed_references"}
LEVELS = ("very_low", "low", "medium")
SURVEY_RE = re.compile(r"\b(survey|review|overview|benchmark|tutorial|meta-analysis)\b", re.I)
CAVEAT = ("Absence of a close match is not evidence of novelty. This search covered only the listed sources "
          "and queries, matched on wording rather than meaning, and did not read full texts. Read the closest "
          "papers (full text where accessible) before making any claim, and report novelty as unverified.")


def query_diversity(queries: list[str]) -> dict:
    sets = [set(tokens(q)) for q in queries if tokens(q)]
    pairs = list(itertools.combinations(sets, 2))
    jac = [len(a & b) / len(a | b) for a, b in pairs if a | b]
    mean = round(sum(jac) / len(jac), 3) if jac else 0.0
    return {"n_queries": len(queries), "distinct_terms": len(set().union(*sets)) if sets else 0,
            "mean_pairwise_term_overlap": mean, "near_paraphrases": len(queries) > 1 and mean > PARAPHRASE_JACCARD}


def design_matches(design: list[str], text: str) -> list[str]:
    return [d for d in design if coverage(d, text) >= DESIGN_MATCH]


def short_probes(texts: list[str], words: int = 3) -> list[str]:
    """OpenAlex's citing-works text filter needs every word to match, so a sentence-length query returns
    nothing. Reduce each text to its few most distinctive words (longest content words, a rough proxy for
    rarity), keeping the original spelling, and drop duplicates."""
    probes = []
    for text in texts:
        content = [w for w in re.findall(r"[A-Za-z0-9-]+", text) if tokens(w)]
        picked = sorted(dict.fromkeys(content), key=lambda w: -len(w))[:words]
        probe = " ".join(w for w in content if w in picked)
        if probe and probe.lower() not in [p.lower() for p in probes]:
            probes.append(probe)
    return probes


def expand(client, papers: list, top_n: int, seeds: list[str], queries: list[str], limit: int = 25,
           design: list[str] | None = None) -> dict:
    """Citation-graph expansion. Returns {'papers', 'log', 'errors', 'seeds'}."""
    found, log, errors, seed_info = [], [], [], []
    probes = short_probes(list(queries) + list(design or []))

    def tag(results, strategy, seed_label):
        for p in results:
            p.found_by.append({"source": "openalex", "strategy": strategy, "query": seed_label})
        return results

    for ident in seeds:
        paper, notes = resolve(client, ident)
        if paper is None:
            errors.append({"step": "seed", "source": "resolve", "kind": "not_found", "message": ident})
            seed_info.append({"seed": ident, "resolved": False})
            continue
        seed_info.append({"seed": ident, "resolved": True, "title": paper.title, "openalex_id": paper.openalex_id})
        rel = related(client, paper, "all" if not paper.openalex_id else "references", limit)
        found += tag(rel["papers"], "seed_references", ident)
        errors += rel["errors"]
        if paper.openalex_id:
            for sort in ("citations", "date"):
                try:
                    found += tag(openalex.citing(client, paper.openalex_id, limit * 2, sort), "seed_citations", ident)
                except SourceError as exc:
                    errors.append({**exc.to_dict(), "step": "seed_citations"})
            for probe in probes:
                try:
                    hits = openalex.citing(client, paper.openalex_id, limit, "citations", text=probe)
                    found += tag(hits, "seed_citing_search", f"{ident} :: {probe}")
                    log.append({"seed": ident, "query": probe, "results": len(hits)})
                except SourceError as exc:
                    errors.append({**exc.to_dict(), "step": "seed_citing_search"})
        else:
            errors.append({"step": "seed_citations", "source": "openalex", "kind": "not_found",
                           "message": f"no OpenAlex record for seed {ident}; citing works not searched"})

    for paper in [p for p in papers if p.openalex_id or p.arxiv_id or p.doi][:top_n]:
        rel = related(client, paper, "citations", limit)
        found += rel["papers"]
        errors += rel["errors"]
        ref = related(client, paper, "references", limit)
        found += ref["papers"]
        errors += ref["errors"]
        log.append({"expanded": paper.title, "citing_and_references": len(rel["papers"]) + len(ref["papers"])})
    return {"papers": found, "log": log, "errors": errors, "seeds": seed_info}


def challenge(client, claim: str, queries: list[str], sources: list[str], limit: int = 15,
              from_year: int | None = None, top: int = 12, progress=None, design: list[str] | None = None,
              seeds: list[str] | None = None, expand_top: int = 3, anchor: str | None = None,
              ranking: str = "claim", semantic: bool = False, arxiv_match: str = "all",
              cooldown: float = 0.0) -> dict:
    """ranking: 'claim' (original order: overlap with the claim) or 'fusion' (reciprocal rank fusion, fusion.py).
    semantic: add a local-embedding similarity list to the fusion (semantic.py; optional dependency).
    arxiv_match / cooldown: see search.run_search. The verdict ('signal') logic is the same in every mode."""
    if ranking not in ("claim", "fusion"):
        raise ValueError("ranking must be 'claim' or 'fusion'")
    design = [d for d in (design or []) if tokens(d)]
    seeds = seeds or []
    search_kw = {"arxiv_match": arxiv_match, "cooldown": cooldown}
    run = run_search(client, queries, ["keyword", "surveys", "recent"], sources, limit, from_year, None, progress,
                     **search_kw)
    papers = run["papers"]
    # Design-based retrieval: the experiment described in its own words, anchored to the topic.
    anchor = anchor if anchor is not None else (short_probes([claim])[0] if short_probes([claim]) else "")
    dq = design_queries(design, anchor)
    if dq:
        drun = run_search(client, dq, ["keyword"], sources, limit, from_year, None, progress, **search_kw)
        papers = dedupe(papers + drun["papers"])
        run["log"] += drun["log"]
        for name, st in drun["sources_status"].items():
            base = run["sources_status"].setdefault(name, st)
            if base is not st and st["state"] == "failed" and base["state"] == "ok":
                base["state"] = "partial"
    fetched = fill_missing_abstracts(client, papers, claim, queries)

    # First pass ranks the keyword results; the closest of them seed the citation expansion.
    semantic_note = None
    if semantic:
        from . import semantic as sem
        semantic_note = sem.describe()
    first = _order(_score(claim, papers, design), claim, queries, design, ranking, semantic)
    expansion = {"papers": [], "log": [], "errors": [], "seeds": []}
    if expand_top > 0 or seeds:
        expansion = expand(client, [s["paper"] for s in first], expand_top, seeds, queries, design=design)
        if expansion["papers"]:
            papers = dedupe(papers + [p for p in expansion["papers"] if p.title])
            fetched += fill_missing_abstracts(client, papers, claim, queries)
    scored = _order(_score(claim, papers, design), claim, queries, design, ranking, semantic)

    high = [s for s in scored if s["term_overlap"] >= HIGH_OVERLAP]
    # A design match only signals prior work when the paper is also on topic: generic design elements ("MLP
    # baseline", "shuffled features") match many unrelated papers (a negative-control fixture was flagged by a
    # WiFi floor-classification paper). Off-topic design matches are still listed for reading.
    design_hits = [s for s in scored if len(s["design_elements_matched"]) >= DESIGN_MIN_ELEMENTS]
    same_design = [s for s in design_hits if s["term_overlap"] >= NEIGHBOUR_OVERLAP]
    design_off_topic = [s for s in design_hits if s["term_overlap"] < NEIGHBOUR_OVERLAP]
    ok_sources = [s for s, st in run["sources_status"].items() if st["state"] != "failed"]
    failed_sources = [s for s, st in run["sources_status"].items() if st["state"] == "failed"]
    diversity = query_diversity(queries)

    if len(high) >= CROWDED_COUNT or any(s["is_survey_like"] for s in high):
        signal, ceiling = "crowded", "very_low"
        reading = ("Many closely worded papers, or a survey of the exact topic, were found. Treat the topic as "
                   "well studied unless a specific, narrower gap survives reading them.")
    elif high or same_design:
        signal, ceiling = "close_prior_work_found", "low"
        reading = ("Prior work close to the idea exists" + (" (matching its wording)" if high else "") +
                   (f"; {len(same_design)} paper(s) mention {DESIGN_MIN_ELEMENTS}+ of the stated design elements, "
                    "so the same experiment may have been run under different words" if same_design else "") +
                   ". Read them in full. Revise the idea to differ in a stated, checkable way, or reframe it as a "
                   "replication or extension.")
    else:
        signal = "no_close_match_in_this_search"
        neighbours = sum(1 for s in scored if s["term_overlap"] >= NEIGHBOUR_OVERLAP)
        broad = len(ok_sources) >= 3 and len(queries) >= 4 and not set(failed_sources) & {"openalex",
                                                                                         "semantic_scholar"}
        ceiling = "medium" if broad and neighbours >= MIN_NEIGHBOURS else "low"
        if neighbours < MIN_NEIGHBOURS:
            reading = (f"No closely worded paper was retrieved, but only {neighbours} retrieved paper(s) were even "
                       "loosely related, so the queries probably missed the relevant literature. Reword the "
                       "queries and follow the citations of the nearest known paper before concluding anything.")
        else:
            reading = ("No closely worded paper was retrieved among related work. This supports only an "
                       "'unverified novelty hypothesis'; coverage was " + ("reasonable" if broad else
                       "degraded (" + (", ".join(failed_sources) + " failed" if failed_sources else "few sources or queries")
                       + ")") + ".")

    # Coverage gaps can only lower the ceiling.
    reasons = []
    top10 = scored[:10]
    title_only = sum(1 for s in top10 if not s["has_abstract"]) / len(top10) if top10 else 0.0
    if failed_sources:
        reasons.append(f"sources failed: {', '.join(failed_sources)}")
    if len(queries) < 4:
        reasons.append(f"only {len(queries)} query phrasing(s); use at least 4")
    if diversity["near_paraphrases"]:
        reasons.append("the queries are near-paraphrases of each other; add alternative terminology, "
                       "method-equivalent and critic phrasings")
    if expand_top <= 0 and not seeds:
        reasons.append("citation graph not followed (expand_top=0 and no seeds)")
    elif expansion["errors"] and not expansion["papers"]:
        reasons.append("citation expansion failed")
    elif expansion["errors"]:
        kinds = sorted({e.get("kind") or "error" for e in expansion["errors"]})
        reasons.append(f"citation expansion partly failed ({len(expansion['errors'])} call(s): {', '.join(kinds)})")
    unresolved = [s["seed"] for s in expansion["seeds"] if not s.get("resolved")]
    if unresolved:
        reasons.append(f"seed(s) not resolved: {', '.join(unresolved)}")
    if title_only > TITLE_ONLY_LIMIT:
        reasons.append(f"{title_only:.0%} of the ten closest records have no abstract")
    if not design:
        reasons.append("no design elements given, so differently worded versions of the same experiment were "
                       "not checked")
    if reasons and LEVELS.index(ceiling) > LEVELS.index("low"):
        ceiling = "low"

    via_citations = [s for s in scored if s["found_only_via_citations"]
                     and (s["term_overlap"] >= NEIGHBOUR_OVERLAP or s["design_elements_matched"])]
    must_read = []
    for s in scored[:5] + same_design[:5] + via_citations[:5] + [s for s in high if s["is_survey_like"]][:2]:
        p = s["paper"]
        entry = {"title": p.title, "year": p.year, "arxiv_id": p.arxiv_id, "doi": p.doi, "pdf_url": p.pdf_url,
                 "why": _why(s), "next": f"fulltext --id {p.arxiv_id}" if p.arxiv_id else
                 ("read the open-access PDF" if p.pdf_url else "find an accessible copy; otherwise record "
                  "read_level 'abstract' or 'not_accessible'")}
        if entry not in must_read:
            must_read.append(entry)

    return {
        "claim": claim, "queries": queries, "design_elements": design, "design_queries": dq, "anchor": anchor,
        "seeds": expansion["seeds"],
        "sources_ok": ok_sources, "sources_failed": failed_sources, "sources_status": run["sources_status"],
        "query_diversity": diversity,
        "n_papers_examined": len(papers), "n_high_overlap": len(high), "abstracts_fetched": fetched,
        "n_without_abstract": sum(1 for p in papers if not p.abstract),
        "n_from_citation_expansion": sum(1 for s in scored if s["found_only_via_citations"]),
        "n_possible_same_design": len(same_design), "n_design_matches_off_topic": len(design_off_topic),
        "high_overlap_by_year": _by_year(high),
        "signal": signal, "max_supported_novelty_confidence": ceiling, "ceiling_lowered_because": reasons,
        "interpretation": reading, "caveat": CAVEAT,
        "closest": scored[:top], "possible_same_design": same_design[:top],
        "design_matches_off_topic": design_off_topic[:top], "found_via_citations": via_citations[:top],
        "ranked": [{"title": x["paper"].title, "arxiv_id": x["paper"].arxiv_id, "doi": x["paper"].doi,
                    "year": x["paper"].year} for x in scored],
        "ranking": ranking, "semantic_model": semantic_note, "arxiv_match": arxiv_match,
        "must_read": must_read, "expansion_log": expansion["log"], "expansion_errors": expansion["errors"],
        "log": run["log"],
    }


def _score(claim: str, papers: list, design: list[str]) -> list[dict]:
    if not papers:
        return []
    texts = [f"{p.title} {p.abstract or ''}" for p in papers]
    cosines = tfidf_cosine(claim, texts)
    overlaps = distinctive_coverage(claim, texts)
    scored = []
    for paper, text, cov, cos in zip(papers, texts, overlaps, cosines):
        strategies = {f.get("strategy") for f in paper.found_by}
        matched = design_matches(design, text)
        scored.append({
            "paper": paper, "term_overlap": round(cov, 3), "tfidf_similarity": round(cos, 3),
            "design_elements_matched": matched,
            "is_survey_like": bool(SURVEY_RE.search(paper.title)),
            "has_abstract": bool(paper.abstract),
            "found_only_via_citations": bool(strategies) and strategies <= EXPANSION_STRATEGIES,
        })
    scored.sort(key=lambda s: -(s["term_overlap"] + s["tfidf_similarity"]
                                + 0.25 * len(s["design_elements_matched"])))
    return scored


def _order(scored: list[dict], claim: str, queries: list[str], design: list[str], ranking: str,
           semantic: bool) -> list[dict]:
    if ranking == "claim" or not scored:
        return scored
    from .fusion import fuse
    sims = None
    if semantic:
        from . import semantic as sem
        sims = sem.similarities([claim, *queries], [f"{s['paper'].title}. {s['paper'].abstract or ''}"
                                                    for s in scored])
    fused = fuse(claim, queries, [s["paper"] for s in scored], sims)
    for s, (score, parts) in zip(scored, fused):
        s["fusion_score"], s["fusion"] = round(score, 5), parts
    return sorted(scored, key=lambda s: -s["fusion_score"])


def _why(s: dict) -> str:
    parts = [f"term overlap {s['term_overlap']}"]
    if s["design_elements_matched"]:
        parts.append("design elements: " + "; ".join(s["design_elements_matched"]))
    if s["found_only_via_citations"]:
        parts.append("found only through the citation graph")
    if s["is_survey_like"]:
        parts.append("survey-like")
    if not s["has_abstract"]:
        parts.append("no abstract retrieved")
    return ", ".join(parts)


def fill_missing_abstracts(client, papers: list, claim: str, queries: list[str]) -> int:
    """Some sources return titles only, which hides how close a paper really is.
    Look up abstracts for the most promising title-only records."""
    missing = [p for p in papers if not p.abstract and (p.doi or p.arxiv_id)]
    missing.sort(key=lambda p: -max(coverage(q, p.title) for q in [claim, *queries]))
    fetched = 0
    for paper in missing[:MAX_ABSTRACT_LOOKUPS]:
        try:
            full = arxiv.get_paper(client, paper.arxiv_id) if paper.arxiv_id else openalex.get_work(client, paper.doi)
        except SourceError:
            continue
        if full.abstract:
            paper.absorb(full)
            fetched += 1
    return fetched


def _by_year(items: list[dict]) -> dict:
    years: dict[str, int] = {}
    for item in items:
        key = str(item["paper"].year or "unknown")
        years[key] = years.get(key, 0) + 1
    return dict(sorted(years.items()))
