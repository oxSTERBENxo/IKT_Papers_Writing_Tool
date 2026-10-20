"""Shared test helpers: an offline HTTP opener and canned API payloads.

Everything here is fabricated test data with obviously fake identifiers. It
exercises parsing and control flow only and says nothing about whether the
live services work; tests/test_live.py covers that.
"""
from __future__ import annotations

import io
import json
import sys
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from sra.http import HttpClient  # noqa: E402


class FakeResponse:
    def __init__(self, body: str, status: int = 200, headers: dict | None = None):
        self._body, self.status, self.headers = body.encode("utf-8"), status, headers or {}

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def http_error(url: str, status: int, headers: dict | None = None):
    return urllib.error.HTTPError(url, status, "error", headers or {}, io.BytesIO(b""))


class FakeOpener:
    """Routes are (url substring, response) pairs tried in order. A response is a
    str/dict/list body, an Exception to raise, an int HTTP status to raise, or a
    list of those consumed one per call (the last one repeats)."""

    def __init__(self, routes: list[tuple[str, object]]):
        self.routes = routes
        self.calls: list[str] = []

    def __call__(self, request, timeout=None):
        url = request.full_url
        self.calls.append(url)
        for needle, response in self.routes:
            if needle in url:
                if isinstance(response, list):
                    response = response.pop(0) if len(response) > 1 else response[0]
                if isinstance(response, int):
                    raise http_error(url, response)
                if isinstance(response, Exception):
                    raise response
                return FakeResponse(response if isinstance(response, str) else json.dumps(response))
        raise http_error(url, 404)

    def count(self, needle: str) -> int:
        return sum(1 for c in self.calls if needle in c)


def make_client(routes) -> tuple[HttpClient, FakeOpener, list[float]]:
    opener, sleeps = FakeOpener(routes), []
    client = HttpClient(cache_dir=None, opener=opener, sleep=sleeps.append)
    return client, opener, sleeps


# -- canned payloads ------------------------------------------------------
def openalex_work(wid="W1000001", title="Graph Networks for Text Labelling: A Test Fixture", doi=None,
                  year=2021, cites=10, arxiv=None, abstract_words=("graph", "networks", "label", "text"), pmid=None):
    return {
        "id": f"https://openalex.org/{wid}", "doi": f"https://doi.org/{doi}" if doi else None, "title": title,
        "publication_year": year, "publication_date": f"{year}-05-01",
        "authorships": [{"author": {"display_name": "Ada Example"}}, {"author": {"display_name": "Bo Sample"}}],
        "primary_location": {"source": {"display_name": "Journal of Fixtures"},
                             "landing_page_url": f"https://arxiv.org/abs/{arxiv}" if arxiv else "https://example.org/p"},
        "best_oa_location": {"pdf_url": "https://example.org/p.pdf"},
        "cited_by_count": cites, "open_access": {"is_oa": True, "oa_url": "https://example.org/p.pdf"},
        "ids": {"pmid": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}"} if pmid else {},
        "abstract_inverted_index": {w: [i] for i, w in enumerate(abstract_words)},
        "type": "article", "is_retracted": False,
        "referenced_works": ["https://openalex.org/W2000001"], "related_works": ["https://openalex.org/W3000001"],
    }


ARXIV_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2101.00001v3</id>
    <published>2021-01-01T00:00:00Z</published>
    <title>Graph Networks for Text Labelling:
      A Test Fixture</title>
    <summary>We study graph networks that label text. Code: https://github.com/example-org/fixture-repo.</summary>
    <author><name>Ada Example</name></author>
    <author><name>Bo Sample</name></author>
    <arxiv:comment>Accepted somewhere. 9 pages.</arxiv:comment>
    <arxiv:primary_category term="cs.CL"/>
    <link title="pdf" href="http://arxiv.org/pdf/2101.00001v3" rel="related" type="application/pdf"/>
  </entry>
</feed>"""

ARXIV_EMPTY = '<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"></feed>'

PUBMED_XML = """<?xml version="1.0"?>
<PubmedArticleSet><PubmedArticle>
  <MedlineCitation><PMID>123456</PMID><Article>
    <Journal><Title>Fixture Medicine</Title><JournalIssue><PubDate><Year>2020</Year></PubDate></JournalIssue></Journal>
    <ArticleTitle>A <i>fixture</i> trial of graphs.</ArticleTitle>
    <Abstract><AbstractText Label="BACKGROUND">Background text.</AbstractText><AbstractText>Result text.</AbstractText></Abstract>
    <AuthorList><Author><LastName>Example</LastName><ForeName>Ada</ForeName></Author></AuthorList>
  </Article></MedlineCitation>
  <PubmedData><ArticleIdList><ArticleId IdType="doi">10.1234/FIXTURE.1</ArticleId></ArticleIdList></PubmedData>
</PubmedArticle></PubmedArticleSet>"""

CROSSREF_ITEM = {
    "DOI": "10.1234/fixture.2", "title": ["Graph Networks for Text Labelling: A Test Fixture"],
    "author": [{"given": "Ada", "family": "Example"}], "issued": {"date-parts": [[2021, 5, 1]]},
    "container-title": ["Journal of Fixtures"], "is-referenced-by-count": 7,
    "abstract": "<jats:p>We study <jats:italic>graph</jats:italic> networks.</jats:p>",
    "URL": "https://doi.org/10.1234/fixture.2", "type": "journal-article",
}
