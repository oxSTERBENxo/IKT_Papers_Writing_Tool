"""Optional semantic similarity from a small local embedding model (CPU, no API, no GPU needed).

Nothing here is required: the toolkit stays standard-library only. If neither backend is installed, available()
returns False and callers fall back to lexical ranking and say so.

Backends, tried in order:
- model2vec (static embeddings; numpy only; default model minishlab/potion-base-8M, about 30 MB):
      pip install model2vec
- sentence-transformers (needs PyTorch; e.g. sentence-transformers/all-MiniLM-L6-v2):
      pip install sentence-transformers
Set SRA_EMBED_MODEL to choose a model, and SRA_EMBED_BACKEND=model2vec|sentence-transformers to force a backend.
The model is downloaded once by the backend library into its own cache (Hugging Face hub cache).

Embeddings only re-rank candidates that a lexical source already returned. They cannot find a paper that no
search returned.
"""
from __future__ import annotations

import math
import os

DEFAULT_MODELS = {"model2vec": "minishlab/potion-base-8M",
                  "sentence-transformers": "sentence-transformers/all-MiniLM-L6-v2"}
_cache: dict = {}


def _load():
    if "model" in _cache:
        return _cache["model"]
    forced = os.environ.get("SRA_EMBED_BACKEND")
    order = [forced] if forced else ["model2vec", "sentence-transformers"]
    model, err = None, []
    for backend in order:
        name = os.environ.get("SRA_EMBED_MODEL") or DEFAULT_MODELS.get(backend, "")
        try:
            if backend == "model2vec":
                from model2vec import StaticModel  # type: ignore
                m = StaticModel.from_pretrained(name)
                model = (backend, name, lambda texts: [list(map(float, v)) for v in m.encode(texts)])
            elif backend == "sentence-transformers":
                from sentence_transformers import SentenceTransformer  # type: ignore
                m = SentenceTransformer(name, device="cpu")
                model = (backend, name, lambda texts: [list(map(float, v)) for v in m.encode(texts)])
            if model:
                break
        except Exception as exc:  # missing package, no network for first download, bad model name
            err.append(f"{backend}: {type(exc).__name__}: {exc}"[:200])
    _cache["model"], _cache["errors"] = model, err
    return model


def available() -> bool:
    return _load() is not None


def describe() -> str:
    m = _load()
    return f"{m[0]}:{m[1]}" if m else "unavailable (" + "; ".join(_cache.get("errors") or ["no backend"]) + ")"


def _cos(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def similarities(query_texts: list[str], docs: list[str]) -> list[float] | None:
    """Max cosine similarity of each doc to any query text, or None when no backend is available."""
    m = _load()
    if m is None or not docs:
        return None
    encode = m[2]
    qv = encode(query_texts)
    dv = encode([d[:2000] for d in docs])
    return [max(_cos(q, d) for q in qv) for d in dv]
