"""Deterministic train/test leakage and shortcut diagnostics for a dataset split.

Input: one record per evaluation item (a graph, document, claim, image...)
with its split, label and, optionally, the entities it contains (users,
authors, sources, molecules...) and its text. The checks answer:

- Do test items share entities with training items, and can a model-free
  vote over those shared entities' training labels predict the test labels?
- Are there exact duplicate texts across splits (after normalisation)?
- Does a single scalar (e.g. graph size) separate the classes on its own?
- Could a split that keeps entities disjoint exist (connected components)?
- How much of the test data would disappear if seen entities were masked?

These are diagnostics. A high vote accuracy shows that entity identity
carries label information that models may exploit; it does not prove that any
particular model exploits it.
"""
from __future__ import annotations

import hashlib
import json
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path

VOTE_MARGIN_HIGH = 0.10   # vote accuracy this far above majority-class accuracy is a high risk
VOTE_MARGIN_MEDIUM = 0.03
DUPLICATE_SHARE_HIGH = 0.01  # duplicates above 1% of the test set, or any with a conflicting label, are high


def load_records(path: str) -> list[dict]:
    text = Path(path).read_text(encoding="utf-8-sig")
    if path.lower().endswith(".jsonl"):
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    data = json.loads(text)
    if isinstance(data, dict) and "records" in data:
        data = data["records"]
    if not isinstance(data, list):
        raise ValueError("expected a JSON list of records, {'records': [...]}, or a .jsonl file")
    return data


def _norm_text(t: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", (t or "").lower())).strip()


def entity_vote(records: list[dict], train: set, test: set, max_entity_items: int | None = None) -> dict:
    counts = Counter(e for r in records for e in set(r["entities"]))
    votes: dict = defaultdict(Counter)
    for r in records:
        if r["split"] in train:
            for e in set(r["entities"]):
                if max_entity_items and counts[e] >= max_entity_items:
                    continue
                votes[e][r["label"]] += 1
    train_labels = Counter(r["label"] for r in records if r["split"] in train)
    if not train_labels:
        raise ValueError("no training records")
    majority = train_labels.most_common(1)[0][0]
    tests = [r for r in records if r["split"] in test]
    if not tests:
        raise ValueError("no test records")
    correct = covered = 0
    seen_share = []
    for r in tests:
        ents = set(r["entities"])
        seen = [e for e in ents if e in votes]
        seen_share.append(len(seen) / len(ents) if ents else 0.0)
        tally: Counter = Counter()
        for e in seen:
            tally.update(votes[e])
        if tally:
            covered += 1
            top = tally.most_common()
            pred = top[0][0] if len(top) == 1 or top[0][1] > top[1][1] else majority
        else:
            pred = majority
        correct += pred == r["label"]
    maj_acc = sum(r["label"] == majority for r in tests) / len(tests)
    return {
        "test_items": len(tests),
        "share_test_items_with_seen_entity": round(covered / len(tests), 4),
        "mean_share_of_entities_seen_in_train": round(statistics.mean(seen_share), 4),
        "entity_vote_accuracy": round(correct / len(tests), 4),
        "majority_class_accuracy": round(maj_acc, 4),
        "dropped_entities_in_at_least_n_items": max_entity_items,
    }


def components(records: list[dict], max_entity_items: int | None = None) -> dict:
    counts = Counter(e for r in records for e in set(r["entities"]))
    parent = list(range(len(records)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    first: dict = {}
    for i, r in enumerate(records):
        for e in set(r["entities"]):
            if max_entity_items and counts[e] >= max_entity_items:
                continue
            if e in first:
                a, b = find(first[e]), find(i)
                if a != b:
                    parent[a] = b
            else:
                first[e] = i
    sizes = sorted(Counter(find(i) for i in range(len(records))).values(), reverse=True)
    return {"dropped_entities_in_at_least_n_items": max_entity_items, "n_components": len(sizes),
            "largest_component_share": round(sizes[0] / len(records), 4) if sizes else None,
            "singleton_items": sum(1 for s in sizes if s == 1)}


def masking(records: list[dict], train: set, test: set) -> dict:
    seen = {e for r in records if r["split"] in train for e in r["entities"]}
    before, after = [], []
    for r in records:
        if r["split"] in test:
            before.append(len(r["entities"]))
            after.append(sum(1 for e in r["entities"] if e not in seen))
    return {"median_entities_per_test_item_before": statistics.median(before) if before else None,
            "median_entities_per_test_item_after": statistics.median(after) if after else None,
            "test_items_left_without_entities": sum(1 for a in after if a == 0),
            "share_of_test_entity_occurrences_removed": round(1 - sum(after) / max(1, sum(before)), 4)}


def scalar_rule(records: list[dict], field: str, train: set, test: set) -> dict:
    """Best single threshold on a numeric field, fitted on train, applied to test (binary labels only)."""
    tr = [(r[field], r["label"]) for r in records if r["split"] in train and r.get(field) is not None]
    te = [(r[field], r["label"]) for r in records if r["split"] in test and r.get(field) is not None]
    labels = sorted({lab for _, lab in tr})
    if len(labels) != 2 or not te:
        return {"field": field, "note": "needs a numeric field and exactly two labels"}
    lo, hi = labels
    best = None
    for t in sorted({v for v, _ in tr}):
        for above in (hi, lo):
            below = lo if above == hi else hi
            acc = sum((above if v > t else below) == lab for v, lab in tr) / len(tr)
            if best is None or acc > best[0]:
                best = (acc, t, above, below)
    acc, t, above, below = best
    test_acc = sum((above if v > t else below) == lab for v, lab in te) / len(te)
    return {"field": field, "threshold": t, "label_above": above, "train_accuracy": round(acc, 4),
            "test_accuracy": round(test_acc, 4)}


def duplicates(records: list[dict], train: set, test: set) -> dict:
    train_hashes = defaultdict(list)
    for r in records:
        if r["split"] in train and r.get("text"):
            train_hashes[hashlib.sha1(_norm_text(r["text"]).encode()).hexdigest()].append(r["label"])
    dup = conflicting = 0
    n_text = 0
    for r in records:
        if r["split"] in test and r.get("text"):
            n_text += 1
            h = hashlib.sha1(_norm_text(r["text"]).encode()).hexdigest()
            if h in train_hashes:
                dup += 1
                conflicting += any(lab != r["label"] for lab in train_hashes[h])
    return {"test_items_with_text": n_text, "exact_duplicates_of_train_text": dup,
            "duplicates_with_a_different_label": conflicting}


def analyse(records: list[dict], train=("train",), test=("test",), entities_field="entities",
            label_field="label", split_field="split", text_field=None, scalar_fields=(),
            hub_thresholds=(50, 10)) -> dict:
    train, test = set(train), set(test)
    norm = []
    for i, r in enumerate(records):
        if split_field not in r or label_field not in r:
            raise ValueError(f"record {i} lacks '{split_field}' or '{label_field}'")
        ents = r.get(entities_field) or []
        if not isinstance(ents, list):
            raise ValueError(f"record {i}: '{entities_field}' must be a list")
        item = {"split": str(r[split_field]), "label": r[label_field], "entities": [str(e) for e in ents]}
        if text_field:
            item["text"] = r.get(text_field)
        for f in scalar_fields:
            item[f] = r.get(f)
        norm.append(item)

    counts = Counter(e for r in norm for e in set(r["entities"]))
    repeat = {e for e, c in counts.items() if c > 1}
    labels_of = defaultdict(set)
    for r in norm:
        for e in set(r["entities"]):
            labels_of[e].add(r["label"])
    occ = sum(len(r["entities"]) for r in norm)
    out: dict = {
        "n_items": len(norm), "split_sizes": dict(Counter(r["split"] for r in norm)),
        "label_counts_by_split": {s: dict(Counter(r["label"] for r in norm if r["split"] == s))
                                  for s in sorted({r["split"] for r in norm})},
        "entities": {
            "unique": len(counts), "occurrences": occ,
            "in_more_than_one_item": len(repeat),
            "share_of_occurrences_from_repeat_entities": round(
                sum(1 for r in norm for e in r["entities"] if e in repeat) / occ, 4) if occ else None,
            "repeat_entities_with_a_single_label": round(
                sum(1 for e in repeat if len(labels_of[e]) == 1) / len(repeat), 4) if repeat else None,
            "max_items_per_entity": max(counts.values()) if counts else 0,
        },
    }
    if occ:
        out["entity_vote"] = [entity_vote(norm, train, test)] + [entity_vote(norm, train, test, t)
                                                                 for t in hub_thresholds]
        out["disjoint_split_feasibility"] = [components(norm)] + [components(norm, t) for t in hub_thresholds]
        out["masking_seen_entities"] = masking(norm, train, test)
    if text_field:
        out["duplicates"] = duplicates(norm, train, test)
    out["scalar_rules"] = [scalar_rule(norm, f, train, test) for f in scalar_fields]
    out["risks"] = assess(out)
    return out


def assess(out: dict) -> list[dict]:
    """Turn the numbers into labelled findings. Thresholds are conventions, not statistics."""
    risks = []
    for v in out.get("entity_vote") or []:
        margin = v["entity_vote_accuracy"] - v["majority_class_accuracy"]
        if v["dropped_entities_in_at_least_n_items"] is None:
            level = "high" if margin >= VOTE_MARGIN_HIGH else "medium" if margin >= VOTE_MARGIN_MEDIUM else "low"
            risks.append({"type": "train_test_overlap", "level": level,
                          "finding": f"A vote over entities seen in training reaches {v['entity_vote_accuracy']:.1%} "
                                     f"vs {v['majority_class_accuracy']:.1%} for the majority class; "
                                     f"{v['share_test_items_with_seen_entity']:.1%} of test items share an entity "
                                     "with training."})
    feas = out.get("disjoint_split_feasibility") or []
    if feas and feas[0]["largest_component_share"] and feas[0]["largest_component_share"] > 0.8:
        risks.append({"type": "disjoint_split_infeasible", "level": "medium",
                      "finding": f"{feas[0]['largest_component_share']:.1%} of items are linked through shared "
                                 "entities, so an entity-disjoint split cannot keep most of the data."})
    mask = out.get("masking_seen_entities")
    if mask and mask["share_of_test_entity_occurrences_removed"] > 0.3:
        risks.append({"type": "masking_distribution_shift", "level": "medium",
                      "finding": f"Masking entities seen in training removes "
                                 f"{mask['share_of_test_entity_occurrences_removed']:.1%} of test entity occurrences; "
                                 "a masked evaluation would change the test distribution substantially."})
    dup = out.get("duplicates")
    if dup and dup["exact_duplicates_of_train_text"]:
        share = dup["exact_duplicates_of_train_text"] / max(1, dup["test_items_with_text"])
        level = "high" if share >= DUPLICATE_SHARE_HIGH or dup["duplicates_with_a_different_label"] else "low"
        risks.append({"type": "duplicate_items", "level": level,
                      "finding": f"{dup['exact_duplicates_of_train_text']} test items duplicate a training text "
                                 f"({dup['duplicates_with_a_different_label']} with a different label)."})
    for rule in out.get("scalar_rules") or []:
        if "test_accuracy" in rule and rule["test_accuracy"] >= 0.7:
            risks.append({"type": "scalar_shortcut", "level": "medium",
                          "finding": f"A single threshold on '{rule['field']}' reaches {rule['test_accuracy']:.1%} "
                                     "test accuracy."})
    return risks
