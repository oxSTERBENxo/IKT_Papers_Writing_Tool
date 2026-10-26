# {{TITLE}}

| File | What it is |
|---|---|
| `paper.json` | Paper metadata (title, keywords, results files, number rules). Repository defaults come from `research.json` |
| `paper.md` | The text. Numbers are `{{res:…}}` placeholders; citations are `[@key]` |
| `ANALYSIS_PLAN.md` | Hypotheses and tests, fixed before the analysis, plus every deviation |
| `analysis.py` | Computes every reported number into `results/results.json` |
| `refs/<key>.json` | One verified record per cited work, added with `manuscript cite` |
| `figures/` | Figures, written by the analysis |
| `project.json` | Decision checkpoints: scope → question → methodology → execution → results → manuscript |
| `build/` | Drafts (`paper.draft.*`), rebuilt at will |
| `final/` | Final `paper.md`, `.docx`, `.pdf` and `MANIFEST.json`, built only after the manuscript is approved |

```
S=<skill>/scripts/sra.py
python $S project run --evidence results/results.json -- python analysis.py
python $S manuscript cite --id 10.1145/2630069 --key allodi2014
python $S manuscript check
python $S manuscript build            # draft
python $S manuscript review           # propose the manuscript checkpoint
python $S manuscript build --final    # after the user approves
```
