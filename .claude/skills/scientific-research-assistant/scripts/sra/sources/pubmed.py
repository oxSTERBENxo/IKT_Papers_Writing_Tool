"""PubMed via NCBI E-utilities. Optional env: NCBI_API_KEY."""
from __future__ import annotations

import os
import re
import xml.etree.ElementTree as ET

from ..http import SourceError
from ..models import Paper

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
SORTS = {"relevance": "relevance", "citations": "relevance", "date": "pub_date"}


def _params(**extra) -> dict:
    params = {"db": "pubmed", "tool": "scientific-research-assistant",
              "email": os.environ.get("SRA_CONTACT_EMAIL"), "api_key": os.environ.get("NCBI_API_KEY")}
    params.update(extra)
    return params


def parse_articles(xml_text: str) -> list[Paper]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise SourceError("pubmed", "parse", f"invalid efetch XML: {exc}") from exc
    papers = []
    for art in root.findall(".//PubmedArticle"):
        cit = art.find("MedlineCitation")
        article = cit.find("Article") if cit is not None else None
        if article is None:
            continue
        title = "".join(article.find("ArticleTitle").itertext()) if article.find("ArticleTitle") is not None else ""
        abstract = " ".join("".join(n.itertext()) for n in article.findall("Abstract/AbstractText")) or None
        authors = [" ".join(x for x in (a.findtext("ForeName"), a.findtext("LastName")) if x)
                   for a in article.findall("AuthorList/Author")]
        pub = article.find("Journal/JournalIssue/PubDate")
        year_text = (pub.findtext("Year") or pub.findtext("MedlineDate") or "") if pub is not None else ""
        year = re.search(r"\d{4}", year_text)
        doi = next((i.text for i in art.findall("PubmedData/ArticleIdList/ArticleId")
                    if i.get("IdType") == "doi"), None)
        pmid = cit.findtext("PMID")
        papers.append(Paper(
            title=title, authors=[a for a in authors if a], year=int(year.group(0)) if year else None,
            venue=article.findtext("Journal/Title"), doi=doi, pmid=pmid,
            url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/", abstract=abstract, type="article",
            sources=["pubmed"],
        ))
    return papers


def fetch(client, pmids: list[str]) -> list[Paper]:
    if not pmids:
        return []
    xml_text = client.get(f"{BASE}/efetch.fcgi", _params(id=",".join(pmids), retmode="xml"),
                          source="pubmed", parse="text")
    return parse_articles(xml_text)


def search(client, query: str, limit: int = 20, from_year: int | None = None, to_year: int | None = None,
           sort: str = "relevance") -> list[Paper]:
    params = _params(term=query, retmax=min(limit, 100), retmode="json", sort=SORTS[sort])
    if from_year or to_year:
        params.update(datetype="pdat", mindate=from_year or 1900, maxdate=to_year or 2100)
    data = client.get(f"{BASE}/esearch.fcgi", params, source="pubmed")
    return fetch(client, (data.get("esearchresult") or {}).get("idlist") or [])


def get_paper(client, pmid: str) -> Paper:
    papers = fetch(client, [pmid])
    if not papers:
        raise SourceError("pubmed", "not_found", f"no PubMed record for {pmid}")
    return papers[0]
