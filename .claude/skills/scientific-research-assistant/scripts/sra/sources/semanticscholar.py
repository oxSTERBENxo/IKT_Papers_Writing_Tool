"""Semantic Scholar Graph API. Optional env: SEMANTIC_SCHOLAR_API_KEY.

Without a key requests share a public pool and are often answered with
HTTP 429, so unauthenticated calls retry only once before reporting it.
"""
from __future__ import annotations

import os

from ..models import Paper

BASE = "https://api.semanticscholar.org/graph/v1"
RECS = "https://api.semanticscholar.org/recommendations/v1"
FIELDS = "title,abstract,year,publicationDate,authors,externalIds,citationCount,venue,openAccessPdf,url"


def _auth() -> tuple[dict, int | None]:
    key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
    return ({"x-api-key": key}, None) if key else ({}, 1)


def _get(client, url: str, params: dict):
    headers, retries = _auth()
    return client.get(url, params, headers=headers, source="semantic_scholar", retries=retries)


def to_paper(item: dict) -> Paper:
    ext = item.get("externalIds") or {}
    pdf = item.get("openAccessPdf") or {}
    return Paper(
        title=item.get("title") or "",
        authors=[a.get("name") for a in item.get("authors") or [] if a.get("name")],
        year=item.get("year"),
        date=item.get("publicationDate"),
        venue=item.get("venue") or None,
        doi=ext.get("DOI"),
        arxiv_id=ext.get("ArXiv"),
        pmid=str(ext["PubMed"]) if ext.get("PubMed") else None,
        s2_id=item.get("paperId"),
        url=item.get("url"),
        pdf_url=pdf.get("url") or None,
        abstract=item.get("abstract"),
        citations=item.get("citationCount"),
        is_oa=bool(pdf.get("url")) or None,
        sources=["semantic_scholar"],
    )


def search(client, query: str, limit: int = 20, from_year: int | None = None, to_year: int | None = None,
           sort: str = "relevance") -> list[Paper]:
    params = {"query": query, "limit": min(limit, 100), "fields": FIELDS}
    if from_year or to_year:
        params["year"] = f"{from_year or ''}-{to_year or ''}"
    papers = [to_paper(p) for p in _get(client, f"{BASE}/paper/search", params).get("data") or []]
    if sort == "citations":
        papers.sort(key=lambda p: -(p.citations or 0))
    elif sort == "date":
        papers.sort(key=lambda p: p.date or str(p.year or ""), reverse=True)
    return papers


def paper_ref(kind: str, value: str) -> str:
    return {"arxiv": f"ARXIV:{value}", "doi": f"DOI:{value}", "pmid": f"PMID:{value}"}.get(kind, value)


def get_paper(client, ref: str) -> Paper:
    return to_paper(_get(client, f"{BASE}/paper/{ref}", {"fields": FIELDS}))


def _linked(client, ref: str, edge: str, key: str, limit: int) -> list[Paper]:
    data = _get(client, f"{BASE}/paper/{ref}/{edge}", {"fields": FIELDS, "limit": min(limit, 100)})
    return [to_paper(row[key]) for row in data.get("data") or [] if row.get(key) and row[key].get("title")]


def citations(client, ref: str, limit: int = 25) -> list[Paper]:
    return _linked(client, ref, "citations", "citingPaper", limit)


def references(client, ref: str, limit: int = 50) -> list[Paper]:
    return _linked(client, ref, "references", "citedPaper", limit)


def recommendations(client, ref: str, limit: int = 20) -> list[Paper]:
    data = _get(client, f"{RECS}/papers/forpaper/{ref}", {"fields": FIELDS, "limit": min(limit, 100)})
    return [to_paper(p) for p in data.get("recommendedPapers") or []]
