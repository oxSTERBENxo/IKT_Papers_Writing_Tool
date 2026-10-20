"""UPFD data audit on the official split files (no model training, no numpy).

Usage: python -I upfd_official.py <small_dir> <maps_dir> <pol|gos> <out_json> [feature ...]

<small_dir>/<pol|gos>/ holds members extracted from the PyG UPFD zip (A.txt,
graph_labels.npy, node_graph_id.npy, train/val/test_idx.npy, new_<feature>_feature.npz).
<maps_dir> holds <pol|gos>_id_twitter_mapping.pkl from GNN-FakeNews.
"""
import ast
import hashlib
import io
import json
import pickle
import random
import statistics
import struct
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

DT = {"<i8": "q", "<i4": "i", "<u4": "I", "<f4": "f", "<f8": "d", "|i1": "b", "|u1": "B", "|b1": "?", "<i2": "h"}


def read_npy(buf: bytes):
    if buf[:6] != b"\x93NUMPY":
        raise ValueError("not an npy file")
    major = buf[6]
    hlen, start = (struct.unpack("<H", buf[8:10])[0], 10) if major == 1 else (struct.unpack("<I", buf[8:12])[0], 12)
    header = ast.literal_eval(buf[start:start + hlen].decode("latin1"))
    descr = header["descr"]
    if descr not in DT or header["fortran_order"]:
        raise ValueError(f"unsupported npy {header}")
    shape = header["shape"]
    n = 1
    for s in shape:
        n *= s
    data = buf[start + hlen:]
    vals = list(struct.unpack(f"<{n}{DT[descr]}", data[:n * struct.calcsize(DT[descr])]))
    return vals, shape


def read_sparse_npz(path: Path):
    """scipy.sparse.save_npz -> (format, shape, data, indices, indptr)."""
    with zipfile.ZipFile(path) as z:
        arr = {n[:-4]: z.read(n) for n in z.namelist()}
    fmt = bytes(read_npy_raw_str(arr["format"])).decode() if "format" in arr else "csr"
    shape = tuple(read_npy(arr["shape"])[0])
    data, _ = read_npy(arr["data"])
    indices, _ = read_npy(arr["indices"])
    indptr, _ = read_npy(arr["indptr"])
    return fmt, shape, data, indices, indptr


def read_npy_raw_str(buf: bytes):
    hlen = struct.unpack("<H", buf[8:10])[0]
    header = ast.literal_eval(buf[10:10 + hlen].decode("latin1"))
    raw = buf[10 + hlen:]
    if header["descr"].startswith("|S"):
        return raw.rstrip(b"\x00")
    if header["descr"].startswith("<U"):
        return raw.decode("utf-32-le").rstrip("\x00").encode()
    raise ValueError(header)


class SafeUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        raise pickle.UnpicklingError(f"blocked {module}.{name}")


small, maps, ds, out_path = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], Path(sys.argv[4])
features = sys.argv[5:]
d = small / ds
full = {"pol": "politifact", "gos": "gossipcop"}[ds]

node_graph = read_npy((d / "node_graph_id.npy").read_bytes())[0]
labels = read_npy((d / "graph_labels.npy").read_bytes())[0]
split = {s: read_npy((d / f"{s}_idx.npy").read_bytes())[0] for s in ("train", "val", "test")}
mapping = SafeUnpickler(io.BytesIO((maps / f"{ds}_id_twitter_mapping.pkl").read_bytes())).load()

n_graphs = len(labels)
nodes_of = defaultdict(list)
for nid, g in enumerate(node_graph):
    nodes_of[g].append(nid)
root_of = {g: min(ns) for g, ns in nodes_of.items()}
users_of = {g: [mapping[n] for n in ns if n != root_of[g]] for g, ns in nodes_of.items()}

checks = {
    "n_graphs": n_graphs, "n_nodes": len(node_graph),
    "mapping_covers_all_nodes": len(mapping) == len(node_graph) and all(i in mapping for i in range(len(node_graph))),
    "graph_ids_contiguous_blocks": all(ns == list(range(ns[0], ns[0] + len(ns))) for ns in nodes_of.values()),
    "root_maps_to_news_id": all(str(mapping[root_of[g]]).startswith(full) for g in nodes_of),
    "split_sizes": {s: len(v) for s, v in split.items()},
    "split_fractions": {s: round(len(v) / n_graphs, 3) for s, v in split.items()},
    "splits_disjoint_and_complete": sorted(split["train"] + split["val"] + split["test"]) == list(range(n_graphs)),
    "label_counts": dict(Counter(labels)),
    "label_counts_by_split": {s: dict(Counter(labels[i] for i in v)) for s, v in split.items()},
}


def overlap_and_vote(train, test, ident_of):
    votes = defaultdict(Counter)
    for g in train:
        for u in set(ident_of[g]):
            votes[u][labels[g]] += 1
    maj = Counter(labels[g] for g in train).most_common(1)[0][0]
    correct = covered = 0
    seen_share = []
    for g in test:
        us = set(ident_of[g])
        seen = [u for u in us if u in votes]
        seen_share.append(len(seen) / len(us) if us else 0.0)
        c = Counter()
        for u in seen:
            c.update(votes[u])
        if c:
            covered += 1
            frac = c[1] / sum(c.values())
            pred = 1 if frac > 0.5 else 0 if frac < 0.5 else maj
        else:
            pred = maj
        correct += pred == labels[g]
    return {"test_graphs": len(test), "share_test_graphs_with_seen_identity": round(covered / len(test), 4),
            "mean_share_of_test_identities_seen": round(statistics.mean(seen_share), 4),
            "vote_accuracy": round(correct / len(test), 4),
            "majority_class_accuracy": round(sum(labels[g] == maj for g in test) / len(test), 4)}


official = {
    "train_to_test": overlap_and_vote(split["train"], split["test"], users_of),
    "train_plus_val_to_test": overlap_and_vote(split["train"] + split["val"], split["test"], users_of),
}

# Feature-level identity: can a model recognise a repeat user from its feature vector alone?
feature_report = {}
for feat in features:
    fmt, shape, data, indices, indptr = read_sparse_npz(d / f"new_{feat}_feature.npz")
    if fmt != "csr":
        raise SystemExit(f"unexpected sparse format {fmt}")

    def row_hash(i):
        a, b = indptr[i], indptr[i + 1]
        return hashlib.sha1(repr((indices[a:b], [round(x, 6) for x in data[a:b]])).encode()).hexdigest()

    hashes = [row_hash(i) for i in range(shape[0])]
    by_user = defaultdict(set)
    nodes_by_user = defaultdict(int)
    for g, ns in nodes_of.items():
        for n in ns:
            if n != root_of[g]:
                by_user[mapping[n]].add(hashes[n])
                nodes_by_user[mapping[n]] += 1
    repeat = [u for u, k in nodes_by_user.items() if k > 1]
    consistent = sum(1 for u in repeat if len(by_user[u]) == 1)
    user_hashes = [hashes[n] for g, ns in nodes_of.items() for n in ns if n != root_of[g]]
    hash_users = defaultdict(set)
    for g, ns in nodes_of.items():
        for n in ns:
            if n != root_of[g]:
                hash_users[hashes[n]].add(mapping[n])
    shared_vectors = {h: us for h, us in hash_users.items() if len(us) > 1}
    zero = hashlib.sha1(repr(([], [])).encode()).hexdigest()
    feat_ident = {g: [hashes[n] for n in ns if n != root_of[g]] for g, ns in nodes_of.items()}
    feature_report[feat] = {
        "shape": list(shape),
        "repeat_users": len(repeat),
        "repeat_users_with_identical_vector_everywhere": consistent,
        "share_identical": round(consistent / len(repeat), 4) if repeat else None,
        "distinct_vectors_among_user_nodes": len(set(user_hashes)),
        "user_nodes": len(user_hashes),
        "all_zero_user_vectors": sum(1 for h in user_hashes if h == zero),
        "vectors_shared_by_more_than_one_user": len(shared_vectors),
        "largest_group_of_users_sharing_one_vector": max((len(v) for v in shared_vectors.values()), default=1),
        "vote_using_feature_vector_as_identity_official_split": overlap_and_vote(split["train"], split["test"], feat_ident),
    }

# Feasibility of a user-disjoint split: connected components of graphs linked by shared users.
def components(max_graphs=None):
    cnt = Counter(u for g in nodes_of for u in set(users_of[g]))
    parent = list(range(n_graphs))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    first = {}
    for g in range(n_graphs):
        for u in set(users_of[g]):
            if max_graphs and cnt[u] >= max_graphs:
                continue
            if u in first:
                a, b = find(first[u]), find(g)
                if a != b:
                    parent[a] = b
            else:
                first[u] = g
    comp = Counter(find(g) for g in range(n_graphs))
    sizes = sorted(comp.values(), reverse=True)
    return {"drop_users_in_at_least_n_graphs": max_graphs, "n_components": len(sizes),
            "largest_component_share": round(sizes[0] / n_graphs, 4), "singleton_graphs": sum(1 for s in sizes if s == 1)}


feasibility = {"components": [components(t) for t in (None, 200, 50, 10, 3)]}

# Masking alternative: drop test-graph users seen in training and measure the size shift.
train_users = {u for g in split["train"] + split["val"] for u in users_of[g]}
before, after, by_label = [], [], defaultdict(lambda: [[], []])
for g in split["test"]:
    b = len(users_of[g])
    a = sum(1 for u in users_of[g] if u not in train_users)
    before.append(b)
    after.append(a)
    by_label[labels[g]][0].append(b)
    by_label[labels[g]][1].append(a)
feasibility["mask_seen_users_in_test"] = {
    "median_users_per_test_graph_before": statistics.median(before),
    "median_users_per_test_graph_after": statistics.median(after),
    "test_graphs_left_with_no_users": sum(1 for a in after if a == 0),
    "share_of_test_user_nodes_removed": round(1 - sum(after) / max(1, sum(before)), 4),
    "by_label_median_before_after": {str(k): [statistics.median(v[0]), statistics.median(v[1])] for k, v in by_label.items()},
}

# Graph size alone as a shortcut (threshold chosen on train, applied to test).
size = {g: len(nodes_of[g]) for g in nodes_of}
best = None
for t in sorted(set(size[g] for g in split["train"])):
    for sign in (1, -1):
        acc = sum((sign * (size[g] - t) > 0) == bool(labels[g]) for g in split["train"]) / len(split["train"])
        if best is None or acc > best[0]:
            best = (acc, t, sign)
_, t, sign = best
size_rule = {"threshold_nodes": t, "fake_if": "larger" if sign == 1 else "smaller",
             "train_accuracy": round(best[0], 4),
             "test_accuracy": round(sum((sign * (size[g] - t) > 0) == bool(labels[g]) for g in split["test"]) / len(split["test"]), 4)}

out = {"dataset": full, "checks": checks, "official_split_user_vote": official,
       "feature_identity": feature_report, "user_disjoint_feasibility": feasibility, "graph_size_rule": size_rule}
out_path.write_text(json.dumps(out, indent=1), encoding="utf-8")
print(json.dumps(out, indent=1))
