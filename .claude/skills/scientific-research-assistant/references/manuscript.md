# Paper workspaces and the manuscript build

A paper is written in Markdown, built to DOCX and PDF, and finalised only after the user approves the `manuscript` gate. The build rests on two rules:
- **No typed results.** Every number from the analysis comes from a results file through a placeholder.
- **No references from memory.** Every reference is a record that a literature API resolved and verified.

## Configuration

| File | Scope | Holds |
| --- | --- | --- |
| `research.json` (repository root, found by walking up; or `SRA_RESEARCH_CONFIG`) | every paper | `author`, `affiliation`, `date` (`auto` uses `date_format`), `lang`, `outputs`, `pandoc`, `browser`, `numbers` defaults |
| `paper.json` (workspace) | one paper | `title`, `subtitle`, `keywords`, `results` (namespace → file), `numbers.allow`, `css`, `reference_docx`, `project`, any override of the above |

`paper.json` wins over `research.json`, which wins over the built-in defaults. Nested `numbers` settings merge; lists replace. JSON is used because the toolkit needs no YAML parser; pandoc reads it as metadata directly.

## Workspace

```
sra.py manuscript init --dir papers/kev-epss --title "…"
```

This creates:
- `paper.json` and `paper.md`, the template with TODOs, which block the final build;
- `ANALYSIS_PLAN.md` and `analysis.py`, a seeded skeleton that writes `results/results.json`;
- `README.md` and `.gitignore`;
- `refs/`, `results/`, `figures/` and `data/`.

The workspace belongs to a project:
- the project it sits in, for example `research-projects/<name>/paper/`;
- or the one given with `--project`;
- otherwise a new six-gate `project.json` is created in the workspace.

## Numbers: placeholders and the untraced-number check

In `paper.md`, write `{{namespace:path|format}}`:

| Placeholder | Renders |
| --- | --- |
| `{{res:n\|,}}` | `180,432` |
| `{{sens\|.1%}}` (default namespace) | `89.2%` |
| `{{res:main.H3[">=7.0"].ppv\|.2%}}` | keys with dots or symbols in `["…"]` |
| `{{res:ci[0]\|.3f}}` | list index |
| `{{res:p\|p}}` | `< 0.001`, or 3 decimals |
| `{{res:p\|sci1}}` | `2.5 × 10⁻¹⁴⁴` |

Any Python format spec works. A missing key is a blocking issue, and the draft shows it as `**[?res:path]**`.

`manuscript check` also scans every number typed outside placeholders:
- **matched** (warning): it equals a result at the precision shown, directly or as a percentage. Prefer a placeholder, so the number updates with the analysis.
- **allowed:** it is listed in `numbers.allow` in `paper.json`. Use this for method constants that are not results, such as `0.05`, `95%` and thresholds.
- **ignored:** years (1900 to 2100), labels (`Table 3`, `Section 2`, `H1`), and integers up to `ignore_integers_upto` (default 10).
- **untraced** (blocking): no result explains it. Add it to the analysis, use a placeholder, or allow it if it is truly a constant.

Not scanned:
- code;
- placeholders and citations;
- URLs and DOIs;
- section numbers and list markers;
- the References section.

`manuscript check-numbers --paper X.md --results Y.json` runs the same scan read-only on any Markdown file, for example a finished paper.

## References and citations

```
sra.py manuscript cite --id 10.1145/2630069 --key allodi2014
sra.py manuscript verify-refs        # re-verify every record in refs/
```

- **What `cite` saves:** it resolves the identifier (DOI, arXiv ID, PMID, URL or exact title) through the toolkit's sources, verifies that the title matches, and saves `refs/<key>.json`: the record, its verification and the identifier.
- **In the text:** write `[@key]`, `[see @a, p. 4; @b]`, or narrative `@key`.
- **Rendering:** the build renders APA author-year: (Allodi & Massacci, 2014), Allodi and Massacci (2014), or Jacobs et al. (2021). Same-author, same-year works get a/b suffixes.
- **The reference list:** generated at `{{references}}`, sorted APA. If the marker is missing, a References section is appended.
- **Blocking:**
  - a cited key without a record;
  - a cited record whose verification is not `verified`.
- **Warnings:** `identifier_resolves` (the DOI exists but its title was not checked), and records that are never cited.

## Build

```
sra.py manuscript check                # blocking issues and warnings; exit 1 if any are blocking
sra.py manuscript build                # draft: build/paper.draft.md, .docx, .pdf (+ .check.json, .meta.json)
sra.py manuscript review               # check must pass; builds a draft and proposes the manuscript gate
sra.py manuscript build --final        # final/paper.md, .docx, .pdf + MANIFEST.json
```

**Pipeline:**
1. Placeholders and citations are resolved into `paper.md` in the output folder.
2. pandoc builds the DOCX, using `reference_docx` if set.
3. pandoc builds a self-contained HTML file with MathML and the print CSS (`templates/manuscript/paper_print.css`, or `css`).
4. Headless Edge or Chrome prints the HTML to PDF.

**Tools:**
- pandoc is found from `research.json`, then `SRA_PANDOC`, then PATH, then `pypandoc_binary` in the current Python, then the repository's own `.venv`, then another project's venv under the repository root (`*/.venv/Lib/site-packages/pypandoc/files/pandoc.exe`). Setup: `.venv\Scripts\python -m pip install pypandoc_binary==1.17`.
- If pandoc or a browser is missing, a draft still writes the Markdown and says what was skipped.

**Draft and final:**
- **Draft:** always allowed, and marked DRAFT at the top with the number of blocking issues. It never needs an approval.
- **Final:** refused unless all of the following hold:
  - the `manuscript` gate is approved and current, which implies every earlier gate is too;
  - every input on disk is covered by the approved version, with the same hash: `paper.json`, `paper.md`, results files, `refs/*.json`, figures, css, reference docx and `research.json`;
  - the check has no blocking issues.

  `final/MANIFEST.json` records the approval (version, the user's words, date), the input and output hashes, and the trace counts.

## The manuscript gate

1. Write the paper. Run `manuscript check` until nothing blocks. Fix numbers in the analysis, not in the text.
2. `manuscript review` builds the draft and proposes the gate. Every input is attached, and the check summary and warnings become items and risks.
3. Show the user the draft (`build/paper.draft.pdf`) and the proposal, and stop.
4. The user approves: `checkpoint approve manuscript --version N --said "…"`. Then run `manuscript build --final`.
5. Any later edit to the text, a result, a reference or the settings makes the approval stale. The final build then refuses until the user approves again.
6. When `final/` no longer matches, `manuscript check` (and every build) warns with `final_outdated`, but leaves the files alone. This covers changed or new sources, a manuscript approval that is no longer current, and edited or missing final files. Tell the user, and rebuild only after they approve the current manuscript.

Submitting or publishing the paper anywhere needs the approved manuscript and an explicit request from the user.
