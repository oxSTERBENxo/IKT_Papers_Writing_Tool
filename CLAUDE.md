# Research workspace rules

This repository holds the `scientific-research-assistant` skill (`.claude/skills/scientific-research-assistant/`) and the research projects and papers you make with it. The skill's `SKILL.md` has the detailed workflow; these are the rules that apply to every project here.

The toolkit is `python .claude/skills/scientific-research-assistant/scripts/sra.py <command>`, shown below as `sra`. New here? Read `.claude/skills/scientific-research-assistant/QUICKSTART.md`.

## Decisions belong to the user

- Every research project runs through six gates: `scope → question → methodology → execution → results → manuscript`, in `project.json` (protocol: `references/checkpoints.md` in the skill).
- **Never approve, reject or mark not applicable for the user.** Propose, show the decision with its alternatives and risks, and stop the turn. Record the reply with the user's own words in `--said`. A question, a doubt or "thanks" is not an approval.
- **Offer real choices.** At scope, question, methodology and other real forks, give 2–4 concrete options with the recommended one first (`AskUserQuestion` in Claude Code), and save them with `checkpoint propose --option` so "option 2" can be resolved in a later session.
- **An approval is for one version.** After a material change (methodology, data, plan file, results, paper text), the affected gate and every later one need the user again.
- **`execution` may be marked not applicable** only with a reason and the user's agreement, never silently. Anything that computes still needs an approved execution.
- **Run project analyses only through `sra project run --evidence <outputs> [--input <data>] -- <command>`.** Authorization (the approval) and completion (the recorded run) are separate; results need both. Each run writes a manifest (`runs/run-*.json`). A hook blocks direct runs of scripts inside project folders; it is a guard rail, not a sandbox, so never route around it.
- **Free of approvals:** reading, searches, drafting, drafts of papers (`manuscript build`), and every check or validation.

## Session start

If the user continues earlier research ("continue", "where were we", "I approve…"), run `sra project list` and `sra project status --project <dir>` first, and re-present pending decisions with `sra checkpoint show`.

## Papers

- **Workspace:** `sra manuscript init --dir <folder> --title "…"` creates `paper.json`, `paper.md`, `ANALYSIS_PLAN.md`, `analysis.py`, `refs/`, `results/` and `figures/`. It also creates the project, unless the folder already sits inside one.
- **Author line:** comes from `research.json` (copy `research.example.json` and fill in `author`), or from each paper's `paper.json`.
- **Deliverables:** `.md`, `.docx` and `.pdf`.
  - Drafts: `sra manuscript build` writes `build/paper.draft.*`, marked DRAFT.
  - Final: `sra manuscript review` proposes the manuscript gate. After the user approves, `sra manuscript build --final` writes `final/` with a `MANIFEST.json`.
  - Submitting or publishing anything needs the approved manuscript, and the user asks for it explicitly.
- **Numbers:**
  - Every number from an analysis is written to `results/results.json` by code and appears in the text as a placeholder, `{{res:path|format}}`.
  - Method constants that are not results (alpha, thresholds) go in `paper.json` → `numbers.allow`.
  - `sra manuscript check` lists every untraced number; the final build refuses while any remain.
- **References:**
  - Cite only records added with `sra manuscript cite --id <DOI/arXiv/PMID> --key <key>`, which resolve and verify through the literature APIs.
  - Write `[@key]` or `@key` in the text. Never type a reference from memory.
- **Statistics:** real tests on real data; report effect sizes and confidence intervals, not p-values alone. Write a replication up as a replication.

## Do not change finished work

The skill's `examples/` are finished reports, and so is any paper with an approved `final/` folder. Read them; do not edit, rebuild or "fix" them unless the user asks. Read-only audits are fine, for example `sra manuscript check-numbers --paper <dir>/paper.md --results <dir>/results/results.json`.

Personal rules (your author name, your own finished projects) go in `CLAUDE.local.md`, which is gitignored.

## Environment

- The skill's Python core uses the standard library only.
- pandoc comes from `pypandoc_binary` in the root `.venv` (`.venv\Scripts\python -m pip install pypandoc_binary==1.17`; gitignored). It is found automatically, after `research.json`, `SRA_PANDOC` and PATH. PDFs print through Edge, headless.
- If `manuscript check` warns `final_outdated`, the files in `final/` no longer match the approved sources. Tell the user; do not rebuild or delete them without their approval.
- Local-first: free APIs only, no paid compute.
- Ask before downloads over about 1 GB, training, or anything irreversible.
- **Git:** do not commit or push without asking.
