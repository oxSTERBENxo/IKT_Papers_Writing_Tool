"""Rank fusion for challenge candidates.

The original challenge orders candidates by rarity-weighted word overlap with the one-sentence claim only. The
failure analysis (evals/results/2026-10-19-retrieval-reliability.md) found this buries papers that match one of the
queries almost exactly: rare filler words of a long claim ("controlled", "showing", "held") carry most of the
weight. "Does syntax matter? ..." was returned third by Crossref and ranked 150th of 304.

Fusion scores each candidate against the claim and against every query separately, with the same lexical measure
the challenge already uses (rarity-weighted term coverage + TF-IDF cosine), and combines the per-text rankings by
reciprocal rank fusion: score(p) = sum over lists L of 1 / (K + rank_L(p)). A paper that closely matches any one
query therefore rises even if it shares little wording with the claim. K = 60 is the value from the original RRF
paper (Cormack et al. 2009); it was not tuned on the fixtures.

Variants compared on a fixed candidate pool of the old benchmark before the blind evaluation (see the results
file): adding each source's own result order as extra lists made ranking worse (Crossref ranks loosely related
papers first in dozens of lists), so source positions are recorded but not used here.

An optional semantic list (semantic.py) can be added; that is the 'hybrid' configuration.
"""
from __future__ import annotations

from .text import distinctive_coverage, tfidf_cosine

K = 60


def _ranks(values: list[float]) -> list[int | None]:
    """1-based rank by descending value; non-positive or missing values get no rank."""
    order = sorted((i for i, v in enumerate(values) if v is not None and v > 0), key=lambda i: -values[i])
    ranks: list[int | None] = [None] * len(values)
    for r, i in enumerate(order, 1):
        ranks[i] = r
    return ranks


def lexical_lists(texts_to_match: list[str], docs: list[str]) -> list[list[int | None]]:
    lists = []
    for q in texts_to_match:
        cov, cos = distinctive_coverage(q, docs), tfidf_cosine(q, docs)
        lists.append(_ranks([a + b for a, b in zip(cov, cos)]))
    return lists


def fuse(claim: str, queries: list[str], papers: list, semantic: list[float] | None = None
         ) -> list[tuple[float, dict]]:
    """Return [(score, components)] aligned with papers."""
    docs = [f"{p.title} {p.abstract or ''}" for p in papers]
    texts = [claim, *[q for q in queries if q.strip()]]
    lists = lexical_lists(texts, docs)
    lex = [sum(1.0 / (K + r) for r in (lst[i] for lst in lists) if r) for i in range(len(papers))]
    if semantic is not None:
        # Hybrid: the fused lexical order and the semantic order count equally (two-list RRF).
        lex_ranks, sem_ranks = _ranks(lex), _ranks(semantic)
        scores = [(1.0 / (K + lr) if lr else 0.0) + (1.0 / (K + sr) if sr else 0.0)
                  for lr, sr in zip(lex_ranks, sem_ranks)]
    else:
        scores = lex
    out = []
    for i in range(len(papers)):
        ranks = [lst[i] for lst in lists]
        best = min((r for r in ranks if r), default=None)
        out.append((scores[i], {"best_text_rank": best,
                                "best_text": texts[ranks.index(best)][:80] if best else None,
                                **({"semantic": round(semantic[i], 3)} if semantic is not None else {})}))
    return out
