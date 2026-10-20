"""Group similar questions and lay the groups out as stars.

Representation (STARRY_BACKEND):
- "sentence" (default): a small sentence-embedding model (STARRY_MODEL, default all-MiniLM-L6-v2, about 90 MB,
  downloaded once by sentence-transformers). Runs on CPU; uses the GPU if available.
- "tfidf": word overlap only. No download; used automatically when the model cannot be loaded, and in tests.

Grouping: agglomerative clustering with average linkage on cosine distance, cut at a similarity threshold, so the
number of groups is not fixed in advance. The same algorithm is used for every representation, so a comparison of
representations (Study 1) changes only one thing.
"""
from __future__ import annotations

import os
import threading

import numpy as np

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
_model = {"obj": None, "name": None, "error": None}
_lock = threading.Lock()
_cache: dict[str, np.ndarray] = {}


def backend() -> str:
    want = os.environ.get("STARRY_BACKEND", "sentence")
    if want == "sentence" and _load_model() is None:
        return "tfidf"
    return want


def _load_model():
    with _lock:
        if _model["obj"] is None and _model["error"] is None:
            name = os.environ.get("STARRY_MODEL", DEFAULT_MODEL)
            try:
                from sentence_transformers import SentenceTransformer
                _model["obj"], _model["name"] = SentenceTransformer(name), name
            except Exception as exc:  # no package, no network for the first download, bad name
                _model["error"] = f"{type(exc).__name__}: {exc}"[:300]
        return _model["obj"]


def describe() -> str:
    b = backend()
    return f"sentence:{_model['name']}" if b == "sentence" else "tfidf" + (
        f" (sentence model unavailable: {_model['error']})" if _model["error"] else "")


def embed(texts: list[str], method: str | None = None) -> np.ndarray:
    """Unit-length vectors, one row per text."""
    method = method or backend()
    if not texts:
        return np.zeros((0, 1))
    if method == "sentence":
        # Cache per text: the instructor view refreshes every few seconds and most questions are unchanged.
        todo = [t for t in dict.fromkeys(texts) if t not in _cache]
        if todo:
            for t, v in zip(todo, _load_model().encode(todo, normalize_embeddings=True, show_progress_bar=False)):
                _cache[t] = np.asarray(v)
            while len(_cache) > 20000:
                _cache.pop(next(iter(_cache)))
        vecs = np.stack([_cache[t] for t in texts])
    elif method == "tfidf":
        from sklearn.feature_extraction.text import TfidfVectorizer
        try:
            vecs = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=1,
                                   token_pattern=r"(?u)\b\w+\b").fit_transform(texts).toarray()
        except ValueError:  # nothing but punctuation or emoji
            vecs = np.zeros((len(texts), 1))
    else:
        raise ValueError(f"unknown method {method}")
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vecs / norms


def cluster(vecs: np.ndarray, threshold: float) -> np.ndarray:
    """Labels 0..k-1. Questions join a group when their average cosine similarity reaches `threshold`."""
    n = len(vecs)
    if n == 0:
        return np.zeros(0, dtype=int)
    if n == 1:
        return np.zeros(1, dtype=int)
    from sklearn.cluster import AgglomerativeClustering
    labels = np.arange(n)  # rows without any content (e.g. only emoji) stay on their own
    valid = np.where(np.linalg.norm(vecs, axis=1) > 0)[0]
    if len(valid) >= 2:
        model = AgglomerativeClustering(n_clusters=None, metric="cosine", linkage="average",
                                        distance_threshold=max(1e-6, 1.0 - threshold))
        labels[valid] = model.fit_predict(vecs[valid]) + n
    _, labels = np.unique(labels, return_inverse=True)
    return labels


def layout(centroids: np.ndarray, sizes: list[int], seed: int = 7) -> list[tuple[float, float]]:
    """2-D positions in [0.08, 0.92]: similar groups sit near each other (PCA), then overlapping stars are pushed
    apart. Deterministic for the same input."""
    k = len(centroids)
    if k == 0:
        return []
    if k == 1:
        return [(0.5, 0.5)]
    x = centroids - centroids.mean(axis=0)
    u, s, _ = np.linalg.svd(x, full_matrices=False)
    pts = u[:, :2] * s[:2] if u.shape[1] >= 2 else np.c_[u[:, :1] * s[:1], np.zeros(k)]
    rng = np.random.default_rng(seed)
    pts = pts + rng.normal(0, 1e-3, pts.shape)
    span = pts.max(axis=0) - pts.min(axis=0)
    span[span == 0] = 1.0
    pts = (pts - pts.min(axis=0)) / span
    radius = np.array([0.03 + 0.02 * np.sqrt(sz) for sz in sizes])
    for _ in range(200):  # simple repulsion so stars do not overlap
        moved = False
        for i in range(k):
            for j in range(i + 1, k):
                d = pts[i] - pts[j]
                dist = float(np.hypot(*d)) or 1e-6
                need = (radius[i] + radius[j]) * 0.6
                if dist < need:
                    push = (need - dist) / 2 * d / dist
                    pts[i] += push
                    pts[j] -= push
                    moved = True
        pts = np.clip(pts, 0, 1)
        if not moved:
            break
    pts = 0.08 + 0.84 * pts
    return [(round(float(a), 4), round(float(b), 4)) for a, b in pts]


def sky(questions: list[dict], votes: list[dict], threshold: float, method: str | None = None) -> dict:
    """Groups with brightness = number of distinct students who asked; upvotes reported separately.

    questions: [{id, participant_id, text}]; votes: [{question_id, participant_id}].
    A group's id is its smallest question id, so it stays stable when new questions arrive.
    """
    method = method or backend()
    if not questions:
        return {"method": method, "threshold": threshold, "stars": [], "assignment": {}}
    vecs = embed([q["text"] for q in questions], method)
    labels = cluster(vecs, threshold)
    voters: dict[int, set] = {}
    for v in votes:
        voters.setdefault(v["question_id"], set()).add(v["participant_id"])
    groups: dict[int, list[int]] = {}
    for i, lab in enumerate(labels):
        groups.setdefault(int(lab), []).append(i)
    stars, centroids = [], []
    for idxs in groups.values():
        members = [questions[i] for i in idxs]
        sub = vecs[idxs]
        sim = sub @ sub.T
        medoid = idxs[int(np.argmax(sim.mean(axis=1)))]
        group_voters = set().union(*(voters.get(q["id"], set()) for q in members))
        stars.append({
            "id": min(q["id"] for q in members),
            "askers": len({q["participant_id"] for q in members}),
            "n_questions": len(members),
            "upvotes": sum(len(voters.get(q["id"], ())) for q in members),
            "upvoters": len(group_voters),
            "representative": questions[medoid]["text"],
            "questions": [{"id": q["id"], "text": q["text"], "upvotes": len(voters.get(q["id"], ()))}
                          for q in sorted(members, key=lambda q: q["id"])],
        })
        centroids.append(sub.mean(axis=0))
    for star, (x, y) in zip(stars, layout(np.array(centroids), [s["askers"] for s in stars])):
        star["x"], star["y"] = x, y
    stars.sort(key=lambda s: (-s["askers"], -s["upvotes"], s["id"]))
    assignment = {}
    for star in stars:
        for q in star["questions"]:
            assignment[str(q["id"])] = star["id"]
    return {"method": method, "threshold": threshold, "stars": stars, "assignment": assignment}
