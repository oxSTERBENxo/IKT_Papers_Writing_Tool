# Report JSON schema

`report` renders one JSON file through `templates/<type>.md`. Sections you leave out are rendered as "Not provided (missing information)", so omissions stay visible. Complete, real examples: `examples/nlp-graph-theory/*.json`.

## Contents

- Top level
- Citations and evidence levels
- `papers`
- `opportunities` (opportunity_report)
- `reproduction_candidates` (reproducibility_report)
- `datasets`
- `sections` and `proposal`
- Schema version 3: evidence ledger and question types
- What the validator enforces

## Top level

```json
{
  "type": "opportunity_report",
  "title": "...",
  "date": "2026-10-13",
  "constraints": {"field": "...", "hardware": "...", "time_budget_weeks": 8, "defaults_used": ["hardware", "time_budget_weeks"]},
  "search_log": {
    "sources_ok": ["openalex", "arxiv"],
    "sources_failed": [{"source": "semantic_scholar", "reason": "rate_limited"}],
    "strategies": ["keyword", "surveys"], "queries": ["..."], "date_range": "2018 onwards",
    "n_retrieved": 1113, "n_after_dedup": 397, "date": "2026-10-13", "notes": ["..."]
  },
  "papers": [], "sections": {}, "opportunities": [], "reproduction_candidates": [], "datasets": [],
  "proposal": {}, "ranking": {}, "limitations": ["..."]
}
```

`type` is one of `literature_review`, `opportunity_report`, `reproducibility_report`, `research_proposal`. Copy `search_log` values from the `search` output (`sources_status`, `n_retrieved`, `n_after_dedup`, `queries`). `ranking` is the output of `score`; pass it with `report --ranking ranking.json` rather than pasting it.

## Citations and evidence levels

- Cite inside any text with `[@key]` or `[@key1; @key2]`. Markdown gets linked author-year labels; LaTeX gets `\cite{}`.
- Any list item or text field may be a plain string, or a claim object rendered with its tag:

```json
{"text": "The repository has no dependency file", "level": "verified", "sources": ["yao2019"]}
```

`level`: `verified` (checked against a cited source or API response), `estimate` (reasoned from evidence), `speculative` (a suggestion). A `verified` claim may not cite a paper whose `read_level` is `title_only` or `not_accessible`.

## papers

```json
{"key": "galke2022", "title": "...", "authors": ["Lukas Galke", "Ansgar Scherp"], "year": 2022, "date": "2022-01-01",
 "venue": "...", "doi": "10.18653/v1/2022.acl-long.279", "arxiv_id": "2109.03777", "pmid": null, "url": null,
 "method": "...", "datasets": "...", "findings": "...", "limitations": null, "role": "closest"}
```

Copy bibliographic fields from command output (`paper --out`, `search --out`). `key` matches `[A-Za-z0-9_:-]+`. Add `"read_level"`: `full_text` (you read the body, e.g. via `fulltext`), `abstract`, `title_only` or `not_accessible`. At least one of `doi`, `arxiv_id`, `pmid`, `url` is required. `verify-refs` adds a `verification` object; do not write it by hand. Leave `method`, `datasets`, `findings`, `limitations` null when the source does not say.

## opportunities

```json
{
  "title": "...",
  "category": "underexplored_setting",
  "mode": "extension",
  "status": "kept",
  "revision_note": "required when status is revised or rejected: what evidence changed the idea",
  "research_question": "...",
  "motivation": "... [@key]",
  "supporting_papers": ["key1", "key2"],
  "closest_existing_work": [{"key": "key3", "how_it_differs": "...", "read_level": "full_text",
                             "overlap": "partial"}],
  "gap_evidence": [{"text": "...", "level": "verified", "sources": ["key1"]}],
  "contribution": "...",
  "novelty": {
    "confidence": "low",
    "uncertainty": "what the search could have missed",
    "signal": "close_prior_work_found",
    "ceiling": "low",
    "challenge_searches": ["query 1", "query 2"]
  },
  "feasibility": [{"text": "...", "level": "estimate"}],
  "methodological_risks": [
    {"type": "train_test_overlap", "status": "found",
     "evidence": {"text": "entity vote 86% vs 49% majority", "level": "verified"},
     "mitigation": "evaluate with seen users masked"},
    {"type": "weak_baseline", "status": "checked_ok", "evidence": "same-feature MLP included"},
    {"type": "model_selection_on_test", "status": "not_checked"}
  ],
  "decision": {
    "verdict": "conditional_go",
    "rationale": "...",
    "conditions": ["what must be checked, and the result that would flip the verdict"],
    "unresolved_risks": ["..."]
  }
}
```

`overlap` per closest work: `same_experiment`, `same_question_different_design`, `partial`, `different`, `unknown`. `ceiling` is `max_supported_novelty_confidence` from the `challenge` output.

Risk `type`:
- **leakage group:** `train_test_overlap`, `temporal_leakage`, `duplicate_items`, `pretraining_contamination`, `label_leakage`;
- **baselines group:** `weak_baseline`;
- **evaluation group:** `protocol_mismatch`, `metric_definition`, `model_selection_on_test`, `insufficient_runs`;
- **other:** `confound`, `distribution_shift`, `other`.

Risk `status`: `found`, `checked_ok`, `not_checked`, `not_applicable`.

`decision.verdict`: `go`, `conditional_go`, `no_go`. See `references/adversarial-verification.md` for when each is justified.

`category`: `open_question`, `underexplored_setting`, `reported_limitation`, `unresolved_contradiction`, `unverified_novelty_hypothesis`, `well_studied`. `mode`: `original`, `reproduction`, `replication`, `extension`. `status`: `kept`, `revised`, `rejected`. `novelty.confidence`: `very_low`, `low`, `medium`. Copy `signal` and `challenge_searches` from the `challenge` output.

## reproduction_candidates

```json
{
  "paper": "galke2022",
  "mode": "reproduction",
  "result_status": "assessed_only",
  "executed": false,
  "code": "https://github.com/... (licence MIT, last push 2026-04-21)",
  "checklist": {"code": {"label": "Implementation available", "status": "found", "evidence": ["https://..."], "note": null}},
  "value": "...", "hardware": [], "missing": [], "risks": [], "suggested_experiments": [],
  "execution_evidence": []
}
```

Take `checklist` from the `repro` output and update items after manual review. `result_status`: `not_assessed`, `assessed_only`, `reproduced`, `partially_reproduced`, `failed_to_reproduce`. The last three require `executed: true` and non-empty `execution_evidence`.

## datasets

```json
{"name": "...", "url": "https://huggingface.co/datasets/...", "purpose": "...", "size": "31088 rows", "format": "csv",
 "license": "afl-3.0", "access": "open", "preprocessing": "...", "suitability": "...", "verified": true}
```

Set `verified: true` only for datasets that `dataset-verify` confirmed. Null fields render as "not reported".

## sections and proposal

Free-text or list fields looked up by the template placeholders.

| Report type | Keys under `sections` |
| --- | --- |
| `literature_review` | `synthesis`, `well_explored`, `open_questions` |
| `opportunity_report` | `summary`, `well_explored`, `recommendation` |
| `reproducibility_report` | `summary`, `recommendation` |

For `research_proposal`, put these under `proposal`: `problem_statement`, `background`, `research_question`, `hypothesis`, `falsification`, `dataset`, `project_type`, `methodology`, `variables`, `confounds`, `baselines`, `metrics`, `procedure`, `statistics`, `feasibility`, `contribution`, `risks`.

## Schema version 3: evidence ledger and question types

New reports set `"schema_version": 3`. The literature map comes first, as an evidence ledger; every question is derived from its entries and typed:

```json
"schema_version": 3,
"evidence_ledger": [
  {"id": "L1", "type": "methodological_weakness", "level": "verified", "sources": ["dai2021"],
   "text": "The official code selects the best epoch on the test set"},
  {"id": "L2", "type": "disagreement", "level": "verified", "sources": ["dai2021", "li2024"],
   "text": "One study finds tree heads add nothing on RoBERTa; later papers report gains"}
],
"opportunities": [{
  "question_type": "replication",
  "derived_from": ["L1", "L2"],
  "...": "the fields described above"
}]
```

- **Ledger `type`:** `stated_limitation`, `methodological_weakness`, `disagreement`, `missing_control`, `negative_result`, `reproducibility_gap`, `benchmark_validity_concern`.
- **Ledger `sources`:** each entry needs at least one source paper with `read_level` `full_text` or `abstract`.
- **`question_type`:** one of `novel`, `extension`, `replication`, `benchmark_validity`, `answered` (see `references/gap-discovery.md`, step 3).
- **Type and mode must agree:**
  - `novel` needs mode `original`;
  - `extension` needs mode `extension`;
  - `replication` needs mode `reproduction` or `replication`;
  - `answered` must be rejected with verdict `no_go`.

The report renders the ledger as an "Evidence map" section, and shows each question's type and the ledger entries it derives from. Reports without `schema_version` 3 still render. Missing types or derivations then produce warnings, not errors.

## What the validator enforces

Errors (nothing is written unless `--force`, which adds a draft banner):

- a paper without DOI, arXiv ID, PMID or URL; a duplicate or malformed key; a `[@key]` or key reference that matches no paper
- a reference whose verification is `title_mismatch`, `unresolved` or `no_identifier`
- an opportunity with any of these problems:
  - an invalid category or no research question;
  - novelty confidence outside the allowed scale;
  - no `uncertainty`, no `challenge_searches` or no `closest_existing_work`;
  - no `decision`, or (unless rejected) no `methodological_risks`.
- novelty confidence above `novelty.ceiling`; `medium` without at least one closest work read in full and none unread
- an opportunity whose closest work has `overlap: same_experiment` kept as `original` or `extension`
- a `go` verdict when:
  - no closest work was read in full, or any closest work is unread or `title_only`;
  - any risk group (leakage, baselines, evaluation) has no checked entry;
  - a `found` risk has no mitigation.
- `conditional_go` without both `conditions` and `unresolved_risks`; a rejected opportunity whose verdict is not `no_go`
- a claim tagged `verified` that cites a paper with `read_level` `title_only` or `not_accessible`
- schema 3: an opportunity without `question_type` or (unless rejected) `derived_from`; a `derived_from` ID not in the ledger; a ledger entry with an unknown type or no source read at abstract level or better; an empty ledger
- a `novel` question whose closest work has `overlap` `same_experiment` or `same_question_different_design`; an `answered` question that is not rejected with `no_go`; a question type that contradicts the mode
- a `well_studied` topic kept as an opportunity; a revised or rejected opportunity without `revision_note`
- a reproduction candidate marked as reproduced, partially reproduced or failed without execution evidence
- a dataset without a URL

Warnings: references not yet verified or only weakly verified (`identifier_resolves`, `url_reachable`, `unchecked`); datasets not verified. Weakly verified references are flagged in the reference list.

```
python "<skill-dir>/scripts/sra.py" verify-refs --input report.json
python "<skill-dir>/scripts/sra.py" report --input report.json --ranking ranking.json --out-dir research-reports --format md,latex
```

LaTeX output is `<name>.tex` plus `references.bib`; compile with `pdflatex`, `bibtex`, `pdflatex`, `pdflatex`.
