# Quick start

The assistant prepares research decisions and you make them. Every project passes six gates, in order:

`scope → question → methodology → execution → results → manuscript`

Nothing is approved unless you say so. Each decision is saved in the project's `project.json`, so you can stop at any point and continue in a later session.

## Once, before first use

1. **Load the hook.** Restart Claude Code, or open `/hooks` once. It loads the hook in `.claude/settings.json`, which stops Claude from running a project's scripts outside `project run`.
2. **Check that the tests pass.** From the repository root, run:
   ```
   python -m unittest discover -s .claude/skills/scientific-research-assistant/tests -t .claude/skills/scientific-research-assistant/tests
   ```
3. **Install pandoc.** DOCX and PDF need pandoc. The PDF also needs Edge or Chrome, which Windows already has. The smallest setup is the `pypandoc_binary` wheel, which contains pandoc 3.9, in the repository's own `.venv`. That folder is gitignored. Run this once:
   ```
   python -m venv .venv                                  # only if .venv does not exist yet
   .venv\Scripts\python -m pip install pypandoc_binary==1.17
   ```
   - pandoc is then found automatically.
     - Search order: the `pandoc` setting in `research.json`, the `SRA_PANDOC` variable, PATH, `pypandoc` in the running Python, the root `.venv`, and finally another project's `.venv`.
     - It is found the same way whichever Python runs the toolkit.
   - A pandoc installed system-wide (`winget install JohnMacFarlane.Pandoc`) works too.
   - Without pandoc, drafts are written as Markdown only, and the final build refuses.

## Talking to Claude

You don't need to remember commands. Say what you want:

| You say | What happens |
| --- | --- |
| "I want to start a research project on X. I have a laptop and a week." | Claude creates the project and proposes the **scope** with 2–4 options, then stops. |
| "Approve", "option 2", "go with the matched design" | Claude records your decision in your own words, then prepares the next gate. |
| "Change X", "use 10 seeds instead" | Claude records a revision, writes a new version, and asks you again. |
| A question or a doubt ("isn't leakage a problem?") | Claude answers it. **Nothing is recorded:** a question is not an approval. |
| "Continue my project", "where were we?" | Claude reads the saved state and shows the pending decision again. |
| "Run the analysis" (once execution is approved) | Claude runs it through `project run`, which writes a log and a run manifest. |
| "Build a draft of the paper" | Claude writes `build/paper.draft.docx` and `.pdf`, marked DRAFT. No approval is needed. |
| "Check the paper" | Claude lists untraced numbers, unverified references and leftover TODOs. |
| "I want the final version" | Claude proposes the **manuscript** gate with the draft, and waits for you. |
| "Approve the manuscript" | Claude records your approval and builds `final/paper.docx`, `.pdf` and `.md`, plus `MANIFEST.json`. |

Any change after an approval (the plan, the data, the results, the paper text) makes that gate and every later one **stale**. Claude then shows you the new version and asks again.

## The commands behind it

Everything goes through the toolkit at `.claude/skills/scientific-research-assistant/scripts/sra.py`. Define a short alias first:

```
sra() { python .claude/skills/scientific-research-assistant/scripts/sra.py "$@"; }               # Git Bash
function sra { python .claude/skills/scientific-research-assistant/scripts/sra.py @args }         # PowerShell
```

| Task | Command |
| --- | --- |
| List projects, and show one project's state | `sra project list`, then `sra project status --project <dir>` |
| Show a pending decision | `sra checkpoint show <gate> --project <dir>` |
| Record your decision | `sra checkpoint approve <gate> --project <dir> --version N --said "<your words>"`; also `reject`, or `revise --request "…"` |
| Run the approved analysis | `sra project run --project <dir> --evidence results/results.json -- python analysis.py` |
| Start a paper | `sra manuscript init --dir papers/<name> --title "…"` |
| Add a verified reference | `sra manuscript cite --workspace <dir> --id <DOI or arXiv ID> --key <key>`; cite it in the text as `[@key]` |
| Check, draft, review, final | `sra manuscript check`, `sra manuscript build`, `sra manuscript review`, then `sra manuscript build --final`, each with `--workspace <dir>` |

In the paper, write numbers from the analysis as placeholders, for example `{{res:sens|.1%}}`. The build fills them in from `results/results.json`.

## One complete example

This example was run as written, from the repository root in Git Bash, on 2026-10-26. It takes about a minute: one network call fetches the reference. The data are synthetic.

When you run it yourself, each `approve` line is your decision. When you work through Claude, Claude shows you each proposal and waits for your reply.

```bash
sra() { python .claude/skills/scientific-research-assistant/scripts/sra.py "$@"; }
P=papers/quickstart

sra manuscript init --dir $P --title "Does a Score Threshold Find the Positives? A Walkthrough on Synthetic Data"

sra checkpoint propose scope --project $P --summary "Walkthrough of the paper pipeline on synthetic data; laptop; 10 minutes" \
  --option "Approve v1 (Recommended)" --option "Change the scope"
sra checkpoint approve scope --project $P --version 1 --said "approve"
sra checkpoint propose question --project $P --summary "What is the sensitivity of a score threshold on synthetic data?"
sra checkpoint approve question --project $P --version 1 --said "approve"

cat > $P/analysis.py <<'EOF'
"""Synthetic walkthrough: sensitivity of score >= 7.0 with a Wilson 95% CI."""
import json, math, random
from pathlib import Path

random.seed(20261026)
THRESHOLD = 7.0
positive = [random.random() < 0.05 for _ in range(5000)]
score = [random.gauss(7.8 if p else 6.0, 1.5) for p in positive]
n_pos = sum(positive)
tp = sum(1 for p, s in zip(positive, score) if p and s >= THRESHOLD)
sens = tp / n_pos
z = 1.959964
d = 1 + z * z / n_pos
mid = (sens + z * z / (2 * n_pos)) / d
half = z * math.sqrt(sens * (1 - sens) / n_pos + z * z / (4 * n_pos * n_pos)) / d
Path("results").mkdir(exist_ok=True)
Path("results/results.json").write_text(json.dumps(
    {"n": len(positive), "positives": n_pos, "threshold": THRESHOLD, "sens": sens, "ci": [mid - half, mid + half]},
    indent=2), encoding="utf-8")
print(f"sensitivity {sens:.3f}")
EOF
sed -i 's/^\*\*Type:\*\* TODO.*/**Type:** walkthrough on synthetic data./' $P/ANALYSIS_PLAN.md

sra checkpoint propose methodology --project $P --summary "Sensitivity of score >= 7.0 with a Wilson 95% CI" \
  --artifact $P/ANALYSIS_PLAN.md --artifact $P/analysis.py
sra checkpoint approve methodology --project $P --version 1 --said "approve"
sra checkpoint propose execution --project $P --summary "Run analysis.py once (under 1 s, no downloads)"
sra checkpoint approve execution --project $P --version 1 --said "go ahead"

sra project run --project $P --evidence results/results.json -- python analysis.py

sra checkpoint propose results --project $P --summary "Sensitivity on synthetic data" \
  --finding "Sensitivity of score >= 7.0 is about 0.7 [Wilson 95% CI]" --limitation "Synthetic data only" \
  --interpretation "The pipeline works; nothing is claimed about real data" --artifact $P/results/results.json
sra checkpoint approve results --project $P --version 1 --said "approve"

sra manuscript cite --workspace $P --id 10.1145/3436242 --key jacobs2021

cat > $P/paper.md <<'EOF'
# Abstract

We measure how many positives a score threshold of {{res:threshold|.1f}} finds in {{res:n|,}} synthetic cases. Its sensitivity is {{res:sens|.1%}} (95% CI {{res:ci[0]|.1%}} to {{res:ci[1]|.1%}}).

# Introduction

Exploit prediction asks which vulnerabilities will be attacked [@jacobs2021]. This walkthrough only exercises the pipeline.

# Methods

We drew {{res:n|,}} cases, of which {{res:positives|,}} were positive, and computed a Wilson interval for the sensitivity.

# Results

The threshold finds {{res:sens|.1%}} of the positives.

# Limitations

The data are synthetic and say nothing about real vulnerabilities.

# References

{{references}}
EOF

sra manuscript check --workspace $P          # 0 blocking issues
sra manuscript build --workspace $P          # build/paper.draft.docx and .pdf, marked DRAFT
sra manuscript review --workspace $P         # proposes manuscript v1 with every input attached
sra checkpoint approve manuscript --project $P --version 1 --said "approve the paper"
sra manuscript build --workspace $P --final  # final/paper.md, paper.docx, paper.pdf, MANIFEST.json
```

**Result:** "sensitivity is 67.7% (95% CI 61.4% to 73.5%)", with the reference rendered as Jacobs et al. (2021).

**To see the gates work:** change a word in `paper.md` and run the final build again. It refuses, because the approved manuscript no longer matches the files, and `project status` shows `manuscript STALE`.

**Clean up:** delete `papers/quickstart` when you are done.

## Where things are saved

| File | Holds |
| --- | --- |
| `project.json` | the gates, every version, your decisions in your own words, and the event log |
| `runs/run-*.log`, `runs/run-*.json` | each run's output, and its manifest: the command, times, Python and package versions, git revision, the approvals it ran under, and input and output hashes |
| `results/results.json` | every number the paper reports, written by the analysis |
| `refs/<key>.json` | the verified reference records |
| `build/` and `final/` | drafts, and the approved final files with `MANIFEST.json` |

## Limits to know

- **The hook is a guard rail, not a sandbox.** It catches Claude running a project script directly, but not every route: inline code, `make`, notebooks and your own terminal all get past it. The full list is in `references/checkpoints.md`.
- **`--said` holds what you said, as Claude typed it.** The record is only as honest as the one who writes it, which is why Claude must never approve for you.
- **The number check cannot trace derived values.** A difference or a complement of results ("14 points higher", "98.5% never") shows up as untraced. Compute it in the analysis, or allow it on purpose.
- **References are verified against the literature APIs** (Crossref, arXiv, PubMed). `cite` needs the network, and a DataCite DOI (Zenodo, SSRN) can only be confirmed to exist; its title is not checked.
