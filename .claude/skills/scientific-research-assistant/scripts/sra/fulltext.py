"""Fetch the accessible full text of a paper and pull out the parts an
adversarial reader needs: methodology, experiments, ablations, baselines,
limitations and related work, plus sentences that state evaluation details.

Only legitimately open sources are used: the arXiv e-print (LaTeX source) and
arXiv HTML. For anything else the result says the text was not accessible and
lists the open-access PDF link, if one is known, for manual reading.

The flags are sentence-level pattern matches. They point a reader at the
passages to check; they do not establish what a paper did.
"""
from __future__ import annotations

import gzip
import html
import io
import re
import tarfile

from .http import SourceError
from .models import parse_identifier

MAX_SOURCE_BYTES = 25_000_000   # refuse larger e-print archives
MAX_MEMBER_BYTES = 3_000_000    # ignore single .tex files larger than this
CACHE_VERSION = "sra-fulltext:v1:"

# section role -> heading pattern
ROLES = {
    "method": r"method|approach|model|framework|proposed",
    "data": r"data ?set|data$|benchmark|corpus|corpora",
    "experiments": r"experiment|evaluation|setup|setting|implementation|training",
    "results": r"result|performance|comparison|main",
    "ablation": r"ablation|analysis|variant|component|sensitivity",
    "baselines": r"baseline",
    "limitations": r"limitation|discussion|threats|future|conclusion|broader",
    "related_work": r"related|background|prior work|literature",
}

# flag -> sentence pattern (case-insensitive)
FLAGS = {
    "runs_and_seeds": r"\b(\d+|five|ten|three)\s+(independent\s+|different\s+|random\s+)?(runs|seeds|trials|repetitions)\b|"
                      r"random seeds?|averaged over|mean (±|\+/-|and standard deviation)",
    "split_protocol": r"\b\d{1,2}\s*%?\s*[-/:]\s*\d{1,2}\s*%?\s*[-/:]\s*\d{1,2}\s*%|train(ing)?[- /](val(idation)?[- /])?test split|"
                      r"cross[- ]validation|\bk-fold|\d+-fold|random split|temporal split|chronolog|split by (time|user|author|source)",
    "validation_only_reporting": r"(report|we report)[^.]{0,60}validation (accuracy|performance|score)|"
                                 r"mean validation accuracy|best (validation|val) (accuracy|epoch)",
    "variance_reported": r"±|\+/-|standard deviation|confidence interval|\bstd\b|t-test|wilcoxon|significan",
    "structure_free_baseline": r"\bMLP\b|multilayer perceptron|logistic regression|bag[- ]of[- ]words|"
                               r"(content|text|news|feature)[- ]only|without (the )?(graph|edges|structure)|"
                               r"structure[- ]agnostic|no[- ]graph",
    "ablation_or_control": r"ablation|remove[sd]? (all |the )?edges|shuffl|randomi[sz]ed? (edges|features|labels)|"
                           r"rewir|w/o|variant without|(?-i:\(-[A-Z]{2,5}\)|\s-[A-Z]{2,5}\b)",
    "leakage_or_overlap": r"leak|contaminat|overlap|duplicate|same (users?|authors?|entities)|seen (users?|entities)|"
                          r"memori[sz]|shortcut|spurious|future (information|knowledge)",
    "code_or_data_link": r"github\.com/|gitlab\.com/|huggingface\.co/|zenodo\.org/|code (is|will be) (publicly )?available",
    "hardware_and_cost": r"\bGPU\b|\bA100\b|\bH100\b|\bV100\b|RTX|hours? (of|on)|GB (of )?(RAM|memory)",
    "stated_limitation": r"limitation|we leave .{0,40}future|does not (address|consider|handle)|"
                         r"(fails|unable) to|is restricted to|assum(e|es|ing) that",
}


def _tex_to_text(tex: str) -> str:
    tex = re.sub(r"(?<!\\)%.*", "", tex)                       # comments (keep escaped \%)
    tex = re.sub(r"\\begin\{CCSXML\}.*?\\end\{CCSXML\}|\\ccsdesc(\[\d+\])?\{[^}]*\}", " ", tex, flags=re.S)
    tex = re.sub(r"\\begin\{(figure|table)\*?\}.*?\\end\{\1\*?\}",
                 lambda m: _table_text(m.group(0)), tex, flags=re.S)
    tex = re.sub(r"\\(cite|citep|citet|ref|eqref|label)\{[^}]*\}", "", tex)
    tex = re.sub(r"\\(textbf|textit|emph|texttt|underline|mathbf|mathrm|text)\{([^{}]*)\}", r"\2", tex)
    tex = tex.replace("\\%", "%").replace("\\&", "&").replace("\\_", "_").replace("~", " ")
    return tex


def _table_text(block: str) -> str:
    """Keep captions and cell text of floats; tables often hold the numbers that matter."""
    caption = " ".join(re.findall(r"\\caption\{(.*?)\}\s*(?:\\label|$|\n)", block, flags=re.S))
    cells = re.sub(r"\\(hline|toprule|midrule|bottomrule|cline\{[^}]*\})", " ", block)
    cells = re.sub(r"\\(multirow|multicolumn)\{[^}]*\}\{[^}]*\}", " ", cells)
    cells = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?", " ", cells)
    cells = re.sub(r"[{}]", " ", cells).replace("&", "|").replace("\\\\", "\n")
    return f"\n[FLOAT] {caption}\n{cells}\n[/FLOAT]\n"


def split_tex_sections(tex: str) -> list[dict]:
    text = _tex_to_text(tex)
    pattern = re.compile(r"\\(section|subsection|subsubsection|paragraph)\*?\{([^}]*)\}")
    out, last, last_head, last_level = [], 0, "Front matter", "section"
    for m in pattern.finditer(text):
        out.append({"heading": last_head, "level": last_level, "text": text[last:m.start()]})
        last, last_head, last_level = m.end(), m.group(2).strip(), m.group(1)
    out.append({"heading": last_head, "level": last_level, "text": text[last:]})
    return [s for s in out if s["text"].strip()]


def split_html_sections(page: str) -> list[dict]:
    page = re.sub(r"<(script|style)\b.*?</\1>", " ", page, flags=re.S | re.I)
    parts = re.split(r"<h([1-4])[^>]*>(.*?)</h\1>", page, flags=re.S | re.I)
    out = [{"heading": "Front matter", "level": "section", "text": parts[0]}]
    for i in range(1, len(parts) - 2, 3):
        out.append({"heading": _strip_tags(parts[i + 1]), "level": f"h{parts[i]}", "text": parts[i + 2]})
    for s in out:
        s["text"] = _strip_tags(s["text"])
    return [s for s in out if s["text"].strip()]


def _strip_tags(fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def role_of(heading: str) -> list[str]:
    h = heading.lower()
    return [role for role, pat in ROLES.items() if re.search(pat, h)]


def sentences(text: str) -> list[str]:
    flat = re.sub(r"\s+", " ", text)
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z\[(\\])", flat) if len(s.strip()) > 20]


def flag_sentences(sections: list[dict], per_flag: int = 6) -> dict:
    found: dict[str, list[dict]] = {k: [] for k in FLAGS}
    for sec in sections:
        for sent in sentences(sec["text"]):
            for name, pat in FLAGS.items():
                if len(found[name]) < per_flag and re.search(pat, sent, flags=re.I):
                    found[name].append({"section": sec["heading"], "sentence": sent[:400]})
    return found


def _main_tex_first(members: dict[str, str]) -> str:
    names = sorted(members, key=lambda n: (0 if "\\documentclass" in members[n] else 1, n))
    main = members[names[0]]
    # Inline \input / \include files that exist in the archive, in document order.
    def inline(m):
        target = m.group(2).strip()
        for cand in (target, target + ".tex"):
            for name in members:
                if name.endswith(cand):
                    return members[name]
        return ""
    main = re.sub(r"\\(input|include)\{([^}]*)\}", inline, main)
    rest = [members[n] for n in names[1:] if members[n] not in main and "\\documentclass" not in members[n]]
    return main + "\n".join(rest)


def tex_from_eprint(blob: bytes) -> str | None:
    """Extract LaTeX from an arXiv e-print: a tar(.gz) archive or a single gzipped file.
    Members are read in memory only; nothing is written to disk."""
    try:
        with tarfile.open(fileobj=io.BytesIO(blob), mode="r:*") as tar:
            members = {}
            for m in tar.getmembers():
                if m.isfile() and m.name.lower().endswith(".tex") and m.size <= MAX_MEMBER_BYTES:
                    fh = tar.extractfile(m)
                    if fh:
                        members[m.name] = fh.read().decode("utf-8", "replace")
            return _main_tex_first(members) if members else None
    except tarfile.TarError:
        pass
    try:
        text = gzip.decompress(blob).decode("utf-8", "replace")
    except OSError:
        text = blob.decode("utf-8", "replace")
    return text if "\\begin{document}" in text or "\\section" in text else None


def fetch(client, ident: str, paper=None) -> dict:
    """Return {'status', 'source', 'sections', 'flags', 'notes'}; status is 'full_text' or 'not_accessible'."""
    kind, value = parse_identifier(ident)
    arxiv_id = value if kind == "arxiv" else getattr(paper, "arxiv_id", None)
    notes: list[str] = []
    result = {"ident": ident, "arxiv_id": arxiv_id, "status": "not_accessible", "source": None,
              "sections": [], "flags": {}, "notes": notes,
              "oa_pdf": getattr(paper, "pdf_url", None) if paper else None}
    if not arxiv_id:
        notes.append("No arXiv version known; only arXiv full text is fetched automatically. Read the open-access "
                     "PDF or publisher page manually if one exists, and record read_level accordingly.")
        return result

    cache_key = CACHE_VERSION + arxiv_id
    cached = client.cache_text(cache_key)
    if cached:
        kind_, _, body = cached.partition("\n")
        sections = split_tex_sections(body) if kind_ == "tex" else split_html_sections(body)
        return _finish(result, kind_, sections, notes)

    try:
        blob = client.get_bytes(f"https://arxiv.org/e-print/{arxiv_id}", source="arxiv_eprint",
                                max_bytes=MAX_SOURCE_BYTES)
        tex = tex_from_eprint(blob)
        if tex:
            client.cache_text(cache_key, "tex\n" + tex)
            return _finish(result, "tex", split_tex_sections(tex), notes)
        notes.append("e-print has no LaTeX source (PDF-only submission)")
    except SourceError as exc:
        notes.append(f"e-print: {exc.kind} {exc.message}")
    try:
        page = client.get(f"https://arxiv.org/html/{arxiv_id}", source="arxiv_html", parse="text", cache=False)
        sections = split_html_sections(page)
        if sum(len(s["text"]) for s in sections) > 2000:
            client.cache_text(cache_key, "html\n" + page)
            return _finish(result, "html", sections, notes)
        notes.append("arXiv HTML page too short to be the full text")
    except SourceError as exc:
        notes.append(f"arXiv HTML: {exc.kind} {exc.message}")
    return result


def _finish(result: dict, source: str, sections: list[dict], notes: list[str]) -> dict:
    for s in sections:
        s["roles"] = role_of(s["heading"])
        s["chars"] = len(s["text"])
    result.update(status="full_text", source=f"arxiv_{source}", sections=sections, flags=flag_sentences(sections))
    present = {r for s in sections for r in s["roles"]}
    result["missing_roles"] = [r for r in ("experiments", "results", "limitations", "related_work") if r not in present]
    return result


def to_text(result: dict, roles: list[str] | None = None) -> str:
    """Plain-text dump for reading, optionally only sections with the given roles."""
    out = []
    for s in result.get("sections") or []:
        if roles and not set(roles) & set(s.get("roles") or []):
            continue
        out.append(f"\n## {s['heading']}  [{', '.join(s.get('roles') or []) or 'other'}]\n")
        out.append(re.sub(r"[ \t]+", " ", s["text"]).strip())
    return "\n".join(out)
