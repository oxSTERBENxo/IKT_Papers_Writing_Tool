## Table 1. Accuracy (%) by model, prompt and test set [Wilson 95% CI]

| Model | Prompt | S2019 | S2023 | S2026 | Invalid answers |
|---|---|---|---|---|---|
| Llama-2-7B | P0 | 44.3 [40.4, 48.3] | 46.3 [42.5, 50.0] | 41.2 [37.3, 45.1] | 3.3% |
| Llama-3.2-3B | P0 | 44.0 [40.1, 48.0] | 47.2 [43.4, 50.9] | 36.8 [33.1, 40.8] | 1.2% |
| Qwen2.5-7B | P0 | 65.3 [61.4, 69.0] | 62.1 [58.4, 65.7] | 53.3 [49.3, 57.3] | 0.0% |
| Gemma-3-4B | P0 | 35.8 [32.1, 39.7] | 33.2 [29.8, 36.9] | 32.5 [28.9, 36.3] | 0.5% |
| Llama-2-7B | P1 | 44.8 [40.9, 48.8] | 43.9 [40.1, 47.6] | — | 2.6% |
| Llama-3.2-3B | P1 | 46.8 [42.9, 50.8] | 48.1 [44.3, 51.8] | — | 0.9% |
| Qwen2.5-7B | P1 | 65.2 [61.3, 68.9] | 63.6 [59.9, 67.2] | — | 0.0% |
| Gemma-3-4B | P1 | 35.3 [31.6, 39.2] | 33.5 [30.1, 37.2] | — | 0.6% |
| GCN (no text, 5 seeds) | — | 67.5 ± 0.7 | 69.3 ± 0.7 | — | — |

## Table 2. H1: drop from S2019 to S2023, LLM (P0) vs GCN

| Model | LLM drop (pp) | GCN drop (pp) | Difference [95% CI] | p (bootstrap) |
|---|---|---|---|---|
| Llama-2-7B | -1.9 | -1.8 | -0.1 [-6.3, 6.1] | 0.934 |
| Llama-3.2-3B | -3.2 | -1.8 | -1.4 [-6.8, 4.5] | 0.646 |
| Qwen2.5-7B | 3.2 | -1.8 | 5.0 [-0.5, 10.3] | 0.08 |
| Gemma-3-4B | 2.6 | -1.8 | 4.4 [-2.1, 10.8] | 0.177 |

## Table 3. H2: extra 2023-vs-2026 advantage of new models over Llama-2 (P0)

Pooled GEE interaction (new model × 2023, category-adjusted): OR = 1.09 [0.86, 1.38], p = 0.469 (Holm 0.938).

| Model | Accuracy DiD (pp) [95% CI] | Category-reweighted DiD (pp) [95% CI] | GEE interaction OR [95% CI] | p |
|---|---|---|---|---|
| Llama-3.2-3B | 5.2 [-0.9, 11.5] | 2.6 [-3.8, 9.0] | 1.29 [0.95, 1.75] | 0.0997 |
| Qwen2.5-7B | 3.7 [-2.6, 9.7] | 2.8 [-3.4, 9.0] | 1.22 [0.90, 1.66] | 0.204 |
| Gemma-3-4B | -4.4 [-10.5, 1.8] | 2.0 [-4.1, 8.3] | 0.81 [0.60, 1.10] | 0.185 |

## Table 4. H3: title-completion probe

| Model | Exact 2023 | Exact 2026 | Fisher p | Mean F1 2023 | Mean F1 2026 | F1 Mann–Whitney p |
|---|---|---|---|---|---|---|
| Llama-2-7B | 0/614 (0.0%) | 0/566 (0.0%) | 1 | 12.1 | 9.8 | 0.0503 |
| Llama-3.2-3B | 0/614 (0.0%) | 0/566 (0.0%) | 1 | 12.4 | 9.6 | 0.0211 |
| Qwen2.5-7B | 3/614 (0.5%) | 0/566 (0.0%) | 0.251 | 15.0 | 12.7 | 0.189 |
| Gemma-3-4B | 2/614 (0.3%) | 0/566 (0.0%) | 0.5 | 12.5 | 11.6 | 0.273 |

Pooled DiD in exact-match rate (new models minus Llama-2, 2023 minus 2026): 0.27 pp [0.05, 0.54], bootstrap p = 0.02 (Holm 0.08).

## Table 5. H4: effect of citation-neighbour titles (P1 vs P0), McNemar exact tests

| Model | Set | Acc P0 | Acc P1 | Gain (pp) | Only P0 right | Only P1 right | p |
|---|---|---|---|---|---|---|---|
| Llama-2-7B | S2019 | 44.3 | 44.8 | 0.5 | 36 | 39 | 0.818 |
| Llama-2-7B | S2023 | 46.3 | 43.9 | -2.4 | 56 | 40 | 0.125 |
| Llama-3.2-3B | S2019 | 44.0 | 46.8 | 2.8 | 14 | 31 | 0.0161 |
| Llama-3.2-3B | S2023 | 47.2 | 48.1 | 0.9 | 25 | 31 | 0.504 |
| Qwen2.5-7B | S2019 | 65.3 | 65.2 | -0.2 | 15 | 14 | 1 |
| Qwen2.5-7B | S2023 | 62.1 | 63.6 | 1.5 | 10 | 20 | 0.0987 |
| Gemma-3-4B | S2019 | 35.8 | 35.3 | -0.5 | 32 | 29 | 0.798 |
| Gemma-3-4B | S2023 | 33.2 | 33.5 | 0.3 | 32 | 34 | 0.902 |

GEE (all models, both sets): neighbour prompt OR = 0.95 [0.88, 1.04]; prompt × homophily OR = 1.10 [0.98, 1.25], p = 0.114 (Holm 0.342).

