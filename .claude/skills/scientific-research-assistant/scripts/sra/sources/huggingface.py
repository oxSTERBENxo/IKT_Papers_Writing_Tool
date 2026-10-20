"""Hugging Face Hub: datasets, paper pages and repos linked to an arXiv ID.

Optional env: HF_TOKEN. Paper pages replace the retired Papers With Code API.
"""
from __future__ import annotations

import os

from ..models import Paper

BASE = "https://huggingface.co/api"
VIEWER = "https://datasets-server.huggingface.co"


def _headers() -> dict:
    token = os.environ.get("HF_TOKEN")
    return {"Authorization": f"Bearer {token}"} if token else {}


def search_datasets(client, query: str, limit: int = 10) -> list[dict]:
    return client.get(f"{BASE}/datasets", {"search": query, "limit": limit, "sort": "downloads",
                                           "direction": -1, "full": "true"},
                      headers=_headers(), source="huggingface")


def get_dataset(client, dataset_id: str) -> dict:
    return client.get(f"{BASE}/datasets/{dataset_id}", headers=_headers(), source="huggingface")


def dataset_size(client, dataset_id: str) -> dict:
    """Size summary from the dataset viewer; unavailable for gated or script datasets."""
    data = client.get(f"{VIEWER}/size", {"dataset": dataset_id}, headers=_headers(), source="huggingface")
    size = data.get("size") or {}
    return {"dataset": size.get("dataset") or {}, "splits": size.get("splits") or [],
            "partial": bool(data.get("partial"))}


def get_paper(client, arxiv_id: str) -> dict:
    return client.get(f"{BASE}/papers/{arxiv_id}", headers=_headers(), source="huggingface")


def arxiv_repos(client, arxiv_id: str) -> dict:
    """Models, datasets and spaces whose cards are tagged with this arXiv ID."""
    return client.get(f"{BASE}/arxiv/{arxiv_id}/repos", headers=_headers(), source="huggingface")


def search(client, query: str, limit: int = 20, from_year: int | None = None, to_year: int | None = None,
           sort: str = "relevance") -> list[Paper]:
    """Search Hugging Face paper pages (arXiv papers, mostly machine learning)."""
    data = client.get(f"{BASE}/papers/search", {"q": query}, headers=_headers(), source="huggingface")
    papers = []
    for item in data or []:
        info = item.get("paper") or item
        published = info.get("publishedAt") or item.get("publishedAt") or ""
        year = int(published[:4]) if published[:4].isdigit() else None
        if (from_year and year and year < from_year) or (to_year and year and year > to_year):
            continue
        papers.append(Paper(
            title=info.get("title") or item.get("title") or "",
            authors=[a.get("name") for a in info.get("authors") or [] if a.get("name")],
            year=year, date=published[:10] or None, venue="arXiv", arxiv_id=info.get("id"),
            url=f"https://arxiv.org/abs/{info.get('id')}", abstract=info.get("summary") or item.get("summary"),
            is_oa=True, type="preprint", sources=["huggingface"],
        ))
    return papers[:limit]
