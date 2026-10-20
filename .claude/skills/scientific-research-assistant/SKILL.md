---
name: scientific-research-assistant
description: Evidence-backed help with scientific research planning for students and researchers. Use whenever the user wants to find a research topic, thesis idea or research gap; asks what is underexplored or already done in a field; wants papers they can reproduce or replicate (with code, data and modest hardware); asks whether a specific paper's experiments are reproducible; wants a simple extension of a published paper; needs datasets, baselines, a methodology, a hypothesis or a research proposal; or wants research ideas compared for feasibility. Runs real literature searches (OpenAlex, arXiv, Crossref, Semantic Scholar, PubMed, Hugging Face, GitHub, Zenodo), follows citation graphs, reads open full texts, tries to disprove novelty claims, checks for train/test leakage and weak baselines, verifies code, datasets and citations, scores feasibility with hard blockers, gives each shortlisted question a go / conditional-go / no-go decision, and writes Markdown, LaTeX and JSON reports. Use it even when the user only says something like "I'm interested in X and Y, what could I work on?" or "is this idea new?".
---

# Scientific Research Assistant

Guide a user from a vague interest to a research project they can actually finish, with every claim traceable to a source. Reproducing, replicating or extending published work is a legitimate outcome and often the best one for a student; a new algorithm is not the default goal.

The toolkit is `scripts/sra.py` inside this skill's directory (shown as the base directory when the skill loads; `${CLAUDE_SKILL_DIR}` in Claude Code). It needs only Python 3.9+ and no packages:

```
python "<skill-dir>/scripts/sra.py" <command> --help
```

Each command prints a compact summary and, with `--out FILE`, saves full JSON. Read the summary; open the JSON only for the abstracts or fields you need. Searches take one to four minutes because arXiv allows one request every three seconds, so give those commands a timeout of at least 300000 ms.

## The rules that make the output trustworthy

These exist because a research plan built on a made-up citation or a false "nobody has done this" wastes months of someone's work.

1. **Cite only what a command retrieved.** Take titles, authors, years, DOIs and URLs from command output. Never write a reference from memory, even a famous one: resolve it with `paper --id` first.
2. **A search that finds nothing proves nothing.** It covered some sources, some wording, and no full texts. Report gaps as hypotheses with a stated confidence (`very_low`, `low` or `medium`; the report validator rejects anything higher) and say what the search could have missed.
3. **Attack every idea before proposing it.** Run `challenge` on each candidate. For the shortlist, run the full adversarial verification in `references/adversarial-verification.md`: alternative and method-equivalent phrasings, design elements, the citation graph of the benchmark paper, full text of the closest work (the original paper's own ablations included), leakage, weak baselines, evaluation flaws. Then keep, revise or reject. Show the rejected ones in the report; they are part of the evidence.
4. **A repository is not a reproduction.** `repro` reports what is present and what is missing. Say "reproduced" only for experiments that were actually run, with the commands and measured numbers.
5. **Verify before describing.** Code, datasets, licences and sizes come from `repro`, `dataset-verify` and the pages themselves. If something was not reported, write "not reported".
6. **Label the kind of claim.** Tag statements as `verified` [V], `estimate` [E] or `speculative` [S].
7. **Say what failed.** If a source was rate-limited or down, name it in the report's search log and limitations.
8. **Prefer the simplest method that answers the question.** See `references/project-design.md`.
9. **Map first, then derive.** Never propose a question before mapping published comparisons, negative results, reproducibility studies and benchmark critiques. Every question must trace to an evidence-ledger entry, and must be typed honestly:
   - **novel;**
   - **extension;**
   - **replication** and **benchmark validity:** judged on replication value, not penalised for lacking novelty;
   - **already answered:** reported as such.
10. **Decide, with the evidence and what is still open.** Each shortlisted question gets `go`, `conditional_go` or `no_go`:
   - **`go`** needs the closest work read in full and leakage, baseline and evaluation risks checked.
   - **`conditional_go`** lists the checks still owed and what would flip the verdict.
   - **`no_go`** covers experiments that are already done, or that cannot isolate the effect they claim to measure.
11. **Keep four kinds of verification apart:**
    - **source existence:** `verify-refs`;
    - **claim support:** which text was read, at what `read_level`;
    - **novelty confidence:** search coverage, never above medium;
    - **reproducibility:** what was executed.

    Passing tests or the validator shows the bookkeeping is complete, not that a conclusion is right.

Summaries drawn from abstracts must be described as such, and lower the novelty confidence. Read the full text (`fulltext --id`, or the open-access PDF) before asserting what a paper's experiments or limitations sections say, and record each paper's `read_level`.

## Start: constraints

Ask only for what is missing and changes the answer, in one short message. The research field or the paper in question is the only thing that must come from the user. Otherwise proceed on these defaults and list them in the report under `constraints.defaults_used`:

| Constraint | Default |
| --- | --- |
| Experience | undergraduate, comfortable with Python |
| Hardware | one consumer GPU with 8 GB VRAM (or a free cloud notebook) |
| Time budget | 8 weeks |
| Language | Python |
| Difficulty | moderate |
| Research mode | any (reproduction, replication, extension or original) |
| Venue | none |

## Choose the workflow

| The user wants | Workflow | Read first |
| --- | --- | --- |
| Topics, gaps, "what is underexplored", "is this idea new" | A. Literature-first discovery | `references/gap-discovery.md` (map, evidence ledger, typed questions), then `references/adversarial-verification.md` for the shortlist |
| Papers to reproduce, "can I reproduce this paper", an extension of a paper | B. Reproducibility | `references/reproducibility.md` |
| A methodology, hypothesis, dataset choice or full proposal | C. Project design | `references/project-design.md` |
| Compare or rank ideas | Scoring step of A or B | `references/scoring-rubric.md` |

Requests often chain: "a topic I can finish in a month" is A, then scoring, then C for the winner. Read each reference file when you reach that step, not all at once. `references/sources.md` covers source choice, API keys and rate limits; read it if a source fails or the field is outside computer science.

## Commands

| Command | Purpose |
| --- | --- |
| `sources` | Which integrations respond and which optional keys are set. Run once at the start. |
| `search` | Multi-source search with deduplication. Takes repeatable `--query`, synonym groups via `--concept`, `--strategies`, `--domain` and `--from-year`; see the example below. |
| `paper --id` | Resolve one paper (arXiv ID, DOI, PMID, URL or exact title); `--abstract` prints the abstract. |
| `related --id` | References, citing works and related works of a paper. |
| `challenge --claim` | Try to disprove that an idea is new. It takes 4 or more varied `--query` phrasings, `--design` elements of the experiment and `--seed` papers. It also follows citations of the closest papers and seeds, flags papers that run the same design under other words, and explains any lowering of its confidence ceiling. |
| `map --query/--concept` | Literature-first landscape before any question is written. It runs comparison, negative-result, critique, reproducibility and design-based queries, plus citation exploration from seeds. It sorts papers into evidence buckets and prints a read-first list, web-search queries and an evidence-ledger template. |
| `retrieval-eval --fixtures` | Measures recall of curated known-relevant papers (`evals/retrieval/`, dev and held-out topics) for the baseline, challenge, landscape and combined configurations. It lists the papers every configuration missed. |
| `fulltext --id` | Fetch the open full text (arXiv LaTeX source or HTML), split it into sections, and point to sentences about runs, seeds, splits, baselines, ablations, leakage and limitations. |
| `leakage --input` | Measure train/test entity overlap, run a model-free entity vote, find exact duplicates and one-feature shortcuts, and check whether an entity-disjoint split is feasible. |
| `repro --id` | Reproducibility pre-assessment: full text, code, licence, dependencies, configs, seeds, hardware, evaluation, maintenance. |
| `dataset-search`, `dataset-verify` | Find datasets; confirm existence, licence, size, splits and access. |
| `score --input` | Rank candidates from per-criterion scores with evidence; blockers cannot be outvoted. |
| `verify-refs --input` | Check that every paper in a report JSON resolves and its title matches. |
| `report --input` | Validate the report JSON and write Markdown, LaTeX (`--format md,latex`) and BibTeX. |
| `obsidian-export --input` | Copy finished reports into an Obsidian vault as linked notes (project notes, paper notes for verified references, a Research Dashboard). Optional; see "Obsidian export" below. |

A typical search. Each `--concept` is a group of synonyms separated by `|`; every combination across groups is searched. Strategies: `keyword`, `recent`, `foundational`, `limitations`, `surveys`, `reproducibility`. Domains: `cs`, `biomed`, `general`.

```
python "<skill-dir>/scripts/sra.py" search \
  --concept "graph neural network|graph convolutional network" \
  --concept "text classification|document classification" \
  --strategies keyword,surveys,foundational,recent,limitations \
  --domain cs --from-year 2018 --out work/search.json
```

## Workflows in brief

**A. Literature-first discovery.** Map before proposing:
1. **Map.** `map` with synonym groups, design elements and seed papers. It collects comparisons, negative results, reproducibility studies, benchmark critiques, limitations and surveys. Also run the web-search queries it prints.
2. **Read and record.** Read the "read first" papers (full text for anything the project may rest on). Write the evidence ledger: limitations, methodological weaknesses, disagreements, missing controls, negative results, reproducibility gaps and benchmark-validity concerns, each citing papers actually read.
3. **Derive questions.** Draft questions only from ledger entries (`derived_from`). Type each as `novel`, `extension`, `replication`, `benchmark_validity` or `answered`.
4. **Challenge.** Run `challenge` on each, with design elements and seeds.

Deep pass on a shortlist of 3 to 5 (`references/adversarial-verification.md`):
1. Re-challenge with alternative terminology, design elements and seeds.
2. Read the closest work in full with `fulltext`.
3. Classify the overlap of each closest paper.
4. Attack leakage, baselines and protocol, using `leakage` on the data where it is small enough.
5. Record a go / conditional-go / no-go decision.

Then check data and code for the survivors, run `score`, and write the report. Details: `references/gap-discovery.md`.

**B. Reproducibility.** Find candidates (or take the user's paper) → `repro` each → `fulltext` and read the paper for the items marked `manual_review`; compare the code with the paper (splits, model selection, metric computation) → `dataset-verify` the data, and `leakage` if the split might leak → decide whether the project is a reproduction, replication or extension → `score` with the user's hardware and time → report. Details: `references/reproducibility.md`.

**C. Project design.** State the problem and a falsifiable hypothesis → pick the simplest valid method and baselines → fix variables, splits, metrics, seeds and the statistical comparison before any run → write the proposal. Details: `references/project-design.md`.

## Producing the report

1. Write a report JSON following `references/report-schema.md`. Types: `literature_review`, `opportunity_report`, `reproducibility_report`, `research_proposal`.
2. `verify-refs --input report.json` (writes verification results into the file).
3. `score --input scoring.json --out ranking.json` if candidates are being compared.
4. `report --input report.json --ranking ranking.json --out-dir research-reports --format md,latex`.
5. Optional: `obsidian-export --input report.json` (or `report ... --obsidian`) if the user keeps notes in Obsidian.

The validator refuses to render when:
- a reference cannot be checked;
- an opportunity lacks a recorded novelty challenge, closest prior work, methodological risks or a decision;
- novelty confidence is above `medium`, above the challenge ceiling, or `medium` without full-text reading of the closest work;
- a `go` is given with unread closest work or unchecked risk groups;
- an idea that a closest paper already performed (`overlap: same_experiment`) is kept as original or extension;
- a verified claim cites a paper read only by title;
- something is marked reproduced without execution evidence. Fix the content; do not reach for `--force`, which only produces a draft with a warning banner. Save outputs in the user's project (default `research-reports/`), then give the user the key findings in the conversation:
- the decision for each shortlisted question, and the top recommendation;
- what was rejected and why;
- what could not be verified or read.

A worked example with all intermediate files is in `examples/nlp-graph-theory/`.

## Obsidian export (optional)

If the user keeps notes in Obsidian, export finished reports as linked Markdown notes. Plain files only: no plugins, no MCP server.

```
python "<skill-dir>/scripts/sra.py" obsidian-export --input research-reports/x/report.json --vault "D:\Obsidian\MyVault" --dry-run
python "<skill-dir>/scripts/sra.py" obsidian-export --input research-reports/x/report.json --vault "D:\Obsidian\MyVault"
```

- **Vault:** `--vault` or `SRA_OBSIDIAN_VAULT`. It is the folder that holds the notes (it contains `.obsidian`), not `Obsidian.exe`. The vaults Obsidian knows about are listed in `%APPDATA%\obsidian\obsidian.json`. **Ask the user before the first write to a real vault**, and show a `--dry-run` first.
- **Folder:** `--folder` or `SRA_OBSIDIAN_FOLDER`, default `Scientific Research`. Inside it: `Research Dashboard.md`, `Projects/` (one note per report) and `Papers/` (one note per reference with verification status `verified`).
- **Content is never invented.** Paper notes copy title, authors, year, links, findings and limitations from the report, attributed to the report and its `read_level`; missing fields read "not reported". Run `verify-refs` first, or references get no paper note.
- **Safe to rerun:**
  - Only the region between `%% sra:begin %%` and `%% sra:end %%`, and the exporter's frontmatter keys, are rewritten. User text, user frontmatter keys and user tags are kept.
  - Notes are found by `sra_id`, so renamed or moved notes are updated, not duplicated. Nothing is deleted.
  - A generated region that the user edited, or whose markers were removed, is skipped with a warning (`--overwrite-managed` forces it).
- **Existing reports** export directly from their JSON; no research is rerun. Every previously exported report is re-read, so cross-links stay complete. Source reports are only read.
- **Automatic export:** `report ... --obsidian`, or set `SRA_OBSIDIAN_AUTO=1` together with `SRA_OBSIDIAN_VAULT` so every `report` run also exports.
- **At a glance:** each exported project note starts with an `[!abstract] At a glance` box, built from the report's own fields:
  - the main question or topic, the type, field and status, and the datasets;
  - the research questions and hypotheses;
  - each question's go / conditional-go / no-go decision;
  - the conclusion.

  No extra input is needed.

### Experiments that were run

`obsidian-export` covers reports only. When a project goes on to run experiments and write a paper, also write a project note by hand in `Projects/` of the same folder. Leave out `sra_*` frontmatter keys, so the exporter never touches it.

Put an `[!abstract] At a glance` box at the top, so the project can be understood in a minute:
- **Main question.**
- **Type:** replication, extension or original.
- **Data:** names, sizes, snapshot dates.
- **Hypotheses table:** hypothesis, test and result, with ✅ supported, ❌ rejected or ⚠️ mixed.
- **Conclusion:** two or three plain sentences.

Below the box:
- what was done, step by step;
- the methods;
- the results with the figures (copy them to `Attachments/<project>/` and embed them);
- deviations from the analysis plan;
- limitations;
- a table of logs and files with their paths;
- a timeline.

For links:
- Link every cited paper as `[[Paper note]]`. Reuse existing paper notes, and create missing ones only from what the paper or report states.
- Add a row for the project under a hand-written section of `Research Dashboard.md`, below `%% sra:end %%`.

As with reports, every number in the note must come from the project's own results files.

## Limits on what to do without asking

Do not download datasets larger than about 1 GB, start model training, or run anything that needs paid compute without the user's explicit go-ahead. Assessing a paper never requires either. Data-level leakage checks usually need only split and index files. Fetch those selectively (HTTP range requests on a zip), and ask before fetching large feature files.
