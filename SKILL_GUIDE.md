# Scientific Research Assistant: Summary and How to Use It

The skill lives in `.claude/skills/scientific-research-assistant/`. This file is a short guide to it. For full details, see the skill's own `SKILL.md` and `README.md`.

## What it does

It takes you from a vague interest ("I like NLP and graphs") to a research project you can finish. Every claim in the result traces back to a paper or source it actually retrieved. Reproducing, replicating or extending published work counts as a good outcome. You don't have to invent a new algorithm.

It has two parts:

1. **Instructions for Claude** (`SKILL.md` and `references/`), which set the workflow and the rules.
2. **A Python toolkit** (`scripts/sra.py`, standard library only, Python 3.9+) that searches, checks, scores and writes reports.

### The three workflows

| You want | Workflow | What happens |
| --- | --- | --- |
| A topic, a research gap, or to know "is this idea new?" | **A. Literature-first discovery** | Maps the field (comparisons, negative results, critiques, surveys), builds an evidence ledger, derives questions from it, then tries to disprove each one's novelty |
| Papers to reproduce, or "can I reproduce paper X?" | **B. Reproducibility** | Checks code, licence, dependencies, seeds, hardware, datasets and data leakage, then reads the full text for anything missing |
| A method, hypothesis, datasets or a full proposal | **C. Project design** | Falsifiable hypothesis, simplest valid method, baselines, splits, metrics and statistics fixed before any experiment runs |

Requests often chain together. For example, "a topic I can finish in a month" runs A, then scoring, then C for the winning idea.

### Where it searches

OpenAlex, arXiv, Crossref, Semantic Scholar, PubMed, Hugging Face, GitHub and Zenodo. It also follows citation graphs and reads open-access full texts.

### What makes it trustworthy

- **It cites only what it retrieved.** It never writes a reference from memory.
- **"Nothing found" isn't proof of novelty.** Novelty confidence is capped at `medium`.
- **It attacks every idea before proposing it.** It searches other wordings, follows citations and reads the closest papers in full. Rejected ideas still appear in the report.
- **It checks for common flaws:** train/test leakage, weak baselines and evaluation problems.
- **Every shortlisted question gets a verdict:** `go`, `conditional_go` (with the checks still owed) or `no_go`.
- **Claims are labelled** verified [V], estimate [E] or speculative [S].
- **A GitHub repository doesn't count as a reproduction.** Only experiments that were actually run are called "reproduced".
- **The report validator refuses to render** when references are unchecked, confidence is inflated, or a `go` was given without reading the closest work.

### Output

Reports are saved to `research-reports/` as Markdown, with optional LaTeX and BibTeX, plus the underlying JSON. There are four report types: literature review, opportunity report, reproducibility report and research proposal. In the chat, Claude also gives you the verdicts, the top recommendation, what was rejected and why, and what couldn't be verified.

## How to use it properly

### 1. Just ask in plain language

The skill loads automatically in this project. You don't need to memorise any commands. Examples:

- "I'm interested in NLP and graph theory. Find underexplored research opportunities."
- "Find five computer vision papers I can reproduce on a consumer GPU."
- "Can I reproduce the experiments in arXiv 1809.05679?"
- "I want a machine learning topic I can complete in one month."
- "Find a simple extension to this paper: <link or DOI>."
- "Compare these three research ideas and recommend the most feasible."
- "Is this idea new? <describe it>"

You can also force it to load by typing `/scientific-research-assistant`.

### 2. State your constraints up front

The only thing it needs is your **field or paper**. For everything else it uses the defaults below and lists them in the report. If your situation is different, say so in your first message. That saves a round of questions and gives you a better-fitted answer.

| Constraint | Default |
| --- | --- |
| Experience | undergraduate, comfortable with Python |
| Hardware | one consumer GPU with 8 GB VRAM, or a free cloud notebook |
| Time budget | 8 weeks |
| Language | Python |
| Difficulty | moderate |
| Research mode | any (reproduction, replication, extension or original) |
| Venue | none |

Example: *"Field: fake news detection with GNNs. I have 6 weeks, only a laptop CPU, and I'd prefer a replication for my 6th-semester IKT project."*

### 3. Set API keys (strongly recommended)

Everything works without keys, but the free limits run out quickly. Without a key, OpenAlex allows about 100 requests per day and GitHub 60 per hour, which is only enough for a few full runs. Set these keys as environment variables (they're all free):

| Variable | Why |
| --- | --- |
| `OPENALEX_API_KEY` | lifts the small daily budget |
| `GITHUB_TOKEN` | 5,000 requests per hour instead of 60 |
| `SEMANTIC_SCHOLAR_API_KEY` | without it, searches mostly fail with HTTP 429 |
| `NCBI_API_KEY` | faster PubMed (biomedical topics) |
| `HF_TOKEN` | gated Hugging Face datasets |
| `SRA_CONTACT_EMAIL` | polite identification for Crossref, OpenAlex and NCBI |

To set a key permanently on Windows, run this in PowerShell, then restart the terminal and Claude Code:

```powershell
setx GITHUB_TOKEN "your_token_here"
```

Check which sources respond:

```
python .claude/skills/scientific-research-assistant/scripts/sra.py sources
```

### 4. Be patient

arXiv allows one request every 3 seconds, so a single search takes 1 to 4 minutes. A full discovery workflow can take much longer. Results are cached for a day, so repeated searches are faster.

### 5. Read the output critically

- **Abstract-only summaries are labelled as such.** Treat those claims as weaker.
- **Novelty is never certain.** Even "medium" confidence means "we searched and found nothing close", not "nobody has done this". The skill's own tests show it still misses some closely related papers. Do a quick Google Scholar search yourself before committing to an idea.
- **Act on `conditional_go`.** It lists the checks still owed. Do them before you start.
- **Check the search log.** If a source was down or rate-limited, it says so there. Coverage was lower than usual for that run.

### 6. Things it won't do without asking

It won't download datasets over about 1 GB, start model training, or use paid compute unless you explicitly say so. Assessing a paper never requires any of these.

## Obsidian notes

Your vault is `D:\Obsidian\6ti Semestar`, and the research lives in `Scientific Research/`:
- `Research Dashboard.md`: every project, with its status.
- `Projects/`: one note per project. Each starts with an **At a glance** box: the main question, the data, the hypotheses or questions with their go / no-go decisions, and the conclusion.
- `Papers/`: one note per cited paper, linked to every project that uses it.

How the notes get there:
- **Research reports** are exported automatically by the skill. To re-export after a change, ask Claude to "export the reports to Obsidian".
- **Experiments we actually ran** (like cvss-kev) get a hand-written project note. It has the same box, plus the steps, results, figures, logs and file paths.
- **Your own text is safe in both.** In exported notes, write above or below the `%% sra:begin %% … %% sra:end %%` part, because only that part is replaced on re-export. Hand-written notes are never touched by the exporter.

To export every new report automatically, set these once (in PowerShell):

```powershell
setx SRA_OBSIDIAN_VAULT "D:\Obsidian\6ti Semestar"
setx SRA_OBSIDIAN_AUTO 1
```

## Using the toolkit by hand (optional)

Every command prints a short summary, and `--out FILE` saves the full JSON. Run `--help` on any command for details.

```bash
S=.claude/skills/scientific-research-assistant/scripts/sra.py
python $S sources                                   # which sources work
python $S search --concept "graph neural network|GNN" --concept "text classification" \
                 --strategies keyword,surveys,recent --from-year 2018 --out search.json
python $S map --concept "graph neural network|GNN" --concept "fake news detection" \
              --design "MLP baseline on the same features" --seed 2104.12259 --out map.json
python $S paper --id 1809.05679 --abstract         # resolve one paper
python $S related --id 1809.05679                  # references and citing works
python $S challenge --claim "..." --query "..." --query "..." --query "..." --query "..." \
                    --design "..." --seed 2104.12259 --out challenge.json
python $S fulltext --id 2104.12259 --out ft.json   # sections, seeds, splits, limitations
python $S repro --id 2109.03777 --out repro.json   # reproducibility pre-check
python $S dataset-search --query "fake news" --limit 10
python $S dataset-verify masakhane/masakhanews
python $S leakage --input items.jsonl --entities-field users --text-field text
python $S score --input scoring.json --out ranking.json
python $S verify-refs --input report.json
python $S report --input report.json --ranking ranking.json --format md,latex
```

Note: `--concept` takes synonyms separated by `|`, and every combination across concepts gets searched. Strategies are `keyword`, `recent`, `foundational`, `limitations`, `surveys` and `reproducibility`. Domains are `cs`, `biomed` and `general`.

## Known limitations

- Similarity scoring is word-based, so it misses paraphrases. Claude has to read the closest papers itself.
- Reproducibility checks read READMEs and file names, not the code. A seed set inside a script may show up as "not found".
- Dataset search covers only Hugging Face and Zenodo (not Kaggle, UCI or OpenML).
- It searches in English only. Coverage outside computer science and biomedicine is thinner.
- Feasibility scores are Claude's judgement. The tool enforces evidence and blockers but can't check that a score is reasonable.

## See a full example

`.claude/skills/scientific-research-assistant/examples/nlp-graph-theory/` contains a complete run on "NLP and graph theory": an opportunity report, a reproducibility report, a research proposal, and every intermediate file.
