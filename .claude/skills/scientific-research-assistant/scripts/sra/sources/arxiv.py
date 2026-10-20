"""arXiv export API (Atom). No key; one request every three seconds."""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET

from ..http import SourceError
from ..models import Paper
from ..text import STOPWORDS

BASE = "https://export.arxiv.org/api/query"
NS = {"a": "http://www.w3.org/2005/Atom", "x": "http://arxiv.org/schemas/atom"}
SORTS = {"relevance": "relevance", "citations": "relevance", "date": "submittedDate"}


MATCH_MODES = ("all", "any")


def build_query(query: str, match: str = "all") -> str:
    """Quoted phrases stay phrases (always required). Remaining content words are ANDed ("all"), or ORed ("any")
    so that arXiv's relevance sort ranks papers by how many of them they contain.

    With "all", a query of six or more content words usually returns nothing: in the 2026-10-19 retrieval
    evaluation 646 of 745 arXiv searches came back empty for that reason."""
    if match not in MATCH_MODES:
        raise ValueError(f"match must be one of {MATCH_MODES}")
    phrases = re.findall(r'"([^"]+)"', query)
    rest = re.sub(r'"[^"]+"', " ", query)
    words = [w for w in re.findall(r"[\w\-]+", rest) if w.lower() not in STOPWORDS]
    required = [f'all:"{p}"' for p in phrases]
    if match == "all" or len(words) <= 1:
        return " AND ".join(required + [f"all:{w}" for w in words])
    optional = "(" + " OR ".join(f"all:{w}" for w in words) + ")"
    return " AND ".join(required + [optional])


def _text(node, path: str) -> str | None:
    found = node.find(path, NS)
    return found.text.strip() if found is not None and found.text else None


def parse_feed(xml_text: str) -> list[Paper]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise SourceError("arxiv", "parse", f"invalid Atom feed: {exc}") from exc
    papers = []
    for entry in root.findall("a:entry", NS):
        entry_id = _text(entry, "a:id") or ""
        if "/api/errors" in entry_id:
            raise SourceError("arxiv", "http", _text(entry, "a:summary") or "arXiv API error")
        published = _text(entry, "a:published")
        pdf = next((link.get("href") for link in entry.findall("a:link", NS) if link.get("title") == "pdf"), None)
        primary = entry.find("x:primary_category", NS)
        paper = Paper(
            title=_text(entry, "a:title") or "",
            authors=[n.text.strip() for n in entry.findall("a:author/a:name", NS) if n.text],
            year=int(published[:4]) if published else None,
            date=published[:10] if published else None,
            venue=_text(entry, "x:journal_ref") or "arXiv",
            doi=_text(entry, "x:doi"),
            arxiv_id=entry_id.split("/abs/")[-1],
            url=re.sub(r"v\d+$", "", entry_id).replace("http://", "https://"),
            pdf_url=pdf,
            abstract=_text(entry, "a:summary"),
            is_oa=True,
            type="preprint",
            sources=["arxiv"],
        )
        if _text(entry, "x:comment"):
            paper.extra["arxiv_comment"] = _text(entry, "x:comment")
        if primary is not None:
            paper.extra["arxiv_category"] = primary.get("term")
        papers.append(paper)
    return papers


def search(client, query: str, limit: int = 20, from_year: int | None = None, to_year: int | None = None,
           sort: str = "relevance", match: str = "all") -> list[Paper]:
    search_query = build_query(query, match)
    if not search_query:
        return []
    if from_year or to_year:
        search_query += f" AND submittedDate:[{from_year or 1991}01010000 TO {to_year or 2100}12312359]"
    xml_text = client.get(BASE, {"search_query": search_query, "start": 0, "max_results": min(limit, 100),
                                 "sortBy": SORTS[sort], "sortOrder": "descending"},
                          source="arxiv", parse="text")
    return parse_feed(xml_text)


def get_paper(client, arxiv_id: str) -> Paper:
    papers = parse_feed(client.get(BASE, {"id_list": arxiv_id}, source="arxiv", parse="text"))
    if not papers or not papers[0].title:
        raise SourceError("arxiv", "not_found", f"no arXiv record for {arxiv_id}")
    return papers[0]
