#!/bin/bash
# Live retrieval-reliability evaluation, 2026-10-19. One process at a time so arXiv sees a single client.
PY="$TEMP/claude/C--Users-eva-Desktop-6th-semester-Projects-IKT/e8d0e6f2-10b5-4037-938d-4607f70ff3f2/scratchpad/embvenv/Scripts/python"
S=".claude/skills/scientific-research-assistant/scripts/sra.py"
OUT=work/retrieval_eval/reliability
export SRA_EMBED_MODEL=minishlab/potion-retrieval-32M PYTHONWARNINGS=ignore
CFG=challenge,challenge_arxiv_any,challenge_lexical,challenge_hybrid
"$PY" $S retrieval-eval --fixtures ".claude/skills/scientific-research-assistant/evals/retrieval_blind/fixtures/*.json" \
  --configs $CFG --sources arxiv,crossref --snapshot $OUT/snapshot_blind --out $OUT/blind.json > $OUT/blind.txt 2> $OUT/blind.log
echo "BLIND DONE $?"
"$PY" $S retrieval-eval --fixtures ".claude/skills/scientific-research-assistant/evals/retrieval/*.json" \
  --configs $CFG --sources arxiv,crossref --snapshot $OUT/snapshot_old --out $OUT/old.json > $OUT/old.txt 2> $OUT/old.log
echo "OLD DONE $?"
