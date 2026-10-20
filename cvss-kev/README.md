# CVSS vs. real-world exploitation (CISA KEV), replication of Allodi & Massacci (2014)

| File | What it is |
|---|---|
| `paper.md` / `paper.docx` | The research paper (Markdown source and Word version) |
| `ANALYSIS_PLAN.md` | Hypotheses and tests, fixed before the analysis, plus the one recorded deviation |
| `extract.py` | Streams the NVD feed into `data/nvd_cvss.csv` |
| `analysis.py` | Computes every statistic, table and figure |
| `results/results.json`, `results/tables.md` | All numbers |
| `figures/` | Figures 1–4 (PNG, 200 dpi) |
| `refs/` | Metadata retrieved for each cited paper |

## Rerun from scratch

```
python -m venv .venv
.venv/Scripts/python -m pip install numpy pandas scipy statsmodels matplotlib ijson
curl -L -o data/kev.csv https://raw.githubusercontent.com/cisagov/kev-data/main/known_exploited_vulnerabilities.csv
curl -L -o data/CVE-all.json.xz https://github.com/fkie-cad/nvd-json-data-feeds/releases/latest/download/CVE-all.json.xz
.venv/Scripts/python extract.py     # ~1.5 min
.venv/Scripts/python analysis.py    # ~1.5 min
```

Both data sources update daily, so a fresh download will shift the numbers slightly. The paper uses the snapshot from 2026-10-19.
