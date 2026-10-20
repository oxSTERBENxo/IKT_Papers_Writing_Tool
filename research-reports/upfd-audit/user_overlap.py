"""Measure user overlap across UPFD propagation graphs (data audit, no model training).

Usage: python -I user_overlap.py <data_dir> <pol|gos> <out_json> [drop users in >= N graphs]

Graphs are rebuilt from the node-id -> twitter-id mapping: node ids are assumed
contiguous per graph with the news (root) node first, which is checked against
the released news list. Labels come from FakeNewsNet's fake/real CSV id lists.
"""
import csv
import io
import json
import pickle
import random
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

csv.field_size_limit(10**9)


class SafeUnpickler(pickle.Unpickler):
    def find_class(self, module, name):  # refuse any object construction
        raise pickle.UnpicklingError(f"blocked {module}.{name}")


d = Path(sys.argv[1])
ds = sys.argv[2]
full = {"pol": "politifact", "gos": "gossipcop"}[ds]
mapping = SafeUnpickler(io.BytesIO((d / f"{ds}_id_twitter_mapping.pkl").read_bytes())).load()
news_list = (d / f"{ds}_news_list.txt").read_text().split()

labels = {}
for lab, name in [(1, "fake"), (0, "real")]:
    with open(d / f"{full}_{name}.csv", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            labels[row["id"]] = lab

# rebuild graphs: walk node ids in order; a string value starting with the dataset name is a root
graphs, cur = [], None
for nid in sorted(mapping):
    v = mapping[nid]
    if isinstance(v, str) and v.startswith(full):
        cur = {"news": v, "users": []}
        graphs.append(cur)
    else:
        cur["users"].append(str(v))

MAXG = int(sys.argv[4]) if len(sys.argv) > 4 else 0
if MAXG:
    cnt = Counter(u for g in graphs for u in set(g["users"]))
    for g in graphs:
        g["users"] = [u for u in g["users"] if cnt[u] < MAXG]

roots = [g["news"] for g in graphs]
check = {
    "n_graphs": len(graphs),
    "n_nodes": len(mapping),
    "roots_match_news_list_order": roots == news_list,
    "roots_match_news_list_set": set(roots) == set(news_list),
    "labelled": sum(r in labels for r in roots),
}
y = [labels.get(r) for r in roots]
check["n_fake"] = sum(1 for v in y if v == 1)

# user statistics
user_graphs = defaultdict(set)
for i, g in enumerate(graphs):
    for u in g["users"]:
        user_graphs[u].add(i)
n_users = len(user_graphs)
multi = {u: s for u, s in user_graphs.items() if len(s) > 1}
nodes_total = sum(len(g["users"]) for g in graphs)
nodes_multi = sum(1 for g in graphs for u in g["users"] if u in multi)
pure = sum(1 for u, s in multi.items() if len({y[i] for i in s}) == 1)
dup_in_graph = sum(len(g["users"]) - len(set(g["users"])) for g in graphs)

stats = {
    "unique_users": n_users,
    "user_nodes": nodes_total,
    "duplicate_user_nodes_within_a_graph": dup_in_graph,
    "users_in_more_than_one_graph": len(multi),
    "share_of_user_nodes_whose_user_appears_in_another_graph": round(nodes_multi / nodes_total, 4),
    "repeat_users_whose_graphs_all_share_one_label": round(pure / len(multi), 4) if multi else None,
}


def split(seed, n):
    idx = list(range(n))
    random.Random(seed).shuffle(idx)
    a, b = int(0.2 * n), int(0.1 * n)
    return idx[:a], idx[a:a + b], idx[a + b:]


# Diagnostic: label a test graph by the majority training label of its users
# (no model, no features, no edges). Graphs with no seen users get the training majority class.
diag = []
for seed in range(20):
    tr, va, te = split(seed, len(graphs))
    votes = defaultdict(Counter)
    for i in tr:
        for u in set(graphs[i]["users"]):
            votes[u][y[i]] += 1
    maj = Counter(y[i] for i in tr).most_common(1)[0][0]
    correct, covered, seen_share = 0, 0, []
    for i in te:
        us = set(graphs[i]["users"])
        seen = [u for u in us if u in votes]
        seen_share.append(len(seen) / len(us) if us else 0.0)
        c = Counter()
        for u in seen:
            c.update(votes[u])
        if c:
            covered += 1
            pred = 1 if c[1] / sum(c.values()) > 0.5 else 0 if c[1] / sum(c.values()) < 0.5 else maj
        else:
            pred = maj
        correct += pred == y[i]
    diag.append({
        "seed": seed,
        "test_graphs": len(te),
        "test_graphs_with_any_user_seen_in_train": round(covered / len(te), 4),
        "mean_share_of_test_graph_users_seen_in_train": round(statistics.mean(seen_share), 4),
        "user_vote_accuracy": round(correct / len(te), 4),
    })


def summ(k):
    v = [r[k] for r in diag]
    return {"mean": round(statistics.mean(v), 4), "sd": round(statistics.stdev(v), 4), "min": min(v), "max": max(v)}


out = {
    "dataset": full,
    "dropped_users_in_at_least_n_graphs": MAXG or None,
    "checks": check,
    "user_stats": stats,
    "diagnostic_20_random_20_10_70_splits": {
        k: summ(k) for k in ["test_graphs_with_any_user_seen_in_train",
                             "mean_share_of_test_graph_users_seen_in_train", "user_vote_accuracy"]
    },
    "per_seed": diag,
}
Path(sys.argv[3]).write_text(json.dumps(out, indent=1), encoding="utf-8")
print(json.dumps({k: out[k] for k in ["dataset", "dropped_users_in_at_least_n_graphs", "checks", "user_stats", "diagnostic_20_random_20_10_70_splits"]}, indent=1))
