# Analysis plan (fixed before any model output was looked at)

**Working title:** Has the leakage-free split expired? Testing memorisation in LLM node classification on arXiv citation graphs with newer open models.

**Type:** replication and extension of Huang et al. (arXiv:2309.16595), who found "no substantial evidence" of data leakage using ChatGPT and Llama-2 on ogbn-arxiv (2019 test papers) versus their arxiv-2023 dataset. Their 2023 test papers predate those models' training data, but not the training data of models released from 2024 on.

## Test sets
| Set | Source | Papers | Seen in training by |
|---|---|---|---|
| **S2019** | ogbn-arxiv test split (year 2019); random sample, seed 20261020 | 600 | all four models |
| **S2023** | arxiv-2023 test split (Jan–Aug 2023), Huang et al. | all 668 | the 2024–2025 models, *not* Llama-2 |
| **S2026** | fresh sample of arXiv CS papers submitted Jan–Aug 2026, via the arXiv API; primary category must be one of the 40 ogbn-arxiv classes | 600 | none of the models |

The label is the paper's arXiv CS sub-category (40 classes).

## Models (local, via Ollama; temperature 0, seed 42)
- **Llama-2-7B-chat** (`llama2:7b-chat`): old model. Pretraining cut-off is before the 2023 test papers; it is the control.
- **Llama-3.2-3B** (`llama3.2`), **Qwen2.5-7B** (`qwen2.5:7b`), **Gemma-3-4B** (`gemma3:4b`): new models, released after the 2023 papers, with cut-offs after mid-2023. Exact cut-offs are taken from the model cards.

## Prompt conditions
- **P0 (text only):** title + abstract, using Huang et al.'s system prompt ("Please predict the most appropriate arXiv Computer Science (CS) sub-category for the paper. The predicted sub-category should be in the format 'cs.XX'."). Run on all three sets.
- **P1 (+ citation neighbours):** P0 plus the titles of up to 5 randomly chosen 1-hop citation neighbours (Huang's "1-hop title" style). Run on S2019 and S2023, which have graphs.
- **Title-completion probe:** the model gets only the first half of the title (no abstract) and is asked to complete it. Run on S2023 and S2026, all models.

Parsing: the first `cs.XX` in the answer, case-insensitive. An answer with no valid class counts as wrong; the invalid rate is reported separately.

## Graph baseline (neural network, no text)
A 2-layer GCN trained on each citation graph with the datasets' own 128-dimensional node features, on each dataset's official train/validation split, with 5 seeds. Test accuracy is measured on the same S2019 and S2023 nodes.

## Hypotheses and tests (alpha = 0.05; Holm correction across H1–H4)
| # | Question | Test |
|---|---|---|
| H1 (replication) | For **Llama-2**, is the accuracy drop from S2019 to S2023 larger than the GCN's drop? (Huang: no.) | Difference-in-differences with 2,000-sample node bootstrap CI |
| H2 (main) | Do **new** models do relatively better on S2023 (seen) than on S2026 (unseen), compared with Llama-2 (both unseen)? | GEE logistic regression `correct ~ model × period + category`, clustered by paper, on S2023 ∪ S2026 under P0; test the new-model × S2023 interaction; DiD in accuracy with bootstrap CI |
| H3 (verbatim memorisation) | Is the title-completion exact-match rate higher on S2023 than on S2026 for new models, but not for Llama-2? | Fisher's exact test per model; GEE logistic regression with model × period interaction |
| H4 (graph) | Do citation-neighbour titles (P1 vs P0) change accuracy, and does the gain depend on the node's label homophily (share of neighbours with the same label)? | McNemar test per model × set; logistic GEE `correct ~ prompt × homophily` |

All accuracies are reported with Wilson 95% CIs. Effect sizes (accuracy differences in percentage points, odds ratios) drive the conclusions.

## Pre-registered confounds and how they are handled
- **Category mix differs by year** (for example, more cs.CL/cs.LG in 2023/2026): category fixed effects in H2 and H3, plus a category-reweighted accuracy as a robustness check.
- **"Knowing the era" vs memorising the paper:** new models may know 2023-era topics without having memorised specific papers. H3 (verbatim title completion) separates the two.
- **Model quality:** absorbed by model main effects; only the interactions are interpreted.
- **S2026 has no citation graph:** H4 uses only S2019 and S2023.

## Deviations
(Recorded here if anything changes after outputs are seen.)
1. **Prompt and answer length (decided after a smoke test of 5–24 papers per model, before the full run).** Three changes:
   - The user prompt now ends with "Reply with only the sub-category code in the format 'cs.XX' (for example cs.LG), nothing else." The system prompt is still Huang et al.'s.
   - Answers are capped at 24 tokens, except Llama-2-7B-chat, which always writes a one-sentence preamble and gets 64 (24 tokens parsed 0/24 of its answers; 64 parsed 24/24).
   - The probe uses only titles of at least 6 words, so that half a title is a meaningful cue. If an answer contains a quoted title, the quoted part is scored.
2. **Throughput.** Requests are sent 4 at a time. Ollama may batch concurrent requests, which can make temperature-0 outputs very slightly non-deterministic; this is noted as a limitation.
3. **H2 regression fixes (2026-10-20, after the outputs were collected; code bugs, not changes to the hypothesis).** Both fitted models returned NaN:
   - **Collinear term.** The pooled model wrote `new * s23 + C(model)`, but `new` is the sum of the model dummies, so the design was rank-deficient. It is now `new:s23 + s23 + C(model) + C(cat)`. This is the same model with the same interaction term.
   - **Rare categories.** The rule "pool categories with fewer than 15 into *other*" counted rows (4 per paper) instead of papers. Categories with only 4 papers stayed separate, and two of them had zero correct answers (perfect separation). The rule now counts papers, as intended.
4. **GCN runs (engineering only; the model, settings and seeds are unchanged).**
   - The first GCN run (started about 01:20 on 2026-10-20, alongside the LLM run) stopped after 2 of 10 seeds without writing any results. Its log is kept in `results/gcn_log_attempt1.txt`.
   - The rerun stores the normalised adjacency matrix in CSR instead of COO format. It is the same matrix, and the change makes CPU training about 3× faster (2.4 s vs 7.1 s per epoch on ogbn-arxiv).
   - It also prints progress every 50 epochs.
   - That CPU rerun was stopped after 2 seeds (log: `results/gcn_log_attempt2_cpu.txt`). The final run used the GPU (NVIDIA RTX 5060 Laptop, PyTorch 2.14.1+cu130, in `.venv-gpu`) and took 2.5 minutes for all 10 seed × dataset runs. The model, hyperparameters and seeds are identical. GPU sparse kernels are not bit-for-bit identical to CPU ones, so per-seed numbers differ slightly from the CPU attempts (S2019 seed 0: 67.3% GPU vs 68.7% CPU).
