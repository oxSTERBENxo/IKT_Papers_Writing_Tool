"""Analysis for: {{TITLE}}

Run it through the project so the approvals are checked and the run is recorded:

    python <skill>/scripts/sra.py project run --evidence results/results.json -- python analysis.py

Every number the paper reports must be written to results/results.json by this
script. The paper refers to them with placeholders such as {{res:n|,}}.
"""
import json
import random
from pathlib import Path

SEED = 20261026
random.seed(SEED)

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results" / "results.json"


def main() -> None:
    results = {"seed": SEED}
    # TODO: load data from data/, run the tests fixed in ANALYSIS_PLAN.md, and store every reported value.
    RESULTS.parent.mkdir(exist_ok=True)
    RESULTS.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"wrote {RESULTS}")


if __name__ == "__main__":
    main()
