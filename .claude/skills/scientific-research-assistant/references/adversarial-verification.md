# Adversarial verification of shortlisted research questions

Every research question you are about to recommend goes through this procedure. It is part of the standard workflow, not an optional extra. Its purpose is to try to kill the idea before the user spends weeks on it.

`SRA` means `python "<skill-dir>/scripts/sra.py"`.

Prerequisite: the literature map and evidence ledger (`references/gap-discovery.md`, steps 1-3). The shortlisted questions arrive here already typed and traced to ledger entries. This pass tries to show that the typing is wrong (a "novel" question that is really an extension or already answered) or that the design cannot isolate its effect.

## Why this exists

In a real investigation (UPFD fake-news benchmark, October 2026), the workflow ranked an experiment 75/100 and recommended it. The idea was to compare GNNs with a no-graph baseline over many seeds. An audit then found three problems:

- **Same experiment, other words.** A 2025 preprint had run it as "a structure-agnostic MLP on the same node features" with "edge randomization". The keyword challenge returned `no_close_match` twice. The paper was later found by web search, and it cited the benchmark paper.
- **The control already existed.** The benchmark paper's own ablation section (removing all edges) already contained the proposed control. Only its abstract had been read.
- **A confound made the comparison uninterpretable.** Test items shared users with training items. A vote over those users' training labels, with no model, reached about 86% on PolitiFact and 90% on GossipCop on the official split. That is above or close to the published models.

The tool searches by wording. Equivalence of experiments, confounds and leakage are matters of meaning. Python can make the search wider and the bookkeeping strict, but Claude has to read the papers and the data.

## Budget: broad first, deep on the shortlist

1. **Broad pass (all candidates).** Run the map searches from `gap-discovery.md` and one `challenge` per candidate. Drop anything `crowded`.
2. **Deep pass (shortlist of 3 to 5).** Run steps A to F below for each one. This is where time goes. A typical deep pass makes 10 to 30 OpenAlex calls, plus arXiv downloads throttled to one every 3 seconds. Responses and extracted full texts are cached for a day.
3. Never claim exhaustive coverage. Say which sources, queries, seeds and papers were covered.

## A. Write the idea four ways

Before running `challenge`, write down:

| Item | Example (UPFD case) |
| --- | --- |
| Claim: one sentence, with distinguishing terms | "Test whether propagation graphs help fake news detection beyond news features on UPFD" |
| Alternative terminology (older terms, neighbouring fields) | "social context", "user engagement graph", "retweet cascade", "rumour detection" |
| Method-equivalent phrasings | "structure-agnostic baseline", "graph ablation", "edge removal", "MLP vs GNN" |
| Critic phrasing (someone arguing it is pointless or done) | "do GNNs really need the graph", "benchmark does not test structure" |
| Design elements (one per `--design`) | "MLP baseline on the same node features", "randomly rewired edges", "shuffled node features", "multiple random seeds" |
| Seeds: the benchmark, dataset or method papers the idea builds on | the UPFD paper (arXiv 2104.12259) |

```
SRA challenge --claim "<claim>" \
  --query "<wording 1>" --query "<alternative terminology>" --query "<method-equivalent>" --query "<critic>" \
  --design "<design element 1>" --design "<design element 2>" --design "<design element 3>" \
  --seed <benchmark paper arXiv ID or DOI> --expand 3 --out work/challenge_<id>.json
```

What the command adds beyond keyword search:

- **Citation expansion.** It follows citing works and references of the three closest papers (`--expand`) and of each seed. For seeds it also searches their citing works for each query, through OpenAlex's citing-works filter. Papers reached only this way are marked `via citations only`.
- **Design matching.** A paper that mentions two or more design elements is listed under "possibly the same experiment", whatever its title says.
- **A coverage-aware ceiling.** The ceiling is lowered, with the reason printed, when:
  - a source failed;
  - there were fewer than 4 queries, or the queries are near-paraphrases of each other;
  - no design elements were given;
  - the citation graph was not followed;
  - most of the closest records lack abstracts.
- **A must-read list,** with the next command for each paper.

All of this is still lexical. A paper can describe your experiment in words none of your design elements share. So also:

- **Web search** (when available) for the design in plain words, e.g. "MLP matches GNN on PolitiFact GossipCop edge randomization". Add any paper found this way with `paper --id`.
- **The benchmark's leaderboard or papers-with-code page,** and the dataset page's "used in" list.

## B. Read the closest work in full

For the benchmark or method paper itself, and for the two or three closest papers:

```
SRA fulltext --id <arXiv ID> --save-text work/fulltext_<key>.txt --out work/fulltext_<key>.json
```

The command fetches the arXiv LaTeX source (or arXiv HTML) and lists the sections with guessed roles. It then prints the sentences that state:
- runs and seeds;
- split protocol;
- validation-only reporting;
- variance;
- structure-free baselines;
- ablations and controls;
- leakage and overlap;
- code links;
- hardware;
- stated limitations.

These are pointers. Read the experiments, ablation, baselines, limitations and related-work sections yourself. Check the tables: numbers often live only there. Look especially for:

- **an ablation in the original paper that already is your control;**
- **text and tables that disagree** (they did in the closest UPFD paper);
- **validation accuracy reported as the result,** with no held-out test;
- **a related-work section naming the paper you missed.**

For non-arXiv papers, use the open-access PDF if one is listed (WebFetch or a local PDF-to-text tool). Otherwise record the paper as `abstract` or `not_accessible`. Never record `full_text` for a paper you did not read.

Record `read_level` on every paper in the report (`full_text`, `abstract`, `title_only`, `not_accessible`). A claim tagged verified may not cite a paper read at `title_only` or `not_accessible`.

## C. Classify the overlap

For each closest paper, set `overlap` on its `closest_existing_work` entry:

| Overlap | Meaning | Consequence |
| --- | --- | --- |
| `same_experiment` | Same question, same kind of comparison or intervention, same or equivalent data, possibly other words | Reject, or reframe as a reproduction or replication of that paper. The validator refuses `original` or `extension` here. |
| `same_question_different_design` | Answers the question by another method | The new design must add something stated and checkable |
| `partial` | Shares the setting or a component | State the difference precisely |
| `different` | Related only by topic | Fine |
| `unknown` | Not read | Allowed only with `conditional_go` |

The test for `same_experiment`: if you ran your plan and the other paper's plan on the same data, would the main table show the same comparison? If yes, it is the same experiment.

## D. Attack the method: leakage, confounds, weak baselines, protocol

Fill `methodological_risks` with one entry per risk. Status is one of:
- `found`: with evidence, and a `mitigation` if the verdict is go;
- `checked_ok`: you looked and it is fine, and you say how;
- `not_checked`;
- `not_applicable`.

A `go` needs at least one checked entry in each group.

| Group | Types | What to check |
| --- | --- | --- |
| leakage | `train_test_overlap`, `temporal_leakage`, `duplicate_items`, `pretraining_contamination`, `label_leakage` | Shared users, authors, entities or molecules across splits. Future information in features. Duplicate or near-duplicate items. Benchmark text inside an LLM's training data. Features computed with label access. |
| baselines | `weak_baseline` | Is the strongest simple baseline present and tuned? Examples: same-feature MLP, logistic regression, content-only model, majority class, a single-feature rule (graph size, length). |
| evaluation | `protocol_mismatch`, `metric_definition`, `model_selection_on_test`, `insufficient_runs` | Does the code do what the paper says (split, pooling, regularisation)? Is the metric computed as defined (macro-F1 over the whole set, not averaged over batches)? Is model selection on validation, not test? Are there enough runs, with variance reported? |
| other | `confound`, `distribution_shift`, `other` | Graph size, source or time correlating with the label. A control that changes the data distribution. |

Read the code as well as the paper. In the UPFD case the official script:
- ignored the fixed split files;
- had no validation-based model selection;
- used a different pooling and weight decay from the paper;
- averaged macro-F1 over batches.

**Data-level check.** When the data is small enough to fetch (ask before anything over about 1 GB), export one record per item and run:

```
SRA leakage --input work/items.jsonl --entities-field users --text-field text --scalar size --out work/leakage.json
```

The command reports:
- entity overlap between splits;
- a model-free entity vote compared with the majority class;
- exact duplicate texts across splits;
- one-threshold rules on numeric fields;
- whether an entity-disjoint split is feasible (connected components);
- how much masking seen entities would change the test set.

Huge archives can often be read selectively with HTTP range requests, fetching only the split files rather than the whole download. A high vote accuracy means identity carries label information. It does not prove a given model uses it.

## E. Decide

Every shortlisted question gets `decision.verdict`:

| Verdict | Required | Use when |
| --- | --- | --- |
| `go` | Closest work read in full (at least one), none unread. Every risk group checked. Found risks mitigated. No `same_experiment` unless the project is a reproduction or replication. | You would bet the user's weeks on it |
| `conditional_go` | `conditions` (what must be checked, how, and what result would flip it) and `unresolved_risks` | Promising, but something specific is unread or unchecked |
| `no_go` | Rationale; rejected candidates must be `no_go` | Already done, uninterpretable as designed, or infeasible |

Novelty confidence follows the same evidence:
- **`medium`** requires the closest work read in full. It must never exceed the `challenge` ceiling, which you record as `novelty.ceiling`.
- **Lower the confidence** when sources failed, papers went unread, or only abstracts were available.
- **In scoring,** set `novelty_evidence.closest_read` and `novelty_evidence.prior_overlap` on each candidate. Novelty is capped at 2/5 without full-text reading, and at 1/5 for a `same_experiment` framed as original or extension.

## F. Report the four kinds of verification separately

The report's "What was verified" table keeps these apart. Do the same in the conversation.

1. **Source existence:** `verify-refs` confirmed that the record exists and its title matches. It says nothing about what the paper shows.
2. **Claim support:** which claims were checked against which text, and at what read level.
3. **Novelty confidence:** how far the searches support the gap. Never more than medium.
4. **Reproducibility:** whether anything was executed. A repository is not a reproduction.

Passing the validator means the bookkeeping is complete. It does not mean the conclusion is right.
