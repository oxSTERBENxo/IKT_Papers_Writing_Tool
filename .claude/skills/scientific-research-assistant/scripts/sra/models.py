"""Paper record, identifier normalisation and deduplication."""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

from .text import normalize_title

DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\"<>]+", re.I)
ARXIV_NEW_RE = re.compile(r"(?<![\d.])(\d{4}\.\d{4,5})(?:v\d+)?(?![\d])")
ARXIV_OLD_RE = re.compile(r"\b([a-z\-]+(?:\.[A-Z]{2})?/\d{7})(?:v\d+)?\b")
OPENALEX_RE = re.compile(r"\b(W\d{4,})\b")


# Whose abstract to trust when records are merged: the source that hosts or
# registers the paper first, aggregators last. Aggregated metadata is sometimes
# attached to the wrong work, so "longest abstract wins" is not safe.
ABSTRACT_TRUST = ["arxiv", "pubmed", "crossref", "huggingface", "semantic_scholar", "openalex"]


def normalize_doi(value: str | None) -> str | None:
    if not value:
        return None
    m = DOI_RE.search(value.strip())
    return m.group(0).rstrip(".,;)]}").lower() if m else None


def normalize_arxiv_id(value: str | None) -> str | None:
    if not value:
        return None
    v = re.sub(r"^arxiv:", "", value.strip(), flags=re.I)
    m = ARXIV_NEW_RE.search(v) or ARXIV_OLD_RE.search(v)
    return m.group(1) if m else None


def arxiv_from_doi(doi: str | None) -> str | None:
    if doi and doi.lower().startswith("10.48550/arxiv."):
        return normalize_arxiv_id(doi[len("10.48550/arxiv."):])
    return None


def surname(name: str | None) -> str:
    """Best-effort family name from 'Given Family' or 'Family, Given'."""
    if not name:
        return ""
    part = name.split(",")[0] if "," in name else name
    words = normalize_title(part).split()
    return (words[0] if "," in name else words[-1]) if words else ""


def parse_identifier(value: str) -> tuple[str, str]:
    """Classify a user-supplied identifier. Returns (kind, value); kind is one of
    openalex, doi, arxiv, pmid, title."""
    v = value.strip()
    if "openalex.org" in v.lower() or re.fullmatch(r"W\d{4,}", v):
        m = OPENALEX_RE.search(v)
        if m:
            return "openalex", m.group(1)
    m = re.search(r"(?:pmid:\s*|pubmed\.ncbi\.nlm\.nih\.gov/)(\d+)", v, re.I)
    if m:
        return "pmid", m.group(1)
    doi = normalize_doi(v)
    if doi:
        ax = arxiv_from_doi(doi)
        return ("arxiv", ax) if ax else ("doi", doi)
    if re.search(r"arxiv", v, re.I) or re.fullmatch(r"\d{4}\.\d{4,5}(v\d+)?", v) or ARXIV_OLD_RE.fullmatch(v):
        ax = normalize_arxiv_id(v)
        if ax:
            return "arxiv", ax
    return "title", v


@dataclass
class Paper:
    title: str = ""
    authors: list = field(default_factory=list)
    year: int | None = None
    date: str | None = None
    venue: str | None = None
    doi: str | None = None
    arxiv_id: str | None = None
    pmid: str | None = None
    openalex_id: str | None = None
    s2_id: str | None = None
    url: str | None = None
    pdf_url: str | None = None
    abstract: str | None = None
    citations: int | None = None
    is_oa: bool | None = None
    is_retracted: bool | None = None
    type: str | None = None
    sources: list = field(default_factory=list)
    found_by: list = field(default_factory=list)
    extra: dict = field(default_factory=dict)

    def __post_init__(self):
        self.title = re.sub(r"\s+", " ", self.title or "").strip()
        self.doi = normalize_doi(self.doi)
        self.arxiv_id = normalize_arxiv_id(self.arxiv_id) or arxiv_from_doi(self.doi)
        if self.abstract:
            self.abstract = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", self.abstract)).strip() or None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Paper":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})

    def best_url(self) -> str | None:
        if self.doi and not arxiv_from_doi(self.doi):
            return f"https://doi.org/{self.doi}"
        if self.arxiv_id:
            return f"https://arxiv.org/abs/{self.arxiv_id}"
        if self.pmid:
            return f"https://pubmed.ncbi.nlm.nih.gov/{self.pmid}/"
        return self.url

    def identity_keys(self) -> list[str]:
        keys = []
        if self.doi and not arxiv_from_doi(self.doi):
            keys.append(f"doi:{self.doi}")
        if self.arxiv_id:
            keys.append(f"arxiv:{self.arxiv_id}")
        if self.pmid:
            keys.append(f"pmid:{self.pmid}")
        if self.openalex_id:
            keys.append(f"openalex:{self.openalex_id}")
        if self.s2_id:
            keys.append(f"s2:{self.s2_id}")
        # Title is the fallback that links a preprint to its published version.
        # Short titles collide too easily, so they also need the first author.
        nt = normalize_title(self.title)
        if len(nt.split()) >= 5:
            keys.append(f"title:{nt}")
        elif nt and self.authors:
            keys.append(f"title:{nt}|{surname(self.authors[0])}")
        return keys

    def abstract_source(self) -> str | None:
        if not self.abstract:
            return None
        return self.extra.get("abstract_source") or (self.sources[0] if self.sources else None)

    def absorb(self, other: "Paper") -> None:
        """Fill gaps in self from other; self's non-empty values win, except that a
        published record overrides a preprint's venue and date."""
        def published(p):
            return bool(p.doi and not arxiv_from_doi(p.doi))

        if published(other) and not published(self):
            for name in ("doi", "venue", "year", "date"):
                if getattr(other, name):
                    setattr(self, name, getattr(other, name))

        def trust(p):
            src = p.abstract_source()
            return ABSTRACT_TRUST.index(src) if src in ABSTRACT_TRUST else len(ABSTRACT_TRUST)

        if other.abstract and (not self.abstract or trust(other) < trust(self)):
            self.abstract, self.extra["abstract_source"] = other.abstract, other.abstract_source()
        elif self.abstract:
            self.extra["abstract_source"] = self.abstract_source()
        for name in ("title", "year", "date", "venue", "doi", "arxiv_id", "pmid", "openalex_id", "s2_id",
                     "url", "pdf_url", "type"):
            if not getattr(self, name) and getattr(other, name):
                setattr(self, name, getattr(other, name))
        if not self.authors:
            self.authors = list(other.authors)
        if other.citations is not None:
            self.citations = max(self.citations or 0, other.citations)
        self.is_oa = True if (self.is_oa or other.is_oa) else (self.is_oa if self.is_oa is not None else other.is_oa)
        self.is_retracted = True if (self.is_retracted or other.is_retracted) else (
            self.is_retracted if self.is_retracted is not None else other.is_retracted)
        self.sources = sorted(set(self.sources) | set(other.sources))
        for fb in other.found_by:
            if fb not in self.found_by:
                self.found_by.append(fb)
        for k, v in other.extra.items():
            self.extra.setdefault(k, v)


def dedupe(papers: list[Paper]) -> list[Paper]:
    """Merge records that share a DOI, arXiv ID, PMID, source ID or long title."""
    parent = list(range(len(papers)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    seen: dict[str, int] = {}
    for i, p in enumerate(papers):
        for key in p.identity_keys():
            if key in seen:
                parent[find(i)] = find(seen[key])
            else:
                seen[key] = i

    groups: dict[int, list[Paper]] = {}
    for i, p in enumerate(papers):
        groups.setdefault(find(i), []).append(p)

    merged = []
    for group in groups.values():
        # Published records (non-arXiv DOI) lead so their venue and year are kept.
        group.sort(key=lambda p: 0 if (p.doi and not arxiv_from_doi(p.doi)) else 1)
        head = Paper.from_dict(group[0].to_dict())
        for other in group[1:]:
            head.absorb(other)
        merged.append(head)
    return merged
