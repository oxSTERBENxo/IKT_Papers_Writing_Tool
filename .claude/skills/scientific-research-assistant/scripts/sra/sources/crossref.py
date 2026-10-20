"""Crossref REST API. SRA_CONTACT_EMAIL (optional) opts into the polite pool."""
from __future__ import annotations

import os
import urllib.parse

from ..models import Paper

BASE = "https://api.crossref.org"
SELECT = "DOI,title,author,issued,container-title,is-referenced-by-count,abstract,URL,type"
SORTS = {"relevance": "relevance", "citations": "is-referenced-by-count", "date": "issued"}


def to_paper(item: dict) -> Paper:
    parts = ((item.get("issued") or {}).get("date-parts") or [[None]])[0]
    year = parts[0] if parts else None
    date = "-".join(f"{p:02d}" if i else str(p) for i, p in enumerate(parts)) if parts and parts[0] else None
    authors = [" ".join(x for x in (a.get("given"), a.get("family")) if x) or a.get("name")
               for a in item.get("author") or []]
    return Paper(
        title=" ".join(item.get("title") or []),
        authors=[a for a in authors if a],
        year=year,
        date=date,
        venue=" ".join(item.get("container-title") or []) or None,
        doi=item.get("DOI"),
        url=item.get("URL"),
        abstract=item.get("abstract"),
        citations=item.get("is-referenced-by-count"),
        type=item.get("type"),
        sources=["crossref"],
    )


def search(client, query: str, limit: int = 20, from_year: int | None = None, to_year: int | None = None,
           sort: str = "relevance") -> list[Paper]:
    filters = []
    if from_year:
        filters.append(f"from-pub-date:{from_year}")
    if to_year:
        filters.append(f"until-pub-date:{to_year}")
    data = client.get(f"{BASE}/works", {
        "query.bibliographic": query, "rows": min(limit, 100), "select": SELECT, "sort": SORTS[sort],
        "order": "desc", "filter": ",".join(filters) or None, "mailto": os.environ.get("SRA_CONTACT_EMAIL"),
    }, source="crossref")
    return [to_paper(i) for i in (data.get("message") or {}).get("items") or [] if i.get("title")]


def get_work(client, doi: str) -> Paper:
    data = client.get(f"{BASE}/works/{urllib.parse.quote(doi, safe='/')}",
                      {"mailto": os.environ.get("SRA_CONTACT_EMAIL")}, source="crossref")
    return to_paper(data.get("message") or {})
