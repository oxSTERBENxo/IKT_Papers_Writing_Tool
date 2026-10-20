S=.claude/skills/scientific-research-assistant/scripts/sra.py
SRC=arxiv,crossref,huggingface
python $S challenge --claim "Evaluating how well embedding and LLM clustering of live student lecture questions agrees with instructor groupings, and how sensitive the most frequent question cluster is to the clustering threshold" \
  --query "clustering student questions evaluation" --query "student question grouping human agreement" \
  --query "short text clustering student questions embeddings" --query "LLM question similarity clustering education" \
  --query "duplicate student questions detection forum" \
  --design "agreement with instructor groupings" --design "adjusted rand index" --design "clustering threshold sensitivity" \
  --sources $SRC --limit 10 --out work/qa-sky/challenge_q1.json > work/qa-sky/challenge_q1.txt 2>&1
sleep 20
python $S challenge --claim "Comparing upvote counts with semantic cluster size as signals for which student questions instructors should answer first" \
  --query "upvoting student questions lecture" --query "question voting audience prioritization" \
  --query "popular questions upvotes versus frequency" --query "crowd voting questions classroom" \
  --query "Q&A upvotes instructor answer priority" \
  --design "upvote ranking" --design "cluster size ranking" --design "instructor priority judgement" \
  --sources $SRC --limit 10 --out work/qa-sky/challenge_q2.json > work/qa-sky/challenge_q2.txt 2>&1
sleep 20
python $S challenge --claim "Whether a frequency-encoded constellation visualization of clustered student questions helps instructors identify the most widely shared questions faster and more accurately than a ranked list" \
  --query "visualization student questions instructor" --query "real-time classroom dashboard visualization questions" \
  --query "instructor dashboard student confusion visualization" --query "question cluster visualization user study" \
  --query "teacher orchestration dashboard evaluation" \
  --design "ranked list baseline" --design "task completion time and accuracy" --design "within-subjects user study" \
  --sources $SRC --limit 10 --out work/qa-sky/challenge_q3.json > work/qa-sky/challenge_q3.txt 2>&1
echo ALLDONE
