# Retrieval reliability, 2026-10-19

Follows `2026-10-19-retrieval.md` (run A). That file and the fixtures in `evals/retrieval/` are unchanged and
serve as the regression benchmark. Raw outputs: the project's `work/retrieval_eval/reliability/`.

## Part 1. Why known papers were missed (failure analysis, before any change)

### Method

1. **Offline replay of run A.** Every response the toolkit received is still in its response cache (with the request
   URL). Re-running the `challenge` configuration against the cache alone, with any uncached request treated as
   failed, reproduced run A's dev ranks exactly (1, 122, 150, 98). Held-out replays are approximate: 12–16
   responses per fixture had been overwritten or never cached. The replay records where each target first
   appears: raw source results, citation expansion, or the final ranking.
2. **Cache scan.** All 3,448 cached responses (from 10-13 to 10-19) were searched for each target's title and
   identifiers, to see whether any API had ever returned it.
3. **Live probes.** Live probes ran with arXiv and Crossref only; OpenAlex's keyless budget was exhausted, returning
   HTTP 429. For each missed paper:
   - each fixture query was sent at depth 50 in the current arXiv form (all words ANDed), in a relaxed arXiv form
     (words ORed, relevance-ranked), and to Crossref;
   - a search for the paper's own title checked that the index holds it;
   - the share of query words appearing in the paper's title and abstract was computed.

### A systemic finding first

In run A, **646 of 745 arXiv searches (87%) returned zero results**, against 0 of 854 Crossref searches.

| Query length (words) | arXiv searches empty |
| --- | --- |
| 3–5 | 10/24 |
| 6–8 | 306/367 |
| 9–11 | 267/289 |
| 12–14 | 63/65 |

The arXiv client ANDs every content word, and fixture queries are 6–14 words long. arXiv, the main index for recent
ML preprints, therefore contributed almost nothing. Crossref, which does not index arXiv-only preprints and often
returns title-only records, carried the search. Between 27% and 50% of each fixture's candidates had no abstract.

### Missed papers (challenge configuration, run A)

| Paper | Fixture | Indexed by a searched source? | Cause | Evidence |
| --- | --- | --- | --- | --- |
| Sachan et al., "Do Syntax Trees Help Pre-trained Transformers Extract Information?" | dev ABSA | yes (arXiv) | **terminology mismatch**, then **truncation** | It is about information extraction, not sentiment: at most 40% of any query's words appear in it. The relaxed arXiv form returns it at position 43; the toolkit keeps 10 per query. |
| "Reproducibility, Replicability and Beyond … ABSA in the Wild" | dev ABSA | yes (arXiv, Crossref) | **query formulation** | No query, form or depth up to 50 returns it. Its own title finds it at rank 1 in Crossref. The only reproducibility query also asked for "graph neural network variance seeds", which it does not mention. |
| "On the Current State of Reproducibility … for ABSA" | dev ABSA | yes (Crossref only; no arXiv) | **query formulation** | Same as above. It does not cite the seed paper, so citation expansion cannot reach it. |
| "Revisiting Fake News Detection: Towards Temporality-aware Evaluation…" | dev UPFD | yes | **candidate truncation in citation expansion**, plus **rate limiting** | It cites the seed (UPFD). It appeared in the seed's citing list sorted by date when fetched 100 at a time on 10-17; the challenge fetches 20 per sort. During run A, OpenAlex (needed for expansion) was over budget. No query returns it at depth 50. |
| "Enhancing Fake-News Detection with Node-Level Topological Features" | dev UPFD | yes (arXiv) | **query formulation** (AND), then **truncation** | Every AND query returned nothing. The relaxed form returns it at position 14 for "UPFD fake news detection reproducibility text-only baseline"; the toolkit keeps 10. |
| Huang et al., "Can LLMs Effectively Leverage Graph Structural Information…?" | held-out leakage | yes (arXiv) | **query formulation / source ranking**, then **citation-expansion availability** | Queries share up to 83% of their words with it, yet no form returns it at depth 50. It is position 21 in the Semantic Scholar reference list of a closely related 2025 paper, fetched once during the earlier held-out run; Semantic Scholar mostly returns 429 without a key. |
| "When Do LLMs Help With Node Classification?" (LLMNodeBed) | held-out simple baselines | yes (arXiv) | as for Huang et al. | Position 4 in the same reference list; no query returns it at depth 50. |
| LLMNodeBed | held-out TAPE | yes (arXiv) | as for Huang et al. | No source failed for this fixture in run A. In the later probe arXiv was rate-limited, so depth-50 positions are unknown. |
| "RPO-RAG: Aligning Small LLMs…" | held-out GNN-RAG | arXiv only | **API rate limiting**, plus **source set** | arXiv answered the fixture's first query with HTTP 429, which switched arXiv off for the whole fixture in both runs. Crossref cannot hold arXiv-only preprints. Only Hugging Face paper search ever returned it (10-17); that source is in the toolkit's default `cs` source list but was not in the evaluation's source list. |

### Found, but ranked too low to be read

| Paper | Rank in run A | Cause | Evidence |
| --- | --- | --- | --- |
| "Does syntax matter? A strong baseline for ABSA with RoBERTa" | 150 of 304 | **ranking** | Crossref returned it third, with an abstract. The challenge ranks only by rarity-weighted overlap with the one-sentence claim. Rare filler words in the claim ("controlled", "showing", "still", "held", "plain") carry most of the weight. Its overlap with the claim was 0.06; with the first query, 0.88. |
| BERT4GCN | 98 | ranking | claim overlap 0.09, best query coverage 0.75 |
| "Nothing Stands Alone…" | 122 | ranking | reached only through citations; claim overlap 0.09 |
| "Exploring the Potential of LLMs in Learning on Graphs" | 76–88 | ranking | claim overlap 0.08 |
| "A critical look at the evaluation of GNNs under heterophily" | 53–55 | ranking | reached only through references of a top result |

Poor first-pass ranking also hurts recall. The challenge expands citations only for its three top-ranked papers. On
the ABSA fixture these included "Multi-aspect sentiment classification on USA-based…", an off-topic paper.

### Causes not observed

- **Deduplication or identifier mismatch: none observed.** Every target present in the final candidate list was
  matched by arXiv ID, DOI or title. The closest non-matching title for each missed target had a similarity of at
  most 0.64, so no target was lost to a near-duplicate.

### Verdict failures despite successful retrieval

Run A's challenge said "no close match" on 4 of 9 topics with known prior work:
- **Simple baselines** (a known paper at rank 1) and **TextGCN** (rank 2): both papers were title-only records.
  The abstract lookup for title-only records goes through OpenAlex, which was over budget. A title cannot reach the
  0.6 word overlap the verdict requires.
- **ABSA and leakage:** the known papers were in the list but ranked 76–150.

These are failures of metadata and verdict, not of retrieval.

### Counts

Nine missed target instances, eight distinct papers. Several have more than one cause:

| Cause | Missed papers |
| --- | --- |
| Query formulation (arXiv AND, missing query angle) | 6 |
| Candidate truncation (per-query limit or citing-list depth) | 3 |
| Citation expansion unavailable (OpenAlex budget, Semantic Scholar 429) | 4 |
| API rate limiting of a search source | 1 |
| Terminology mismatch | 1 |
| Missing from all searched indexes | 0 |
| Deduplication or identifier mismatch | 0 |

Ranking buried 5 further found papers below rank 50. The verdict failed on 2 topics where retrieval had succeeded.

### Which improvements this justifies

| Diagnosed cause | Candidate change | Tested here? |
| --- | --- | --- |
| arXiv AND returns nothing | relevance-ranked OR for arXiv queries | yes (`challenge_arxiv_any`) |
| Ranking by claim only | rank fusion over the claim and each query | yes (`challenge_lexical`) |
| Paraphrase and terminology gaps in ranking | local embeddings as an extra ranking signal | yes (`challenge_hybrid`) |
| A single 429 disables arXiv for a fixture | one cool-down retry | yes (part of `challenge_arxiv_any`) |
| Citing lists truncated at 20 | fetch one deep page of citing works and rank locally | no: needs OpenAlex, which was over budget all day |
| Title-only records defeat the verdict | abstract fallback through Crossref or arXiv title search | no: found during the analysis, after the plan was fixed |
| Hugging Face search not in the evaluation's source list | add it to the evaluation sources | no: a source change, not an algorithm change |
| Cross-source merging and deduplication | — | not justified: no deduplication failure was found |
