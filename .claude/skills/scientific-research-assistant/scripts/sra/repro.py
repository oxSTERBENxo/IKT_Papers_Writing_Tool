"""Reproducibility pre-assessment of a published paper.

Collects observable facts (open access, repositories, licences, files) and
text signals (README mentions). It never runs any experiment, so it cannot
say a paper *is* reproducible; it says what is present, what is missing and
what a person still has to read.
"""
from __future__ import annotations

import re

from .http import SourceError
from .models import Paper
from .search import resolve
from .sources import github, huggingface, openalex
from .text import coverage, normalize_title

DISCLAIMER = ("Automated pre-assessment only. No code was executed and no result was reproduced. 'found' means a "
              "file or phrase is present, not that it is complete or correct; 'not_found' means the automated "
              "check did not find it, not that it does not exist.")

# status vocabulary: verified | found | not_found | manual_review | unavailable
README_SIGNALS = {
    "dependencies": r"requirements\.txt|environment\.ya?ml|pip install|conda (?:env )?create|docker|poetry install|uv sync",
    "data_instructions": r"download(?:ing)? (?:the )?(?:data|dataset)|data preparation|pre-?process|prepare (?:the )?data|"
                         r"datasets? (?:can be|is|are) (?:found|available|downloaded)",
    "configs": r"hyper-?parameter|learning[ _-]rate|batch[ _-]size|--lr\b|--epochs?\b|configs?/",
    "seeds": r"\bseeds?\b|deterministic",
    "hardware": r"\b(?:V100|A100|H100|T4|P100|K80|RTX ?\d{4}|GTX ?\d{3,4}|Titan ?\w*|TPU)\b|GPU[- ]hours?|"
                r"\d+ ?GB (?:of )?(?:GPU|VRAM|memory|RAM)|\b\d+ GPUs?\b",
    "evaluation": r"evaluat(?:e|ion)|reproduc(?:e|ing) (?:the |our )?results|python\s+\S*(?:eval|test)\w*\.py",
    "pretrained": r"pre-?trained (?:model|weight|checkpoint)s?|checkpoints?|model zoo|huggingface\.co/",
    "reported_results": r"\|\s*(?:accuracy|acc|f1|bleu|rouge|map|auc|mrr|hits@)\b|results? (?:table|in the paper)|"
                        r"we (?:obtain|achieve|report)",
}
TREE_SIGNALS = {
    "dependencies": r"(?:^|/)(?:requirements[\w\-.]*\.txt|environment[\w\-.]*\.ya?ml|pyproject\.toml|setup\.py|Pipfile|"
                    r"poetry\.lock|uv\.lock|Dockerfile|conda[\w\-.]*\.ya?ml)$",
    "configs": r"(?:^|/)(?:configs?|conf|hparams|experiments?)/.+\.(?:ya?ml|json|toml|cfg|ini|py)$|"
               r"(?:^|/)[\w\-]*config[\w\-]*\.(?:ya?ml|json|toml|cfg|ini)$",
    "training": r"(?:^|/)(?:train\w*|run\w*|main|finetune\w*|fit\w*)\.(?:py|sh|ipynb)$",
    "evaluation": r"(?:^|/)(?:eval\w*|test\w*|evaluate\w*|score\w*|predict\w*|infer\w*)\.(?:py|sh|ipynb)$",
    "data_instructions": r"(?:^|/)(?:prepare\w*|preprocess\w*|download\w*|get_data\w*|build_\w*|make_data\w*)\.(?:py|sh)$",
}
ITEMS = [
    ("full_text", "Full paper publicly available"),
    ("code", "Implementation available"),
    ("license", "Code licence"),
    ("dependencies", "Dependencies / environment specified"),
    ("data_instructions", "Dataset access and preprocessing instructions"),
    ("configs", "Training configuration and hyperparameters"),
    ("training", "Training entry point"),
    ("seeds", "Random seeds / determinism controls"),
    ("hardware", "Hardware requirements stated"),
    ("evaluation", "Evaluation script or protocol"),
    ("pretrained", "Pretrained weights or checkpoints"),
    ("reported_results", "Published results to compare against"),
    ("architecture", "Model architecture fully specified"),
    ("maintenance", "Repository maintenance"),
    ("prior_reproductions", "Existing reproduction attempts"),
]
PAPER_ONLY_NOTE = "Not determinable from metadata; read the paper's method and experiment sections."
RELATION_ORDER = {"linked_by_paper": 0, "readme_cites_paper": 1, "name_match_only": 2, "paper_list": 3}
# Reading lists and course notes cite thousands of papers without implementing any.
LIST_RE = re.compile(r"awesome|paper[-_ ]?(?:s|list|study|notes|reading|with[-_ ]?code)|reading[-_ ]?list|"
                     r"survey|must[-_ ]?read|literature|bibliography|resources|collection|interview|notes", re.I)
MANY_PAPERS = 15  # distinct arXiv links in a README beyond which it reads as a list
REPRO_TERMS = 'reproducibility OR "replication study" OR "reproduction study" OR "fail to reproduce"'


def _item(status: str, evidence=None, note: str | None = None) -> dict:
    return {"status": status, "evidence": evidence or [], "note": note}


def _snippet(text: str, match: re.Match, width: int = 70) -> str:
    start, end = max(0, match.start() - width), min(len(text), match.end() + width)
    return re.sub(r"\s+", " ", text[start:end]).strip()


def inspect_repo(client, full_name: str, paper: Paper, relationship: str) -> dict:
    """Fetch a repository's metadata, README and file list and derive checks."""
    info = {"repo": full_name, "url": f"https://github.com/{full_name}", "relationship": relationship,
            "checks": {}, "errors": []}
    try:
        meta = github.get_repo(client, full_name)
    except SourceError as exc:
        info["errors"].append(exc.to_dict())
        info["exists"] = False if exc.kind == "not_found" else None
        return info
    info.update(
        exists=True, url=meta.get("html_url") or info["url"], stars=meta.get("stargazers_count"),
        forks=meta.get("forks_count"), open_issues=meta.get("open_issues_count"),
        archived=meta.get("archived"), pushed_at=meta.get("pushed_at"), created_at=meta.get("created_at"),
        license=(meta.get("license") or {}).get("spdx_id"), language=meta.get("language"),
        description=meta.get("description"), is_fork=meta.get("fork"),
    )
    readme, paths, truncated = "", [], False
    try:
        readme = github.get_readme(client, full_name)
    except SourceError as exc:
        info["errors"].append({**exc.to_dict(), "step": "readme"})
    try:
        paths, truncated = github.get_tree(client, full_name, meta.get("default_branch") or "main")
    except SourceError as exc:
        info["errors"].append({**exc.to_dict(), "step": "file_tree"})
    info["n_files"], info["tree_truncated"], info["readme_chars"] = len(paths), truncated, len(readme)

    if relationship == "name_match_only" and readme and _mentions_paper(readme, paper):
        info["relationship"] = "readme_cites_paper"
    n_arxiv_links = len(set(re.findall(r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})", readme)))
    if relationship != "linked_by_paper" and (
            LIST_RE.search(f"{full_name.split('/')[-1]} {meta.get('description') or ''}")
            or n_arxiv_links > MANY_PAPERS):
        info["relationship"] = "paper_list"

    checks = info["checks"]
    lic = info["license"]
    checks["license"] = (_item("verified", [f"SPDX: {lic}"]) if lic and lic != "NOASSERTION" else
                         _item("not_found", note="No recognised licence; reuse rights are unclear."))
    for key in ("dependencies", "data_instructions", "configs", "training", "seeds", "hardware", "evaluation",
                "pretrained", "reported_results"):
        evidence = []
        if key in TREE_SIGNALS:
            hits = [p for p in paths if re.search(TREE_SIGNALS[key], p, re.I)]
            evidence += [f"file: {p}" for p in hits[:5]]
        if key in README_SIGNALS and readme:
            m = re.search(README_SIGNALS[key], readme, re.I)
            if m:
                evidence.append(f"README: \"...{_snippet(readme, m)}...\"")
        if evidence:
            checks[key] = _item("found", evidence, "Presence only; read it to confirm it is complete.")
        elif not readme and not paths:
            checks[key] = _item("unavailable", note="README and file list could not be fetched.")
        else:
            checks[key] = _item("not_found", note="No matching file or README text.")
    age = (info.get("pushed_at") or "")[:10]
    checks["maintenance"] = _item("verified", [f"last push {age}", f"archived: {info.get('archived')}",
                                               f"open issues: {info.get('open_issues')}"])
    try:
        n = github.count_issues(client, full_name, "reproduce OR reproducibility OR \"cannot reproduce\"")
        info["reproduction_issue_count"] = n
        checks["maintenance"]["evidence"].append(f"issues mentioning reproduction: {n}")
    except SourceError as exc:
        info["errors"].append({**exc.to_dict(), "step": "issue_search"})
    return info


def _mentions_paper(readme: str, paper: Paper) -> bool:
    if paper.arxiv_id and paper.arxiv_id in readme:
        return True
    if paper.doi and paper.doi.lower() in readme.lower():
        return True
    title = normalize_title(paper.title)
    return bool(title) and len(title.split()) >= 4 and title in normalize_title(readme)


def find_code(client, paper: Paper, extra_repos: list[str], max_inspect: int = 4) -> tuple[list[dict], list[dict]]:
    errors: list[dict] = []
    candidates: dict[str, dict] = {}  # lower-cased repo -> {repo, relationship, stars}

    def add(repo: str, relationship: str, stars: int | None = None):
        entry = candidates.setdefault(repo.lower(), {"repo": repo, "relationship": relationship, "stars": stars,
                                                     "about": ""})
        if RELATION_ORDER[relationship] < RELATION_ORDER[entry["relationship"]]:
            entry["relationship"] = relationship
        if stars is not None:
            entry["stars"] = stars
        return entry

    for repo in extra_repos:
        add(repo, "linked_by_paper")
    for text in (paper.abstract, paper.extra.get("arxiv_comment")):
        for repo in github.extract_repos(text):
            add(repo, "linked_by_paper")
    if paper.arxiv_id:
        try:
            page = huggingface.get_paper(client, paper.arxiv_id)
            for repo in github.extract_repos(str(page.get("githubRepo") or "")):
                add(repo, "linked_by_paper")
        except SourceError as exc:
            if exc.kind != "not_found":
                errors.append({**exc.to_dict(), "step": "huggingface_paper_page"})

    searches = []
    if paper.arxiv_id:
        searches.append((f'"{paper.arxiv_id}" in:readme', "readme_cites_paper"))
    if paper.title:
        searches.append((f'"{paper.title}" in:readme,description', "readme_cites_paper"))
        searches.append((f"{' '.join(normalize_title(paper.title).split()[:8])} in:name,description",
                         "name_match_only"))
    for query, relationship in searches:
        try:
            for item in github.search_repos(client, query, 5):
                add(item["full_name"], relationship, item.get("stargazers_count"))["about"] = (
                    f"{item['full_name'].split('/')[-1]} {item.get('description') or ''}")
        except SourceError as exc:
            errors.append({**exc.to_dict(), "step": f"github_search: {query}"})
            if exc.kind in ("rate_limited", "auth"):
                break

    # Closest relationship first; then repositories that do not look like reading
    # lists, whose name and description match the paper's title; then the most used.
    def priority(c: dict):
        return (RELATION_ORDER[c["relationship"]] if c["relationship"] == "linked_by_paper" else 1,
                bool(LIST_RE.search(c["about"])), -round(coverage(paper.title, c["about"]), 2), -(c["stars"] or 0))

    ordered = sorted(candidates.values(), key=priority)[:max_inspect]
    inspected = [inspect_repo(client, c["repo"], paper, c["relationship"]) for c in ordered]
    inspected.sort(key=lambda r: (RELATION_ORDER[r["relationship"]], -(r.get("stars") or 0)))
    return inspected, errors


def assess(client, ident: str, extra_repos: list[str] | None = None, max_repos: int = 4) -> dict:
    paper, notes = resolve(client, ident)
    if paper is None:
        return {"resolved": False, "identifier": ident, "resolution_notes": notes, "executed": False,
                "disclaimer": DISCLAIMER}
    errors: list[dict] = []
    checklist: dict[str, dict] = {}

    # Full text
    if paper.arxiv_id:
        checklist["full_text"] = _item("verified", [f"https://arxiv.org/abs/{paper.arxiv_id}"])
    elif paper.is_oa and paper.pdf_url:
        checklist["full_text"] = _item("verified", [paper.pdf_url], "Open access according to source metadata.")
    elif paper.is_oa is False:
        checklist["full_text"] = _item("not_found", note="Sources list no open-access copy; check library access.")
    else:
        checklist["full_text"] = _item("manual_review", note="Open-access status unknown.")

    # Code
    repos, code_errors = find_code(client, paper, extra_repos or [], max_repos)
    errors += code_errors
    live = [r for r in repos if r.get("exists") and r["relationship"] != "paper_list"]
    best = live[0] if live else None
    if best:
        label = {"linked_by_paper": "linked from the paper's own metadata (likely official)",
                 "readme_cites_paper": "README cites the paper (official or third-party; check authorship)",
                 "name_match_only": "name match only (NOT confirmed to implement this paper)"}[best["relationship"]]
        status = "found" if best["relationship"] != "name_match_only" else "manual_review"
        checklist["code"] = _item(status, [best["url"]], label)
        for key, value in best["checks"].items():
            checklist[key] = value
    else:
        blocked = any(e.get("kind") in ("rate_limited", "auth", "network") for e in code_errors)
        checklist["code"] = (_item("unavailable", note="GitHub lookup failed; see errors.") if blocked else
                             _item("not_found", note="No repository linked from the paper or found by search."))
    checklist.setdefault("reported_results", _item("manual_review", note=PAPER_ONLY_NOTE))
    checklist["architecture"] = _item("manual_review", note=PAPER_ONLY_NOTE)
    for key in ("configs", "seeds", "hardware", "evaluation"):
        if checklist.get(key, {}).get("status") in (None, "not_found"):
            checklist[key] = _item(checklist.get(key, {}).get("status") or "manual_review",
                                   note="Not found in a repository; check the paper and its appendix.")

    # Hugging Face artefacts tagged with the paper
    linked = {"datasets": [], "models": [], "note": "Repos tagged with this arXiv ID. They cite the paper; they "
              "are not necessarily the data or weights it used."}
    if paper.arxiv_id:
        try:
            repos_hf = huggingface.arxiv_repos(client, paper.arxiv_id)
            linked["datasets"] = [d.get("id") for d in (repos_hf.get("datasets") or [])[:10]]
            linked["models"] = [m.get("id") for m in (repos_hf.get("models") or [])[:10]]
        except SourceError as exc:
            if exc.kind != "not_found":
                errors.append({**exc.to_dict(), "step": "huggingface_linked_repos"})

    # Prior reproduction attempts: citing works that talk about reproduction
    prior: list[Paper] = []
    if paper.openalex_id:
        try:
            prior = openalex.citing(client, paper.openalex_id, 10, "citations", REPRO_TERMS)
            checklist["prior_reproductions"] = _item(
                "manual_review" if prior else "not_found",
                [f"{p.title} ({p.year}) {p.best_url()}" for p in prior[:5]],
                "Candidates only: citing works that mention reproducibility. Most are not reproductions of this "
                "paper; read them before describing any as one."
                if prior else "No citing work mentioning reproducibility was found in OpenAlex.")
        except SourceError as exc:
            errors.append({**exc.to_dict(), "step": "prior_reproductions"})
    checklist.setdefault("prior_reproductions", _item(
        "unavailable", note="OpenAlex lookup failed; see errors." if paper.openalex_id else
        "Needs an OpenAlex record for the paper, which was not found."))

    blockers = []
    if checklist["full_text"]["status"] == "not_found":
        blockers.append("No open-access full text located.")
    if checklist["code"]["status"] == "not_found":
        blockers.append("No implementation located: reproduction would need a from-scratch re-implementation "
                        "(that is a replication, with higher effort and risk).")
    if best and best.get("archived"):
        blockers.append("Repository is archived (no maintenance or issue support).")
    if paper.is_retracted:
        blockers.append("The paper is marked as retracted in OpenAlex.")

    ordered = {key: {"label": label, **checklist.get(key, _item("manual_review", note=PAPER_ONLY_NOTE))}
               for key, label in ITEMS}
    return {
        "resolved": True, "paper": paper, "resolution_notes": notes, "executed": False,
        "disclaimer": DISCLAIMER, "checklist": ordered, "code_candidates": repos,
        "huggingface_linked": linked, "prior_reproduction_candidates": prior,
        "potential_blockers": blockers,
        "missing": [v["label"] for v in ordered.values() if v["status"] in ("not_found", "manual_review")],
        "errors": errors,
    }
