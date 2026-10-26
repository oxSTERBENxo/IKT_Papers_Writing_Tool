# Human-in-the-loop foundation: research decision checkpoints

**Date:** 2026-10-22 · **Builds on:** roadmap item C1 ([`2026-10-20-roadmap.md`](2026-10-20-roadmap.md)) · **Status: implemented, awaiting your review. The paper infrastructure phase (C8) has not been started.**

## 1. Audit: what existed before this work

| Area | Before | Gap |
| --- | --- | --- |
| Project state | None. Reports were standalone JSON/Markdown files; working files went to `work/` | No record of where a project stands; a new session had to reconstruct it from chat |
| Decisions | Each question in a report gets a `go / conditional_go / no_go` decision. That is the toolkit's judgement of the evidence | Nothing recorded the **user's** decision: which question they chose, which methodology they accepted |
| Approval | One rule in `SKILL.md`: ask before downloads over 1 GB, training or paid compute | Not enforced, not recorded, no notion of approving a specific version |
| Change tracking | None | An edited plan after agreement went unnoticed |
| Resume | None | Roadmap principle 4 ("Claude should run `sra project status` and know where the project stands") unimplemented |

Baseline before the change: 207 offline tests, all passing (13 live tests skipped).

## 2. What was built

All inside the existing skill; no separate app, no new dependencies (standard library only).

| File | Change |
| --- | --- |
| `scripts/sra/checkpoints.py` | **New.** Project file, gates, versions, decisions, hash-based invalidation, next-step logic (~450 lines) |
| `scripts/sra/cli.py` | New commands `project` and `checkpoint`; new `report --project` option. Existing commands unchanged without the new flags |
| `references/checkpoints.md` | **New.** Protocol for Claude: when to start a project, what each gate covers, presentation format, mapping replies to commands, resuming |
| `SKILL.md` | New section "Projects and human decision checkpoints"; description triggers on "continue / approve my project"; gate hooks in workflows A–C, the report step and the limits section |
| `README.md` (skill) | Usage, commands, layout and test results |
| `tests/test_checkpoints.py` | **New.** 18 tests |

No existing research artefact was changed. That covers `examples/`, `research-reports/`, the papers and the Obsidian notes.

### The model

- **One file per project:** `research-projects/<slug>/project.json`.
- **Five gates in a fixed order:** `scope → question → methodology → execution → results`. A project can use a subset.
- **Proposals:** each proposal is a version with:
  - a summary;
  - decision items;
  - open risks;
  - a recommendation;
  - attached files, with their SHA-256 hashes.

  The content hash identifies the version.
- **Decisions:** `approve`, `reject` or `revise`. Each records the user's own words (`--said`, required), who decided and when.
- **Approval rules:** an approval names the version the user saw (`--version`, required). It is refused when:
  - an earlier gate is not approved;
  - the version is not the current one;
  - an attached file changed since the proposal.
- **When an approval stops counting.** State is computed from the file on every call, so edits made outside the toolkit are caught. An approval stops counting when:
  - a new version of the gate is proposed;
  - an attached file is edited or deleted (restoring the exact approved content restores the approval);
  - an earlier gate is re-proposed, rejected or sent back for revision. Later gates then become `stale` until the user re-approves them or a new version is proposed.
- **Enforcement points:**
  - `checkpoint require <gates>` exits 3 (`BLOCKED`).
  - `report --project` refuses discovery and reproducibility reports without `scope`, and research proposals without `scope` and `question`.
  - `SKILL.md` ties the existing download/training rule to `require methodology execution`.
- **Resume:** run `project list`, then `project status` (states, reasons and the next step), then `checkpoint show` (the full proposal and its history, for re-presenting it).

### Natural-language mapping (from `references/checkpoints.md`)

| You say | Claude runs |
| --- | --- |
| "yes", "approved", "go ahead" | `checkpoint approve <gate> --version N --said "…"` |
| "no", "drop it" | `checkpoint reject <gate> --said "…" --reason "…"` |
| "change X", "yes but use 10 seeds" | `checkpoint revise …`, makes the change, proposes the next version |
| a question or doubt | nothing; answers and asks again. Not an approval |
| "continue my project", "where was I?" | `project list`, `project status`, re-presents what is pending |

After proposing, Claude shows the decision and **stops the turn**.

## 3. Tests

`tests/test_checkpoints.py`: 18 tests, all passing on Python 3.14, 3.11 and 3.10. The full offline suite: 225 tests, all passing (13 live skipped).

- **Approval enforcement (9 tests):**
  - a proposal is not an approval;
  - approval needs `--said` and the version the user saw;
  - gates go in order, including when an earlier gate is reopened;
  - rejection and revision block until a new version is approved;
  - identical re-proposals are refused;
  - a file edited between proposal and approval cannot be approved;
  - `report --project` refuses a research proposal until `question` is approved.
- **Invalidation after methodology changes (5 tests):**
  - a new methodology version makes `execution` stale. It stays stale even after the new methodology is approved, until execution is re-approved;
  - a silently edited `ANALYSIS_PLAN.md` makes methodology and execution stale, and the old version cannot be re-approved;
  - a deleted plan file invalidates;
  - reopening the question makes all three later gates stale;
  - rejecting an approved gate revokes it.
- **Resume in a new session (4 tests):** every step runs as a separate Python process, so only `project.json` carries state. A later "session":
  - finds the project with `project list`;
  - sees `question AWAITING REVIEW v1` and the next step in `status`;
  - re-reads the full proposal, including its open risk, with `show`;
  - is blocked from methodology;
  - then records the reply.

  The tests also check the env/working-folder lookup, a clean state file and the full history.

**Mutation check.** The tests can fail: four deliberately broken versions of the rules were each caught by at least two tests. The broken versions were:
- stale counted as approved;
- the pre-approval file check removed;
- `--said` not required;
- post-approval file hashes ignored.

## 4. Demonstration: a complete guided workflow

**How it was run.** In a scratch workspace, the research content was copied from `examples/nlp-graph-theory/` (its opportunity report and research proposal), so no searches were rerun and the originals are untouched. The reviewer's replies were scripted, and they are recorded as `--by demo-reviewer`, so the log never presents them as your decisions. No experiments were run.

| Step | What happened |
| --- | --- |
| Start | `project init`; `require scope` → **BLOCKED** before any literature search |
| scope v1 | proposed with the defaults flagged as a risk → approved ("Yes, those constraints are right.") |
| Discovery | opportunity report allowed; research proposal **BLOCKED** (question not started) |
| question v1 | low-resource-language question → **rejected** ("I don't want to depend on low-resource datasets…") |
| question v2 | BoW MLP vs post-2022 graph models, with the unread Abdalla et al. 2023 as an open risk → approved |
| Design | research proposal now validates for the project; `ANALYSIS_PLAN.md` written |
| methodology v1 | 5 seeds, accuracy → **revision requested** ("Use 10 seeds, and report macro-F1…") |
| methodology v2 | plan file updated; addresses the request → approved |
| execution v1 | download plus 150 runs, about 10–20 GPU h → approved; `require methodology execution` → OK |
| **Methodology change** | plan edited to exclude transductive models. Status: methodology **STALE** (file changed) and execution **STALE**; `require` → BLOCKED; re-approving v2 → refused |
| methodology v3 | inductive only → approved. Execution is still stale ("methodology changed since this approval") until re-approved ("The run plan is still fine.") |
| **Session 2** | fresh processes: `project list` → 4/5 gates; `status` → next step is the results gate; `require results` → BLOCKED (nothing has been run) |

Known limits:
- A silent file edit is detected and shown by `status`, but it is not written to the event log, because `status` does not write.
- `--said` is typed by Claude. The record is only as truthful as the instruction never to approve for the user, which is stated in `SKILL.md` and `references/checkpoints.md`.
- The example's opportunity report predates schema 3, so it prints validator warnings (missing `question_type`, `derived_from`). These are unrelated to this work; it still validates.

### Full transcript

```
=== SESSION 1 - user: 'I'm interested in NLP and graph theory; I want a thesis project I can finish.' ===

$ sra project init --name BoW vs text graphs --question I'm interested in NLP and graph theory. What could I work on for my thesis?
Created <demo>\research-projects\bow-vs-text-graphs\project.json
Gates: scope -> question -> methodology -> execution -> results
Next: Prepare the 'scope' proposal (Field, constraints (experience, hardware, time), research mode and the defaults assumed.) and run `checkpoint propose scope`; then show it to the user and wait for their reply.
[exit 0]

=== Claude checks the gate before any literature search ===

$ sra checkpoint require scope --project research-projects/bow-vs-text-graphs
BLOCKED. Do not continue until the user has decided:
  - 'scope' is not started
Next: Prepare the 'scope' proposal (Field, constraints (experience, hardware, time), research mode and the defaults assumed.) and run `checkpoint propose scope`; then show it to the user and wait for their reply.
[exit 3]

=== Gate 1: scope ===

$ sra checkpoint propose scope --project research-projects/bow-vs-text-graphs --summary Find a thesis-sized project at the intersection of NLP and graph neural networks. --item Field: GNNs for text classification --item Experience: undergraduate, comfortable with Python (default) --item Hardware: one consumer GPU with 8 GB VRAM (default) --item Time: 8 weeks; mode: any (reproduction, replication, extension or original) --risk All constraints except the field are defaults; correct any that are wrong --recommendation Approve, or tell me the constraints that differ
Proposed 'scope' v1 (7fceb4ddba). It is awaiting the user's review.

Show this to the user, ask them to approve, reject or say what to change, and stop until they reply.

Checkpoint 'scope' v1 (7fceb4ddba), proposed 2026-10-22T12:55:03+00:00
State: awaiting review

Find a thesis-sized project at the intersection of NLP and graph neural networks.

- Field: GNNs for text classification
- Experience: undergraduate, comfortable with Python (default)
- Hardware: one consumer GPU with 8 GB VRAM (default)
- Time: 8 weeks; mode: any (reproduction, replication, extension or original)

Open risks and caveats:
- All constraints except the field are defaults; correct any that are wrong

Recommendation: Approve, or tell me the constraints that differ
[exit 0]

>>> REVIEWER (scripted): Yes, those constraints are right.

$ sra checkpoint approve scope --project research-projects/bow-vs-text-graphs --version 1 --by demo-reviewer --said Yes, those constraints are right.
Approved 'scope' v1 on the user's words: "Yes, those constraints are right."
Next: Prepare the 'question' proposal (The research question to pursue, its type, its go / conditional-go decision and the closest work.) and run `checkpoint propose question`; then show it to the user and wait for their reply.
[exit 0]

$ sra checkpoint require scope --project research-projects/bow-vs-text-graphs
OK: scope approved and current.
[exit 0]

=== Research step: map, challenge, deep pass, score (outputs reused from the worked example) ===

$ sra report --input research-projects/bow-vs-text-graphs/reports/opportunity_report.json --project research-projects/bow-vs-text-graphs --check
warning: opportunity 'Does a bag-of-words wide MLP still match text-graph models published after 2022?': question_type missing (one of ['answered', 'benchmark_validity', 'extension', 'novel', 'replication'])
warning: opportunity 'Does a bag-of-words wide MLP still match text-graph models published after 2022?': derived_from is empty; trace the question to evidence-ledger entries (a limitation, weakness, disagreement or missing control)
warning: opportunity 'How sensitive is TextGCN to the random seed and to the co-occurrence window used to build its graph?': question_type missing (one of ['answered', 'benchmark_validity', 'extension', 'novel', 'replication'])
warning: opportunity 'How sensitive is TextGCN to the random seed and to the co-occurrence window used to build its graph?': derived_from is empty; trace the question to evidence-ledger entries (a limitation, weakness, disagreement or missing control)
warning: opportunity 'Do text-graph classifiers beat a bag-of-words MLP on low-resource languages?': question_type missing (one of ['answered', 'benchmark_validity', 'extension', 'novel', 'replication'])
warning: opportunity 'Do text-graph classifiers beat a bag-of-words MLP on low-resource languages?': derived_from is empty; trace the question to evidence-ledger entries (a limitation, weakness, disagreement or missing control)
warning: opportunity 'Is a text graph necessary for text classification at all?': question_type missing (one of ['answered', 'benchmark_validity', 'extension', 'novel', 'replication'])
Validation passed.
[exit 0]
(opportunity report validates and is allowed: scope is approved)

=== A research proposal cannot be rendered yet ===

$ sra report --input research-projects/bow-vs-text-graphs/reports/research_proposal.json --project research-projects/bow-vs-text-graphs --check
BLOCKED by project checkpoints: a research_proposal for this project needs the user's approval first.
  - 'question' is not started
Next: Prepare the 'question' proposal (The research question to pursue, its type, its go / conditional-go decision and the closest work.) and run `checkpoint propose question`; then show it to the user and wait for their reply.
[exit 3]

=== Gate 2: question (v1) ===

$ sra checkpoint propose question --project research-projects/bow-vs-text-graphs --summary Pursue: Do text-graph classifiers beat a bag-of-words MLP on low-resource languages? --item Type: extension; decision: conditional_go --risk Needs low-resource benchmark data with comparable splits --recommendation Interesting but riskier than the replication question --artifact research-projects/bow-vs-text-graphs/reports/opportunity_report.md --artifact research-projects/bow-vs-text-graphs/reports/opportunity_report.json
Proposed 'question' v1 (ab46c04e81). It is awaiting the user's review.

Show this to the user, ask them to approve, reject or say what to change, and stop until they reply.

Checkpoint 'question' v1 (ab46c04e81), proposed 2026-10-22T12:55:05+00:00
State: awaiting review

Pursue: Do text-graph classifiers beat a bag-of-words MLP on low-resource languages?

- Type: extension; decision: conditional_go

Open risks and caveats:
- Needs low-resource benchmark data with comparable splits

Recommendation: Interesting but riskier than the replication question

Attached files:
- reports/opportunity_report.md (c195a2fa58)
- reports/opportunity_report.json (7eca49afe6)
[exit 0]

>>> REVIEWER (scripted): No - I don't want to depend on low-resource datasets. Take the replication question.

$ sra checkpoint reject question --project research-projects/bow-vs-text-graphs --by demo-reviewer --said No - I don't want to depend on low-resource datasets. Take the replication question. --reason avoid low-resource data dependency
Rejected 'question' v1: "avoid low-resource data dependency"
Next: 'question' v1 was rejected ("avoid low-resource data dependency"). Discuss an alternative with the user and propose a new version.
[exit 0]

=== Gate 2: question (v2) ===

$ sra checkpoint propose question --project research-projects/bow-vs-text-graphs --addresses rejection of v1: avoid low-resource data --summary Pursue: Does a bag-of-words wide MLP still match text-graph models published after 2022? --item Type: replication of Galke & Scherp 2022 with more seeds, then extension to one post-2022 graph model --item Decision: conditional_go --risk Abdalla et al. 2023 may already contain this comparison; not read in full, so novelty confidence is low --risk Fallback if it does: report the replication stage alone --recommendation Approve: highest-ranked feasible question, and the replication has value even if novelty fails --artifact research-projects/bow-vs-text-graphs/reports/opportunity_report.md --artifact research-projects/bow-vs-text-graphs/reports/opportunity_report.json
Proposed 'question' v2 (c8983fe221). It is awaiting the user's review.

Show this to the user, ask them to approve, reject or say what to change, and stop until they reply.

Checkpoint 'question' v2 (c8983fe221), proposed 2026-10-22T12:55:05+00:00
State: awaiting review

Pursue: Does a bag-of-words wide MLP still match text-graph models published after 2022?

Addresses: rejection of v1: avoid low-resource data

- Type: replication of Galke & Scherp 2022 with more seeds, then extension to one post-2022 graph model
- Decision: conditional_go

Open risks and caveats:
- Abdalla et al. 2023 may already contain this comparison; not read in full, so novelty confidence is low
- Fallback if it does: report the replication stage alone

Recommendation: Approve: highest-ranked feasible question, and the replication has value even if novelty fails

Attached files:
- reports/opportunity_report.md (c195a2fa58)
- reports/opportunity_report.json (7eca49afe6)

Decisions:
- v1 rejected 2026-10-22T12:55:05+00:00 by demo-reviewer: "No - I don't want to depend on low-resource datasets. Take the replication question." (avoid low-resource data dependency)
[exit 0]

>>> REVIEWER (scripted): Yes, go with that one.

$ sra checkpoint approve question --project research-projects/bow-vs-text-graphs --version 2 --by demo-reviewer --said Yes, go with that one.
Approved 'question' v2 on the user's words: "Yes, go with that one."
Next: Prepare the 'methodology' proposal (Hypothesis, falsification rule, datasets, splits, baselines, metrics, seeds and statistics.) and run `checkpoint propose methodology`; then show it to the user and wait for their reply.
[exit 0]

=== Design step: the proposal may now be rendered for this project ===

$ sra report --input research-projects/bow-vs-text-graphs/reports/research_proposal.json --project research-projects/bow-vs-text-graphs --check
Validation passed.
[exit 0]

=== Gate 3: methodology (v1) ===

$ sra checkpoint propose methodology --project research-projects/bow-vs-text-graphs --summary Replicate the BoW MLP vs graph comparison under one protocol, then add TokenGraph. --item H1 and falsification rule as in ANALYSIS_PLAN.md --item Baselines: TF-IDF logistic regression and the BoW MLP; equal tuning budget --item 5 seeds; test accuracy --risk Transductive graph models see unlabelled test documents during training --recommendation Approve --artifact research-projects/bow-vs-text-graphs/ANALYSIS_PLAN.md --artifact research-projects/bow-vs-text-graphs/reports/research_proposal.md
Proposed 'methodology' v1 (fce77b349f). It is awaiting the user's review.

Show this to the user, ask them to approve, reject or say what to change, and stop until they reply.

Checkpoint 'methodology' v1 (fce77b349f), proposed 2026-10-22T12:55:06+00:00
State: awaiting review

Replicate the BoW MLP vs graph comparison under one protocol, then add TokenGraph.

- H1 and falsification rule as in ANALYSIS_PLAN.md
- Baselines: TF-IDF logistic regression and the BoW MLP; equal tuning budget
- 5 seeds; test accuracy

Open risks and caveats:
- Transductive graph models see unlabelled test documents during training

Recommendation: Approve

Attached files:
- ANALYSIS_PLAN.md (a445102e2a)
- reports/research_proposal.md (bb900c7d0a)
[exit 0]

>>> REVIEWER (scripted): Use 10 seeds, and report macro-F1 as well as accuracy.

$ sra checkpoint revise methodology --project research-projects/bow-vs-text-graphs --by demo-reviewer --said Use 10 seeds, and report macro-F1 as well as accuracy. --request 10 seeds; add macro-F1
Revision of 'methodology' v1 requested: "10 seeds; add macro-F1"
Next: Revise 'methodology' as the user asked ("10 seeds; add macro-F1"), then propose v2 with --addresses.
[exit 0]

$ sra project status --project research-projects/bow-vs-text-graphs
Project: BoW vs text graphs  (<demo>\research-projects\bow-vs-text-graphs\project.json)
Question: I'm interested in NLP and graph theory. What could I work on for my thesis?
Last updated: 2026-10-22T12:55:06+00:00

  scope        APPROVED            v1 7fceb4ddba   approved 2026-10-22 by demo-reviewer
  question     APPROVED            v2 c8983fe221   approved 2026-10-22 by demo-reviewer
  methodology  REVISION REQUESTED  v1 fce77b349f   revision requested 2026-10-22 by demo-reviewer
  execution    NOT STARTED         -               
  results      NOT STARTED         -               

Next: Revise 'methodology' as the user asked ("10 seeds; add macro-F1"), then propose v2 with --addresses.
[exit 0]

=== Claude revises the plan and proposes v2 ===

$ sra checkpoint propose methodology --project research-projects/bow-vs-text-graphs --addresses revision request on v1: 10 seeds, macro-F1 --summary Replicate the BoW MLP vs graph comparison under one protocol, then add TokenGraph. --item H1 and falsification rule as in ANALYSIS_PLAN.md --item Baselines: TF-IDF logistic regression and the BoW MLP; equal tuning budget --item 10 seeds; test accuracy (primary) and macro-F1 --risk Transductive graph models see unlabelled test documents during training --recommendation Approve --artifact research-projects/bow-vs-text-graphs/ANALYSIS_PLAN.md --artifact research-projects/bow-vs-text-graphs/reports/research_proposal.md
Proposed 'methodology' v2 (847d596426). It is awaiting the user's review.

Show this to the user, ask them to approve, reject or say what to change, and stop until they reply.

Checkpoint 'methodology' v2 (847d596426), proposed 2026-10-22T12:55:07+00:00
State: awaiting review

Replicate the BoW MLP vs graph comparison under one protocol, then add TokenGraph.

Addresses: revision request on v1: 10 seeds, macro-F1

- H1 and falsification rule as in ANALYSIS_PLAN.md
- Baselines: TF-IDF logistic regression and the BoW MLP; equal tuning budget
- 10 seeds; test accuracy (primary) and macro-F1

Open risks and caveats:
- Transductive graph models see unlabelled test documents during training

Recommendation: Approve

Attached files:
- ANALYSIS_PLAN.md (89c32b5726)
- reports/research_proposal.md (bb900c7d0a)

Decisions:
- v1 revision requested 2026-10-22T12:55:06+00:00 by demo-reviewer: "Use 10 seeds, and report macro-F1 as well as accuracy." (10 seeds; add macro-F1)
[exit 0]

>>> REVIEWER (scripted): Approved.

$ sra checkpoint approve methodology --project research-projects/bow-vs-text-graphs --version 2 --by demo-reviewer --said Approved.
Approved 'methodology' v2 on the user's words: "Approved."
Next: Prepare the 'execution' proposal (What will be downloaded and run, on what hardware, for how long, at what cost.) and run `checkpoint propose execution`; then show it to the user and wait for their reply.
[exit 0]

=== Gate 4: execution ===

$ sra checkpoint require methodology execution --project research-projects/bow-vs-text-graphs
BLOCKED. Do not continue until the user has decided:
  - 'execution' is not started
Next: Prepare the 'execution' proposal (What will be downloaded and run, on what hardware, for how long, at what cost.) and run `checkpoint propose execution`; then show it to the user and wait for their reply.
[exit 3]

$ sra checkpoint propose execution --project research-projects/bow-vs-text-graphs --summary Download the TextGCN benchmark files and run 3 models x 10 seeds x 5 datasets on the 8 GB GPU. --item Download: benchmark folder from the TextGCN repository (size to be confirmed on download; expected well under 1 GB) --item Runs: 150 training runs; estimate 10-20 GPU hours in total --item No paid compute --risk The TokenGraph code was not run yet; it may need fixes --recommendation Approve; I will stop and report if the download exceeds 1 GB
Proposed 'execution' v1 (e0f5f749da). It is awaiting the user's review.

Show this to the user, ask them to approve, reject or say what to change, and stop until they reply.

Checkpoint 'execution' v1 (e0f5f749da), proposed 2026-10-22T12:55:07+00:00
State: awaiting review

Download the TextGCN benchmark files and run 3 models x 10 seeds x 5 datasets on the 8 GB GPU.

- Download: benchmark folder from the TextGCN repository (size to be confirmed on download; expected well under 1 GB)
- Runs: 150 training runs; estimate 10-20 GPU hours in total
- No paid compute

Open risks and caveats:
- The TokenGraph code was not run yet; it may need fixes

Recommendation: Approve; I will stop and report if the download exceeds 1 GB
[exit 0]

>>> REVIEWER (scripted): Go ahead.

$ sra checkpoint approve execution --project research-projects/bow-vs-text-graphs --version 1 --by demo-reviewer --said Go ahead.
Approved 'execution' v1 on the user's words: "Go ahead."
Next: Prepare the 'results' proposal (Measured results, deviations from the plan and their interpretation, before any write-up.) and run `checkpoint propose results`; then show it to the user and wait for their reply.
[exit 0]

$ sra checkpoint require methodology execution --project research-projects/bow-vs-text-graphs
OK: methodology, execution approved and current.
[exit 0]

=== A methodology change after approval: the plan file is edited (transductive models excluded) ===

$ sra project status --project research-projects/bow-vs-text-graphs
Project: BoW vs text graphs  (<demo>\research-projects\bow-vs-text-graphs\project.json)
Question: I'm interested in NLP and graph theory. What could I work on for my thesis?
Last updated: 2026-10-22T12:55:08+00:00

  scope        APPROVED            v1 7fceb4ddba   approved 2026-10-22 by demo-reviewer
  question     APPROVED            v2 c8983fe221   approved 2026-10-22 by demo-reviewer
  methodology  STALE               v2 847d596426   approved 2026-10-22 by demo-reviewer
               - attached file changed after approval: ANALYSIS_PLAN.md
  execution    STALE               v1 e0f5f749da   approved 2026-10-22 by demo-reviewer
               - earlier gate 'methodology' is stale
  results      NOT STARTED         -               

Next: 'methodology' changed after approval; propose it again and ask the user to re-approve.
[exit 0]

$ sra checkpoint require methodology execution --project research-projects/bow-vs-text-graphs
BLOCKED. Do not continue until the user has decided:
  - 'methodology' is stale (attached file changed after approval: ANALYSIS_PLAN.md)
  - 'execution' is stale (earlier gate 'methodology' is stale)
Next: 'methodology' changed after approval; propose it again and ask the user to re-approve.
[exit 3]

=== Re-approving the old version is refused: the file on disk is not what was approved ===

$ sra checkpoint approve methodology --project research-projects/bow-vs-text-graphs --version 2 --by demo-reviewer --said fine
error: attached file(s) changed since this version was proposed: ANALYSIS_PLAN.md. Propose a new version so the user approves what is actually on disk.
[exit 2]

$ sra checkpoint propose methodology --project research-projects/bow-vs-text-graphs --addresses leakage concern: transductive models see test documents --summary As v2, but only inductive models are compared; TokenGraph runs in inductive mode. --item H1 and falsification rule as in ANALYSIS_PLAN.md --item Baselines: TF-IDF logistic regression and the BoW MLP; equal tuning budget --item 10 seeds; test accuracy (primary) and macro-F1 --item Inductive setting only, to remove test-document exposure --recommendation Approve: removes the leakage risk at little cost --artifact research-projects/bow-vs-text-graphs/ANALYSIS_PLAN.md --artifact research-projects/bow-vs-text-graphs/reports/research_proposal.md
Proposed 'methodology' v3 (eeb67b1aa7). It is awaiting the user's review.

Show this to the user, ask them to approve, reject or say what to change, and stop until they reply.

Checkpoint 'methodology' v3 (eeb67b1aa7), proposed 2026-10-22T12:55:09+00:00
State: awaiting review

As v2, but only inductive models are compared; TokenGraph runs in inductive mode.

Addresses: leakage concern: transductive models see test documents

- H1 and falsification rule as in ANALYSIS_PLAN.md
- Baselines: TF-IDF logistic regression and the BoW MLP; equal tuning budget
- 10 seeds; test accuracy (primary) and macro-F1
- Inductive setting only, to remove test-document exposure

Recommendation: Approve: removes the leakage risk at little cost

Attached files:
- ANALYSIS_PLAN.md (331bdb9866)
- reports/research_proposal.md (bb900c7d0a)

Decisions:
- v1 revision requested 2026-10-22T12:55:06+00:00 by demo-reviewer: "Use 10 seeds, and report macro-F1 as well as accuracy." (10 seeds; add macro-F1)
- v2 approved 2026-10-22T12:55:07+00:00 by demo-reviewer: "Approved."
[exit 0]

>>> REVIEWER (scripted): Yes, inductive only is better.

$ sra checkpoint approve methodology --project research-projects/bow-vs-text-graphs --version 3 --by demo-reviewer --said Yes, inductive only is better.
Approved 'methodology' v3 on the user's words: "Yes, inductive only is better."
Next: 'execution' v1 was approved before an earlier gate changed. Ask the user whether it still holds: re-approve v1, or propose a new version.
[exit 0]

$ sra checkpoint require methodology execution --project research-projects/bow-vs-text-graphs
BLOCKED. Do not continue until the user has decided:
  - 'execution' is stale (earlier gate 'methodology' changed since this approval (now v3))
Next: 'execution' v1 was approved before an earlier gate changed. Ask the user whether it still holds: re-approve v1, or propose a new version.
[exit 3]

>>> REVIEWER (scripted): The run plan is still fine.

$ sra checkpoint approve execution --project research-projects/bow-vs-text-graphs --version 1 --by demo-reviewer --said The run plan is still fine.
Approved 'execution' v1 on the user's words: "The run plan is still fine."
Next: Prepare the 'results' proposal (Measured results, deviations from the plan and their interpretation, before any write-up.) and run `checkpoint propose results`; then show it to the user and wait for their reply.
[exit 0]

$ sra checkpoint require methodology execution --project research-projects/bow-vs-text-graphs
OK: methodology, execution approved and current.
[exit 0]

=== SESSION 2 (fresh processes, no memory) - user: 'Where did we leave off?' ===

$ sra project list
BoW vs text graphs: 4/5 gates approved | updated 2026-10-22T12:55 | research-projects\bow-vs-text-graphs
[exit 0]

$ sra project status --project research-projects/bow-vs-text-graphs
Project: BoW vs text graphs  (<demo>\research-projects\bow-vs-text-graphs\project.json)
Question: I'm interested in NLP and graph theory. What could I work on for my thesis?
Last updated: 2026-10-22T12:55:10+00:00

  scope        APPROVED            v1 7fceb4ddba   approved 2026-10-22 by demo-reviewer
  question     APPROVED            v2 c8983fe221   approved 2026-10-22 by demo-reviewer
  methodology  APPROVED            v3 eeb67b1aa7   approved 2026-10-22 by demo-reviewer
  execution    APPROVED            v1 e0f5f749da   approved 2026-10-22 by demo-reviewer
  results      NOT STARTED         -               

Next: Prepare the 'results' proposal (Measured results, deviations from the plan and their interpretation, before any write-up.) and run `checkpoint propose results`; then show it to the user and wait for their reply.
[exit 0]

$ sra checkpoint require results --project research-projects/bow-vs-text-graphs
BLOCKED. Do not continue until the user has decided:
  - 'results' is not started
Next: Prepare the 'results' proposal (Measured results, deviations from the plan and their interpretation, before any write-up.) and run `checkpoint propose results`; then show it to the user and wait for their reply.
[exit 3]

$ sra project log --project research-projects/bow-vs-text-graphs
2026-10-22T12:55:03+00:00  project_created                      BoW vs text graphs
2026-10-22T12:55:03+00:00  proposed            scope v1         Find a thesis-sized project at the intersection of NLP and graph neural networks.
2026-10-22T12:55:04+00:00  approved            scope v1         Yes, those constraints are right.
2026-10-22T12:55:05+00:00  proposed            question v1      Pursue: Do text-graph classifiers beat a bag-of-words MLP on low-resource languages?
2026-10-22T12:55:05+00:00  rejected            question v1      avoid low-resource data dependency
2026-10-22T12:55:05+00:00  proposed            question v2      Pursue: Does a bag-of-words wide MLP still match text-graph models published after 2022?
2026-10-22T12:55:05+00:00  approved            question v2      Yes, go with that one.
2026-10-22T12:55:06+00:00  proposed            methodology v1   Replicate the BoW MLP vs graph comparison under one protocol, then add TokenGraph.
2026-10-22T12:55:06+00:00  revision_requested  methodology v1   10 seeds; add macro-F1
2026-10-22T12:55:07+00:00  proposed            methodology v2   Replicate the BoW MLP vs graph comparison under one protocol, then add TokenGraph.
2026-10-22T12:55:07+00:00  approved            methodology v2   Approved.
2026-10-22T12:55:07+00:00  proposed            execution v1     Download the TextGCN benchmark files and run 3 models x 10 seeds x 5 datasets on the 8 GB GPU.
2026-10-22T12:55:08+00:00  approved            execution v1     Go ahead.
2026-10-22T12:55:09+00:00  proposed            methodology v3   As v2, but only inductive models are compared; TokenGraph runs in inductive mode.
2026-10-22T12:55:09+00:00  approved            methodology v3   Yes, inductive only is better.
2026-10-22T12:55:10+00:00  approved            execution v1     The run plan is still fine.
[exit 0]
```

## 5. Waiting for your review

Before the paper infrastructure phase (C8: manuscript type and build), please confirm or change:

1. **The five gates and their order.** Should `execution` be optional for analysis-only projects?
2. **Whether `report --project` should also gate on `methodology`** before rendering a final research proposal. Currently the proposal itself is what the user reviews at that gate.
3. **Where the paper phase plugs in.** The plan is `require results` before `paper build`, plus a sixth gate, `manuscript`, for the final approval of the paper.
