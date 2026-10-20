# Starry Sky

Students ask questions anonymously during a lecture. Similar questions are grouped into one star, and a star shines
brighter the more students asked it. The instructor sees the sky, and after the lecture ranks the groups blind.

The app is also the data-collection instrument for the research proposal
(`research-reports/qa-starry-sky/brightest-stars-...md`): it records everything Study 1 (are the groups right?) and
Study 2 (upvotes or number of askers?) need.

## Run it

Requirements: Python 3.10+ (developed with 3.13). The grouping model (all-MiniLM-L6-v2, about 90 MB) is downloaded
on first start; a GPU is used if present but not needed.

```
cd starry-sky
py -3.13 -m venv --system-site-packages .venv      # reuses an installed PyTorch if there is one
.venv\Scripts\python -m pip install -r requirements.txt
start.bat                                           # or: .venv\Scripts\python -m uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000`, create a lecture, and keep the **instructor link** private (it controls the lecture).
Students open `http://<your laptop's IP>:8000/s/<CODE>` on the same Wi-Fi; `start.bat` prints that address.
Windows asks once whether to allow Python through the firewall: allow it on private networks. University Wi-Fi often
blocks connections between devices; then use a phone hotspot or ask IT.

## A lecture, step by step

1. **Asking** (default): students send questions privately. Nobody sees anyone else's questions, so repeat
   questions are not suppressed by a visible feed. The instructor sees the sky fill up.
2. **Voting**: every student sees all questions in their own random order, without counts, and taps "Me too".
3. **Close**: nothing more is accepted.
4. **Blind ranking**: the instructor ranks the groups by how important they are to answer for the whole class. Groups
   appear in random order without sizes or votes. This ranking is the reference for Study 2.
5. **Download all data (JSON)** from the settings panel.

Instructor tools: click a star to see its questions; "Hide" removes off-topic or inappropriate questions from the
sky (they stay in the data, marked hidden); the strictness slider changes how similar questions must be to share a
star (default 0.55 cosine similarity).

## What is recorded

| Table | Fields | Used for |
| --- | --- | --- |
| questions | text, anonymous participant, time, phase, hidden | both studies |
| votes | question, voter, **position in the voter's shuffled list**, time | Study 2; position-bias check |
| cluster_runs | method, threshold, question-to-group assignment | Study 1 and the frozen groups for ranking |
| rankings | groups in the order shown, the instructor's ranking | Study 2 reference |

No names, e-mail addresses or IP addresses are stored. A participant is a random ID created in the student's browser
for that lecture only. Questions may still contain identifying details: review them before sharing any data.

**Before a real study:** get ethics approval from your university, tell students what is collected and why, make
participation voluntary and unrelated to grades, and keep the database file (`data/starry.sqlite3`) private.

## Settings

| Variable | Default | Meaning |
| --- | --- | --- |
| `STARRY_DB` | `data/starry.sqlite3` | database file |
| `STARRY_BACKEND` | `sentence` | `sentence` (embedding model) or `tfidf` (word overlap, no download) |
| `STARRY_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | any sentence-transformers model |

## Tests

```
.venv\Scripts\python -m pytest -q
```

The tests use the word-overlap backend, so they need no model download. They cover the full lecture flow, the
privacy of the ask phase, vote rules, blind ranking, hiding and export.

## Not built yet

- Annotation tool for Study 1 (for now: export the questions and group them in a spreadsheet).
- Analysis scripts (AMI/ARI against human groupings, NDCG@5 against the instructor ranking).
- A QR code on the instructor screen; LLM-written star labels (the label is currently the most typical question in
  the group).
