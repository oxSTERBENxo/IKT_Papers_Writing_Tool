"""Dataset discovery and verification (Hugging Face Hub, Zenodo, plain URLs).

Every reported property comes from an API response. A property the API does
not report is returned as None and listed under 'missing'; nothing is guessed.
"""
from __future__ import annotations

import re

from .http import SourceError
from .sources import huggingface, zenodo

UNCLEAR_LICENSES = {"other", "unknown", "", None}


def _tag_values(tags: list, prefix: str) -> list[str]:
    return [t.split(":", 1)[1] for t in tags or [] if isinstance(t, str) and t.startswith(prefix + ":")]


def _as_list(value) -> list:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def hf_summary(d: dict) -> dict:
    tags = d.get("tags") or []
    card = d.get("cardData") or {}
    licenses = _as_list(card.get("license")) or _tag_values(tags, "license")
    return {
        "source": "huggingface", "id": d.get("id"), "url": f"https://huggingface.co/datasets/{d.get('id')}",
        "name": card.get("pretty_name") or d.get("id"),
        "license": ", ".join(str(x) for x in licenses) or None,
        "gated": d.get("gated"), "private": d.get("private"), "disabled": d.get("disabled"),
        "downloads": d.get("downloads"), "likes": d.get("likes"), "last_modified": d.get("lastModified"),
        "tasks": _tag_values(tags, "task_categories"), "languages": _tag_values(tags, "language"),
        "modalities": _tag_values(tags, "modality"), "formats": _tag_values(tags, "format"),
        "size_category": (_tag_values(tags, "size_categories") or [None])[0],
        "arxiv_ids": _tag_values(tags, "arxiv"),
        "configs": card.get("config_names") or [],
    }


def zenodo_summary(r: dict) -> dict:
    meta = r.get("metadata") or {}
    files = r.get("files") or []
    return {
        "source": "zenodo", "id": str(r.get("id")), "url": (r.get("links") or {}).get("self_html")
        or f"https://zenodo.org/records/{r.get('id')}",
        "name": meta.get("title") or r.get("title"), "doi": r.get("doi") or meta.get("doi"),
        "license": (meta.get("license") or {}).get("id"), "access_right": meta.get("access_right"),
        "publication_date": meta.get("publication_date"),
        "n_files": len(files), "total_bytes": sum(f.get("size") or 0 for f in files) if files else None,
        "file_names": [f.get("key") for f in files[:10]],
        "description": re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", meta.get("description") or ""))[:400] or None,
    }


def search(client, query: str, limit: int = 8) -> dict:
    out = {"query": query, "huggingface": [], "zenodo": [], "errors": []}
    try:
        out["huggingface"] = [hf_summary(d) for d in huggingface.search_datasets(client, query, limit)]
    except SourceError as exc:
        out["errors"].append(exc.to_dict())
    try:
        out["zenodo"] = [zenodo_summary(r) for r in zenodo.search_datasets(client, query, limit)]
    except SourceError as exc:
        out["errors"].append(exc.to_dict())
    return out


def human_bytes(n: int | None) -> str | None:
    if n is None:
        return None
    value = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024


def parse_ref(ref: str) -> tuple[str, str]:
    """Returns (kind, id) with kind in huggingface, zenodo, url."""
    r = ref.strip()
    m = re.search(r"huggingface\.co/datasets/([^/\s?#]+(?:/[^/\s?#]+)?)", r)
    if m:
        return "huggingface", m.group(1)
    m = re.search(r"zenodo\.org/records?/(\d+)|10\.5281/zenodo\.(\d+)|^zenodo:(\d+)$", r, re.I)
    if m:
        return "zenodo", next(g for g in m.groups() if g)
    if r.lower().startswith("hf:"):
        return "huggingface", r[3:]
    if re.match(r"https?://", r):
        return "url", r
    return "huggingface", r


def verify(client, ref: str) -> dict:
    kind, ident = parse_ref(ref)
    if kind == "huggingface":
        return _verify_hf(client, ident)
    if kind == "zenodo":
        return _verify_zenodo(client, ident)
    probe = client.probe(ident)
    return {
        "source": "url", "ref": ident, "exists": probe["reachable"], "http_status": probe.get("status"),
        "content_type": probe.get("content_type"), "error": probe.get("error"),
        "missing": ["license", "size", "format", "access terms"], "blockers": [] if probe["reachable"] else
        ["URL did not respond successfully."],
        "note": "Only reachability was checked. Licence, size and contents must be read from the page itself.",
    }


def _verify_hf(client, dataset_id: str) -> dict:
    try:
        raw = huggingface.get_dataset(client, dataset_id)
    except SourceError as exc:
        return {"source": "huggingface", "ref": dataset_id, "exists": False if exc.kind == "not_found" else None,
                "error": exc.to_dict(), "missing": [], "blockers": ["Dataset could not be confirmed to exist."]}
    info = hf_summary(raw)
    info.update(ref=dataset_id, exists=True, missing=[], blockers=[], notes=[])
    try:
        size = huggingface.dataset_size(client, dataset_id)
        ds = size["dataset"]
        info["num_rows"] = ds.get("num_rows")
        info["download_bytes"] = ds.get("num_bytes_original_files")
        info["in_memory_bytes"] = ds.get("num_bytes_memory")
        info["splits"] = [{"config": s.get("config"), "split": s.get("split"), "num_rows": s.get("num_rows")}
                          for s in size["splits"][:40]]
        info["storage_estimate"] = (f"about {human_bytes(info['download_bytes'])} to download, "
                                    f"{human_bytes(info['in_memory_bytes'])} in memory (dataset viewer figures"
                                    f"{', partial' if size['partial'] else ''})") if info["download_bytes"] else None
    except SourceError as exc:
        info.update(num_rows=None, download_bytes=None, splits=[], storage_estimate=None)
        info["notes"].append(f"Size not available from the dataset viewer ({exc.kind}).")
    for key, label in (("license", "license"), ("num_rows", "size (rows)"), ("download_bytes", "download size")):
        if not info.get(key):
            info["missing"].append(label)
    if info["license"] in UNCLEAR_LICENSES or (info["license"] or "").lower() in ("other", "unknown"):
        info["notes"].append("Licence is missing or 'other': read the dataset card before using or redistributing.")
    if info.get("gated"):
        info["blockers"].append(f"Gated dataset (gated={info['gated']}): access needs acceptance of terms"
                                + (" and manual approval." if info["gated"] == "manual" else "."))
    if info.get("private") or info.get("disabled"):
        info["blockers"].append("Dataset is private or disabled.")
    return info


def _verify_zenodo(client, record_id: str) -> dict:
    try:
        raw = zenodo.get_record(client, record_id)
    except SourceError as exc:
        return {"source": "zenodo", "ref": record_id, "exists": False if exc.kind == "not_found" else None,
                "error": exc.to_dict(), "missing": [], "blockers": ["Record could not be confirmed to exist."]}
    info = zenodo_summary(raw)
    info.update(ref=record_id, exists=True, missing=[], blockers=[], notes=[])
    info["storage_estimate"] = f"{human_bytes(info['total_bytes'])} across {info['n_files']} file(s)" \
        if info["total_bytes"] else None
    if not info["license"]:
        info["missing"].append("license")
    if not info["total_bytes"]:
        info["missing"].append("file sizes")
    if info["access_right"] and info["access_right"] != "open":
        info["blockers"].append(f"Access is '{info['access_right']}', not open.")
    return info
