# Workflow A: Literature-first research discovery

Goal: three to five research questions worth answering, each traced to a specific limitation, weakness, disagreement or missing control in the literature. Each also needs its closest existing work, its question type, and an honest statement of how sure the search makes us.

`SRA` below means `python "<skill-dir>/scripts/sra.py"`.

Why literature-first: twice in a row, an earlier version of this workflow proposed "novel" questions first and searched for prior work afterwards. Both times the exact experiment turned out to exist already, once in the benchmark paper's own ablation section. Mapping what is established before writing any question avoids this. It also makes the questions better, because they grow out of documented weaknesses instead of intuition.

## 1. Map the established literature (before any question)

Write two or three synonym groups using the field's own vocabulary (abbreviations, older terms, neighbouring task names). Also write the experimental design you have in mind as plain-language design elements (e.g. "MLP baseline on the same features", "model selection on a validation set"). Name the benchmark, dataset or method papers the topic builds on as seeds.

```
SRA map --concept "graph neural network|GNN" --concept "fake news detection|misinformation detection" \
        --design "MLP baseline on the same node features" --design "randomly rewired edges" \
        --seed <benchmark paper arXiv ID> --anchor "fake news propagation graph" --out work/map.json
```

`map` runs several retrieval strategies at once:
- **Topic keywords:** `keyword`, `surveys`.
- **Established findings:** `negative` (revisiting, does not improve), `comparisons` (empirical comparison), `critique` (evaluation pitfalls, simple baseline) and `reproducibility`.
- **Design-based queries.**
- **Citation exploration:** citing works of the seeds, searched with short probes, and references and citations of the top papers.

It sorts the results into evidence buckets: negative results, reproducibility studies, benchmark critiques, comparisons, surveys, stated limitations and method proposals. It also prints:
- **A "read first" list,** drawn from the buckets most likely to hide an existing answer.
- **Web-search queries.** Run them with ordinary web search: in past audits, web search found closest papers that every API missed. Add each paper found with `paper --id`.

Buckets are text-pattern matches on titles and abstracts. They tell you what to read, not what a paper shows.

The older strategies remain available through `search --strategies`:

| Strategy | Finds | Use it to |
| --- | --- | --- |
| `surveys` | surveys and reviews | learn the map quickly and see listed open problems |
| `foundational` | most-cited matches | identify the papers everything else builds on |
| `keyword` | best matches | the core of the comparison table |
| `recent` | best matches from the last two years | see where the field is now |
| `limitations` | papers discussing limitations and challenges | find stated weaknesses |
| `reproducibility` | reproduction and replication studies | find contested results |
| `negative` | "revisiting", "does not improve" | find published negative results |
| `comparisons` | empirical comparisons | find head-to-head studies that may already answer your question |
| `critique` | evaluation pitfalls, simple baselines | find critiques of benchmarks and protocols |

Check the source status lines and coverage notes. If a source failed, say so in the report.

## 2. Read and build the evidence ledger

Read the papers in the "read first" list, and the 8 to 15 most relevant overall:
- **Full text** (`fulltext --id`) for anything the project might rest on, and for every negative result, comparison and critique.
- **Abstracts** (`paper --id ... --abstract`) for the rest.

Record each paper's `read_level`. Write "not reported" for anything the source does not say.

Then write the **evidence ledger**: short entries stating what the literature establishes, disputes or leaves open. Each entry cites only papers you have read at abstract level or better:

| Ledger type | Example |
| --- | --- |
| `stated_limitation` | "The authors leave temporal splits to future work" |
| `methodological_weakness` | "Model selection on the test set in the official code" |
| `disagreement` | "Paper A finds syntax adds nothing; papers B and C report gains" |
| `missing_control` | "No structure-free baseline with the same features" |
| `negative_result` | "An MLP on the same features matches the GNNs" |
| `reproducibility_gap` | "Published numbers 1-2 points above re-runs; single-run results" |
| `benchmark_validity_concern` | "Test items share users with training items" |

Two data hazards seen in practice:
- Aggregated records are sometimes attached to the wrong paper. If an abstract does not fit its title, resolve the paper again by arXiv ID or DOI and trust the primary source.
- Preprints and their published versions differ in year and venue. `paper --id` takes these from Crossref when a published DOI exists.

## 3. Derive questions from the ledger, and type them

Every candidate question cites the ledger entries it comes from (`derived_from`). A question that cannot be traced to an entry is a guess. Either find the evidence or drop it.

Give each question exactly one **question type**. This decides how it is judged:

| Question type | Meaning | Judged on |
| --- | --- | --- |
| `novel` | No read paper addresses the question; it rests on a ledger gap | novelty, with all caps; confidence at most low unless closest work was read in full |
| `extension` | An existing experiment run in a new condition, dataset, scale or with an added control | what the new condition adds, stated precisely |
| `replication` | Re-running a published result to see if it holds (reproduction or replication) | replication value: is the result relied on, contested, single-run or protocol-flawed? Not novelty |
| `benchmark_validity` | Testing whether a benchmark or protocol measures what it claims (leakage, shortcuts, test-set selection) | replication value plus the evidence that the concern is real |
| `answered` | A read paper already answers it | rejected (no-go); listed as evidence |

The validator (schema version 3) refuses:
- a `novel` question whose closest work already addresses it;
- an `answered` question that is not rejected;
- a type that contradicts the mode.

Also classify the kind of gap, as before:

| Category | Meaning | Evidence needed |
| --- | --- | --- |
| `reported_limitation` | A cited paper says this is unsolved or untested | the passage and the paper |
| `unresolved_contradiction` | Two cited papers report conflicting findings | both papers and what conflicts |
| `underexplored_setting` | A known method has not been tested in some data, language, scale or condition | closest work and how its setting differs |
| `open_question` | The field itself names this as open (survey, benchmark paper) | the survey statement |
| `unverified_novelty_hypothesis` | You think it is new, with no positive evidence beyond not finding it | challenge results; confidence at most low |
| `well_studied` | Already answered | the paper that answers it; reject or reframe |

The first four rest on positive evidence that a gap exists. The fifth rests only on absence, so it is the weakest and must be labelled as such.

## 4. Try to disprove each candidate

```
SRA challenge --claim "<one sentence stating what would be new, using its distinguishing terms>" \
    --query "<wording 1>" --query "<synonyms>" --query "<how a critic would phrase it>" \
    --query "<method + setting>" --from-year 2019 --out work/challenge_1.json
```

Give at least four differently worded queries. Include alternative terminology, a method-equivalent phrasing and the phrasing of someone arguing the opposite. The command also searches surveys and recent work for each query, and follows citations and references of the three closest papers. For the shortlist, add `--design` (the elements of the experiment) and `--seed` (the benchmark or method paper). Full procedure: `references/adversarial-verification.md`.

Reading the result:

| Signal | Meaning | Action |
| --- | --- | --- |
| `crowded` | many closely worded papers, or a survey on exactly this | reject, or narrow to a specific sub-question and challenge again |
| `close_prior_work_found` | at least one closely worded paper | read it; revise the idea so it differs in a stated, checkable way, or reframe as a replication or extension of that paper |
| `no_close_match_in_this_search` | nothing closely worded was retrieved | keep as a hypothesis; if the tool says the queries probably missed the literature, reword and rerun |

The signal is a wording-overlap heuristic. Always read the listed closest papers yourself, including any marked:
- "NO ABSTRACT";
- "via citations only";
- "possibly the same experiment".

Read in full (`fulltext`) for the shortlist. The printed "highest novelty confidence this search can support" is a ceiling: go lower whenever relevant papers went unread, a source failed, or the closest work is nearer than the wording suggests. Never go higher.

In the worked example, the first literature search missed the one paper that had already answered a candidate question, and the challenge found it. In the UPFD investigation, both keyword challenges missed a paper that ran the same experiment under other words. The benchmark paper's own ablation also already contained the proposed control. Expect both, and budget time for the deep pass.

## 4b. Deep adversarial pass on the shortlist

For the 3 to 5 most promising candidates, run steps A to E of `references/adversarial-verification.md`:
- rewrite the idea four ways;
- read the closest work in full;
- classify overlap (`same_experiment` means reject or reframe);
- attack leakage, baselines and protocol (`leakage` on the data where possible);
- decide go, conditional go or no-go.

Do this before scoring: a score built on abstracts overstates novelty, and the scoring caps enforce that.

## 5. Check feasibility of the survivors

For each kept candidate: `repro` on the paper whose code would be reused, `dataset-search` and `dataset-verify` for the data, then score (`references/scoring-rubric.md`). An idea with no accessible data is blocked however interesting it is.

## 6. Report

Use type `opportunity_report` with `"schema_version": 3` and a top-level `evidence_ledger` (`references/report-schema.md`). Every opportunity needs:
- `question_type` and `derived_from` (ledger entry IDs);
- research question and motivation;
- supporting papers;
- closest existing work, each with how it differs, its `read_level` and its `overlap`;
- evidence for the gap, with evidence levels;
- potential contribution;
- novelty confidence, with its uncertainty, the challenge queries and the challenge `ceiling`;
- feasibility;
- `methodological_risks`;
- a `decision`.

Include rejected and revised candidates with the paper that caused the change.

Phrase conclusions accordingly: "no paper doing X was found in these sources with these queries", not "X has not been done".
