# Scientific Research Assistant: technical and product audit

**Date:** 2026-10-20 · **Scope:** `.claude/skills/scientific-research-assistant/`, `research-reports/`, `work/`, `evals/`, `cvss-kev/`, `llm-memorisation/`, the Obsidian export · **Companion:** [`2026-10-20-roadmap.md`](2026-10-20-roadmap.md)

The audit changed no code, report or experiment.
- Two analyses were re-run as checks: CVSS/KEV extraction and analysis, and the LLM-memorisation analysis stage. Both ran on copies in a temporary folder, so the original outputs were not overwritten.
- No large files were downloaded.
- No models were trained.

**Status labels:**

| Label | Meaning |
| --- | --- |
| **Working** | Implemented, used on real projects, tested |
| **Partial** | Works, but with a known gap that limits what it can claim |
| **Experimental** | Code exists, but is not reachable from the normal workflow, or has not shown a benefit |
| **Broken** | A default behaviour gives wrong or empty results |
| **Missing** | Not implemented |

A passing test means the code does what the test checks. It does not mean that a search found all relevant work, that a verdict is right, or that a statistic is interpreted correctly.

---

## 0. Summary

1. **The literature side is careful about honesty, but its retrieval is weak.**
   - **What works:** the rules hold. The report validator refuses unchecked references, inflated novelty confidence, a `go` without full-text reading, and "reproduced" without execution evidence.
   - **The weak point is finding papers.** On the blind evaluation set (9 of 16 topics run, arXiv and Crossref only, because no API keys are set), every topic had already been studied. Yet the default `challenge` said "no close match in this search" for **7 of 9**, and found only **5 of 22** known papers.
   - **Known cause:** the arXiv client still requires every query word (AND) by default. In the 2026-10-19 diagnosis, 646 of 745 arXiv searches (87%) came back empty for that reason.
2. **The hybrid/semantic retrieval experiment was not integrated, and should not be yet.**
   - The fusion and hybrid ranking code exists (`fusion.py`, `semantic.py`), but only `retrieval-eval` can reach it.
   - On the old benchmark, fusion raised recall@50 (14/24 vs 10/24) but lowered MRR (0.163 vs 0.194).
   - On the partial blind run, no configuration beat the default.
   - The blind run stopped after 9 of 16 topics, so the pre-registered decision was never made.
3. **The data-analysis side does not exist in the skill.** Both finished papers were analysed with hand-written project scripts, not with skill code.
   - **CVSS/KEV:** pandas, SciPy and statsmodels.
   - **LLM memorisation:** Ollama, a GCN and GEE models.

   Those scripts are good. Re-running both analyses reproduced **every result file and figure byte for byte**. But nothing in the skill supports this stage: no analysis template, no record of inputs and environment, and no check that the paper's numbers come from code.
4. **Traceability gaps are real and measurable.**
   - The CVSS/KEV paper says `analysis.py` "produces every number". Six statements use numbers it does not compute: CVEs per year, score clustering, and vendor concentration. All six are correct; I recomputed them.
   - One sentence ("0 of 1,753") reads as a KEV count, but 1,753 is the number of Physical-vector CVEs.
   - Nothing in the skill would have caught either.
5. **Continuity across sessions depends on Claude's memory and file names.** There is no project state file.
   - The `work/` folder holds 150+ intermediate JSON files from six projects in one flat-ish tree.
   - The Starry Sky proposal files live in `work/qa-sky/`, while the reports live in `research-reports/qa-starry-sky/`.
6. **Usability:** a full Workflow A needs roughly 10–20 CLI calls, plus a hand-written report JSON of 200–600 lines. Claude does this, but it is slow and fragile. A two-question opportunity report took most of a session.

---

## PART 1: Inventory

### 1.1 Overview

| Item | Count / fact |
| --- | --- |
| Python toolkit | 28 modules, about 5,800 lines; standard library only (`scripts/sra/`) |
| Instructions | `SKILL.md` (201 lines), 7 reference files (878 lines), 5 templates |
| CLI commands | 17: `sources`, `search`, `paper`, `related`, `challenge`, `map`, `retrieval-eval`, `fulltext`, `leakage`, `repro`, `dataset-search`, `dataset-verify`, `score`, `verify-refs`, `report`, `obsidian-export`, plus `report --obsidian` |
| Tests | 207 unit and integration tests (mocked HTTP), all pass in 2.0 s on Python 3.14; 13 live-network tests skipped unless `SRA_LIVE=1` |
| Evaluation fixtures | 11 hand-curated retrieval fixtures (2 dev, 7 held-out, 2 negative controls); 19 blind fixtures (16 topics plus 3 controls) frozen with SHA-256 hashes in `evals/retrieval_blind/MANIFEST.json` |
| API keys in this environment | only `HF_TOKEN`. `OPENALEX_API_KEY`, `SEMANTIC_SCHOLAR_API_KEY`, `GITHUB_TOKEN`, `NCBI_API_KEY` and `SRA_CONTACT_EMAIL` are unset. `sources` reports all 8 services reachable today |
| How Claude invokes it | `SKILL.md` loads on research requests. Claude runs `python scripts/sra.py <command>` via Bash, reads the printed summary, opens `--out` JSON when needed, and hand-writes the report JSON |

### 1.2 Component by component

#### Literature search: `search` (`search.py`, `models.py`, `sources/*.py`, `http.py`)

**Status: Partial, with one Broken default.**
- **What it does:** multi-source keyword search with synonym expansion (`--concept`) and strategies (keyword, recent, foundational, limitations, surveys, reproducibility), deduplicated by DOI, arXiv ID and title.
- **Sources:** OpenAlex, arXiv, Crossref, Semantic Scholar, PubMed and Hugging Face papers. Responses are cached for 24 h.
- **Dependencies:** none. Free API keys are optional but practically needed:
  - OpenAlex's keyless budget ran out during evaluations;
  - Semantic Scholar mostly returns HTTP 429 without a key.
- **Tests:**
  - `test_core.py` and `test_workflows.py`: deduplication, retry and back-off, source fallback.
  - No deduplication failure was observed in the 2026-10-19 diagnosis (each missed target's closest non-matching title had similarity ≤ 0.64).
- **Known bugs:**
  - **arXiv AND (Broken default).** `arxiv.build_query(match="all")` ANDs every content word. Queries of 6+ words almost always return nothing: 646/745 empty in run A. The fix (`match="any"`) exists but is not the default, and the CLI does not expose it.
  - **Title-only records.** 27–50% of candidates per topic had no abstract (mostly Crossref). The abstract fallback uses OpenAlex only, so when OpenAlex is over budget the novelty verdict cannot fire.
  - **Truncation.** Each query keeps 10–15 results per source, and citing lists stop at 20 per sort order. Three known papers were missed only because of these caps.
- **Integration:** default workflow.

#### Paper resolution and citation graph: `paper`, `related` (`search.resolve`, `search.related`)

**Status: Working.** Citation coverage depends on OpenAlex and Semantic Scholar availability.
- **What it does:** resolves an arXiv ID, DOI, PMID, OpenAlex ID, URL or title, and lists references, citing works and recommendations.
- **Limitations:**
  - preprints often have no references in OpenAlex (Karn & Jensen 2025 had 0), so no citation route reaches them;
  - Semantic Scholar is effectively unavailable without a key.
- **Integration:** default.

#### Novelty challenge: `challenge` (`novelty.py`)

**Status: Partial.** The guardrails work; retrieval recall is low.
- **What it does:**
  - searches with the given phrasings;
  - runs design-element queries ("MLP on the same features");
  - expands the citations of the top 3 papers and of seeds;
  - ranks candidates by rarity-weighted term overlap plus TF-IDF;
  - outputs a signal (`crowded`, `close_prior_work_found`, `no_close_match_in_this_search`) and a confidence ceiling that coverage gaps can only lower.
- **Measured:**
  - **Held-out (7 topics):** 11/15 known papers found, 9/15 in the top 20. The verdict flagged 4/7.
  - **Dev:** 4/9 found.
  - **Controls:** 0/2 false alarms. The control fix was made after seeing a control result, so that number is not independent.
  - **Blind (partial, 9/16 topics, arXiv and Crossref only):** 5/22 found, 3 in the top 20, mean MRR 0.028. The signal said "no close match" on 7/9 topics that all have known prior work.
- **Known issues:**
  - Ranking by the one-sentence claim buried exact matches. "Does syntax matter? A strong baseline…" ranked 150, because filler words in the claim dominate the overlap weighting.
  - Design-element matching has low precision: in Eval 5, 20 papers matched 2+ elements, including generic GNN papers.
- **Integration:** default. SKILL.md requires it for every idea.

#### Literature map: `map` (`landscape.py`)

**Status: Working**, but its benefit was shown only for reading order.
- **What it does:**
  - runs comparison, negative-result, critique, reproducibility, limitations and design queries;
  - sorts papers into evidence buckets with regex patterns;
  - prints a read-first list, web-search queries and an evidence-ledger template.
- **Measured:** better top-20 ranking on dev (3/9 vs 1/9). No added recall on held-out topics, and fewer known papers than `challenge` on 3 of them.
- **Limitation:** buckets are regex matches on title and abstract, not judgements.
- **Integration:** default first step of Workflow A.

#### Semantic and hybrid retrieval (`fusion.py`, `semantic.py`; `challenge(ranking="fusion", semantic=True)`)

**Status: Experimental, not integrated.**
- **What it does:**
  - reciprocal-rank fusion (K = 60) over the claim and each query;
  - optional embedding similarity, using model2vec or sentence-transformers. These are optional packages, so the toolkit itself stays standard-library only.
- **How to reach it:** only through `retrieval-eval --configs challenge_lexical,challenge_hybrid`. The `challenge` and `map` commands have no flag for it.
- **Measured:**
  - **Fixed pool, old benchmark (24 targets):**

    | Ranking | Recall@20 | Recall@50 | MRR |
    | --- | --- | --- | --- |
    | Claim only (current) | 10 | 10 | 0.194 |
    | Fusion | 9 | 14 | 0.163 |
    | Hybrid (potion-retrieval-32M) | 11 | 13 | 0.081 |

  - **Blind (partial, 22 targets, papers found anywhere in the list):** default 5, arXiv-OR 4, fusion 5, hybrid 3. Hybrid has the best mean MRR (0.042, vs 0.028), but on very few hits.
- **What happened:** the live run was stopped by the user after 9 of 16 blind topics. The regression run on the old fixtures never started (`old.txt` is empty). The pre-registered decision rule in `evals/retrieval_blind/PLAN.md` was never applied. `evals/results/2026-10-19-retrieval-reliability.md` contains Part 1 (failure analysis) only.
- **Conclusion:** no evidence yet that fusion or hybrid helps. Embeddings can only re-rank papers that a lexical search already returned; most blind misses were never retrieved at all.

#### Full text: `fulltext` (`fulltext.py`)

**Status: Partial.**
- **What it does:**
  - fetches the arXiv LaTeX e-print, or arXiv HTML;
  - splits the text into sections with roles (method, data, experiments, ablation, baselines, limitations…);
  - flags sentences about seeds and runs, splits, variance, structure-free baselines, ablations, leakage, code links, hardware and stated limitations;
  - optionally saves section text for reading.
- **Does not handle:**
  - PDFs, including open-access PDFs from publishers and PMC: it only lists the link;
  - page numbers.
- **Flags are regex hints, not facts.**
- **Measured:** in Eval 5 it surfaced the UPFD paper's MLP baselines, the edge-removal ablation, "five runnings" and the 20/10/70 split. Those facts made the proposal a duplicate.
- **Integration:** default for papers with an arXiv ID. Anything else falls back to Claude reading the PDF manually.

#### Reproducibility pre-check: `repro` (`repro.py`)

**Status: Working**, within a narrow scope.
- **What it does:**
  - checks open access;
  - finds code (GitHub search, Papers-with-Code-style links in the text, `--repo`);
  - inspects the README and file tree with regex for dependencies, data instructions, configs, seeds, hardware, evaluation, pretrained weights and licence;
  - flags maintenance (last push, archived).
- **Limitations:**
  - It never reads code, so a seed set inside a script reads as "not found".
  - Without `GITHUB_TOKEN`, search allows 10 requests per minute and the core API 60 per hour.
- **Integration:** default in Workflow B.

#### Datasets: `dataset-search`, `dataset-verify` (`datasets.py`)

**Status: Working**, with narrow coverage.
- **What it does:** searches and verifies Hugging Face and Zenodo records (licence, size, splits, gating). Any other URL gets a reachability probe.
- **Missing:** Kaggle, UCI, OpenML, Papers with Code datasets, institutional repositories.
- **Not reported for arbitrary URLs:** size.

#### Leakage analysis: `leakage` (`leakage.py`)

**Status: Working** for entity leakage; temporal leakage is Missing.
- **What it does:**
  - train/test entity overlap;
  - a model-free entity vote compared with the majority baseline;
  - connected components (is an entity-disjoint split feasible?);
  - masking impact;
  - exact duplicate texts across splits;
  - one-scalar shortcut rules;
  - reruns with hub entities removed.
- **Missing:**
  - **Time:** no time or date field, no check that training items predate test items, no check that a feature was available before the label (look-ahead). This is exactly the CVSS current-score and EPSS problem.
  - **Duplicates:** no near-duplicate detection, only exact matches after normalisation.
  - **Input:** no data adapters. The user must build a JSONL with split, label and entities.
- **Real use:**
  - **UPFD:** needed two custom scripts (`research-reports/upfd-audit/user_overlap.py`, `remote_zip.py`) to get the data into shape.
  - **Sentiment:** `leakage_Laptop.json` and `leakage_Restaurants.json` came from the tool.

#### Scoring: `score` (`scoring.py`, `references/scoring-rubric.md`)

**Status: Working.**
- **What it does:**
  - weighted criteria scores with an evidence field;
  - blockers (data unavailable, hardware) that cannot be outvoted;
  - novelty caps by question type.
- **Limitation:** the scores are Claude's judgement. The tool enforces structure and blockers, not whether a score is sensible.

#### Reference verification: `verify-refs` (`verify.py`)

**Status: Working.**
- **What it does:** resolves each reference's DOI, arXiv ID or PMID and compares titles (similarity ≥ 0.85). Statuses: `verified`, `title_mismatch`, `identifier_resolves`, `url_reachable`, `unresolved`, `unchecked`, `no_identifier`.
- **What it proves:** that the paper exists and is the one named. It does **not** check that the paper supports the sentence citing it.
- **Measured:** every existing report shows all references verified, except two `url_reachable` entries in the Starry Sky files (AskNow, cited by DOI).

#### Report generation and validation: `report` (`report.py`, `templates/`, `references/report-schema.md`)

**Status: Working** for its four types: `literature_review`, `opportunity_report`, `reproducibility_report`, `research_proposal`.
- **54 error and warning checks** in the validator. Examples:
  - every opportunity needs a challenge, closest work, risks and a decision;
  - `go` needs full-text reading and checked risk groups;
  - "reproduced" needs `executed` plus evidence;
  - verified claims cannot cite title-only papers.
- **Outputs:** Markdown, LaTeX and BibTeX.
- **Missing:**
  - **Report types:** no type for a finished empirical paper or results report.
  - **Statistical results:** no statistical results schema.
  - **Traceability:** no check that a number in the text appears in a results file, and no check that a quoted claim matches the source text.
  - **Hand authoring:** the report JSON is written by hand (200–600 lines), which is the most time-consuming step.

#### Obsidian export: `obsidian-export`, `report --obsidian` (`obsidian.py`)

**Status: Working**, and used on a real vault.
- **What it does:**
  - managed regions between `%% sra:begin %%` and `%% sra:end %%`;
  - `sra_id` identity, so moved or renamed notes are updated, not duplicated;
  - edit detection by hash: a region the user edited is skipped;
  - tag and frontmatter merging, paper notes for verified references only, a dashboard, `--dry-run`.
- **Tests:** 18 (idempotency, user edits, Unicode, path safety).
- **Current vault state:** `D:\Obsidian\6ti Semestar\Scientific Research` holds 7 project notes, 74 paper notes, the dashboard and `Attachments/`.
  - The CVSS/KEV and LLM-memorisation project notes are hand-written, as SKILL.md describes: experiments are outside the exporter's scope.
- **Not configured:** `SRA_OBSIDIAN_VAULT` and `SRA_OBSIDIAN_AUTO` are unset, so auto-export is off and every export needs `--vault`.

#### Retrieval evaluation: `retrieval-eval` (`retrieval_eval.py`, `evals/`)

**Status: Working.**
- **What it measures:** recall@20 and @50, MRR, miss cause, HTTP calls and time per configuration.
- **Replay:** `--snapshot` stores every response so configurations see identical data; `--offline` replays.
- **Blind set:** frozen and pre-registered.
- **Gaps:**
  - the miss-cause field was empty for every blind miss, so the classification did not run on that data;
  - all live runs so far lacked OpenAlex or Semantic Scholar.

#### Project design and statistics (`references/project-design.md`)

**Status: Partial.** It exists as instructions only (62 lines): hypothesis, simplest method, baselines, splits, metrics, seeds and the statistical comparison fixed before any run.
- **No code support:** no analysis-plan template file, no plan lock (hash or date), no statistics helpers and no statistical checklist.
- **The `research_proposal` report type** carries hypotheses and a statistical plan as text fields only.

#### Data analysis, statistics and visualisation

**Status: Missing from the skill.** Every executed analysis lives in project folders:
- `cvss-kev/analysis.py`, 344 lines: χ², Mann–Whitney, Wilson CIs, Fisher, logistic regression, bootstrap AUC, case-control bootstrap, 4 figures.
- `llm-memorisation/analyze.py`, 388 lines: GEE, McNemar, difference-in-differences bootstrap, 4 figures. Plus `run_llms.py` and `gcn_baseline.py`.

These follow a good pattern that the skill could adopt: analysis plan first, deviations logged, a fixed seed, and every number in `results.json`.

#### Paper writing and export

**Status: Missing from the skill.**
- **How it was done:** `paper.md` was hand-written by Claude. `.docx` and `.pdf` were built with a manual recipe (stored in Claude's memory, not in the repo: `paper_print.html` and `.css`).
- **Missing:**
  - no manuscript template;
  - no citation formatting from verified references (references were typed in APA by hand);
  - no figure or table cross-reference check.

#### Session continuity

**Status: Missing.**
- **What exists:** no project manifest, stage tracker, decision log or "what's next" file.
- **How continuity works today:**
  - Claude's memory files (2 entries);
  - file naming;
  - the Obsidian dashboard, written after the fact.

### 1.3 Documentation vs reality

| Claim (README, SKILL_GUIDE or SKILL.md) | Reality |
| --- | --- |
| "reads open-access full texts" | arXiv LaTeX and HTML only; other open-access PDFs are only linked |
| "Searches the literature" across 8 sources | The search sources are OpenAlex, arXiv, Crossref, Semantic Scholar, PubMed and HF papers; GitHub and Zenodo are only for code and datasets. Without keys, OpenAlex and Semantic Scholar often fail, and arXiv returns nothing for long queries (AND bug) |
| `retrieval-eval` "measures recall" for the four configurations | Correct. The newer `challenge_arxiv_any`, `challenge_lexical` and `challenge_hybrid` configurations are not mentioned in SKILL.md |
| Known limitation: "similarity scoring is word-based" | Correct, and the optional semantic re-ranker is not mentioned anywhere user-facing (correct, since it is experimental) |
| Root README: each paper folder has "the scripts that compute every number" | True for results tables; false for 6 statements in the CVSS/KEV paper (§2.3) |
| Root README lists the CVSS and LLM papers | `llm-memorisation/paper.md`, `.docx`, `.pdf` and `README.md` are untracked in git (`git status`) |

---

## PART 2: Projects and their state

### 2.1 What exists

| Project | Output | Type | State | Executed analyses | Independently reproducible? |
| --- | --- | --- | --- | --- | --- |
| NLP × graphs (first run) | `research-reports/research-opportunities-at-the-intersection-of-nlp-and-graph-.md` | opportunity report | **Preliminary, superseded.** Old schema: 28 verified refs but no `read_level`, no decisions or question types. It would fail today's validator | none | n/a |
| UPFD fake-news audit | `research-reports/upfd-audit/` | opportunity report (audit) | **Complete as an audit.** 15 refs (6 full text, 5 abstract, 3 inaccessible, 1 title). Decisions: no_go, conditional_go, no_go | user-overlap leakage on official UPFD splits (`user_overlap.py` → 4 JSON files) | Scripts present; fetch splits remotely by HTTP range (`remote_zip.py`). Not re-run in this audit |
| Sentiment (ABSA syntax-GCN) audit | `research-reports/sentiment-audit/` | opportunity report (audit) | **Complete as an audit.** 13 refs (6 full, 5 abstract, 2 title). Decisions: 2 no_go, 3 conditional_go | `leakage` on SemEval Laptop and Restaurants | Inputs came from Hugging Face; not re-run |
| Starry Sky | `research-reports/qa-starry-sky/` (opportunity report and proposal), `starry-sky/` app | opportunity report and research proposal | **Proposal stage.** 3 conditional_go, 1 no_go (answered). Only 1 of 11 references read in full | none (the app is built; no study data) | n/a |
| CVSS vs KEV | `cvss-kev/` paper (md, docx, pdf) | empirical replication paper | **Complete** | extraction plus full statistics | **Yes, from the local snapshot.** Re-running `extract.py` and `analysis.py` gave a byte-identical `nvd_cvss.csv`, `results.json`, `tables.md` and all 4 figures (48 s plus 76 s). The snapshot (`data/`, about 150 MB) is gitignored and the upstream feeds change daily, so a third party cannot regenerate exactly without the archived snapshot. No input hashes are recorded |
| LLM memorisation | `llm-memorisation/` paper (md, docx, pdf) | replication and extension paper | **Complete** (paper files untracked in git) | `prepare_data.py`, `run_llms.py` (about 3 h, 4 models × 3 sets via Ollama), `gcn_baseline.py` (GPU, 5 seeds), `analyze.py` | **Analysis stage: yes.** Re-running `analyze.py` on the saved raw outputs gave a byte-identical `results.json`, `tables.md` and all 4 figures. **Model stage: not re-run** (expensive). The S2026 sample came from the live arXiv API. Temperature-0 batching and GPU sparse kernels are not bit-identical (both disclosed in ANALYSIS_PLAN deviations 2 and 4) |
| Retrieval reliability (skill evaluation) | `evals/results/2026-10-19-retrieval-reliability.md`, `work/retrieval_eval/reliability/` | evaluation | **Incomplete.** Part 1 written; blind run 9/16 topics; regression run not started; no decision | partial live run with snapshot | The partial run is replayable offline from `snapshot_blind/` |

### 2.2 CVSS/KEV: are the scripts and data present?

- **Scripts:** `extract.py` and `analysis.py` are present and run with the project's `.venv` (pandas 3.0.6, SciPy 1.18.1, statsmodels 0.15.0).
- **Data:** `data/CVE-all.json.xz` (109 MB), `kev.csv` (1,748 rows) and `nvd_cvss.csv` (43 MB) are present locally. `DOWNLOADED_AT.txt` reads 2026-10-19T21:45Z.
- **Regeneration:** confirmed byte-identical (above). The seed is fixed (20261019) and the bootstraps are seeded.

### 2.3 CVSS/KEV: number-to-code check

I listed every number in `paper.md` and looked each one up in `results/results.json`, or derived it from values stored there.

| Number in paper | In `results.json`? | Recomputed in this audit |
| --- | --- | --- |
| Tables 1–6, AUC, OR, CIs, p-values | yes | (byte-identical regeneration) |
| 99,681 flagged (55.2%), 992 exploited, 14.7%, 64.4% missed | derivable from stored TP, FP, FN, TN | 99,681; 55.2; 14.7; 64.4 ✔ |
| "about 14,600 in 2017 to over 48,000 in 2025" | **no** | 14,642 and 48,152 non-rejected ✔ |
| "six values … account for 59%" | **no** | 59.0% ✔ (9.8, 7.5, 7.8, 8.8, 5.5, 6.1) |
| "Microsoft alone 22.3% … top 10 of 289 vendors 53.1%" | **no** | 22.3, 289, 53.1 ✔ |
| "0 of 1,753" (Physical vector) | **no** | 1,753 is the number of *Physical-vector CVEs in the cohort*, of which 0 are in KEV. Read naturally, it looks like a KEV count, which is 1,748 elsewhere. **Wording problem** |
| "0.8–0.9 usually expected of a useful screening test" | n/a | **Unsourced** benchmark claim |
| "Allodi and Massacci … specificity 23–32%" | n/a | **Supported**: their case-controlled table reports 32%, 23.09% and 23.82% (`work/cyber/ft_allodi.json`, read in full) |

All values are correct, but six were computed ad hoc and never saved. The paper's §3.6 sentence ("`analysis.py` produces every number") is therefore not literally true.

### 2.4 CVSS/KEV: methodological concerns and whether they were addressed

| Concern | Where raised | Addressed? |
| --- | --- | --- |
| KEV is a lower bound on exploitation; "controls" include exploited CVEs | plan and paper, Limitations 1 | Acknowledged, not quantified. Unavoidable with this ground truth. A sensitivity analysis (e.g. adding Exploit-DB or EPSS-at-publication as an alternative outcome) is not done |
| KEV selection bias (US federal focus, remediation needed) | plan and paper, L2 | Acknowledged. The vendor concentration figure is given, but not computed in code |
| Look-ahead: current CVSS scores may have been revised after exploitation | plan and paper, L3 | Acknowledged, with a correct argument for its direction (it would make CVSS look *better*, so the conclusion is conservative). **Not tested**; NVD change history would allow a check |
| EPSS leaks the outcome | plan, paper §3.5 | **Addressed** by exclusion, with a source (Paul 2026) |
| Unequal follow-up time (2017 vs 2024 CVEs; KEV began in Nov 2021, so older CVEs entered retrospectively) | plan and paper, L4 | **Partly addressed:** year dummies, year-matched controls, and the 2018–2023 subset all leave the conclusions unchanged. The retrospective-entry mechanism itself is not discussed |
| Complete separation (Physical vector) | deviation 1 | **Addressed** and disclosed |
| Huge n makes everything "significant" | plan | **Addressed:** conclusions rest on effect sizes and CIs |
| Case-control "replication" differs from the original | not raised | **Open.** The original used CVSS v2 ≥ 6 and sampled controls from Symantec's subscore distribution. This study uses v3 ≥ 7.0 and strata on the C/I/A triple. "Reproduces the pattern" should be "is qualitatively similar to" |
| "Not significant" read as "no association" | not raised | **Minor, open.** "Network attack vector is not significant" (OR 1.17 [1.00, 1.37], p = 0.058) is borderline. The paper words it carefully in Results, but the Discussion says the exploitability metrics "add little" |
| Input provenance | not raised | **Open.** No checksums of `CVE-all.json.xz` and `kev.csv`, and no fkie release tag |

None of these invalidates the main conclusion. They are the kind of issue the skill should catch automatically (see Part 4).

### 2.5 The hybrid retrieval experiment: what happened

1. **Part 1 (diagnosis)** was completed and written up. It identified:
   - arXiv AND queries;
   - ranking by the claim alone;
   - truncation;
   - rate limits;
   - title-only records as the verdict's blind spot.
2. **The three experimental configurations were implemented:** `challenge_arxiv_any`, `challenge_lexical` (fusion) and `challenge_hybrid` (fusion plus embeddings). They are tested in `tests/test_retrieval_reliability.py`.
3. **The blind set was built, frozen and pre-registered.** `PLAN.md` holds the decision rule; the targets came from web search.
4. **The live blind run reached 9 of 16 topics.** Then the user stopped it to use the skill on Starry Sky. The regression run never started.
5. **Nothing was integrated.** The `challenge` and `map` defaults are unchanged (`ranking="claim"`, `arxiv_match="all"`). There is no CLI flag for any of the new modes.

---

## PART 3: Elicit and Julius AI

### 3.1 Sources and caveats

**Elicit**
- Official help center and blog, read 2026-10-20:
  - [Introducing Elicit Systematic Review](https://elicit.com/blog/systematic-review)
  - [Research Reports](https://support.elicit.com/en/articles/14756862-get-a-research-report-to-generate-in-depth-answers-automatically-in-elicit)
  - [Research Agent](https://support.elicit.com/en/articles/14756886-elicit-s-research-agent)
  - [Library](https://support.elicit.com/en/articles/14757550)
  - [Export your data](https://support.elicit.com/en/articles/1153857)
  - [Screening papers for systematic review](https://support.elicit.com/en/articles/2601281) (read via search excerpt)
- The pages I read describe "supporting quotes" and "reasoning". **They do not state page-level references**, so this audit does not claim them.

**Julius**
- Official sources, read 2026-10-20:
  - [Getting Started](https://julius.ai/docs/get-started/quickstart)
  - [FAQs](https://julius.ai/docs/faqs)
  - the docs index [`/docs/llms.txt`](https://julius.ai/docs/llms.txt), whose one-line page descriptions are official
  - the blog post [Notebooks Are No Longer Necessary](https://julius.ai/product/notebooks) (19 Aug 2026)
- The site's Cloudflare check blocked the individual pages on Tools, Data Cleaning, Reports, Containers and Visualizations, so only their index descriptions were used.
- **Unverified, and not counted:**
  - R support (third-party reviews say yes; the official text I could read mentions only Python libraries);
  - specific statistical tests beyond the FAQ's "Run a one-way ANOVA".
- **Notebooks are being sunset.** The older "Reproducibility in Notebooks" page now returns 404. Julius's current reproducibility story is unclear from official docs.

### 3.2 Elicit vs our skill

| Elicit feature (official) | What Elicit documents | Our skill | Status |
| --- | --- | --- | --- |
| Semantic literature search | Searches "over 138 million papers"; the Research Agent also searches the web, ClinicalTrials.gov, regulatory documents and uploaded files | Keyword search over 6 public APIs; embeddings experimental | **Partial.** Recall is our weakest point (§1.2). Note that Elicit's own blog says publication-grade reviews often need traditional keyword search |
| Structured screening | Criteria generated from the question, editable; papers sorted by likelihood of meeting all criteria, with recommendations and reasons; overrides; CSV export | No screening step. `map` buckets and `challenge` signals are triage, not inclusion decisions | **Missing** |
| Custom extraction tables | Suggested and editable columns; each answer has supporting quotes and an explanation; up to 20 columns in the guided workflow; CSV and Excel | The evidence ledger and `closest_existing_work` are free text written by Claude; `fulltext` flags are fixed regex categories | **Partial.** No per-paper, per-column table, and no quote stored with each value |
| Sentence-level evidence and page references | Supporting quotes behind each extracted answer and report statement; page level not stated | `read_level` per paper; claims tagged [V], [E] or [S]; no stored quotes; no page numbers (arXiv TeX has none) | **Partial** |
| Systematic review workflow | Guided search → screening → full-text extraction → report; any step can run alone; "living reviews" | Workflow A is gap discovery, not a systematic review. No PRISMA counts, no inclusion log | **Missing.** Only partly appropriate: a full systematic review is rarely what our users need |
| Evidence synthesis and comparison | Research Reports summarise the extraction table; templates include "Research Gap Analysis"; the agent builds comparison tables | Opportunity reports with an evidence ledger, typed questions and adversarial challenge; Elicit does not document anything like this | **Implemented, and different.** Our strength is adversarial novelty checking and go/no-go decisions |
| Reports and citation export | Reports as PDF or Word; tables as CSV or Excel; RIS and BIB from tables and sessions | Markdown, LaTeX, BibTeX, JSON | **Implemented**, except for RIS, docx and PDF |
| Research libraries and collections | Library with uploads, tags, collections, Zotero import, reuse in reviews, RIS export | Per-project JSON in `work/`; Obsidian paper notes act as a de facto library (74 notes) but cannot be searched or reused by the toolkit | **Partial** |

### 3.3 Julius vs our skill

| Julius feature (official) | What Julius documents | Our skill | Status |
| --- | --- | --- | --- |
| Conversational dataset analysis | Ask in plain language; Julius "writes code to analyze your data"; multiple LLMs | Claude does this in Claude Code with ordinary Python (CVSS, LLM projects), but the skill gives no structure | **Partial**, through Claude Code itself |
| CSV, Excel and other imports | CSV, Excel (multi-tab), JSON, PDFs, images; databases and warehouses (Postgres, MySQL, SQL Server, Snowflake, BigQuery, Supabase) | Anything Python can read, done by hand per project | **Partial.** Database connectors are **not appropriate** for us |
| Data cleaning and profiling | "Data Cleaning Basics" page; Data Explorer for viewing dataframes | None in the skill | **Missing** |
| Statistical testing and diagnostics | The FAQ example is "Run a one-way ANOVA"; no official list of tests or assumption checks found | Done well in project scripts (§2), but no skill support: no assumption checks, effect-size helpers or multiple-comparison helpers | **Missing in the skill** |
| Reproducible Python/R analysis | Code is shown. Notebooks (rerunnable code cells) are being sunset (Aug 2026), so the documented reproducibility path is going away | Project scripts with fixed seeds regenerate byte-identically. That is stronger than anything Julius documents, but it is a habit, not tooling | **Partial.** Ours is better in practice but not enforced |
| Charts and publication-quality figures | Bar, line, scatter, histogram, pie; matplotlib, seaborn and plotly; custom visualisations; copy or download | Project scripts produce 200 dpi PNGs with a consistent palette; no shared style module | **Partial** |
| Interactive analysis and iteration | Chat-driven; Data Explorer; interactive artifacts (dashboards) | Claude Code iteration over files | **Implemented in Claude Code.** Dashboards are **not needed** |
| Reports grounded in executed calculations | "Reports" artifact: "long-form write-ups Julius generates from your analysis"; how numbers are tied to code is not documented | Papers written by Claude from `results.json`, with no checker (6 untraced numbers in CVSS) | **Partial.** A **number-to-code check would be a real advantage** over what Julius documents |

### 3.4 What we already do that neither documents

- **Adversarial novelty challenge**, with a confidence ceiling that failed sources lower and that is capped at "medium".
- **Validator-enforced go / conditional-go / no-go**, which needs full-text reading of the closest work.
- **Model-free leakage diagnostics** (entity vote, components, shortcut rules).
- **Pre-registered analysis plans with logged deviations**, a project habit that should become tooling.
- **A blind, hash-frozen retrieval benchmark** with negative controls.
- **Local-first operation:** free APIs, plain files, Obsidian.

---

## PART 4: Gaps along the research workflow

| Stage | Current state | Where it breaks or needs manual work | Example |
| --- | --- | --- | --- |
| Research interest → literature map | `map`; reading order works | Long queries return nothing from arXiv. Without keys OpenAlex and Semantic Scholar drop out, the map is thin, and its coverage notes may go unread | Blind run: arXiv rate-limited twice; OpenAlex not used |
| Paper discovery | `search`, `challenge`, `related` | **Recall.** About 23% of known prior work found on blind topics. Paraphrases ("information extraction" vs "sentiment") are missed. Truncation at 10–20 per query or list | Sentiment audit: "Does syntax matter?" ranked 150, and both ABSA reproducibility papers were missed (`2026-10-19-retrieval-reliability.md`) |
| Evidence extraction | Claude reads `fulltext` output and the PDFs | No extraction table and no stored quotes. The evidence ledger is prose. Non-arXiv PDFs are read manually and cannot be checked later | Starry Sky: 10 of 11 references read at abstract level only, because the closest work (AskNow, CHI) is not on arXiv |
| Gap evaluation | Validator plus `challenge` signal | **"No close match" is the common verdict even for done ideas** (7/9 blind). The safeguards (ceiling ≤ medium, wording) are good, but users read "no match" as "new" | UPFD: the first audit said no_close_match; Karn & Jensen (2025) had already done the experiment (Eval 5) |
| Hypothesis and design | `project-design.md`; `research_proposal` type | No analysis-plan template or lock; no power or sample-size check; no pre-registration timestamp | CVSS and LLM used `ANALYSIS_PLAN.md` by habit; Starry Sky has no sample-size reasoning for its 2 studies |
| Implementation | none | Fine to leave to Claude Code. No scaffolding (folder layout, seeds, environment capture) | Each project invented its own layout (`.venv`, `.venv-gpu`) |
| Dataset analysis | none | No profiling. Data snapshots have no hashes. Data adapters for `leakage` are custom | UPFD needed `remote_zip.py` and `user_overlap.py` |
| Temporal leakage | none | No check that features predate labels, or that train precedes test | CVSS current scores (look-ahead, untested); EPSS leakage was found by reading Paul (2026), not by a tool |
| Statistical testing | project scripts | No assumption checks, no reminder that effect sizes matter more than p with huge n, no "non-significant ≠ no effect" lint | CVSS: "attack vector … adds little" from p = 0.058 with CI to 1.37 |
| Results | `results.json` per project, by habit | No provenance (inputs, versions, commit, time); no checksum | CVSS: byte-identical rerun, but only because the snapshot is still on this laptop |
| Scientific paper | hand-written `paper.md`; manual docx and pdf | **Number-to-code**: 6 untraced numbers. **Claim-to-source**: citations verified for existence only. References typed by hand. No figure or table cross-reference check | CVSS §2.3; "0.8–0.9" benchmark unsourced; "0 of 1,753" ambiguity |
| Obsidian export | working | Experiments need hand-written notes; auto-export env vars unset | 2 hand-written project notes |
| **Continuity** | Claude memory and file names | No project manifest. `work/` is mixed across projects. The retrieval experiment's state lived only in conversation summaries | Retrieval Parts 2–4 left without a written status (now recorded in §2.5) |
| **Usability** | 17 commands; hand-written report JSON | 10–20 tool calls per opportunity report; schema errors only appear at `report` time; searches take 1–4 min each | Starry Sky opportunity report: about 15 commands plus 2 builder scripts (`work/qa-sky/build_report.py`, `build_proposal.py`) |

### Hallucination and unsupported-claim risk, ranked

1. **Highest: false "novel" impressions** from low recall, even with correct caveats. Measured: 7/9 blind topics.
2. **Paper numbers** not produced by code. Measured: 6 in CVSS (all correct this time, by luck of care).
3. **Statements attributed to abstract-only papers.** Starry Sky: 10/11 abstract-level; CVSS: several 2025–2026 papers abstract-only, which the paper discloses.
4. **Unsourced field "norms"** in papers ("AUC 0.8–0.9 expected").
5. **Lowest: fabricated references.** No unverified reference in any report.

---

## Appendix: commands run during this audit

```
python -m unittest discover -s tests                         # 207 tests, OK (13 skipped)
python scripts/sra.py sources                                 # 8/8 OK; only HF_TOKEN set
# CVSS/KEV regeneration in a scratch copy (original data read-only)
cvss-kev/.venv/Scripts/python extract.py   -> nvd_cvss.csv identical (cmp)
cvss-kev/.venv/Scripts/python analysis.py  -> results.json, tables.md, fig1-4 identical
# LLM memorisation analysis stage in a scratch copy
llm-memorisation/.venv/Scripts/python analyze.py -> results.json, tables.md, fig1-4 identical
```

The scratch copies are under the session scratchpad and are not part of the repository.
