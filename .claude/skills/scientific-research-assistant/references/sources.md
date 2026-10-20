# Sources, keys and rate limits

Run `python "<skill-dir>/scripts/sra.py" sources` to see which integrations answer right now and which keys are set.

## Which sources for which field

| `--domain` | Sources searched | Use for |
| --- | --- | --- |
| `cs` (default) | OpenAlex, arXiv, Semantic Scholar, Crossref, Hugging Face papers | machine learning, NLP, vision, computer science |
| `biomed` | OpenAlex, PubMed, Semantic Scholar, Crossref | medicine, biology, health |
| `general` | OpenAlex, Crossref, Semantic Scholar, arXiv | physics, mathematics, social science, anything else |

Override with `--sources openalex,arxiv,pubmed` (names: `openalex`, `arxiv`, `crossref`, `semantic_scholar` or `s2`, `pubmed`, `huggingface` or `hf`). For fields with their own repositories (chemistry, economics, education), say in the report that those were not searched.

## What each source contributes

| Source | Good for | Limits without a key | Optional key (environment variable) |
| --- | --- | --- | --- |
| OpenAlex | broad coverage, citation counts, citation graph, open-access status, retraction flag | a small free daily budget shared per IP address (roughly 100 list requests); resets at midnight UTC | `OPENALEX_API_KEY` (free) |
| arXiv | preprints, authoritative abstracts for arXiv papers | one request every 3 seconds (enforced by the client) | none |
| Crossref | published records, authoritative venue and date for a DOI | generous | none; set `SRA_CONTACT_EMAIL` for the polite pool |
| Semantic Scholar | relevance search, references, citations, recommendations | shared pool, frequently answers HTTP 429 | `SEMANTIC_SCHOLAR_API_KEY` (free on request) |
| PubMed | biomedical literature | 3 requests per second | `NCBI_API_KEY` |
| Hugging Face | datasets (licence, size, gating), paper pages, models and datasets tagged with an arXiv ID | generous | `HF_TOKEN` |
| GitHub | repositories, READMEs, file lists, issues | 60 requests per hour, 10 searches per minute | `GITHUB_TOKEN` or `GH_TOKEN` |
| Zenodo | datasets outside Hugging Face | generous | none |
| doi.org | confirming that a DOI exists | generous | none |

Papers With Code no longer offers an API (its site redirects to Hugging Face), so code discovery uses Hugging Face paper pages, links in abstracts, and GitHub search.

For regular use, set `OPENALEX_API_KEY` and `GITHUB_TOKEN` at least. Keys are read from the environment only; never write them into files or commands that get saved.

```
# PowerShell
$env:OPENALEX_API_KEY = "..." ; $env:GITHUB_TOKEN = "..."
# bash
export OPENALEX_API_KEY=... GITHUB_TOKEN=...
```

## How failures are handled

- Transient errors (429, 5xx, network) are retried with exponential backoff, honouring `Retry-After` up to 20 seconds. Longer waits and exhausted quotas fail immediately instead of hanging.
- A source that is rate-limited, unauthorised or unreachable is skipped for the rest of that command and reported as `FAILED` or `PARTIAL` in the source status lines, with the provider's own message.
- Responses are cached for 24 hours in the system temp directory (`SRA_CACHE_DIR` overrides; `--no-cache` or `SRA_CACHE_DIR=off` disables). Rerunning a command after a partial failure only repeats the failed calls.

When a source fails: continue with the others, record the failure in the report's `search_log.sources_failed` and limitations, and lower any novelty confidence that depended on it. If OpenAlex is down, citation exploration falls back to Semantic Scholar; if both are down, say that citation exploration was not done.

## Budgeting calls

OpenAlex and GitHub are the scarce ones without keys.

- A `search` costs one OpenAlex call per query per strategy variant. Four queries with five strategies is about 30 calls. Prefer three or four well-chosen queries over many.
- A `challenge` costs four OpenAlex calls per query, plus up to 15 abstract lookups.
- A `repro` costs about three GitHub searches plus four calls per inspected repository (`--max-repos`, default 4).

## Data quality cautions

- Aggregators sometimes attach an abstract, year or venue to the wrong work. The toolkit prefers abstracts from the primary source and takes venue and date for a DOI from Crossref, and `verify-refs` checks titles, but read with care: if an abstract does not match its title, resolve the paper again by identifier.
- Citation counts differ between sources and change daily. Quote them as "at retrieval".
- "Open access" flags and licences on mirrors can be wrong or missing; the licence that binds is the one on the original distribution.
- Lexical ranking scores (`match`, `overlap`, `tfidf`) order results by shared wording. They do not measure quality or semantic similarity.
