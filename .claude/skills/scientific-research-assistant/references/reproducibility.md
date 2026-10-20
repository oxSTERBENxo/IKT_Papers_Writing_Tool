# Workflow B: Reproducibility assessment

`SRA` means `python "<skill-dir>/scripts/sra.py"`.

## Terms (use them precisely in every report)

- **Reproduction:** obtaining the reported results with the original method, code and comparable conditions.
- **Replication:** testing whether the findings hold under an independent implementation or changed conditions.
- **Extension:** adding experiments, datasets, conditions or method changes beyond the original study.

Using a third-party port, a different framework or a re-implementation makes the project a replication, even if the numbers match.

## 1. Find candidates (skip if the user named a paper)

```
SRA search --concept "<method terms>" --concept "<task terms>" --strategies keyword,foundational,reproducibility --out work/cands.json
```

Good student candidates tend to have: an open-access paper, a repository linked by the authors, small public datasets, a standard metric, and a claim others rely on. Shortlist five to eight, then assess each.

## 2. Automated pre-assessment

```
SRA repro --id <arXiv ID | DOI | title> --out work/repro_<name>.json
SRA repro --id <...> --repo owner/name        # when you already know the implementation
```

Status values:

| Status | Meaning |
| --- | --- |
| `verified` | a fact from an API (licence, open access, last push) |
| `found` | a file or README phrase is present; completeness unknown |
| `not_found` | the check looked and did not find it; it may still exist elsewhere |
| `manual_review` | cannot be decided from metadata; a person must read |
| `unavailable` | the check could not run (rate limit, outage) |

How code candidates are labelled: `linked_by_paper` (the paper's own metadata links it, likely official), `readme_cites_paper` (official or third-party; check the owner against the author list), `name_match_only` (not confirmed to implement the paper), `paper_list` (a reading list, not an implementation).

Without `GITHUB_TOKEN` the GitHub quota covers about four assessments per hour. Results are cached for a day.

## 3. Manual review (required before recommending anything)

The tool reads READMEs and file names, not code or the paper. For the top candidates, open the paper and repository and fill in:

| Item | Where to look |
| --- | --- |
| Model architecture fully specified | method section, appendix |
| Hyperparameters and training configuration | appendix, config files, argparse defaults in the training script |
| Random seeds, number of runs, variance reported | experiment section, tables (mean ± std?), code (`seed`, `manual_seed`) |
| Hardware and training time | experiment section, appendix, README |
| Dataset versions, splits and preprocessing | experiment section, data scripts |
| Evaluation protocol and metric definition | experiment section; check the metric code |
| Published numbers to compare against | results tables; note which table and row |
| Dependency versions | requirements files; if unpinned, note the repository's last commit date |
| Open issues about failing to reproduce | repository issues (the tool reports the count) |
| Code matches the paper | training script vs paper: split actually used (fixed files or a fresh random split?), model selection (validation or last epoch?), pooling and regularisation, how the metric is computed (e.g. macro-F1 over the whole set, not averaged over batches) |
| Leakage in the evaluation | entities shared between splits, duplicates, future information. Run `leakage` on the split when the data is small. |

`fulltext --id <arXiv ID>` fetches the paper's source and points to the sentences about runs, seeds, splits, baselines and ablations. Read the sections themselves. Text and tables sometimes disagree; record that as a finding.

Record "not stated" explicitly. Missing seeds, missing hyperparameters and unpinned dependencies are findings, not gaps to paper over.

## 4. Verify the data

```
SRA dataset-search --query "<dataset name>"
SRA dataset-verify <hf id | zenodo:<id> | URL> ...
```

Report licence, size, splits and access exactly as returned. A mirror on a hub may differ from the version a paper used (different subset or split); say so unless you have confirmed they match. Gated or restricted access is a blocker until the user has approval.

## 5. Decide what the project is

| Situation | Project type |
| --- | --- |
| Official code runs on the user's hardware with the original data | reproduction |
| Code missing, legacy or too heavy; reimplement or port | replication |
| Reproduction is cheap and the paper leaves an obvious open condition | reproduction followed by an extension |
| Full-scale run exceeds the hardware | scaled-down replication (smaller model or data subset), stated as such; it cannot confirm the original numbers |

Useful controlled experiments to suggest: more random seeds than the paper used; a stronger or better-tuned simple baseline; one dataset the paper did not use; an ablation of the component the paper credits; a different data split.

Reproduction is especially valuable when a result is widely used as a baseline, contradicts other work, was reported from a single run, or has open issues from people who could not match it.

## 6. Rank and report

Score with `references/scoring-rubric.md`, passing the user's hardware and time as constraints. Use report type `reproducibility_report`. Each candidate carries `result_status`:

- `assessed_only`: the default. Nothing was run.
- `reproduced`, `partially_reproduced`, `failed_to_reproduce`: allowed only with `executed: true` and `execution_evidence` (commands, environment, seeds, measured metrics next to the published ones, and the tolerance used to judge a match).

## If the user asks you to run the reproduction

Ask before downloading large data or starting training. Then: record the commit hash and environment, fix and log seeds, run at least three seeds where affordable, keep logs, and report measured against published numbers with the difference. State deviations from the original setup; any deviation in method or data makes it a replication.
