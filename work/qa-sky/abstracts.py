import sys, time, json
sys.path.insert(0, ".claude/skills/scientific-research-assistant/scripts")
from sra.http import HttpClient, SourceError
from sra.search import resolve
from sra.sources import arxiv, crossref
client = HttpClient(max_wait=90, max_retries=4, backoff=8)
ids = ["2511.01248", "2609.38907", "10.1145/3641554.3701965", "2505.06469", "2301.05150", "10.1002/cae.22252",
       "10.26434/chemrxiv-2024-gwxrs", "10.18653/v1/2025.emnlp-main.1760", "10.1145/2379057.2379081"]
out = {}
for i in ids:
    time.sleep(4)
    try:
        p = arxiv.get_paper(client, i) if i[0].isdigit() and "/" not in i else None
        if p is None:
            p, _ = resolve(client, i)
    except SourceError as e:
        print("ERR", i, e.kind); continue
    if not p:
        print("NOT FOUND", i); continue
    out[i] = p.to_dict()
    print(f"\n### {i} | {p.title} | {p.year} | {', '.join(a for a in (p.authors or [])[:3])}\n{(p.abstract or 'NO ABSTRACT')[:1500]}")
json.dump(out, open("work/qa-sky/abstracts.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
