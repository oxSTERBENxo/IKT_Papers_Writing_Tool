"""Small lexical helpers: tokenising, term coverage, TF-IDF similarity.

These are triage aids for ranking search results. They measure word overlap,
not meaning, so their output is never evidence of novelty or of equivalence.
"""
from __future__ import annotations

import difflib
import math
import re
import unicodedata
from collections import Counter

STOPWORDS = set(
    """a an the of and or for in on to with by from at as is are be been was were this that
    these those we our it its their using use used via into over under between toward towards
    can do does how what which why when where whether based new novel approach approaches
    method methods study studies paper work towards than then also not no""".split()
)


def normalize_title(title: str | None) -> str:
    if not title:
        return ""
    t = unicodedata.normalize("NFKD", title)
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", t)).strip()


def stem(word: str) -> str:
    """Very light plural stripping so 'graphs' matches 'graph'."""
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 3 and word.endswith("s") and not word.endswith(("ss", "us", "is")):
        return word[:-1]
    return word


def tokens(text: str | None) -> list[str]:
    return [stem(w) for w in re.findall(r"[a-z0-9]+", normalize_title(text)) if w not in STOPWORDS]


def coverage(query: str, text: str) -> float:
    """Fraction of the query's content terms that appear in the text."""
    q = set(tokens(query))
    if not q:
        return 0.0
    return len(q & set(tokens(text))) / len(q)


def distinctive_coverage(query: str, docs: list[str]) -> list[float]:
    """Like coverage, but each query term counts in proportion to how rare it is
    across docs. Terms that nearly every retrieved paper contains (the topic
    words used to retrieve them) therefore count for almost nothing."""
    doc_sets = [set(tokens(d)) for d in docs]
    n = len(docs)
    df: Counter = Counter()
    for s in doc_sets:
        df.update(s)
    # The small floor keeps the measure defined when every paper contains every
    # term, which is the most crowded case and must score 1, not 0.
    weights = {t: 0.15 + math.log((1 + n) / (1 + df.get(t, 0))) for t in set(tokens(query))}
    total = sum(weights.values())
    if not total:
        return [0.0] * n
    return [sum(w for t, w in weights.items() if t in s) / total for s in doc_sets]


def tfidf_cosine(query: str, docs: list[str]) -> list[float]:
    """Cosine similarity of the query to each doc, IDF estimated from docs."""
    doc_tokens = [tokens(d) for d in docs]
    n = len(docs)
    df: Counter = Counter()
    for toks in doc_tokens:
        df.update(set(toks))

    def vec(toks: list[str]) -> dict[str, float]:
        tf = Counter(toks)
        return {t: (1 + math.log(c)) * (math.log((1 + n) / (1 + df.get(t, 0))) + 1) for t, c in tf.items()}

    qv = vec(tokens(query))
    qn = math.sqrt(sum(v * v for v in qv.values())) or 1.0
    out = []
    for toks in doc_tokens:
        dv = vec(toks)
        dn = math.sqrt(sum(v * v for v in dv.values())) or 1.0
        out.append(sum(qv[t] * dv.get(t, 0.0) for t in qv) / (qn * dn))
    return out


def title_similarity(a: str | None, b: str | None) -> float:
    na, nb = normalize_title(a), normalize_title(b)
    if not na or not nb:
        return 0.0
    return difflib.SequenceMatcher(None, na, nb).ratio()
