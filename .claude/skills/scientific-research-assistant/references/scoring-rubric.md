# Feasibility scoring rubric

`score` ranks candidate projects from scores you assign, each backed by evidence. The number is a summary, not the answer: the report always shows the per-criterion scores, the evidence, what is missing, and any blocker.

## Criteria

Score each 0 to 5. Weights sum to 100.

| Criterion | Weight | 0-1 | 2-3 | 4-5 |
| --- | --- | --- | --- | --- |
| `scientific_relevance` | 12 | nobody cites or needs it | of some interest | addresses something surveys or many papers name as important |
| `novelty_or_replication_value` | 12 | already done, no value in repeating | incremental, or novelty unsupported | supported gap, or a replication of a result that is contested, single-run or widely relied on |
| `paper_and_code_availability` | 10 | paywalled, no code | code exists but undocumented or unlicensed | open paper, licensed and documented code with entry points |
| `dataset_accessibility` | 12 | restricted, gated, missing | public but unclear licence or heavy preprocessing | public, licensed, verified, manageable size |
| `compute_fit` | 12 | exceeds the hardware | fits with reduced scale | fits with margin |
| `implementation_simplicity` | 10 | new system from scratch | substantial adaptation | mostly running and modifying existing code |
| `time_fit` | 10 | exceeds the budget | fits with no slack | fits with room for reruns |
| `reproducibility` | 8 | no seeds, configs or environment | some specified | seeds, configs and pinned environment all present |
| `evaluation_clarity` | 7 | no agreed metric | metric clear, protocol partly specified | standard metric and protocol with published numbers to compare |
| `low_failure_risk` | 7 | likely to end with nothing reportable | some outcomes unreportable | any outcome is reportable |

Rules for assigning scores:

- Every score needs at least one evidence string and an `evidence_level` (`verified`, `estimate`, `speculative`). The command rejects scores without evidence.
- If you lack the information, set `"score": null` and list what is missing. Do not guess a middle value. Unscored criteria widen the reported score range instead of being imputed.
- Score against the user's stated constraints, not in general.
- Adjust for experience: for a beginner, lower `implementation_simplicity` and `low_failure_risk` for anything needing custom training loops or legacy environments.

## Novelty caps

Each candidate states how its closest prior work was read:

```json
"novelty_evidence": {"closest_read": "full_text", "prior_overlap": "partial"}
```

`novelty_or_replication_value` is capped by the command, and the cap is shown in the output:

- **Capped at 2** unless `closest_read` is `full_text`. A missing block counts as unread.
- **Capped at 1** when `prior_overlap` is `same_experiment` and the mode is `original` or `extension`.

The caps exist because an abstract-level reading once scored an already-published experiment 3/5 and ranked it first.

## Question types: novelty versus replication value

Set `question_type` on each candidate (`novel`, `extension`, `replication`, `benchmark_validity`, `answered`). It is inferred as `replication` when the mode is `reproduction` or `replication`.

- **Novel and extension candidates.** `novelty_or_replication_value` is scored as **novelty**, and the caps above apply.
- **Replication and benchmark-validity candidates.** The same criterion is scored as **replication value**: how much the field relies on the result, whether it is contested, single-run or protocol-flawed, and whether the concern is evidenced.
  - Prior work running the same experiment is the premise, not a penalty, so the novelty caps do not apply.
  - The only cap is 3/5 when the study being re-tested was not read in full.
  - These candidates must give a `replication_rationale`, a list of reasons, or the input is rejected.
- **Answered candidates** are blocked.

The output shows `question_type` and `value_basis` for each candidate, so a reader can see which reading of the criterion was used.

```json
{"id": "R1", "mode": "replication", "question_type": "replication",
 "replication_rationale": ["single-run result cited as settled", "model selection on the test set"],
 "novelty_evidence": {"closest_read": "full_text", "prior_overlap": "same_experiment"}}
```

## Hard blockers

A blocked candidate is listed below every viable one and gets no rank, whatever its score. Blockers arise three ways:

1. **Declared** in the candidate's `blockers` list: controlled-access or unavailable data, a licence that forbids the intended use, no obtainable full text, required proprietary software, ethics approval not obtainable in time.
2. **Gating criterion scored 0:** `dataset_accessibility`, `compute_fit` or `time_fit` for any project; `paper_and_code_availability` as well when `mode` is `reproduction` (a reproduction needs the original code; without it the project is a replication).
3. **Budget check:** an entry in `estimates` exceeds the matching constraint: `weeks` vs `time_budget_weeks`, `min_vram_gb` vs `gpu_vram_gb`, `gpu_hours` vs `gpu_hours_budget`, `storage_gb` vs `storage_gb`.

## Input format

```json
{
  "constraints": {"time_budget_weeks": 8, "gpu_vram_gb": 8, "gpu_hours_budget": 60, "storage_gb": 50},
  "weights": {"time_fit": 15},
  "candidates": [
    {
      "id": "A",
      "title": "Multi-seed reproduction of <paper>",
      "mode": "reproduction",
      "estimates": {"weeks": 4, "min_vram_gb": 6, "gpu_hours": 20, "storage_gb": 2},
      "novelty_evidence": {"closest_read": "full_text", "prior_overlap": "different"},
      "blockers": [],
      "criteria": {
        "dataset_accessibility": {
          "score": 4,
          "evidence": ["huggingface.co/datasets/<id>: licence cc-by-4.0, not gated, 12k rows"],
          "evidence_level": "verified",
          "missing": []
        },
        "compute_fit": {"score": null, "evidence": [], "evidence_level": null,
                        "missing": ["Paper and README state no hardware"]}
      }
    }
  ]
}
```

`weights` is optional and overrides individual defaults; say so in the report if you change them. Evidence strings may contain `[@key]` citations that the report renderer expands.

## Reading the output

| Field | Meaning |
| --- | --- |
| `score_percent` | weighted share earned on the criteria that were scored |
| `score_range` | total out of 100 if every unscored criterion were 0, and if every one were 5 |
| `scored_weight_percent` | how much of the rubric was actually scored |
| `verified_weight_percent` | how much rests on verified evidence rather than estimates |
| `status`, `blockers` | `blocked` candidates carry the reasons |

Two candidates whose ranges overlap are not meaningfully ordered; say that instead of presenting the higher number as a winner. A candidate with a low verified share needs more checking before anyone commits to it.

```
python "<skill-dir>/scripts/sra.py" score --input scoring.json --out ranking.json
```
