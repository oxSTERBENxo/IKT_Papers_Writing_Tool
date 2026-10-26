# Human decision checkpoints

The user makes the research decisions; Claude prepares them. A project keeps those decisions in one file, `project.json`. Any later session can see what was approved, what is waiting and what changed.

## When to use a project

Start a project when the user is going to *do* research over more than one sitting: choosing a thesis topic, planning a reproduction, designing and running a study. Skip it for one-off questions ("is this idea new?", "can this paper be reproduced?"). If the user later decides to pursue the answer, start a project then and attach the report.

```
python "<skill-dir>/scripts/sra.py" project init --name "BoW vs text graphs" --question "<the user's words>"
```

This creates `research-projects/<slug>/project.json` in the working folder (`--dir` sets the folder). Keep the project's working files (search JSON, reports, plan) inside that folder. Pass `--project <folder>` to `checkpoint`, `project status` and `report`, or set `SRA_PROJECT`.

## The gates

| Gate | The user decides | Propose it after | Attach (`--artifact`) | Unlocks |
| --- | --- | --- | --- | --- |
| `scope` | field, constraints, research mode, the defaults assumed | the constraints step | none | literature searches, `map`, `challenge`; `report` of any discovery or reproducibility type |
| `question` | which question to pursue: its type, decision, closest work, what is still unchecked | discovery or reproducibility assessment, report rendered | the opportunity or reproducibility report (`.md` and `.json`) | project design; `report` of a `research_proposal` |
| `methodology` | hypothesis, falsification rule, data and splits, baselines, metrics, seeds, statistical test | project design | the research proposal and/or `ANALYSIS_PLAN.md` | planning the runs |
| `execution` | what is downloaded and run, hardware, time, cost | methodology approved | a run plan or script, if one exists | `project run`: downloads over ~1 GB, training, paid compute, any experiment |
| `results` | the findings, their limitations and interpretation, deviations from the plan | a successful recorded run (or execution marked not applicable) | `results.json`, the deviations log | writing the paper for submission |
| `manuscript` | that this exact paper may be finalised and submitted | `manuscript review` (the check passes, a draft is built) | done by `manuscript review`: every input file | `manuscript build --final`, submission, publication |

A project can use fewer gates (`project init --gates scope,question` for a pure topic search). Gates stay in this order. A gate cannot be proposed until every earlier gate is approved (or, for `execution`, marked not applicable).

Projects created before the manuscript gate existed gain it automatically when loaded, as long as they used all five earlier gates.

### Execution: authorization and completion

An approved `execution` is an **authorization**, not a result:
- `project run --project P --evidence results/results.json -- python analysis.py` refuses unless `methodology` and `execution` are approved and current. It then runs the command in the project folder, logs the output to `runs/`, and records a **completion** with the exit code and output hashes.
- `results` cannot be proposed until a successful completion exists under the *current* authorization.
- **When a completion stops counting:** a re-authorized execution, for example after a methodology change, needs a new run. Editing the run's output files also cancels the completion.
- **A new successful run** makes an approved `results` stale.
- **The hook:** the PreToolUse hook in `.claude/settings.json` blocks running a project's scripts directly, so runs go through `project run`.

### Execution not applicable

Some projects run nothing, for example a pure literature review or a re-analysis of published tables. With the user's agreement, record it as:

```
sra.py checkpoint not-applicable execution --project P --reason "re-analysis of the published tables only" --said "<their words>"
```

- The reason and the user's words are required, and the record is shown in `project status`.
- It satisfies the gate order, so `results` may follow.
- It authorizes nothing: `checkpoint require execution` and `project run` stay blocked. If computation turns out to be needed, propose an execution plan; that reopens the gate and makes later approvals stale.
- Only `execution` may be marked not applicable.

### Results: review what the numbers mean

A results proposal needs findings, limitations and an interpretation, plus the files they come from:

```
sra.py checkpoint propose results --project P --summary "…"   --finding "Sensitivity of score >= 7.0 is 89.2% [87.2, 90.9]" --finding "…"   --limitation "KEV under-counts exploitation" --interpretation "CVSS measures severity, not exploitation risk"   --artifact results/results.json --artifact ANALYSIS_PLAN.md
```

Present the findings with their uncertainty, the deviations from the plan, and the limitations. Do not offer only the files.

## The loop at each gate

1. **Prepare.** Do the work the gate needs, and write the files it rests on.
2. **Propose.** Record the proposal:
   ```
   sra.py checkpoint propose methodology --project P \
     --summary "Compare a BoW MLP with TokenGraph under one protocol, 5 seeds" \
     --item "Hypothesis: MLP within 1 point of the graph model on each dataset" \
     --item "Test: 95% bootstrap CI of the accuracy difference; supported if below +1 point" \
     --risk "Abdalla et al. 2023 not read in full: novelty confidence stays low" \
     --recommendation "Approve: it is the simplest design that answers the question" \
     --artifact research-projects/bow/research_proposal.md
   ```
   - One `--item` per decision the user is agreeing to.
   - One `--risk` per open problem, unchecked item or weak point. Do not leave out the weak points to make approval easier.
3. **Present and stop.** Show the user the proposal in the format below, then end the turn. Do not continue past the gate in the same turn, and do not start the next gate's work.
4. **Record the reply.** Use the user's own words in `--said`:

| The user says something like | Run |
| --- | --- |
| "yes", "approved", "go ahead", "looks good, proceed" | `checkpoint approve <gate> --version N --said "<their words>"` |
| "no", "drop it", "not this one" | `checkpoint reject <gate> --said "<their words>" --reason "<why, if they said>"` |
| "change X", "use 10 seeds", "add macro-F1", "yes but …" (approval with a change) | `checkpoint revise <gate> --said "<their words>" --request "<what to change>"`, then make the change, then `propose` the new version with `--addresses` |
| a question, a doubt or an unclear reply ("hmm, what about leakage?") | nothing: answer them and ask again. **This is not an approval.** |

Rules:
- **Never approve on the user's behalf.** Only approve after an explicit approval from the user, in this conversation, for the version you showed them.
- **Approve the version they saw.** `--version` must match the version you presented.
  - The command refuses if the gate has moved on since then.
  - It also refuses if an attached file changed since the proposal. In that case, propose again and show the user the new version.
- **Silence, "thanks" or a new topic is not an approval.**

## Presentation format

Keep it short enough to read in a minute. Show the version number so the reply can be tied to it.

**Offer real choices.** At `scope`, `question` and `methodology`, and wherever the user faces a real fork (which dataset, which test, which question from a shortlist), give **2 to 4 concrete options** with their trade-offs, your recommendation first:
- In Claude Code, use the `AskUserQuestion` tool. Mark the recommended option "(Recommended)". The user can always pick "Other" and type a change.
- Without that tool, list the options as numbered lines under the proposal.
- Save the options with the proposal: `checkpoint propose … --option "Approve v1 (Recommended)" --option "…"`. `checkpoint show` lists them numbered, so a reply such as "option 2" in a later session can be resolved from the record, not from memory.
- Record the chosen option's label in `--said` (for example `--said "Option 2: matched case-control"`). If the user picks an option that differs from the proposed version, record `revise`, propose the chosen design as a new version, and ask once more for that version.
- Approvals of `execution`, `results` and `manuscript` are usually yes/no/change: offer "Approve vN", "Change something" and "Reject".

```
**Decision needed: methodology (v2)**
<summary, one or two sentences>

- <item>
- <item>

**Open risks:** <risk>; <risk>
**Recommendation:** <what you recommend and why>
Files: research_proposal.md

Reply "approve", "reject", or tell me what to change.
```

## Changes after approval

An approval holds only for the exact content approved. It stops counting when:
- **A new version is proposed** for that gate (a changed methodology, dataset or question). The gate then waits for the user again.
- **An attached file changes on disk**, for example an edited `ANALYSIS_PLAN.md`. The gate becomes `stale`.
  - The old version cannot be re-approved; propose the edited content as a new version.
  - Restoring the exact approved file makes the approval count again.
- **An earlier gate changes.** Every later gate becomes `stale`.
  - Ask the user whether the later decision still holds.
  - If it does, re-approve the same version; if not, propose a new one.

`checkpoint propose` prints which approvals a change invalidated. Tell the user. Never quietly change an approved methodology. A deviation found during the runs becomes a new `methodology` version, and the user approves it before the runs continue.

## Enforcement points

Checks in code:
- **`project run`:** methodology and execution must be approved and current.
- **`manuscript build --final`:** the manuscript gate must be approved and current and cover exactly the inputs on disk, and the check must pass.
- **`report --project P`:** a report is rendered only when the gates its type needs are approved: `scope` for discovery and reproducibility reports, and `scope` plus `question` for a research proposal. `report --check` (validation) is never blocked.
- **`checkpoint require <gates…>`:** exits 3 and prints `BLOCKED` unless every listed gate is approved and current. Use it before any other action that needs a gate, for example `require scope` before the literature work.

Checks at the shell:
- **The PreToolUse hook:** blocks direct runs of scripts inside a project folder.

### What the hook does not catch

The hook is a guard rail against Claude running a project script by accident, not a sandbox. It only inspects Claude's own Bash and PowerShell tool calls, and only command lines where an interpreter (`python`, `py`, `Rscript`, `node`, `bash`, …) or the script itself is named with a file that exists inside a folder with a `project.json`. It does not catch:
- code passed inline or through another program: `python -c "exec(open('analysis.py').read())"`, `python -m package`, `make`, `npm run`, a notebook kernel, a script that starts another script;
- a copy of the script placed outside the project folder, or a script written and run in one step;
- commands the user types in their own terminal, or other tools and editors;
- anything while the hook is not loaded: it is read when Claude Code starts, so after creating or changing `.claude/settings.json`, open `/hooks` once or restart Claude Code;
- anything when the hook itself fails (no `python` on PATH, a crash, a timeout): it **fails open**, so ordinary work never stops.

The rule that matters is the one in `SKILL.md`: run analyses only through `project run`. The hook catches the common slip; the recorded runs and the approvals are the evidence.

## Run manifest

Each `project run` writes `runs/run-<stamp>.log` and `runs/run-<stamp>.json`. The manifest records:
- the command, working folder, exit code, start and finish time (UTC) and duration;
- the approvals it ran under: state, version, who approved and when, and the decision hash for every gate up to `execution`;
- the environment: OS, the Python version and executable of the interpreter the command used, and the version of every installed package in it (other interpreters are recorded by name only);
- the git revision, and whether the project folder had uncommitted changes;
- hashes of the inputs (the approved methodology files, plus any `--input` data files) and of the outputs (`--evidence`).

The completion record in `project.json` stores the manifest's path and SHA-256, so a later edit to the manifest is detectable. It does not snapshot data or packages: re-creating the environment is still up to the project's `requirements.txt` or lock file.

Never gated: searches, reading, drafting, `manuscript build` drafts, and all checks.

## Resuming in a new session

When the user returns to research ("continue my project", "where was I?", "I approve the plan"), resume before doing anything else:

1. `project list` finds projects under the working folder.
2. `project status --project P` shows each gate's state, the reasons for anything stale or blocked, and the next step.
3. `checkpoint show <gate>` prints the full proposal and its decision history. Re-present a pending proposal from this output, not from memory: it is the version the user will be approving.

If the user's message is the reply to a pending gate ("yes, go with Q2"), record it as described above, then continue.

## What the checkpoints do not do

- They record and enforce *who decided what, on which version*. They do not judge whether the decision was good; the evidence rules in `SKILL.md` still apply.
- They do not lock files. Editing is always possible; it only makes the dependent approvals visibly stale.
- `--said` records what the user said, as typed by Claude. The record is only as truthful as the person who writes it, which is why approving on the user's behalf is forbidden.
