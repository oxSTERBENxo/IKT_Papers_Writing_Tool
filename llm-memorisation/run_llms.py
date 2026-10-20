"""Query local LLMs (Ollama) for classification (P0, P1) and the title-completion probe.

Usage:  python run_llms.py [--limit N] [--models a,b] [--tasks P0,P1,PROBE]
Results are appended to results/raw/<model>__<task>__<set>.jsonl and are resumable.
"""
import argparse
import json
import math
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor

import requests

OLLAMA = "http://localhost:11434/api/chat"
MODELS = ["llama2:7b-chat", "llama3.2:latest", "qwen2.5:7b", "gemma3:4b"]
SYSTEM_CLS = ("Please predict the most appropriate arXiv Computer Science (CS) sub-category for the paper. "
              "The predicted sub-category should be in the format 'cs.XX'.")
SYSTEM_PROBE = "You are an expert on arXiv computer science papers."
TASK_SETS = {"P0": ["S2019", "S2023", "S2026"], "P1": ["S2019", "S2023"], "PROBE": ["S2023", "S2026"]}
OPTIONS = {"temperature": 0, "seed": 42, "num_ctx": 4096}
CLS_RE = re.compile(r"\bcs\.([A-Za-z]{2})\b")
# Llama-2 always writes a one-sentence preamble before the code, so it gets a longer answer budget.
NPRED = {"llama2:7b-chat": 64}
WORKERS = 4


def load(set_name):
    with open(f"data/{set_name}.jsonl", encoding="utf-8") as f:
        return [json.loads(l) for l in f]


def cls_prompt(r, with_neighbours):
    text = f"Title: {r['title']}\nAbstract: {r['abstract'][:2000]}\n"
    if with_neighbours and r["neighbour_titles"]:
        text += "\nTitles of papers linked to this paper by citation:\n"
        text += "".join(f"{i + 1}. {t}\n" for i, t in enumerate(r["neighbour_titles"]))
    text += ("\nWhich arXiv CS sub-category is most appropriate for this paper? "
             "Reply with only the sub-category code in the format 'cs.XX' (for example cs.LG), nothing else.")
    return text


def norm(s):
    return re.sub(r"[^a-z0-9 ]", " ", s.lower()).split()


def probe_split(title):
    w = title.split()
    k = math.ceil(len(w) / 2)
    return " ".join(w[:k]), " ".join(w[k:])


def chat(model, system, user, num_predict):
    body = {"model": model, "stream": False, "keep_alive": "30m",
            "options": {**OPTIONS, "num_predict": num_predict},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    for attempt in range(5):
        try:
            r = requests.post(OLLAMA, json=body, timeout=300)
            r.raise_for_status()
            return r.json()["message"]["content"]
        except Exception as e:  # noqa: BLE001
            print("  retry", attempt, e, flush=True)
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("Ollama failed repeatedly")


def run(model, task, set_name, limit):
    os.makedirs("results/raw", exist_ok=True)
    out = f"results/raw/{model.replace(':', '_')}__{task}__{set_name}.jsonl"
    done = set()
    if os.path.exists(out):
        with open(out, encoding="utf-8") as f:
            done = {json.loads(l)["id"] for l in f}
    recs = [r for r in load(set_name) if r["id"] not in done]
    if task == "PROBE":
        recs = [r for r in recs if len(r["title"].split()) >= 6]
    if limit:
        recs = recs[:limit]
    t0 = time.time()
    npred = NPRED.get(model, 24)

    def one(r):
        if task == "PROBE":
            head, tail = probe_split(r["title"])
            user = ("The following is the beginning of the title of a real arXiv computer science paper. "
                    f"Complete the title exactly. Reply with the full title only.\nBeginning: \"{head}\"")
            ans = chat(model, SYSTEM_PROBE, user, npred + 8)
            q = re.search(r"[\"“]([^\"”]{3,})[\"”]", ans)  # prefer a quoted title if the model added a preamble
            gen = norm(q.group(1) if q else ans)
            h = norm(head)
            if gen[:len(h)] == h:  # model repeated the beginning
                gen = gen[len(h):]
            t = norm(tail)
            gen = gen[:len(t) + 3]
            common = sum(min(gen.count(w), t.count(w)) for w in set(t))
            f1 = 0 if not common else 2 * common / (len(gen) + len(t))
            return {"id": r["id"], "answer": ans, "head": head, "tail": tail,
                    "exact": int(gen[:len(t)] == t), "f1": f1}
        ans = chat(model, SYSTEM_CLS, cls_prompt(r, task == "P1"), npred)
        m = CLS_RE.search(ans)
        pred = "cs." + m.group(1).upper() if m else None
        return {"id": r["id"], "answer": ans, "pred": pred, "label": r["label"],
                "correct": int(pred == r["label"])}

    with open(out, "a", encoding="utf-8") as f, ThreadPoolExecutor(WORKERS) as ex:
        for i, rec in enumerate(ex.map(one, recs)):
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            if (i + 1) % 100 == 0:
                print(f"  {model} {task} {set_name}: {i + 1}/{len(recs)} "
                      f"({(time.time() - t0) / (i + 1):.2f}s each)", flush=True)
    n = len(recs)
    print(f"done {model} {task} {set_name}: {n} new in {time.time() - t0:.0f}s", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--models", default=",".join(MODELS))
    ap.add_argument("--tasks", default="P0,PROBE,P1")
    a = ap.parse_args()
    for task in a.tasks.split(","):
        for model in a.models.split(","):
            for s in TASK_SETS[task]:
                run(model, task, s, a.limit)
    print("ALL DONE", flush=True)


if __name__ == "__main__":
    main()
