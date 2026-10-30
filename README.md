# IKT Papers Writing Tool

A **Claude Code skill** that takes you from a vague interest ("I like NLP and graphs") to a finished research paper, with you making every decision along the way.

It searches the real literature, finds research gaps, checks whether an idea is new and whether a paper can be reproduced, helps you design and run the analysis, and builds the paper as Markdown, Word and PDF. Every reference it cites was retrieved and verified, and every number in the paper comes from your analysis code, not from typing.

This repository contains only the skill. Clone it, open it in Claude Code, and generate your own projects.

---

## What you can ask it

Open the folder in Claude Code and ask in plain language:

- *"I'm interested in NLP and graph theory. What could I work on?"*
- *"Is this idea new? &lt;describe it&gt;"*
- *"Find five computer vision papers I can reproduce on a consumer GPU."*
- *"Can I reproduce the experiments in arXiv 1809.05679?"*
- *"Design a study on X: hypothesis, datasets, baselines, statistics."*
- *"I want to write a paper on X. I have a laptop and two weeks."*
- *"Continue my project."* / *"Where were we?"*

The skill loads by itself when you ask a research question. You can also call it directly with `/scientific-research-assistant`.

**Tip:** state your constraints (time, hardware, experience) in the first message. Otherwise it assumes an undergraduate with Python, one 8 GB GPU and 8 weeks.

### What it does for you

| You want | What happens |
| --- | --- |
| **A topic or a research gap** | Searches OpenAlex, arXiv, Crossref, Semantic Scholar, PubMed, Hugging Face, GitHub and Zenodo; follows citation graphs; maps comparisons, negative results and critiques; proposes questions from the gaps |
| **To know if an idea is new** | Tries to *disprove* it: searches other wordings, checks who cited the closest papers, reads them in full |
| **A paper to reproduce** | Checks code, licence, dependencies, seeds, hardware, datasets and train/test leakage |
| **A study design** | Fixes the hypothesis, baselines, splits, metrics and statistics before anything runs |
| **A finished paper** | Runs your analysis, fills every number from `results.json`, verifies every reference, and builds `.md`, `.docx` and `.pdf` |

Each candidate question gets a verdict: `go`, `conditional_go` (with the checks still needed) or `no_go`. Rejected ideas stay in the report with the reason.

---

## You make the decisions

Every project passes six gates, in order:

```
scope → question → methodology → execution → results → manuscript
```

At each gate Claude proposes 2–4 options (recommended one first), explains the risks, and **stops until you answer**. Your reply is saved in your own words in the project's `project.json`, so you can close the session and continue later.

- A question or a doubt is not an approval. Only "approve", "option 2" and the like count.
- If anything changes after an approval (the plan, the data, the results, the paper text), that gate and every later one have to be approved again.
- Analyses run only through `sra project run`, which records the command, versions, inputs and output hashes. A hook in `.claude/settings.json` stops Claude from running project scripts any other way.
- The final paper can only be built after you approve the manuscript.

Searching, reading, drafting and checking never need approval.

---

## Setup

### 1. Requirements

- [Claude Code](https://claude.com/claude-code)
- Python 3.9 or newer (the toolkit uses the standard library only)
- For Word and PDF output: pandoc, plus Edge or Chrome for the PDF

### 2. Clone and open

```bash
git clone https://github.com/oxSTERBENxo/IKT_Papers_Writing_Tool.git
cd IKT_Papers_Writing_Tool
claude
```

The first time, restart Claude Code or open `/hooks` once so it loads the hook in `.claude/settings.json`.

### 3. Set your name

```bash
cp research.example.json research.json
```

Open `research.json` and fill in `"author"`. This is the author line on your papers. `research.json` is gitignored, so it stays on your machine.

### 4. Install pandoc (for `.docx` and `.pdf`)

The simplest way is the `pypandoc_binary` wheel in a local `.venv`, which the toolkit finds automatically:

```bash
python -m venv .venv
.venv/Scripts/python -m pip install pypandoc_binary==1.17     # Windows
.venv/bin/python -m pip install pypandoc_binary==1.17         # macOS / Linux
```

A system-wide pandoc on your PATH works too. Without pandoc, drafts come out as Markdown only and the final build refuses.

### 5. API keys (optional, recommended)

Everything works without keys, but the free limits run out quickly. All of these are free. Set them as environment variables:

| Variable | Why |
| --- | --- |
| `SEMANTIC_SCHOLAR_API_KEY` | Without it, most Semantic Scholar searches fail with HTTP 429 |
| `GITHUB_TOKEN` | 5,000 requests per hour instead of 60 |
| `OPENALEX_API_KEY` | Raises the small daily limit |
| `NCBI_API_KEY` | Faster PubMed searches |
| `HF_TOKEN` | Access to gated Hugging Face datasets |
| `SRA_CONTACT_EMAIL` | Polite identification for Crossref, OpenAlex and NCBI |

### 6. Check that it works

```bash
python .claude/skills/scientific-research-assistant/scripts/sra.py sources
python -m unittest discover -s .claude/skills/scientific-research-assistant/tests -t .claude/skills/scientific-research-assistant/tests
```

`sources` shows which literature APIs respond and which keys are set.

Searches are slow on purpose: arXiv allows one request every 3 seconds, so one search takes 1 to 4 minutes. Results are cached for a day.

### Using the skill in another project

Copy `.claude/skills/scientific-research-assistant/` into that project's `.claude/skills/` (or into `~/.claude/skills/` to use it everywhere). Also copy `.claude/settings.json` for the hook, and `CLAUDE.md` for the workspace rules.

---

## Writing a paper

You can do all of this by talking to Claude ("start a paper on X", "build a draft", "check the paper", "approve the manuscript"). Under the hood it uses these commands:

```bash
sra() { python .claude/skills/scientific-research-assistant/scripts/sra.py "$@"; }   # Git Bash / macOS / Linux

sra manuscript init --dir papers/my-paper --title "My Title"       # paper.md, ANALYSIS_PLAN.md, analysis.py, refs/, results/
sra manuscript cite --workspace papers/my-paper --id 10.1145/3436242 --key jacobs2021   # add a verified reference
sra project run --project papers/my-paper --evidence results/results.json -- python analysis.py
sra manuscript check --workspace papers/my-paper                   # untraced numbers, unverified references, TODOs
sra manuscript build --workspace papers/my-paper                   # build/paper.draft.docx and .pdf, marked DRAFT
sra manuscript review --workspace papers/my-paper                  # proposes the manuscript gate
sra manuscript build --workspace papers/my-paper --final           # after you approve: final/ + MANIFEST.json
```

In `paper.md`:

- Write numbers from the analysis as placeholders, for example `{{res:sens|.1%}}`. The build fills them in from `results/results.json`, and the check flags any number that doesn't trace back to it.
- Cite references as `[@jacobs2021]`. Only references added with `manuscript cite` are allowed.

For a complete example you can run in about a minute, see [`QUICKSTART.md`](.claude/skills/scientific-research-assistant/QUICKSTART.md).

### Where your work is saved

| File | Holds |
| --- | --- |
| `project.json` | The gates, every version, your decisions in your own words, and the event log |
| `runs/run-*.json`, `runs/run-*.log` | Each analysis run: command, times, Python and package versions, git revision, approvals, input and output hashes |
| `results/results.json` | Every number the paper reports, written by the analysis |
| `refs/<key>.json` | Verified reference records |
| `build/`, `final/` | Drafts, and the approved final paper with `MANIFEST.json` |
| `research-reports/` | Opportunity, reproducibility and proposal reports (Markdown, optional LaTeX/BibTeX, JSON) |

Your projects, papers and reports (`papers/`, `research-projects/`, `research-reports/`) are gitignored, so they stay local unless you choose to commit them.

---

## Why you can trust the output

- **Only retrieved papers are cited.** References are never written from memory, and every one is verified against Crossref, arXiv or PubMed.
- **"Nothing found" is not proof of novelty.** Novelty confidence is capped at `medium`.
- **Claims are labelled** as verified **[V]**, estimate **[E]** or speculative **[S]**.
- **A GitHub repo is not a reproduction.** Only experiments that actually ran are called "reproduced".
- **Statistics come with effect sizes and confidence intervals**, not p-values alone.
- **The validators refuse** a report with unchecked references or inflated confidence, and a final paper with untraced numbers.

---

## Repository layout

```
.claude/
  settings.json                      hook that guards project runs
  skills/scientific-research-assistant/
    SKILL.md                         instructions Claude follows
    QUICKSTART.md                    step-by-step walkthrough
    README.md                        skill details
    references/                      workflow rules (gates, manuscripts, novelty, reproducibility)
    scripts/sra.py, scripts/sra/     the Python toolkit
    templates/                       report and paper templates
    examples/nlp-graph-theory/       a complete example run
    evals/, tests/                   retrieval evaluations and unit tests
CLAUDE.md                            workspace rules Claude loads in this folder
SKILL_GUIDE.md                       every toolkit command, by hand
research.example.json                paper defaults; copy to research.json
docs/                                design notes and release history
```

---

## Known limitations

- Similarity scoring is word-based, so it can miss paraphrased work. Claude reads the closest papers itself to compensate.
- Reproducibility checks read READMEs and file names, not the code.
- Dataset search covers only Hugging Face and Zenodo.
- English only. Coverage outside computer science and biomedicine is thinner.
- The run hook is a guard rail, not a sandbox: your own terminal, notebooks or inline code get past it.
- Novelty is never certain. Do a quick Google Scholar search yourself before committing to an idea.

---

**Author:** Eva Knezhevikj
