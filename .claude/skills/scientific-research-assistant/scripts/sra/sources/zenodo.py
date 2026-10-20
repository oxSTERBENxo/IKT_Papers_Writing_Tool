"""Zenodo records API, used for dataset discovery outside Hugging Face."""
from __future__ import annotations

BASE = "https://zenodo.org/api"


def search_datasets(client, query: str, limit: int = 10) -> list[dict]:
    data = client.get(f"{BASE}/records", {"q": query, "type": "dataset", "size": limit, "sort": "bestmatch"},
                      source="zenodo")
    return (data.get("hits") or {}).get("hits") or []


def get_record(client, record_id: str) -> dict:
    return client.get(f"{BASE}/records/{record_id}", source="zenodo")
