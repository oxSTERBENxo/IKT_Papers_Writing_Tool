# scientific-research-assistant

A Claude Code skill that helps students and researchers find research gaps, pick papers worth reproducing, and design feasible projects, with every claim traced to a retrieved source.

It has two parts: instructions for Claude (`SKILL.md` and `references/`) and a Python toolkit (`scripts/sra.py`) that does the searching, checking, scoring and report rendering.

**New here? Start with [`QUICKSTART.md`](QUICKSTART.md):** what to say to Claude, the commands behind it, and one complete worked example from a new project to the final DOCX and PDF.

## Install

Requirements: Python, standard library only; no third-party packages. Written for 3.9 or newer, tested on 3.11 and 3.14 under Windows 11 (3.9 and 3.10 are untested).

The skill lives in `.claude/skills/scientific-research-assistant/` of this project, so Claude Code picks it up here automatically. To use it elsewhere, copy the folder:

- one project: `<project>/.claude/skills/scientific-research-assistant/`
- all your projects: `~/.claude/skills/scientific-research-assistant/` (Windows: `%USERPROFILE%\.claude\skills\`)

Check the integrations:

```
python .claude/skills/scientific-research-assistant/scripts/sra.py sources
```

### Optional API keys

Everything runs without keys, but two limits bite quickly: OpenAlex allows roughly 100 keyless list requests per day per IP address, and GitHub allows 60 requests per hour. Free keys remove both. Keys are read from environment variables only.

| Variable | Service | Effect |
| --- | --- | --- |
| `OPENALEX_API_KEY` | OpenAlex | lifts the small keyless daily budget (recommended) |
| `GITHUB_TOKEN` | GitHub | 5,000 requests per hour instead of 60 (recommended) |
| `SEMANTIC_SCHOLAR_API_KEY` | Semantic Scholar | search works reliably instead of mostly HTTP 429 |
| `NCBI_API_KEY` | PubMed | 10 requests per second instead of 3 |
| `HF_TOKEN` | Hugging Face | access to gated dataset metadata you are approved for |
| `SRA_CONTACT_EMAIL` | Crossref, OpenAlex, NCBI | polite-pool identification |
| `SRA_CACHE_DIR` | local | cache location; `off` disables caching |
| `SRA_OBSIDIAN_VAULT` | Obsidian | vault folder for `obsidian-export` (the folder with `.obsidian`, not `Obsidian.exe`) |
| `SRA_OBSIDIAN_FOLDER` | Obsidian | research folder inside the vault (default `Scientific Research`) |
| `SRA_OBSIDIAN_AUTO` | Obsidian | `1` makes every `report` run also export to the vault |

## Use

Talk to Claude Code normally; no commands to memorise:

- "I am interested in NLP and graph theory. Find underexplored research opportunities."
- "Find five computer vision papers I can reproduce on a consumer GPU."
- "Can I reproduce the experiments in arXiv 1809.05679?"
- "I want a machine learning research topic I can complete in one month."
- "Find a simple extension to this published paper."
- "Compare these three research ideas and recommend the most feasible."
- "I have a scientific question but don't know which methodology to use."
- "Continue my research project." / "Where did we leave off?" / "Approved, go ahead."

For research that spans several sessions, Claude keeps a project (`research-projects/<name>/project.json`). Each research decision (scope, question, methodology, execution, results, manuscript) is proposed to you and waits for your reply: approve, reject, or say what to change. Changing an approved decision, or editing a file it rests on, makes it and every later decision need your approval again. Analyses run through `project run`, which checks the approvals and records the run. Papers are built with `manuscript` (Markdown to DOCX and PDF): numbers come from `results.json` placeholders, references from verified records, and only the final build needs the approved manuscript. A new session starts from `project status`. Details: `references/checkpoints.md`, `references/manuscript.md`.

Claude asks only for constraints that are missing and matter, and otherwise uses stated defaults (8 weeks, one 8 GB GPU, Python). Reports are written to `research-reports/` as Markdown, with optional LaTeX plus BibTeX and the underlying JSON.

The toolkit also works by hand:

```
S=.claude/skills/scientific-research-assistant/scripts/sra.py
python $S search --concept "graph neural network|GNN" --concept "text classification" --strategies keyword,surveys,recent --out search.json
python $S map --concept "graph neural network|GNN" --concept "fake news detection" --design "MLP baseline on the same features" --seed 2104.12259 --out map.json
python $S retrieval-eval --fixtures "evals/retrieval/*.json" --split heldout --out retrieval.json
python $S challenge --claim "..." --query "..." --query "..." --design "MLP baseline on the same features" --seed 2104.12259 --out challenge.json
python $S fulltext --id 2104.12259 --save-text upfd.txt --out upfd_fulltext.json
python $S leakage --input items.jsonl --entities-field users --text-field text --out leakage.json
python $S repro --id 2109.03777 --out repro.json
python $S dataset-verify masakhane/masakhanews
python $S score --input scoring.json --out ranking.json
python $S verify-refs --input report.json
python $S report --input report.json --ranking ranking.json --format md,latex
python $S obsidian-export --input report.json --vault "D:\Obsidian\MyVault" --dry-run   # then without --dry-run
python $S project init --name "BoW vs text graphs" --question "..."                  # research-projects/bow-vs-text-graphs/
python $S checkpoint propose scope --project research-projects/bow-vs-text-graphs --summary "..." --item "..." --risk "..."
python $S checkpoint approve scope --project research-projects/bow-vs-text-graphs --version 1 --said "yes, go ahead"
python $S project status --project research-projects/bow-vs-text-graphs          # resume: states and the next step
python $S checkpoint require methodology execution --project research-projects/bow-vs-text-graphs   # exit 3 = blocked
python $S project run --project P --evidence results/results.json -- python analysis.py   # authorized run, recorded
python $S manuscript init --dir papers/x --title "..."      # paper workspace (+ project unless inside one)
python $S manuscript cite --id 10.1145/2630069 --key allodi2014
python $S manuscript check                                 # untraced numbers, unverified references, TODOs
python $S manuscript build                                 # draft .md/.docx/.pdf in build/, marked DRAFT
python $S manuscript review                                # proposes the manuscript checkpoint
python $S manuscript build --final                         # only after the user approved the manuscript
python $S manuscript check-numbers --paper cvss-kev/paper.md --results cvss-kev/results/results.json   # read-only audit
```

## Layout

```
SKILL.md                   workflow routing, integrity rules, command overview
references/                loaded by Claude only when a step needs them
  gap-discovery.md           workflow A
  adversarial-verification.md  deep pass on shortlisted questions: overlap, leakage, baselines, decisions
  reproducibility.md         workflow B
  project-design.md          workflow C (methodology selection)
  scoring-rubric.md          criteria, anchors, blockers, input format
  report-schema.md           report JSON format and validator rules
  sources.md                 sources, keys, rate limits, failure handling
  checkpoints.md             research projects and the human decision gates
  manuscript.md              paper workspaces, placeholders, citations, the DOCX/PDF build
scripts/sra.py             command-line entry point
scripts/sra/               http client, source clients, search, landscape, novelty, fulltext, leakage, retrieval_eval, repro, datasets, scoring, verify, report, obsidian, checkpoints, manuscript, hook
templates/                 Markdown layouts per report type, the LaTeX preamble, manuscript/ (paper workspace + print CSS)
tests/                     offline unit tests and opt-in live tests
examples/nlp-graph-theory/ worked example with every intermediate file
evals/evals.json           prompts for evaluating the skill end to end
evals/retrieval/           retrieval fixtures: known relevant papers per topic, dev and held-out splits
```

## Obsidian export

`obsidian-export` writes finished reports into an Obsidian vault as plain Markdown. No plugin or MCP server is involved.

```
<vault>/Scientific Research/
  Research Dashboard.md        all exported projects, grouped by type, with status and date
  Projects/<report title>.md   the rendered report; citations are [[wikilinks]] to paper notes
  Papers/<paper title>.md      one note per verified reference, shared by every report that cites it
```

- **At a glance:** every project note starts with a short box: the main question or topic, report type, field and status, the datasets, the research questions and hypotheses (proposals), every question considered with its go / conditional-go / no-go decision, and the conclusion (the report's recommendation; for a proposal, its expected contribution). It is built only from fields in the report; a missing field is left out.
- **Frontmatter:** `title`, `research_type`, `created`, `updated`, `tags`, `research_status` (from the report's decisions or results, or `--status`), and `source_report`.
- **Paper notes** copy only what the reports contain: title, authors, year, DOI and arXiv links, findings, limitations, method and data, each attributed to the report and its read level. Missing fields read "not reported".
- **Re-running updates notes in place:**
  - Only the generated section between `%% sra:begin %%` and `%% sra:end %%` changes. Your own text, frontmatter keys and tags are kept.
  - Renamed notes are found again; nothing is ever deleted.
  - A generated section you edited by hand is skipped with a warning.
- **Existing reports** (for example the UPFD and sentiment audits) export from their saved JSON without rerunning any research. Source reports are never modified.
- **Automatic export:** add `--obsidian` to `report`, or set `SRA_OBSIDIAN_AUTO=1` and `SRA_OBSIDIAN_VAULT` once.

## Tests

```
cd .claude/skills/scientific-research-assistant
python -m unittest discover -s tests -t tests              # offline; all HTTP is faked
cd tests && SRA_LIVE=1 python -m unittest test_live -v     # real services (PowerShell: cd tests; $env:SRA_LIVE=1; python -m unittest test_live -v)
python scripts/sra.py retrieval-eval --fixtures "evals/retrieval/*.json" --out retrieval.json   # live retrieval recall
```

Retrieval evaluation (`evals/retrieval/`) uses one fixture per topic. Each fixture records a claim, queries, design elements, seed papers and the known-relevant papers that audits later identified:
- **dev:** the UPFD and sentiment audits.
- **heldout:** seven other topics from the first opportunity report.

Most fixtures reuse the claim and queries recorded before the answers were known. Recall over a few dozen papers is a rough estimate: it can show that a configuration misses papers, but not that novelty detection is reliable. A live run of all fixtures makes several hundred requests and takes about 30-60 minutes without API keys; responses are cached for a day.

Results on 2026-10-26 (v1.0 release candidate):

- Offline: 275 tests run on Python 3.14 and 3.11, all pass; 13 live tests are skipped offline.
- New: the run manifest and a relative interpreter path in `project run`; the hook's JSON deny protocol and its fail-open settings command; options saved with a proposal; a final build that refuses rather than skip DOCX or PDF.
- Checked in fresh `claude -p` sessions on a copy of the workspace:
  - the hook blocks a direct script run through both the Bash and PowerShell tools;
  - a project started in plain language stops at scope with four options;
  - a reply in a new session is recorded in the user's words;
  - a doubtful reply records nothing;
  - a stale manuscript is re-proposed, and approved in a later session to build the final DOCX and PDF.
- The `QUICKSTART.md` example was run as written.

Results on 2026-10-26 (six gates and paper infrastructure):

- Offline: 269 tests run on Python 3.14, all pass; 13 live tests are skipped offline.
- `tests/test_gate_rules.py` (21 tests):
  - execution marked not applicable (needs a reason and the user's words; never authorizes computation; reopening it makes later gates stale);
  - authorization versus completion (no results without a successful recorded run; runs are bound to the authorization they ran under; edited evidence or a newer run makes approved results stale);
  - the results review fields;
  - `project run`;
  - the schema upgrade;
  - free `report --check`;
  - the shell hook (blocks direct script runs in project folders, follows `cd`, leaves ordinary commands alone, fails open).
- `tests/test_manuscript.py` (23 tests):
  - configuration merging and scaffolding;
  - placeholders and formats;
  - the untraced-number scan;
  - APA citations and reference lists;
  - `cite` through faked APIs;
  - every check issue;
  - draft builds with a fake pandoc and browser;
  - final builds refused without approval, after edits, and for inputs added after approval.
- Three earlier checkpoint tests were adjusted, because the requested refinements changed the behaviour they asserted: results now need a completed run and a review, `report --check` is no longer blocked, and projects have six gates.
- Five deliberately broken versions of the new rules were each caught by at least one test.

Results on 2026-10-22 (human decision checkpoints):

- Offline: 225 tests run on Python 3.14, all pass; 13 live tests are skipped offline. `tests/test_checkpoints.py` (18 tests, also passing on 3.10 and 3.11) covers:
  - **approval enforcement:** a proposal is not an approval; approval needs the user's words and the version they saw; gates go in order; rejection and revision block; a file edited between proposal and approval cannot be approved; `report --project` refuses a proposal without the `question` gate;
  - **invalidation:** a new methodology version supersedes its approval and makes `execution` stale until re-approved; editing or deleting an attached plan file makes it and all later gates stale; reopening the question makes every later gate stale;
  - **resume:** each step runs in a separate process, so only `project.json` carries state. A later "session" finds the project with `project list`, sees the pending decision and next step in `status`, re-reads the full proposal with `show`, and records the reply.
- Each of four deliberately broken versions of the rules (stale approvals counted as approved, file-change check removed, `--said` not required, attached-file hashes ignored) fails at least two of these tests.

Results on 2026-10-19 (literature-first discovery update):

- Offline: 172 tests run on Python 3.14, all pass; 13 live tests are skipped offline. `tests/test_discovery.py` covers:
  - the evidence strategies, the landscape map and its classifier (including the product-review false positive);
  - schema-3 validation, and question-type-aware scoring;
  - the retrieval-evaluation harness and fixture integrity.
- Live retrieval evaluation (`evals/results/2026-10-19-retrieval.md`):
  - **Recall:** the current challenge found more known papers than the old keyword challenge, on dev (4 vs 1 of 9) and held-out topics (11 vs 7 of 15).
  - **Verdicts:** it flags prior work on 5 of 9 topics where it exists (old: 0), and on 0 of 2 negative controls.
  - **The `map` step** improved ranking on dev topics only.
  - **Still missed by every configuration:** several closest papers. Web search remains necessary.

Results on 2026-10-18 (after the adversarial-verification update):

- Offline: 144 tests run on Python 3.14, all pass; 13 live tests are skipped offline. `tests/test_adversarial.py` adds regression tests for the failure modes of the UPFD investigation:
  - a differently worded same experiment reachable only through citations or design elements;
  - abstract-level novelty scores;
  - `go` without full-text reading or risk checks;
  - claims "verified" against unread papers;
  - entity-overlap leakage, full-text extraction, and false-positive patterns.
- Live: 13 tests, 11 passed, including full-text extraction from arXiv source. OpenAlex and Semantic Scholar were skipped as rate-limited without keys.
- End-to-end evaluation on two "already done" scenarios: see `evals/results/2026-10-18.md`. Passing tests shows the toolkit enforces its rules. It does not show that the research conclusions it supports are correct.

Results on 2026-10-13:

- Offline: 97 tests pass on Python 3.11.9 and 3.14.0. They cover retries, backoff, rate-limit handling, caching, identifier parsing, deduplication, every source parser, search orchestration, the novelty signal, reproducibility checks, dataset verification, reference verification, scoring and blockers, report validation, Markdown, LaTeX and BibTeX rendering, and the CLI. These use fabricated fixtures and show nothing about the live services.
- Live: 12 tests. In the first run, 11 passed and Semantic Scholar search was skipped as not verified (HTTP 429 without a key). In the final run after later code changes, 10 passed; Semantic Scholar was skipped again and OpenAlex was skipped because the keyless daily budget had been used up by the demonstration.

## What has been verified live

| Capability | Status |
| --- | --- |
| OpenAlex search, single-work lookup, citing works, reference lists | worked throughout the demonstration until the keyless daily budget ran out |
| arXiv search and lookup | verified |
| Crossref search and DOI lookup | verified |
| PubMed search and fetch | verified by the live test only; not used in the demonstration |
| Hugging Face paper search, dataset metadata, dataset sizes, repos by arXiv ID | verified |
| GitHub repository metadata, README, file tree, repository and issue search | verified (unauthenticated) |
| Zenodo dataset search | verified by the live test; record lookup exercised only with fixtures |
| DOI existence through doi.org | endpoint confirmed by hand; the fallback path is exercised only with fixtures |
| Semantic Scholar single-paper lookup | worked intermittently without a key |
| Reference verification, including catching a real ID with a wrong title | verified |
| Markdown, LaTeX and BibTeX output | verified; the LaTeX compiled to a 12-page PDF with pdflatex and bibtex, no errors |
| Skill discovery by Claude Code | verified: the skill appears in the session's skill list |

Not verified:

- Semantic Scholar search, citations, references and recommendations: every keyless search returned HTTP 429. The code paths are covered only by fixtures.
- Any behaviour with API keys set (none were available).
- Whether Claude, following `SKILL.md` in a fresh session, makes the same judgement calls as the worked example. The example was produced by the same session that built the skill. `evals/evals.json` holds prompts for an independent evaluation, which has not been run.
- No experiment from any assessed paper was executed and no dataset was downloaded.

## Worked example

`examples/nlp-graph-theory/` is a real run on "NLP and graph theory" (graph neural networks for text classification), 2026-10-13:

- `opportunity_report.md` (also `.tex`, `references.bib`): nine verified references; three opportunities kept or revised and one rejected because the novelty challenge found it already answered.
- `reproducibility_report.md`: four papers assessed; one blocked because no open-access full text was found.
- `research_proposal.md`: a proposal for the top opportunity.
- `*_scoring_input.json`, `*_ranking.json`, `*_report.json`: the inputs and outputs of each step.

All summaries in it rest on abstracts and repository metadata, and are labelled that way.

## Known limitations

- Novelty and relevance scoring is lexical (word overlap weighted by rarity). It misses paraphrases and cannot judge meaning; Claude has to read the closest papers. The thresholds are heuristics, not calibrated.
- Papers are not downloaded or parsed. Hyperparameters, hardware, seeds and stated limitations that appear only in the full text are marked for manual review.
- Reproducibility checks read READMEs and file names, not code. A seed set inside a script, or a dependency listed only in prose, is reported as not found.
- Choosing among several repositories is heuristic. Reading lists are filtered out, but an official implementation is not told apart from a third-party one unless the paper links it; the output says to check authorship.
- Dataset discovery covers Hugging Face and Zenodo. Kaggle, UCI, OpenML and domain repositories (GEO, PhysioNet and others) are not searched, and other URLs are checked only for reachability.
- Aggregator metadata can be wrong. Abstracts are taken from the primary source where possible and reference titles are verified, but years, venues and citation counts from aggregators are not cross-checked beyond Crossref.
- Without keys, OpenAlex and GitHub quotas allow only a handful of full workflows per day.
- English-language queries and sources only. Coverage outside computer science and biomedicine is thinner.
- Feasibility scores are assigned by Claude from evidence; the tool enforces evidence and blockers but cannot check that a score is reasonable.
- The execution hook is a guard rail, not a sandbox: it inspects only Claude's own shell commands that name a project script (see `references/checkpoints.md`).
- The run manifest records versions and hashes; it does not snapshot data or packages.
- The manuscript number check cannot trace derived values (differences, complements, ratios) and has no notion of numbers quoted from the literature: both appear as untraced.
- `manuscript init` creates new workspaces; it does not adopt an existing paper folder that already has a `paper.md`.

## Possible improvements

1. Fetch and parse open-access PDFs to extract limitations, hyperparameters, hardware and seeds automatically.
2. Embedding-based similarity for the novelty challenge, with the lexical score kept as a transparent fallback.
3. Code search inside repositories (seed handling, argparse defaults) when a GitHub token is available, and checks for pinned dependency versions.
4. More dataset sources: OpenML, Kaggle, UCI, DataCite search, domain repositories.
5. OpenReview and ACL Anthology integration for peer-review status and official code links; ReScience and ML Reproducibility Challenge reports as a source of existing reproductions.
6. A budget counter that tracks remaining OpenAlex and GitHub quota and plans calls accordingly.
7. Run the prompts in `evals/evals.json` with and without the skill and tune `SKILL.md` on the results.
