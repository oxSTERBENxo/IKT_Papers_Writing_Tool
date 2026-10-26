"""Paper workspaces: configuration, scaffolding, number and citation
traceability, and the Markdown -> DOCX/PDF build.

A workspace is a folder with `paper.json` (paper metadata) and `paper.md`
(the text). Repository-wide defaults (author, styles, tool paths) come from
the nearest `research.json` above it. The text never contains a typed result:
- a number from the analysis is written as a placeholder, `{{res:main.n|,}}`, and filled from the results
  files at build time;
- a citation is written as `[@key]`, where `key` names a verified record in `refs/<key>.json`.

`check` reports anything that is not traced. A draft build always works and
is marked DRAFT. A final build needs:
- an approved, current `manuscript` gate in the project, covering exactly the inputs on disk;
- a check with no blocking issues.
"""
from __future__ import annotations

import datetime
import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from . import checkpoints

ROOT_CONFIG = "research.json"
PAPER_CONFIG = "paper.json"
TEMPLATES = Path(__file__).resolve().parents[2] / "templates" / "manuscript"

DEFAULTS = {
    "title": "", "subtitle": "", "author": "", "affiliation": "", "date": "auto", "date_format": "%B %Y",
    "lang": "en-GB", "keywords": [],
    "source": "paper.md", "results": {"res": "results/results.json"}, "refs_dir": "refs",
    "figures_dir": "figures", "build_dir": "build", "final_dir": "final",
    "css": None, "reference_docx": None, "outputs": ["docx", "pdf"], "pandoc": "auto", "browser": "auto",
    "numbers": {"allow": [], "allow_years": True, "ignore_integers_upto": 10,
                "skip_sections": ["References"],
                "label_words": ["figure", "fig.", "table", "section", "sec.", "appendix", "eq.", "equation",
                                "step", "stage", "chapter", "part", "version", "v", "rq", "h", "page", "p.",
                                "pp.", "week", "weeks", "phase", "item", "line", "row", "column"]},
}
VERIFIED_OK = {"verified"}
VERIFIED_WEAK = {"identifier_resolves"}


class ManuscriptError(ValueError):
    """A request the paper rules refuse. The message says why."""


# ---------------------------------------------------------------- configuration

def find_root_config(start: Path) -> Path | None:
    env = os.environ.get("SRA_RESEARCH_CONFIG")
    if env:
        return Path(env) if Path(env).is_file() else None
    for d in [start.resolve()] + list(start.resolve().parents):
        if (d / ROOT_CONFIG).is_file():
            return d / ROOT_CONFIG
    return None


def find_workspace(start: str | os.PathLike | None) -> Path:
    p = Path(start or ".").resolve()
    if p.is_file():
        p = p.parent
    for d in [p] + list(p.parents):
        if (d / PAPER_CONFIG).is_file():
            return d
    raise ManuscriptError(f"no {PAPER_CONFIG} at or above {p}. Create a workspace with `manuscript init`.")


def _merge(base: dict, extra: dict) -> dict:
    out = dict(base)
    for k, v in (extra or {}).items():
        if k.startswith("_") or k == "$comment":
            continue
        out[k] = _merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except ValueError as exc:
        raise ManuscriptError(f"{path} is not valid JSON: {exc}") from None


def load_config(workspace: str | os.PathLike) -> dict:
    """Defaults <- research.json (repository) <- paper.json (workspace). Paths stay relative to the workspace."""
    ws = Path(workspace).resolve()
    root = find_root_config(ws)
    cfg = _merge(DEFAULTS, _read_json(root).get("defaults", _read_json(root)) if root else {})
    cfg = _merge(cfg, _read_json(ws / PAPER_CONFIG))
    cfg["_ws"], cfg["_root_config"] = ws, root
    cfg["_root"] = root.parent if root else ws
    return cfg


def metadata(cfg: dict) -> dict:
    date = cfg.get("date") or "auto"
    if date == "auto":
        date = datetime.date.today().strftime(cfg.get("date_format") or "%B %Y")
    meta = {"title": cfg.get("title") or "", "author": cfg.get("author") or "", "date": date,
            "lang": cfg.get("lang") or "en-GB"}
    for k in ("subtitle", "keywords"):
        if cfg.get(k):
            meta[k] = cfg[k]
    if cfg.get("affiliation"):
        meta["institute"] = cfg["affiliation"]
    return meta


# ---------------------------------------------------------------- scaffolding

def init(directory: str | os.PathLike, title: str, author: str | None = None, project: str | None = None,
         name: str | None = None) -> dict:
    """Create a paper workspace. It belongs to a project: the given one, the one it sits in, or a new one here."""
    ws = Path(directory)
    if (ws / PAPER_CONFIG).exists():
        raise ManuscriptError(f"{ws / PAPER_CONFIG} already exists")
    if ws.exists() and any(p.name in ("paper.md",) for p in ws.iterdir()):
        raise ManuscriptError(f"{ws} already holds a paper.md; refusing to overwrite it")
    ws.mkdir(parents=True, exist_ok=True)
    for sub in ("refs", "results", "figures", "data"):
        (ws / sub).mkdir(exist_ok=True)
    created = []
    for template, target in (("paper.md", "paper.md"), ("ANALYSIS_PLAN.md", "ANALYSIS_PLAN.md"),
                             ("analysis.py", "analysis.py"), ("README.md", "README.md"),
                             ("gitignore.txt", ".gitignore")):
        dest = ws / target
        if not dest.exists():
            text = (TEMPLATES / template).read_text(encoding="utf-8").replace("{{TITLE}}", title)
            dest.write_text(text, encoding="utf-8")
            created.append(target)
    # The project: explicit, enclosing, or a new one in the workspace itself.
    proj_file = checkpoints.project_file(project) if project else checkpoints.find_project_for(ws)
    if proj_file is None:
        proj = checkpoints.init(ws, name or title, f"Paper: {title}")
        proj_file = Path(proj["_file"])
        created.append("project.json")
    elif not proj_file.is_file():
        raise ManuscriptError(f"no project at {proj_file}")
    rel = os.path.relpath(proj_file.parent.resolve(), ws.resolve()).replace(os.sep, "/")
    paper = {"$comment": "Paper metadata. Repository defaults (author, styles, tools) come from research.json.",
             "title": title, "keywords": [], "results": {"res": "results/results.json"},
             "numbers": {"allow": ["0.05", "95%"]}, "project": rel}
    if author:
        paper["author"] = author
    (ws / PAPER_CONFIG).write_text(json.dumps(paper, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    created.insert(0, PAPER_CONFIG)
    return {"workspace": str(ws.resolve()), "created": created, "project": str(proj_file.resolve())}


def project_for(cfg: dict) -> dict | None:
    rel = cfg.get("project")
    f = checkpoints.project_file(cfg["_ws"] / rel) if rel else checkpoints.find_project_for(cfg["_ws"])
    return checkpoints.load(f) if f and Path(f).is_file() else None


# ---------------------------------------------------------------- results and placeholders

PLACEHOLDER = re.compile(r"\{\{\s*([^{}]+?)\s*\}\}")
FENCE = re.compile(r"^\s*(```|~~~)")
INLINE_CODE = re.compile(r"`[^`\n]*`")


def load_results(cfg: dict) -> tuple[dict, list[str]]:
    data, problems = {}, []
    for ns, rel in (cfg.get("results") or {}).items():
        path = cfg["_ws"] / rel
        if not path.is_file():
            problems.append(f"results file '{rel}' (namespace '{ns}') does not exist; run the analysis")
            continue
        data[ns] = {"file": rel, "data": _read_json(path)}
    return data, problems


def parse_path(path: str) -> list:
    """`main.H3[">=7.0"].sensitivity` -> ['main', 'H3', '>=7.0', 'sensitivity']; numeric parts index lists."""
    parts = []
    for m in re.finditer(r'\[\s*"([^"]*)"\s*\]|\[\s*\'([^\']*)\'\s*\]|\[(\d+)\]|([^.\[\]]+)', path):
        if m.group(1) is not None or m.group(2) is not None:
            parts.append(m.group(1) if m.group(1) is not None else m.group(2))
        elif m.group(3) is not None:
            parts.append(int(m.group(3)))
        else:
            parts.append(m.group(4))
    return parts


def lookup(results: dict, ref: str, default_ns: str | None) -> tuple[object, str, str]:
    """Value, namespace and path of a placeholder reference like `res:main.n` or `main.n`."""
    ns, _, path = ref.partition(":") if ":" in ref.split("[")[0] else (default_ns, "", ref)
    if ns not in results:
        raise KeyError(f"unknown results namespace '{ns}'")
    value = results[ns]["data"]
    for part in parse_path(path):
        if isinstance(value, list) and isinstance(part, (int, str)) and str(part).isdigit():
            idx = int(part)
            if idx >= len(value):
                raise KeyError(f"'{path}': index {idx} out of range")
            value = value[idx]
        elif isinstance(value, dict) and str(part) in value:
            value = value[str(part)]
        else:
            raise KeyError(f"'{path}' not found in {results[ns]['file']} (no '{part}')")
    return value, ns, path


SUPERSCRIPT = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")


def format_value(value, spec: str) -> str:
    """Python format spec, plus `p` (p-value: '< 0.001' or 3 decimals) and `sci` / `sciN` (1.2 × 10⁻⁵)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        if spec:
            raise ValueError(f"cannot apply format '{spec}' to a non-number ({value!r})")
        return str(value)
    if spec == "p":
        return "< 0.001" if value < 0.001 else f"{value:.3f}"
    m = re.fullmatch(r"sci(\d?)", spec or "")
    if m:
        if value == 0:
            return "0"
        digits = int(m.group(1) or 1)
        exp = int(f"{value:e}".split("e")[1])
        mant = value / 10 ** exp
        return f"{mant:.{digits}f} × 10{str(exp).translate(SUPERSCRIPT)}"
    return format(value, spec) if spec else str(value)


def render_placeholders(text: str, results: dict, cfg: dict) -> tuple[str, list[dict], list[str]]:
    default_ns = next(iter(cfg.get("results") or {"res": None}))
    trace, errors, out_lines, in_fence = [], [], [], False
    for lineno, line in enumerate(text.split("\n"), 1):
        if FENCE.match(line):
            in_fence = not in_fence
        if in_fence or FENCE.match(line):
            out_lines.append(line)
            continue
        codes = {m.span() for m in INLINE_CODE.finditer(line)}

        def repl(m):
            if any(a <= m.start() < b for a, b in codes):
                return m.group(0)
            body = m.group(1)
            if body == "references":
                return m.group(0)  # filled by the citation step
            ref, _, spec = body.partition("|")
            try:
                value, ns, path = lookup(results, ref.strip(), default_ns)
                rendered = format_value(value, spec.strip())
            except (KeyError, ValueError) as exc:
                errors.append(f"line {lineno}: placeholder {{{{{body}}}}}: {exc}")
                return f"**[?{body}]**"
            trace.append({"line": lineno, "placeholder": body, "namespace": ns, "path": path,
                          "file": results[ns]["file"], "value": value, "rendered": rendered})
            return rendered

        out_lines.append(PLACEHOLDER.sub(repl, line))
    return "\n".join(out_lines), trace, errors


# ---------------------------------------------------------------- literal number scan

NUMBER = re.compile(r"(?<![\w.⁰¹²³⁴⁵⁶⁷⁸⁹/#-])([-−]?)(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)(\s?%)?(?![\w.]*\d)(?![\w⁻⁰¹²³⁴⁵⁶⁷⁸⁹])")


def numeric_leaves(data, prefix="") -> list[tuple[str, float]]:
    out = []
    if isinstance(data, dict):
        for k, v in data.items():
            out += numeric_leaves(v, f"{prefix}.{k}" if prefix else str(k))
    elif isinstance(data, list):
        for i, v in enumerate(data):
            out += numeric_leaves(v, f"{prefix}[{i}]")
    elif isinstance(data, (int, float)) and not isinstance(data, bool):
        out.append((prefix, float(data)))
    return out


def _strip_for_scan(line: str) -> str:
    line = INLINE_CODE.sub(" ", line)
    line = PLACEHOLDER.sub(" ", line)
    line = re.sub(r"<!--.*?-->", " ", line)
    line = re.sub(r"\]\([^)]*\)", "] ", line)          # link and image targets
    line = re.sub(r"https?://\S+|doi:\S+|10\.\d{4,}/\S+", " ", line)
    line = re.sub(r"\[[^\[\]]*@[^\[\]]*\]", " ", line)  # citations
    line = re.sub(r"^\s*#{1,6}\s+[\dA-Z]+(\.\d+)*\.?\s", "# ", line)  # section numbers
    line = re.sub(r"^\s*\d+\.\s", " ", line)           # ordered-list markers
    return line


def scan_numbers(text: str, results: dict, cfg: dict) -> list[dict]:
    """Every number typed into the text (outside placeholders), and whether a result explains it."""
    ncfg = cfg.get("numbers") or {}
    allow = {a.replace(" ", "").replace(",", "") for a in ncfg.get("allow", [])}
    skip_sections = {s.lower() for s in ncfg.get("skip_sections", [])}
    labels = {w.lower() for w in ncfg.get("label_words", [])}
    small = ncfg.get("ignore_integers_upto", 10)
    leaves = [(results[ns]["file"], f"{ns}:{p}", v) for ns in results for p, v in numeric_leaves(results[ns]["data"])]
    found, in_fence, in_front, skipping = [], False, False, False
    lines = text.split("\n")
    for lineno, raw in enumerate(lines, 1):
        if lineno == 1 and raw.strip() == "---":
            in_front = True
            continue
        if in_front:
            in_front = raw.strip() not in ("---", "...")
            continue
        if FENCE.match(raw):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        h = re.match(r"^\s*#{1,6}\s+(.*)", raw)
        if h:
            heading = re.sub(r"^[\dA-Z]+(\.\d+)*\.?\s+", "", h.group(1)).strip().lower()
            skipping = heading in skip_sections
        if skipping or raw.lstrip().startswith("!["):
            continue
        line = _strip_for_scan(raw)
        for m in NUMBER.finditer(line):
            sign, digits, pct = m.group(1), m.group(2), bool(m.group(3))
            literal = (sign and "-") + digits + ("%" if pct else "")
            plain = digits.replace(",", "")
            before = line[: m.start()].rstrip().split()
            prev = before[-1].lower().rstrip("(") if before else ""
            entry = {"line": lineno, "text": literal, "status": "untraced", "matches": []}
            value = float(plain) * (-1 if sign else 1)
            decimals = len(plain.split(".")[1]) if "." in plain else 0
            if literal.replace(",", "") in allow or plain in allow:
                entry["status"] = "allowed"
            elif prev in labels:
                entry["status"] = "label"
            elif decimals == 0 and not pct and ncfg.get("allow_years", True) and 1900 <= value <= 2100 \
                    and "," not in digits:
                entry["status"] = "year"
            elif decimals == 0 and not pct and abs(value) <= small:
                entry["status"] = "small_integer"
            else:
                # A typed number is explained by a result that rounds to it at the precision shown,
                # either as stored or as a percentage of a proportion.
                tol = 0.5 * 10 ** -decimals + 1e-9 * max(1.0, abs(value))
                for _file, key, v in leaves:
                    if abs(v - value) <= tol:
                        entry["matches"].append(key)
                    elif abs(v * 100 - value) <= tol:
                        entry["matches"].append(f"{key} x100")
                if entry["matches"]:
                    entry["status"] = "matched"
            found.append(entry)
    return found


# ---------------------------------------------------------------- references and citations

KEY = r"[A-Za-z0-9_][\w:.#$%&+?<>~/-]*[\w]|[A-Za-z0-9_]"
BRACKET_CITE = re.compile(r"\[([^\[\]]*?@(?:" + KEY + r")[^\[\]]*)\](?!\()")
NARRATIVE_CITE = re.compile(r"(?<![\w@\[])@(" + KEY + r")")


def load_refs(cfg: dict) -> dict:
    refs = {}
    d = cfg["_ws"] / cfg.get("refs_dir", "refs")
    for f in sorted(d.glob("*.json")) if d.is_dir() else []:
        data = _read_json(f)
        paper = data.get("paper") if isinstance(data.get("paper"), dict) else data
        key = data.get("key") or f.stem
        refs[key] = {"key": key, "paper": paper, "verification": data.get("verification") or paper.get("verification"),
                     "file": f.relative_to(cfg["_ws"]).as_posix()}
    return refs


PARTICLES = {"van", "von", "de", "der", "den", "da", "di", "du", "del", "della", "le", "la", "ter", "dos", "das",
             "bin", "al", "el"}
SUFFIXES = {"jr", "jr.", "sr", "sr.", "ii", "iii", "iv"}


def _family_given(name: str) -> tuple[str, str]:
    """('Massacci', 'Fabio') from 'Fabio Massacci' or 'Massacci, Fabio'; keeps particles such as 'van'."""
    name = re.sub(r"\s+", " ", (name or "").strip())
    if "," in name:
        fam, given = [x.strip() for x in name.split(",", 1)]
        return fam, given
    toks = [t for t in name.split(" ") if t]
    while len(toks) > 1 and toks[-1].lower() in SUFFIXES:
        toks = toks[:-1]
    if not toks:
        return name, ""
    i = len(toks) - 1
    while i > 0 and toks[i - 1].lower() in PARTICLES:
        i -= 1
    return " ".join(toks[i:]), " ".join(toks[:i])


def _initials(given: str) -> str:
    parts = [p for p in re.split(r"[\s.]+", given) if p]
    out = []
    for p in parts:
        out.append("-".join(s[0].upper() + "." for s in p.split("-") if s))
    return " ".join(out)


def _label(paper: dict, narrative: bool) -> str:
    authors = paper.get("authors") or []
    fams = [_family_given(a)[0] for a in authors]
    if not fams:
        return (paper.get("title") or "Anonymous")[:40]
    if len(fams) == 1:
        return fams[0]
    if len(fams) == 2:
        return f"{fams[0]} {'and' if narrative else '&'} {fams[1]}"
    return f"{fams[0]} et al."


def year_labels(refs: dict, keys: list[str]) -> dict:
    """APA year with a/b suffixes when the same authors share a year."""
    groups: dict[tuple, list[str]] = {}
    for k in keys:
        p = refs[k]["paper"]
        groups.setdefault((_label(p, False), p.get("year")), []).append(k)
    out = {}
    for (label, year), ks in groups.items():
        ks = sorted(ks, key=lambda k: (refs[k]["paper"].get("title") or "").lower())
        for i, k in enumerate(ks):
            out[k] = f"{year or 'n.d.'}{chr(97 + i) if len(ks) > 1 else ''}"
    return out


def apa_reference(paper: dict, year: str) -> str:
    authors = paper.get("authors") or []
    names = []
    for a in authors:
        fam, given = _family_given(a)
        names.append(f"{fam}, {_initials(given)}".strip().rstrip(","))
    if len(names) > 20:
        who = ", ".join(names[:19]) + ", … " + names[-1]
    elif len(names) > 1:
        who = ", ".join(names[:-1]) + ", & " + names[-1]
    else:
        who = names[0] if names else ""
    title = (paper.get("title") or "Untitled").rstrip(".")
    venue = paper.get("venue") or ""
    doi = paper.get("doi")
    is_preprint = bool(paper.get("arxiv_id")) and not (doi and not doi.lower().startswith("10.48550"))
    kind = (paper.get("type") or "").lower()
    bits = [f"{who} ({year})." if who else f"{title}. ({year})."]
    if who:
        bits.append(f"{title}{' [Data set]' if kind == 'dataset' else ''}.")
    if is_preprint:
        bits.append(f"*arXiv preprint* arXiv:{paper['arxiv_id']}.")
    elif venue:
        bits.append(f"*{venue}*.")
    if doi and not doi.lower().startswith("10.48550"):
        bits.append(f"https://doi.org/{doi}")
    elif paper.get("arxiv_id"):
        bits.append(f"https://arxiv.org/abs/{paper['arxiv_id']}")
    elif paper.get("url"):
        bits.append(paper["url"])
    return " ".join(bits)


def render_citations(text: str, refs: dict) -> tuple[str, list[str], list[str]]:
    """Replace [@key] and @key with APA author-year citations. Returns text, cited keys, missing keys."""
    cited, missing = [], []
    lines, in_fence = text.split("\n"), False
    # Pass 1: collect keys in order so year suffixes are stable.
    for line in lines:
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        clean = INLINE_CODE.sub(" ", line)
        for m in BRACKET_CITE.finditer(clean):
            for k in re.findall(r"@(" + KEY + r")", m.group(1)):
                (cited if k in refs else missing).append(k)
        for m in NARRATIVE_CITE.finditer(BRACKET_CITE.sub(" ", clean)):
            (cited if m.group(1) in refs else missing).append(m.group(1))
    cited = list(dict.fromkeys(cited))
    years = year_labels(refs, cited)

    def one(item: str) -> str:
        m = re.search(r"@(" + KEY + r")", item)
        if not m:
            return item.strip()
        k = m.group(1)
        prefix, suffix = item[: m.start()].strip(), item[m.end():].strip().lstrip(",").strip()
        if k not in refs:
            return f"**[?{k}]**"
        core = f"{_label(refs[k]['paper'], False)}, {years[k]}"
        return " ".join(x for x in (prefix, core + (f", {suffix}" if suffix else "")) if x)

    out, in_fence = [], False
    for line in lines:
        if FENCE.match(line):
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence:
            out.append(line)
            continue
        codes = [m.span() for m in INLINE_CODE.finditer(line)]

        def bracket(m):
            if any(a <= m.start() < b for a, b in codes):
                return m.group(0)
            return "(" + "; ".join(one(part) for part in m.group(1).split(";")) + ")"

        def narrative(m):
            if any(a <= m.start() < b for a, b in codes):
                return m.group(0)
            k = m.group(1)
            if k not in refs:
                return f"**[?{k}]**"
            return f"{_label(refs[k]['paper'], True)} ({years[k]})"

        line = BRACKET_CITE.sub(bracket, line)
        line = NARRATIVE_CITE.sub(narrative, line)
        out.append(line)
    return "\n".join(out), cited, list(dict.fromkeys(missing))


def reference_list(refs: dict, cited: list[str]) -> str:
    years = year_labels(refs, cited)

    def sort_key(k):
        p = refs[k]["paper"]
        fam = _family_given((p.get("authors") or [p.get("title") or ""])[0])[0]
        return (fam.lower(), years[k], (p.get("title") or "").lower())

    return "\n\n".join(apa_reference(refs[k]["paper"], years[k]) for k in sorted(cited, key=sort_key))


def cite(cfg: dict, ident: str, key: str, client, overwrite: bool = False) -> dict:
    """Resolve an identifier through the literature APIs, verify it, and save refs/<key>.json."""
    from . import search, verify
    if not re.fullmatch(KEY, key):
        raise ManuscriptError(f"'{key}' is not a usable citation key (letters, digits, _ : . - only)")
    target = cfg["_ws"] / cfg.get("refs_dir", "refs") / f"{key}.json"
    if target.exists() and not overwrite:
        raise ManuscriptError(f"{target.name} already exists; pass --overwrite to replace it")
    paper, notes = search.resolve(client, ident)
    if paper is None:
        raise ManuscriptError(f"could not resolve '{ident}'; it cannot be cited until it resolves")
    record = paper.to_dict()
    verification = verify.verify_paper(client, record)
    target.parent.mkdir(parents=True, exist_ok=True)
    data = {"key": key, "identifier": ident, "added": datetime.date.today().isoformat(), "paper": record,
            "verification": verification, "notes": notes}
    target.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return data


def verify_refs(cfg: dict, client) -> dict:
    from . import verify
    counts: dict[str, int] = {}
    for key, ref in load_refs(cfg).items():
        path = cfg["_ws"] / ref["file"]
        data = _read_json(path)
        paper = data.get("paper") if isinstance(data.get("paper"), dict) else data
        data["verification"] = verify.verify_paper(client, paper)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        counts[data["verification"]["status"]] = counts.get(data["verification"]["status"], 0) + 1
    return counts


# ---------------------------------------------------------------- check

def _issue(level: str, kind: str, message: str) -> dict:
    return {"level": level, "kind": kind, "message": message}


def check(cfg: dict) -> dict:
    """Everything the final build would refuse (`error`) or would like fixed (`warning`)."""
    ws = cfg["_ws"]
    issues = []
    src = ws / cfg.get("source", "paper.md")
    if not src.is_file():
        raise ManuscriptError(f"manuscript source {src} does not exist")
    text = src.read_text(encoding="utf-8")
    for field in ("title", "author"):
        if not (cfg.get(field) or "").strip():
            issues.append(_issue("error", "metadata", f"'{field}' is empty (paper.json or research.json)"))
    results, problems = load_results(cfg)
    issues += [_issue("error", "results", p) for p in problems]
    rendered, trace, ph_errors = render_placeholders(text, results, cfg)
    issues += [_issue("error", "placeholder", e) for e in ph_errors]
    numbers = scan_numbers(text, results, cfg)
    for n in numbers:
        if n["status"] == "untraced":
            issues.append(_issue("error", "untraced_number",
                                 f"line {n['line']}: '{n['text']}' matches no value in the results files; use a "
                                 "placeholder, add the value to the analysis, or allow it in paper.json"))
        elif n["status"] == "matched":
            issues.append(_issue("warning", "typed_number",
                                 f"line {n['line']}: '{n['text']}' is typed but equals {', '.join(n['matches'][:3])}; "
                                 "prefer a placeholder so it updates with the analysis"))
    refs = load_refs(cfg)
    _, cited, missing = render_citations(rendered, refs)
    for k in missing:
        issues.append(_issue("error", "citation", f"[@{k}] has no refs/{k}.json; add it with `manuscript cite`"))
    for k in cited:
        status = (refs[k]["verification"] or {}).get("status", "unchecked")
        if status in VERIFIED_WEAK:
            issues.append(_issue("warning", "reference", f"@{k}: identifier resolves but its title was not checked"))
        elif status not in VERIFIED_OK:
            issues.append(_issue("error", "reference", f"@{k}: verification status '{status}'; run "
                                 "`manuscript verify-refs` or replace the reference"))
    for k in sorted(set(refs) - set(cited)):
        issues.append(_issue("warning", "unused_reference", f"refs/{refs[k]['file'].split('/')[-1]} is never cited"))
    if cited and "{{references}}" not in text:
        issues.append(_issue("warning", "references", "no {{references}} marker; a References section is appended"))
    for lineno, line in enumerate(text.split("\n"), 1):
        if re.search(r"\bTODO\b", INLINE_CODE.sub(" ", line)):
            issues.append(_issue("error", "todo", f"line {lineno}: TODO left in the text"))
        for m in re.finditer(r"!\[[^\]]*\]\(([^)\s]+)", line):
            if not m.group(1).startswith(("http://", "https://", "data:")) and not (ws / m.group(1)).is_file():
                issues.append(_issue("error", "figure", f"line {lineno}: figure '{m.group(1)}' does not exist"))
    counts = {s: sum(1 for n in numbers if n["status"] == s) for s in
              ("untraced", "matched", "allowed", "label", "year", "small_integer")}
    for reason in final_outdated(cfg):
        issues.append(_issue("warning", "final_outdated", f"final/ is out of date ({reason}); it is left as it is. "
                             "Rebuild it only after the user approves the current manuscript."))
    return {"issues": issues, "errors": sum(1 for i in issues if i["level"] == "error"),
            "warnings": sum(1 for i in issues if i["level"] == "warning"),
            "placeholders": trace, "numbers": numbers, "number_counts": counts,
            "citations": [{"key": k, "file": refs[k]["file"],
                           "status": (refs[k]["verification"] or {}).get("status", "unchecked")} for k in cited]}


# ---------------------------------------------------------------- inputs and tools

def final_outdated(cfg: dict) -> list[str]:
    """Why the files in final/ no longer match the approved sources (empty if they do, or if there is no final).
    Only reports: the final folder is never rebuilt or deleted automatically."""
    out_dir = cfg["_ws"] / cfg.get("final_dir", "final")
    mf = out_dir / "MANIFEST.json"
    if not mf.is_file():
        return []
    try:
        manifest = json.loads(mf.read_text(encoding="utf-8"))
    except ValueError:
        return [f"{mf.name} is not valid JSON"]
    reasons = []
    project = project_for(cfg)
    if project is not None:
        recorded = manifest.get("inputs") or {}
        changed = checkpoints.changed_files(project, recorded)
        if changed:
            reasons.append("sources changed since the final build: " + ", ".join(changed[:6]))
        current = checkpoints.hash_files(project, [str(f) for f in inputs(cfg)])
        added = [k for k in current if k not in recorded]
        if added:
            reasons.append("new inputs not in the final build: " + ", ".join(added[:6]))
        st = checkpoints.evaluate(project).get("manuscript") or {}
        approved = (manifest.get("approval") or {}).get("version")
        if st.get("state") != checkpoints.APPROVED or st.get("version") != approved:
            reasons.append(f"the final was built from manuscript v{approved}, which is no longer the approved, "
                           f"current version (now: v{st.get('version')} {st.get('state')})")
    for name, digest in (manifest.get("outputs") or {}).items():
        f = out_dir / name
        if not f.is_file():
            reasons.append(f"final/{name} is missing")
        elif _sha(f) != digest:
            reasons.append(f"final/{name} was changed after the build")
    return reasons


def inputs(cfg: dict) -> list[Path]:
    """Every file the manuscript is built from. A final build must be covered by the approval of these."""
    ws = cfg["_ws"]
    files = [ws / PAPER_CONFIG, ws / cfg.get("source", "paper.md")]
    files += [ws / rel for rel in (cfg.get("results") or {}).values()]
    files += sorted((ws / cfg.get("refs_dir", "refs")).glob("*.json"))
    text = files[1].read_text(encoding="utf-8") if files[1].is_file() else ""
    for m in re.finditer(r"!\[[^\]]*\]\(([^)\s]+)", text):
        if not m.group(1).startswith(("http://", "https://", "data:")):
            files.append(ws / m.group(1))
    for extra in (cfg.get("css"), cfg.get("reference_docx")):
        if extra:
            files.append(ws / extra)
    if cfg.get("_root_config"):
        files.append(cfg["_root_config"])
    return [f for f in dict.fromkeys(f.resolve() for f in files) if f.is_file()]


def find_pandoc(cfg: dict) -> str | None:
    explicit = cfg.get("pandoc")
    if explicit and explicit != "auto":
        p = Path(explicit)
        p = p if p.is_absolute() else cfg["_root"] / p
        return str(p) if p.is_file() else None
    for cand in (os.environ.get("SRA_PANDOC"), shutil.which("pandoc")):
        if cand and Path(cand).is_file():
            return cand
    try:
        import pypandoc  # optional: pypandoc_binary ships pandoc
        found = Path(pypandoc.get_pandoc_path())
        for cand in (found, found.with_name(found.name + ".exe")):  # pypandoc may omit ".exe" on Windows
            if cand.is_file():
                return str(cand)
    except Exception:  # noqa: BLE001 - absent or broken: fall through
        pass
    # The repository's own venv first (`.venv\Scripts\python -m pip install pypandoc_binary`), then a pandoc
    # that another project's virtual environment already installed.
    for pattern in (".venv/Lib/site-packages/pypandoc/files/pandoc.exe",
                    ".venv/lib/python*/site-packages/pypandoc/files/pandoc",
                    "*/.venv/Lib/site-packages/pypandoc/files/pandoc.exe",
                    "*/.venv/lib/python*/site-packages/pypandoc/files/pandoc"):
        hits = sorted(glob.glob(str(cfg["_root"] / pattern)))
        if hits:
            return hits[0]
    return None


def find_browser(cfg: dict) -> str | None:
    explicit = cfg.get("browser")
    if explicit and explicit != "auto":
        return explicit if Path(explicit).is_file() else None
    cands = [os.environ.get("SRA_BROWSER"),
             r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
             r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
             r"C:\Program Files\Google\Chrome\Application\chrome.exe",
             shutil.which("msedge"), shutil.which("google-chrome"), shutil.which("chromium"), shutil.which("chrome")]
    return next((c for c in cands if c and Path(c).is_file()), None)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------- build

def resolved_markdown(cfg: dict, draft_banner: str = "") -> tuple[str, dict]:
    text = (cfg["_ws"] / cfg.get("source", "paper.md")).read_text(encoding="utf-8")
    results, _ = load_results(cfg)
    text, _, _ = render_placeholders(text, results, cfg)
    refs = load_refs(cfg)
    text, cited, _ = render_citations(text, refs)
    listing = reference_list(refs, cited) if cited else ""
    if "{{references}}" in text:
        text = text.replace("{{references}}", listing)
    elif cited:
        text = text.rstrip() + "\n\n# References\n\n" + listing + "\n"
    if draft_banner:
        text = draft_banner + "\n\n" + text
    return text, {"cited": cited}


def build(cfg: dict, final: bool = False, formats: list[str] | None = None, runner=subprocess.run) -> dict:
    """Write the resolved Markdown and the requested formats. Draft: build/paper.draft.*. Final: final/paper.*"""
    ws = cfg["_ws"]
    formats = [f for f in (formats or cfg.get("outputs") or ["docx", "pdf"]) if f in ("docx", "pdf", "html")]
    report = check(cfg)
    project = project_for(cfg)
    approval = None
    if final:
        problems = []
        if project is None:
            problems.append("the workspace belongs to no project, so there is no manuscript approval to check")
        else:
            problems += checkpoints.require(project, ["manuscript"])
            if not problems:
                st = checkpoints.evaluate(project)["manuscript"]
                version = project["checkpoints"]["manuscript"]["versions"][-1]
                approved = version["artifacts"]
                current = checkpoints.hash_files(project, [str(p) for p in inputs(cfg)])
                uncovered = [k for k, h in current.items() if approved.get(k) != h]
                if uncovered:
                    problems.append("inputs not covered by the approved manuscript version: " + ", ".join(uncovered))
                approval = {"version": st["version"], "hash": st["hash"], "said": st["decision"]["said"],
                            "by": st["decision"]["by"], "at": st["decision"]["at"]}
        if report["errors"]:
            problems.append(f"{report['errors']} blocking issue(s) in `manuscript check`")
        if problems:
            raise ManuscriptError("final build refused:\n  - " + "\n  - ".join(problems))
        # A final build delivers every configured format or nothing: no "final" with the DOCX or PDF missing.
        if formats and not find_pandoc(cfg):
            raise ManuscriptError("final build refused: pandoc not found, so " + "/".join(formats) + " cannot be built "
                                  "(set \"pandoc\" in research.json, SRA_PANDOC, or `pip install pypandoc_binary`)")
        if "pdf" in formats and not find_browser(cfg):
            raise ManuscriptError("final build refused: no Edge or Chrome found for the PDF (set \"browser\" in "
                                  "research.json or SRA_BROWSER)")
    out_dir = ws / (cfg.get("final_dir", "final") if final else cfg.get("build_dir", "build"))
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = "paper" if final else "paper.draft"
    banner = "" if final else (
        f"> **DRAFT, not approved for submission.** Built {checkpoints.now()[:16]} UTC. "
        f"{report['errors']} blocking issue(s) and {report['warnings']} warning(s) in `manuscript check`.")
    text, info = resolved_markdown(cfg, banner)
    md = out_dir / f"{stem}.md"
    md.write_text(text, encoding="utf-8")
    meta = out_dir / f"{stem}.meta.json"
    meta.write_text(json.dumps(metadata(cfg), indent=2, ensure_ascii=False), encoding="utf-8")
    written, skipped = [md], []
    pandoc = find_pandoc(cfg) if formats else None
    if formats and not pandoc:
        skipped.append("docx/pdf: pandoc not found (set \"pandoc\" in research.json, SRA_PANDOC, or "
                       "`pip install pypandoc_binary`)")
    common = ["--metadata-file", str(meta), "--resource-path", str(ws), "--from", "markdown"]
    if pandoc and "docx" in formats:
        docx = out_dir / f"{stem}.docx"
        cmd = [pandoc, str(md), "-o", str(docx)] + common
        if cfg.get("reference_docx"):
            cmd += ["--reference-doc", str(ws / cfg["reference_docx"])]
        _run(runner, cmd, "pandoc (docx)")
        written.append(docx)
    if pandoc and ("pdf" in formats or "html" in formats):
        css = ws / cfg["css"] if cfg.get("css") else TEMPLATES / "paper_print.css"
        html = out_dir / f"{stem}.html"
        _run(runner, [pandoc, str(md), "-s", "--embed-resources", "--mathml", "--css", str(css), "-o", str(html)]
             + common, "pandoc (html)")
        if "html" in formats:
            written.append(html)
        if "pdf" in formats:
            browser = find_browser(cfg)
            if not browser:
                skipped.append("pdf: no Edge or Chrome found (set \"browser\" in research.json or SRA_BROWSER)")
            else:
                pdf = out_dir / f"{stem}.pdf"
                with tempfile.TemporaryDirectory() as profile:
                    _run(runner, [browser, "--headless", "--disable-gpu", "--no-first-run",
                                  f"--user-data-dir={profile}", "--no-pdf-header-footer",
                                  "--print-to-pdf-no-header", f"--print-to-pdf={pdf}", html.resolve().as_uri()],
                         "browser (pdf)")
                if not pdf.is_file():
                    raise ManuscriptError(f"the browser did not write {pdf}")
                written.append(pdf)
    (out_dir / f"{stem}.check.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str),
                                                encoding="utf-8")
    result = {"final": final, "outputs": [str(p) for p in written], "skipped": skipped, "check": report,
              "cited": info["cited"]}
    if final:
        manifest = {"built_at": checkpoints.now(), "approval": approval,
                    "inputs": checkpoints.hash_files(project, [str(p) for p in inputs(cfg)]),
                    "outputs": {p.name: _sha(p) for p in written},
                    "placeholders": len(report["placeholders"]), "number_counts": report["number_counts"],
                    "citations": report["citations"]}
        (out_dir / "MANIFEST.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        checkpoints._log(project, "manuscript_finalized", "manuscript", approval["version"],
                         ", ".join(p.name for p in written))
        checkpoints.save(project)
        result["manifest"] = str(out_dir / "MANIFEST.json")
    return result


def _run(runner, cmd: list[str], what: str) -> None:
    proc = runner(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise ManuscriptError(f"{what} failed (exit {proc.returncode}): {(proc.stderr or proc.stdout or '')[-800:]}")


# ---------------------------------------------------------------- manuscript gate

def review(cfg: dict, summary: str = "", risks: list[str] | None = None, runner=subprocess.run) -> dict:
    """Build a draft and propose the manuscript gate with every input attached. Refused while the check fails."""
    project = project_for(cfg)
    if project is None:
        raise ManuscriptError("the workspace belongs to no project; create one or set \"project\" in paper.json")
    draft = build(cfg, final=False, runner=runner)
    rep = draft["check"]
    if rep["errors"]:
        raise ManuscriptError(f"{rep['errors']} blocking issue(s) remain; fix them before asking for approval "
                              "(the draft was still written: " + ", ".join(Path(p).name for p in draft["outputs"])
                              + ")")
    c = rep["number_counts"]
    items = [f"Numbers: {len(rep['placeholders'])} from placeholders, {c['matched']} typed values that equal a "
             f"result, {c['allowed']} allowed constants, 0 untraced",
             f"References: {len(rep['citations'])} cited, all with verification status "
             + ", ".join(sorted({x['status'] for x in rep['citations']}) or ["none"]),
             "Draft for review: " + ", ".join(Path(p).name for p in draft["outputs"])]
    warn = [i["message"] for i in rep["issues"] if i["level"] == "warning"][:8]
    version = checkpoints.propose(
        project, "manuscript", summary or f"Finalise \"{cfg.get('title')}\" for submission.", items,
        (risks or []) + warn, "Approve to allow the final build; drafts never need approval.",
        [str(p) for p in inputs(cfg)])
    return {"version": version, "draft": draft}
