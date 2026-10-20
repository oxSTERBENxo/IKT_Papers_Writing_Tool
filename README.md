# IKT Papers Writing Tool

A **Claude Code skill** that helps students go from a vague interest ("I like NLP and graphs") to a research project they can actually finish. Every claim in the result is backed by a paper the tool actually found and checked.

This repository has the skill itself, plus three research projects that were planned and written with it.

---

## What the skill does

The skill is called **Scientific Research Assistant** and lives in [`.claude/skills/scientific-research-assistant/`](.claude/skills/scientific-research-assistant/). When you open this folder in Claude Code and ask a research question in plain language, the skill loads by itself and:

1. **Searches the literature.** It queries OpenAlex, arXiv, Crossref, Semantic Scholar, PubMed, Hugging Face, GitHub and Zenodo, follows citation graphs, and reads open-access full texts.
2. **Builds an evidence ledger** of what has been done: comparisons, negative results, critiques and surveys.
3. **Proposes research questions** that come from gaps in that evidence.
4. **Tries to disprove each idea before suggesting it.** It searches other wordings, checks who cited the closest papers, and reads them in full. Rejected ideas still appear in the report, with the reason.
5. **Checks feasibility:** code availability, licences, datasets, hardware, time, and common flaws like train/test leakage or weak baselines.
6. **Gives each question a verdict:** `go`, `conditional_go` (with the checks still needed) or `no_go`.
7. **Writes a report** in Markdown, with optional LaTeX and BibTeX.

Reproducing, replicating or extending a published paper counts as a good result. You don't have to invent a new algorithm.

### Three workflows

| You want | Workflow | What happens |
| --- | --- | --- |
| A topic, a research gap, or "is this idea new?" | **A. Literature-first discovery** | Maps the field, finds gaps, then attacks each idea's novelty |
| Papers to reproduce, or "can I reproduce paper X?" | **B. Reproducibility check** | Checks code, licence, dependencies, seeds, hardware, datasets and leakage |
| A method, hypothesis, datasets or a full proposal | **C. Project design** | Fixes the hypothesis, baselines, splits, metrics and statistics before any experiment runs |

The workflows chain. For example, "a topic I can finish in a month" runs A, then scores the ideas, then runs C for the best one.

### Why you can trust the output

- **It only cites papers it retrieved.** It never writes a reference from memory, and every reference is verified.
- **"Nothing found" is not proof of novelty.** Novelty confidence is capped at `medium`.
- **Claims are labelled** as verified **[V]**, estimate **[E]** or speculative **[S]**.
- **A GitHub repo is not a reproduction.** Only experiments that were actually run are called "reproduced".
- **The report validator refuses to render** if references are unchecked, confidence is inflated, or a `go` was given without reading the closest work.

---

## Quick start

1. Install [Claude Code](https://claude.com/claude-code) and Python 3.9+.
2. Clone this repository and open the folder in Claude Code:
   ```bash
   git clone https://github.com/oxSTERBENxo/IKT_Papers_Writing_Tool.git
   cd IKT_Papers_Writing_Tool
   claude
   ```
3. Ask in plain language, for example:
   - *"I'm interested in NLP and graph theory. Find underexplored research opportunities."*
   - *"Find five computer vision papers I can reproduce on a consumer GPU."*
   - *"Can I reproduce the experiments in arXiv 1809.05679?"*
   - *"Is this idea new? &lt;describe it&gt;"*

   You can also load it directly with `/scientific-research-assistant`.

**Tip:** say your constraints in the first message (time, hardware, experience). Otherwise it assumes an undergraduate with Python, one 8 GB GPU and 8 weeks.

### API keys (optional but recommended)

Everything works without keys, but the free limits run out quickly. These keys are all free. Set them as environment variables:

| Variable | Why |
| --- | --- |
| `OPENALEX_API_KEY` | Raises the small daily limit |
| `GITHUB_TOKEN` | 5,000 requests per hour instead of 60 |
| `SEMANTIC_SCHOLAR_API_KEY` | Without it, most searches fail with HTTP 429 |
| `NCBI_API_KEY` | Faster PubMed searches |
| `HF_TOKEN` | Access to gated Hugging Face datasets |
| `SRA_CONTACT_EMAIL` | Polite identification for Crossref, OpenAlex and NCBI |

Check which sources respond:

```bash
python .claude/skills/scientific-research-assistant/scripts/sra.py sources
```

Searches are slow on purpose: arXiv allows one request every 3 seconds, so one search takes 1 to 4 minutes. Results are cached for a day.

---

## How it is built

| Part | Where | What it is |
| --- | --- | --- |
| Instructions for Claude | `SKILL.md`, `references/` | The workflow and the rules Claude follows |
| Python toolkit | `scripts/sra.py`, `scripts/sra/` | Search, citation graphs, full-text reading, novelty checks, leakage checks, scoring, reference verification and report rendering. Standard library only |
| Report templates | `templates/` | Markdown and LaTeX layouts |
| Evaluations | `evals/` | Tests of how well it finds known related papers, including blind fixtures and negative controls |
| Example run | `examples/nlp-graph-theory/` | A complete run: opportunity report, reproducibility report and research proposal |

The toolkit can also be used by hand. See [`SKILL_GUIDE.md`](SKILL_GUIDE.md) for every command.

---

## Projects made with the skill

| Folder | What it is |
| --- | --- |
| [`cvss-kev/`](cvss-kev/) | Paper: does a vulnerability's CVSS score predict real-world exploitation (CISA KEV)? A replication of Allodi & Massacci (2014) |
| [`llm-memorisation/`](llm-memorisation/) | Paper: do newer open LLMs show memorisation on the arXiv citation graph (ogbn-arxiv)? A replication and extension of Huang et al. (arXiv:2309.16595) |
| [`starry-sky/`](starry-sky/) | Web app: students ask anonymous questions during a lecture, and similar questions group into one "star". It also collects data for a research proposal |
| [`research-reports/`](research-reports/) | Reports produced by the skill (opportunity reports, audits, the Starry Sky proposal) |
| `work/` | Intermediate files from the runs: searches, novelty challenges, reproducibility checks, retrieval evaluations |

Each paper folder has `paper.md`, `paper.docx` and `paper.pdf`, an `ANALYSIS_PLAN.md` written before the analysis, and the scripts that compute every number.

**Datasets are not in the repo** because they are too large. Each project's README or scripts show where to download them.

---

## Known limitations

- Similarity scoring is word-based, so it can miss paraphrased work. Claude has to read the closest papers itself.
- Reproducibility checks read READMEs and file names, not the code.
- Dataset search covers only Hugging Face and Zenodo.
- English only. Coverage outside computer science and biomedicine is thinner.
- Novelty is never certain. Do a quick Google Scholar search yourself before committing to an idea.

---

**Author:** Eva Knezhevikj
