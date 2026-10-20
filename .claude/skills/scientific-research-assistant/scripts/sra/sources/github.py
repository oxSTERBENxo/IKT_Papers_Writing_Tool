"""GitHub REST API. Optional env: GITHUB_TOKEN (or GH_TOKEN).

Unauthenticated limits are 60 core requests per hour and 10 searches per
minute, which covers roughly four paper assessments per hour.
"""
from __future__ import annotations

import os
import re

BASE = "https://api.github.com"
REPO_URL_RE = re.compile(r"github\.com/([A-Za-z0-9_.\-]+)/([A-Za-z0-9_.\-]+)")
NON_REPO_OWNERS = {"orgs", "topics", "features", "about", "sponsors", "settings", "marketplace"}


def _headers(accept: str = "application/vnd.github+json") -> dict:
    headers = {"Accept": accept, "X-GitHub-Api-Version": "2022-11-28"}
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def extract_repos(text: str | None) -> list[str]:
    """owner/name for every GitHub repository URL mentioned in text."""
    out = []
    for owner, name in REPO_URL_RE.findall(text or ""):
        name = re.sub(r"\.git$", "", name).rstrip(".")
        full = f"{owner}/{name}"
        if owner.lower() not in NON_REPO_OWNERS and name and full not in out:
            out.append(full)
    return out


def search_repos(client, query: str, limit: int = 5) -> list[dict]:
    data = client.get(f"{BASE}/search/repositories", {"q": query, "per_page": limit, "sort": "stars"},
                      headers=_headers(), source="github")
    return data.get("items") or []


def get_repo(client, full_name: str) -> dict:
    return client.get(f"{BASE}/repos/{full_name}", headers=_headers(), source="github")


def get_readme(client, full_name: str) -> str:
    return client.get(f"{BASE}/repos/{full_name}/readme", headers=_headers("application/vnd.github.raw+json"),
                      source="github", parse="text")


def get_tree(client, full_name: str, branch: str) -> tuple[list[str], bool]:
    """(file paths, truncated flag) for the whole repository."""
    data = client.get(f"{BASE}/repos/{full_name}/git/trees/{branch}", {"recursive": 1},
                      headers=_headers(), source="github")
    return [t["path"] for t in data.get("tree") or [] if t.get("type") == "blob"], bool(data.get("truncated"))


def count_issues(client, full_name: str, terms: str) -> int:
    data = client.get(f"{BASE}/search/issues", {"q": f"repo:{full_name} is:issue {terms}", "per_page": 1},
                      headers=_headers(), source="github")
    return int(data.get("total_count") or 0)


def rate_limit(client) -> dict:
    return client.get(f"{BASE}/rate_limit", headers=_headers(), source="github", cache=False)
