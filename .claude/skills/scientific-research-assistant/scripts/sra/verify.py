"""Reference verification: confirm that every cited paper resolves to a real
record whose title matches what the report claims. Guards against fabricated
or misremembered citations."""
from __future__ import annotations

import datetime
import urllib.parse

from .http import SourceError
from .models import arxiv_from_doi, normalize_arxiv_id, normalize_doi
from .sources import arxiv, crossref, pubmed
from .text import title_similarity

MATCH_THRESHOLD = 0.85
# verified            identifier resolves and the registered title matches
# title_mismatch      identifier resolves to a differently titled work
# identifier_resolves identifier exists but its title could not be fetched
# url_reachable       only a URL was given and it responded (weak evidence)
# unresolved          identifier or URL does not resolve
# unchecked           the check could not run (network, rate limit)
# no_identifier       nothing to check
STATUSES = ("verified", "title_mismatch", "identifier_resolves", "url_reachable", "unresolved", "unchecked",
            "no_identifier")


def _compare(claimed: str, resolved: str | None, via: str) -> dict:
    sim = title_similarity(claimed, resolved)
    return {"status": "verified" if sim >= MATCH_THRESHOLD else "title_mismatch", "via": via,
            "resolved_title": resolved, "title_similarity": round(sim, 3)}


def verify_paper(client, paper: dict) -> dict:
    title = paper.get("title") or ""
    doi = normalize_doi(paper.get("doi"))
    arxiv_id = normalize_arxiv_id(paper.get("arxiv_id")) or arxiv_from_doi(doi)
    failures = []

    def run(fn, via):
        try:
            return _compare(title, fn().title, via)
        except SourceError as exc:
            failures.append((via, exc))
            return None

    result = None
    if arxiv_id:
        result = run(lambda: arxiv.get_paper(client, arxiv_id), "arxiv")
    if result is None and doi and not arxiv_from_doi(doi):
        result = run(lambda: crossref.get_work(client, doi), "crossref")
        if result is None:
            # Not every DOI is registered with Crossref (DataCite ones are not); ask the DOI system itself.
            try:
                handle = client.get(f"https://doi.org/api/handles/{urllib.parse.quote(doi, safe='/')}",
                                    source="doi.org")
                if handle.get("responseCode") == 1:
                    result = {"status": "identifier_resolves", "via": "doi.org",
                              "note": "DOI exists; title not checked (not in Crossref)."}
            except SourceError as exc:
                failures.append(("doi.org", exc))
    if result is None and paper.get("pmid"):
        result = run(lambda: pubmed.get_paper(client, str(paper["pmid"])), "pubmed")
    if result is None and not (arxiv_id or doi or paper.get("pmid")):
        if paper.get("url"):
            probe = client.probe(paper["url"])
            result = {"status": "url_reachable" if probe["reachable"] else
                      ("unchecked" if probe.get("error") else "unresolved"),
                      "via": "url", "http_status": probe.get("status"),
                      "note": "Only the URL was checked; add a DOI or arXiv ID for a real verification."}
        else:
            result = {"status": "no_identifier", "via": None}
    if result is None:
        kinds = {exc.kind for _, exc in failures}
        status = "unresolved" if kinds <= {"not_found"} else "unchecked"
        result = {"status": status, "via": ", ".join(v for v, _ in failures),
                  "note": "; ".join(f"{v}: {exc.kind}" for v, exc in failures)}
    result["checked_on"] = datetime.date.today().isoformat()
    return result


def verify_report(client, report: dict, progress=None) -> dict:
    """Adds a 'verification' entry to every paper in report['papers']. Returns counts by status."""
    counts: dict[str, int] = {}
    for paper in report.get("papers") or []:
        paper["verification"] = verify_paper(client, paper)
        status = paper["verification"]["status"]
        counts[status] = counts.get(status, 0) + 1
        if progress:
            progress(paper)
    return counts
