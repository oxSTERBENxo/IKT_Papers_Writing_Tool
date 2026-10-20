# Retrieval evaluation, 2026-10-18/19

Command: `retrieval-eval --fixtures "evals/retrieval/*.json"`. Raw outputs are in the project's `work/retrieval_eval/`.

## Fixtures

| Split | Topics | Known relevant papers | Origin |
| --- | --- | --- | --- |
| dev | 2 (UPFD fake news, ABSA syntax GCNs) | 9 | the two adversarial audits |
| heldout | 7 (LLM-graph leakage, simple baselines vs LLM-graph methods, heterophilic TAGs, TAG robustness, GNN-RAG small readers, TAPE with small LLMs, TextGCN vs MLP) | 15 | closest papers found in the first opportunity report |
| control | 2 implausible ideas (chant lyrics on monastery floor plans; beekeeping forum ABSA) | 0 | negative controls: no prior work expected |

**Provenance and fairness.**
- **Claims and queries.** For 8 of the 9 positive fixtures they are copied from challenge runs made before the known papers were found. At the time, every one of those runs returned "no close match".
- **Design elements, anchors and seeds** were written later, by an author who knew the answers. They are generic, but not blind.
- **TextGCN fixture.** Its queries were written for this evaluation.
- **Seeds** are never counted as hits.

## Configurations

- `baseline`: keyword challenge only. This approximates the toolkit before the adversarial update.
- `challenge`: current challenge (design-based queries, seed citing-works probes, citation expansion).
- `landscape`: the literature-first `map`.
- `full`: union of challenge and landscape.

## Results

### Run A: arXiv and Crossref only, all configurations equal (controlled)

OpenAlex's keyless daily budget was exhausted, so citation expansion, which needs OpenAlex, mostly failed in every configuration.

| Split | baseline | challenge | landscape | full |
| --- | --- | --- | --- | --- |
| dev, found | 1/9 | 4/9 | 4/9 | 4/9 |
| dev, top 20 | 0/9 | 1/9 | 3/9 | 3/9 |
| heldout, found | 7/15 | 11/15 | 7/15 | 11/15 |
| heldout, top 20 | 7/15 | 9/15 | 7/15 | 7/15 |

Run B (dev with OpenAlex, 2026-10-18) gave the same dev numbers. A held-out run with OpenAlex was confounded: OpenAlex failed for some configurations and not others. Its numbers (7, 10, 7 and 10 of 15) are not used.

### Challenge signal ("close prior work found")

| Split | baseline | challenge (before topic-overlap fix) | challenge (after fix, run A sources) |
| --- | --- | --- | --- |
| dev (2 topics with prior work) | 0/2 | 2/2 | 1/2 |
| heldout (7 topics with prior work) | 0/7 | 4/7 | 4/7 |
| control (2 topics without) | 0/2 | 1/2 | 0/2 |

The "before" counts for dev and held-out topics come from the runs with OpenAlex partly available; the control and "after" counts come from arXiv+Crossref runs, so the columns are not strictly comparable. Before the fix, the false alarm on a control came from an off-topic paper (WiFi indoor floor classification) that matched two generic design elements. Design matches now count toward the signal only for papers with topic-term overlap ≥ 0.3. This change was made after seeing the control result, so the control numbers after the fix are not an independent test.

## What this shows

- **Design-based queries and seed probes improve recall.** The current challenge found more known papers than the old keyword challenge on both dev (4 vs 1 of 9) and held-out topics (11 vs 7 of 15, 9 vs 7 in the top 20).
- **Verdicts changed most.** The old challenge said "no close match" for all 9 topics with known prior work. On 3 held-out topics it said so although it ranked the known papers 1-3: the failure was the verdict, not retrieval. The current one flags 5 of 9 and neither control (before the fix: 6 of 9 and 1 of 2 controls).
- **The literature-first `map` mainly helps ranking on dev topics** (3/9 vs 1/9 in the top 20). It added no recall on held-out topics, and on three held-out topics (leakage, simple baselines, heterophily) it found fewer known papers than the plain challenge. Its value is the reading order and the evidence buckets, not extra recall, and that was not established on held-out data.
- **The union (`full`) dilutes ranking:** its top 20 is worse than the challenge alone on held-out topics.

## What remains unreliable

- **Small samples.** 24 known papers over 9 topics, and 2 controls. Differences of one or two papers are noise. There is no meaningful estimate of false-alarm rate from 2 controls.
- **Several closest papers are missed by every configuration.** Examples: Sachan et al., both ABSA reproducibility studies, DAWN, Xu et al., Huang et al. 2023, LLMNodeBed (simple-baselines and TAPE topics), and RPO-RAG. Web search found several of them in the audits. It is not automated, so it is not measured here.
- **The signal still misses.** 4 of 9 topics with known prior work are not flagged after the fix.
- **Results depend on the day.** Rate limits and index coverage vary: OpenAlex was unavailable for part of the run, and Semantic Scholar throughout.
- **Seen during development.** The read-first change (top matches added) and the topic-overlap rule were made after inspecting dev and control results.

## Evidence-bucket precision (smoke test)

I ran `map` live on an unseen topic (GNN recommender systems; arXiv and Crossref):
- **Useful:** it surfaced a relevant reproducibility study (Dacrema et al. 2025, on SIGIR 2022 GNN recommender papers).
- **Imprecise:** its negative-result bucket held a survey and a method paper (PinSage), both matched by the phrase "as well as". That phrase was removed from the pattern, with a regression test.

Bucket precision was not measured systematically; treat buckets as a reading order only.
