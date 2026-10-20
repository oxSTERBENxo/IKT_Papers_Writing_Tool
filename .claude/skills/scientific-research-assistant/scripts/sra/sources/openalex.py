"""OpenAlex works API. Optional env: OPENALEX_API_KEY, SRA_CONTACT_EMAIL."""
from __future__ import annotations

import os
import re

from ..models import Paper, normalize_arxiv_id

BASE = "https://api.openalex.org"
SELECT = ("id,doi,title,publication_year,publication_date,authorships,primary_location,best_oa_location,"
          "cited_by_count,open_access,ids,abstract_inverted_index,type,is_retracted")
SORTS = {"relevance": "relevance_score:desc", "citations": "cited_by_count:desc", "date": "publication_date:desc"}


def _params(**extra) -> dict:
    params = {"api_key": os.environ.get("OPENALEX_API_KEY"), "mailto": os.environ.get("SRA_CONTACT_EMAIL")}
    params.update(extra)
    return params


def _abstract(inverted: dict | None) -> str | None:
    if not inverted:
        return None
    positions = [(pos, word) for word, poss in inverted.items() for pos in poss]
    return " ".join(word for _, word in sorted(positions))


def short_id(openalex_id: str | None) -> str | None:
    return openalex_id.rsplit("/", 1)[-1] if openalex_id else None


def to_paper(work: dict) -> Paper:
    primary = work.get("primary_location") or {}
    best_oa = work.get("best_oa_location") or {}
    oa = work.get("open_access") or {}
    ids = work.get("ids") or {}
    arxiv_id = None
    for loc in (primary, best_oa):
        for key in ("landing_page_url", "pdf_url"):
            if "arxiv.org" in (loc.get(key) or ""):
                arxiv_id = arxiv_id or normalize_arxiv_id(loc[key])
    pmid = re.search(r"(\d+)\s*$", ids.get("pmid") or "")
    paper = Paper(
        title=work.get("title") or "",
        authors=[(a.get("author") or {}).get("display_name") for a in work.get("authorships") or []
                 if (a.get("author") or {}).get("display_name")],
        year=work.get("publication_year"),
        date=work.get("publication_date"),
        venue=(primary.get("source") or {}).get("display_name"),
        doi=work.get("doi"),
        arxiv_id=arxiv_id,
        pmid=pmid.group(1) if pmid else None,
        openalex_id=short_id(work.get("id")),
        url=primary.get("landing_page_url") or work.get("id"),
        pdf_url=oa.get("oa_url") or best_oa.get("pdf_url"),
        abstract=_abstract(work.get("abstract_inverted_index")),
        citations=work.get("cited_by_count"),
        is_oa=oa.get("is_oa"),
        is_retracted=work.get("is_retracted"),
        type=work.get("type"),
        sources=["openalex"],
    )
    for key in ("referenced_works", "related_works"):
        if work.get(key):
            paper.extra[key] = [short_id(w) for w in work[key]]
    return paper


def search(client, query: str, limit: int = 20, from_year: int | None = None, to_year: int | None = None,
           sort: str = "relevance", extra_filters: tuple = ()) -> list[Paper]:
    """Search titles and abstracts (not full text, which is too noisy for triage)."""
    cleaned = re.sub(r"[,:|]", " ", query).strip()
    filters = [f"title_and_abstract.search:{cleaned}", *extra_filters]
    if from_year:
        filters.append(f"from_publication_date:{from_year}-01-01")
    if to_year:
        filters.append(f"to_publication_date:{to_year}-12-31")
    data = client.get(f"{BASE}/works", _params(**{
        "filter": ",".join(filters), "sort": SORTS[sort], "per-page": min(limit, 100), "select": SELECT,
    }), source="openalex")
    return [to_paper(w) for w in data.get("results", [])]


def get_work(client, ident: str) -> Paper:
    """ident: OpenAlex W-id, or a DOI (bare or URL). Includes reference/related lists."""
    path = ident if re.fullmatch(r"W\d+", ident) else f"https://doi.org/{ident.split('doi.org/')[-1]}"
    return to_paper(client.get(f"{BASE}/works/{path}", _params(), source="openalex"))


def by_ids(client, ids: list[str], limit: int = 50) -> list[Paper]:
    ids = [i for i in ids if i][:limit]
    if not ids:
        return []
    data = client.get(f"{BASE}/works", _params(**{
        "filter": "openalex:" + "|".join(ids), "per-page": min(len(ids), 100), "select": SELECT,
    }), source="openalex")
    return [to_paper(w) for w in data.get("results", [])]


def citing(client, openalex_id: str, limit: int = 25, sort: str = "citations", text: str | None = None,
           from_year: int | None = None) -> list[Paper]:
    """Works citing openalex_id, optionally restricted to those mentioning text."""
    extra = [f"cites:{openalex_id}"]
    if text:
        extra.append("title_and_abstract.search:" + re.sub(r"[,:|]", " ", text))
    if from_year:
        extra.append(f"from_publication_date:{from_year}-01-01")
    data = client.get(f"{BASE}/works", _params(**{
        "filter": ",".join(extra), "sort": SORTS[sort], "per-page": min(limit, 100), "select": SELECT,
    }), source="openalex")
    return [to_paper(w) for w in data.get("results", [])]
