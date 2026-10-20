"""Build the three test sets (S2019, S2023, S2026) as JSONL files in data/.

Each record: set, id, title, abstract, label, neighbour_titles (up to 5), degree, homophily.
"""
import gzip
import io
import json
import random
import re
import tarfile
import time
import xml.etree.ElementTree as ET
from collections import defaultdict

import pandas as pd
import requests

SEED = 20261020
N_2019, N_2026, K_NEIGH = 600, 600, 5
rng = random.Random(SEED)


def clean(s):
    return re.sub(r"\s+", " ", str(s)).strip()


def neighbours(edges, n):
    adj = defaultdict(set)
    for a, b in edges:
        if a != b:
            adj[a].add(b); adj[b].add(a)
    return adj


def node_record(set_name, nid, pid, title, abstract, label, adj, titles, labels):
    nb = sorted(adj.get(nid, ()))
    with_label = [labels[j] for j in nb if labels[j] is not None]
    hom = sum(l == label for l in with_label) / len(with_label) if with_label else None
    pick = rng.sample(nb, min(K_NEIGH, len(nb)))
    return {"set": set_name, "id": str(pid), "title": clean(title), "abstract": clean(abstract),
            "label": label, "neighbour_titles": [clean(titles[j]) for j in pick],
            "degree": len(nb), "homophily": hom}


# ------------------------------------------------------------------ S2019: ogbn-arxiv
def build_2019():
    base = "data/ogbn/arxiv"
    cats = pd.read_csv(f"{base}/mapping/labelidx2arxivcategeory.csv.gz")
    idx2cat = {i: "cs." + c.split()[-1].upper() for i, c in zip(cats["label idx"], cats["arxiv category"])}
    lab = pd.read_csv(f"{base}/raw/node-label.csv.gz", header=None)[0].map(idx2cat).tolist()
    year = pd.read_csv(f"{base}/raw/node_year.csv.gz", header=None)[0].tolist()
    pid = pd.read_csv(f"{base}/mapping/nodeidx2paperid.csv.gz")["paper id"].tolist()
    edges = pd.read_csv(f"{base}/raw/edge.csv.gz", header=None).values.tolist()
    with tarfile.open("data/ogbn/titleabs.tsv.gz") as tf:
        member = [m for m in tf.getmembers() if m.isfile()][0]
        raw = tf.extractfile(member).read().decode("utf-8", errors="replace")
    ta = {}
    for line in raw.splitlines():
        parts = line.split("\t")
        if len(parts) >= 3 and parts[0].isdigit():
            ta[int(parts[0])] = (parts[1], parts[2])
    titles = [ta.get(p, ("", ""))[0] for p in pid]
    adj = neighbours(edges, len(pid))
    test = [i for i, y in enumerate(year) if y == 2019 and pid[i] in ta and ta[pid[i]][1].strip()]
    chosen = rng.sample(test, N_2019)
    recs = [node_record("S2019", i, pid[i], ta[pid[i]][0], ta[pid[i]][1], lab[i], adj, titles, lab)
            for i in chosen]
    print("S2019:", len(recs), "of", len(test), "2019 test nodes;", len(set(idx2cat.values())), "classes")
    return recs, sorted(set(idx2cat.values()))


# ------------------------------------------------------------------ S2023: arxiv-2023
def build_2023():
    base = "data/arxiv2023"
    rd = lambda f: pd.read_csv(f"{base}/{f}.csv.gz")
    ids, titles = rd("raw/ids")["ids"].astype(str).tolist(), rd("raw/titles")["titles"].tolist()
    abstracts, labels = rd("raw/abstracts")["abstracts"].tolist(), rd("raw/labels")["labels"].tolist()
    labels = [l.upper().replace("CS.", "cs.") if isinstance(l, str) else None for l in labels]
    edges = rd("raw/edges").values.tolist()
    adj = neighbours(edges, len(ids))
    test = rd("split/test")["test_id"].tolist()
    recs = [node_record("S2023", i, ids[i], titles[i], abstracts[i], labels[i], adj, titles, labels)
            for i in test]
    print("S2023:", len(recs), "test nodes")
    return recs


# ------------------------------------------------------------------ S2026: arXiv API
def build_2026(classes):
    ns = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom",
          "os": "http://a9.com/-/spec/opensearch/1.1/"}
    api = "https://export.arxiv.org/api/query"
    pool = {}
    months = [(2026, m) for m in range(1, 9)]
    for y, m in months:
        last = 31 if m in (1, 3, 5, 7, 8) else (28 if m == 2 else 30)
        q = f"cat:cs.* AND submittedDate:[{y}{m:02d}010000 TO {y}{m:02d}{last}2359]"
        r = requests.get(api, params={"search_query": q, "max_results": 1}, timeout=60)
        total = int(ET.fromstring(r.text).find("os:totalResults", ns).text)
        time.sleep(3.2)
        for start in sorted(rng.sample(range(0, max(total - 100, 1)), 3)):
            for attempt in range(4):
                r = requests.get(api, params={"search_query": q, "start": start, "max_results": 100,
                                              "sortBy": "submittedDate", "sortOrder": "ascending"}, timeout=90)
                time.sleep(3.2)
                if r.status_code == 200 and "<entry>" in r.text:
                    break
                time.sleep(10)
            for e in ET.fromstring(r.text).findall("a:entry", ns):
                aid = e.find("a:id", ns).text.rsplit("/", 1)[-1].split("v")[0]
                pe = e.find("arxiv:primary_category", ns)
                if pe is None:
                    pe = e.find("a:category", ns)
                if pe is None:
                    continue
                prim = pe.attrib["term"]
                lab = "cs." + prim.split(".")[-1].upper() if prim.startswith("cs.") else None
                if lab in classes and not aid.startswith(("23", "24", "25")):
                    pool[aid] = {"title": e.find("a:title", ns).text, "abstract": e.find("a:summary", ns).text,
                                 "label": lab, "published": e.find("a:published", ns).text[:10]}
        print(f"  {y}-{m:02d}: total {total}, pool now {len(pool)}", flush=True)
    keys = rng.sample(sorted(pool), N_2026)
    recs = [{"set": "S2026", "id": k, "title": clean(pool[k]["title"]), "abstract": clean(pool[k]["abstract"]),
             "label": pool[k]["label"], "published": pool[k]["published"], "neighbour_titles": [],
             "degree": None, "homophily": None} for k in keys]
    print("S2026:", len(recs), "of pool", len(pool))
    return recs


def main():
    r19, classes = build_2019()
    r23 = build_2023()
    bad = {r["label"] for r in r23} - set(classes)
    print("S2023 labels outside class list:", bad)
    r26 = build_2026(set(classes))
    json.dump(classes, open("data/classes.json", "w"))
    for name, recs in [("S2019", r19), ("S2023", r23), ("S2026", r26)]:
        with open(f"data/{name}.jsonl", "w", encoding="utf-8") as f:
            for r in recs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
