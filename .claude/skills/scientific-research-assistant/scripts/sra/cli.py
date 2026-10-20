"""Command line interface. Each command prints a compact summary to stdout and,
with --out, writes the full machine-readable JSON to a file."""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
from pathlib import Path

from . import (__version__, datasets, fulltext, landscape, leakage, novelty, report, repro, retrieval_eval,
               scoring, search, verify)
from .http import HttpClient, SourceError
from .models import Paper, parse_identifier
from .sources import arxiv, crossref, github, huggingface, openalex, pubmed, semanticscholar, zenodo

KEY_VARS = {
    "openalex": "OPENALEX_API_KEY", "semantic_scholar": "SEMANTIC_SCHOLAR_API_KEY", "pubmed": "NCBI_API_KEY",
    "github": "GITHUB_TOKEN", "huggingface": "HF_TOKEN",
}


def jsonable(value):
    if isinstance(value, Paper):
        return value.to_dict()
    if isinstance(value, dict):
        return {k: jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    return value


def write_out(path: str | None, data) -> None:
    if not path:
        return
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(jsonable(data), indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nFull JSON written to {target}")


def read_json(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def err(message: str) -> None:
    print(message, file=sys.stderr)


def progress(entry: dict) -> None:
    state = f"error {entry['error']['kind']}" if entry["error"] else f"{entry['results']} results"
    err(f"  [{entry['source']}/{entry['strategy']}] {entry['query']!r}: {state}")


def short(text: str | None, n: int) -> str:
    text = text or ""
    return text if len(text) <= n else text[: n - 1] + "…"


def paper_line(i: int, p: Paper, extra: str = "") -> str:
    ident = (f"arXiv:{p.arxiv_id}" if p.arxiv_id else f"doi:{p.doi}" if p.doi else f"pmid:{p.pmid}" if p.pmid
             else p.openalex_id or p.url or "no-id")
    flags = "".join([" RETRACTED" if p.is_retracted else "", " OA" if p.is_oa else ""])
    who = (p.authors[0].split()[-1] + (" et al." if len(p.authors) > 1 else "")) if p.authors else "?"
    return (f"{i:>3}. {short(p.title, 110)}\n     {who} {p.year or 'n.d.'} | {short(p.venue, 40) or 'venue n/a'} | "
            f"cited {p.citations if p.citations is not None else '?'} | {ident}{flags} | "
            f"via {','.join(p.sources)}{extra}")


def print_source_status(status: dict) -> None:
    print("Sources:")
    for name, st in status.items():
        detail = f"{st['ok_calls']}/{st['calls']} calls ok, {st['results']} records"
        if st["errors"]:
            detail += " | " + "; ".join(st["errors"])
        print(f"  {name:<17} {st['state'].upper():<8} {detail}")
    failed = [n for n, st in status.items() if st["state"] == "failed"]
    if failed:
        print(f"  NOTE: no results from {', '.join(failed)}. State this gap in any report built on this search.")


def pick_sources(args) -> list[str]:
    if args.sources:
        return search.normalize_sources(args.sources.split(","))
    return search.DOMAIN_SOURCES[args.domain]


# -- commands -------------------------------------------------------------
def cmd_sources(args, client) -> int:
    """Ping every integration and report which optional keys are set."""
    checks = {
        "openalex": lambda: openalex.search(client, "graph neural network", 1),
        "arxiv": lambda: arxiv.search(client, "graph neural network", 1),
        "crossref": lambda: crossref.search(client, "graph neural network", 1),
        "semantic_scholar": lambda: semanticscholar.search(client, "graph neural network", 1),
        "pubmed": lambda: pubmed.search(client, "graph neural network", 1),
        "huggingface": lambda: huggingface.search_datasets(client, "glue", 1),
        "github": lambda: github.rate_limit(client),
        "zenodo": lambda: zenodo.search_datasets(client, "graph", 1),
    }
    results = {}
    for name, check in checks.items():
        key_var = KEY_VARS.get(name)
        entry = {"key_variable": key_var, "key_set": bool(key_var and os.environ.get(key_var))}
        try:
            data = check()
            entry["state"] = "ok"
            if name == "github":
                core, srch = data["resources"]["core"], data["resources"]["search"]
                entry["detail"] = (f"core {core['remaining']}/{core['limit']} left, "
                                   f"search {srch['remaining']}/{srch['limit']} left")
        except SourceError as exc:
            entry["state"], entry["detail"] = "failed", f"{exc.kind}: {exc.message}"
        results[name] = entry
        key = f"{key_var} {'set' if entry['key_set'] else 'not set'}" if key_var else "no key needed"
        print(f"{name:<17} {entry['state'].upper():<7} {key:<36} {entry.get('detail', '')}")
    write_out(args.out, results)
    return 0


def cmd_search(args, client) -> int:
    queries = list(args.query or [])
    if args.concept:
        expanded, truncated = search.expand_concepts([c.split("|") for c in args.concept])
        queries += [q for q in expanded if q not in queries]
        if truncated:
            err("Concept combinations were capped at 12 queries.")
    if not queries:
        err("Give at least one --query or --concept.")
        return 2
    strategies = [s.strip() for s in args.strategies.split(",")]
    unknown = [s for s in strategies if s not in search.STRATEGIES]
    if unknown:
        err(f"Unknown strategies {unknown}; choose from {sorted(search.STRATEGIES)}")
        return 2
    run = search.run_search(client, queries, strategies, pick_sources(args), args.limit, args.from_year,
                            args.to_year, progress)
    print(f"Queries: {len(queries)} | strategies: {', '.join(strategies)} | "
          f"retrieved {run['n_retrieved']} records, {run['n_after_dedup']} after deduplication\n")
    print_source_status(run["sources_status"])
    print(f"\nTop {min(args.top, len(run['papers']))} by lexical match (a sorting aid, not a quality judgement):")
    for i, p in enumerate(run["papers"][: args.top], 1):
        print(paper_line(i, p, f" | match {p.extra['rank']['query_match']}"))
    run["date"] = datetime.date.today().isoformat()
    write_out(args.out, run)
    return 0


def cmd_paper(args, client) -> int:
    paper, notes = search.resolve(client, args.id)
    if paper is None:
        print(f"Could not resolve '{args.id}'. Do not cite it until it resolves.")
        for n in notes:
            print(f"  {n}")
        return 1
    print(paper_line(1, paper))
    print(f"     URL: {paper.best_url()}\n     PDF: {paper.pdf_url or 'not found'}")
    if args.abstract:
        print(f"\nAbstract: {paper.abstract or 'not available from the sources queried'}")
    for n in notes:
        print(f"  note: {n.get('source')}: {n.get('kind')} {n.get('message')}")
    write_out(args.out, {"paper": paper, "notes": notes})
    return 0


def cmd_related(args, client) -> int:
    paper, notes = search.resolve(client, args.id)
    if paper is None:
        print(f"Could not resolve '{args.id}'.")
        return 1
    result = search.related(client, paper, args.direction, args.limit)
    print(f"Seed: {paper.title} ({paper.year})\nCounts: {result['counts']}")
    for e in result["errors"]:
        print(f"  error in {e.get('step')}: {e['source']} {e['kind']} {e['message']}")
    by_label: dict[str, list[Paper]] = {}
    for p in result["papers"]:
        by_label.setdefault(p.found_by[0]["strategy"], []).append(p)
    for label, papers in by_label.items():
        print(f"\n{label} (showing {min(args.top, len(papers))} of {len(papers)}):")
        for i, p in enumerate(sorted(papers, key=lambda p: -(p.citations or 0))[: args.top], 1):
            print(paper_line(i, p))
    write_out(args.out, {**result, "resolution_notes": notes})
    return 0


def cmd_challenge(args, client) -> int:
    queries = args.query or [args.claim]
    result = novelty.challenge(client, args.claim, queries, pick_sources(args), args.limit, args.from_year,
                               args.top, progress, design=args.design or [], seeds=args.seed or [],
                               expand_top=args.expand)
    print(f"Claim: {args.claim}\nQueries tried: {len(queries)} | papers examined: {result['n_papers_examined']} | "
          f"high wording overlap: {result['n_high_overlap']} {result['high_overlap_by_year']} | "
          f"title-only records: {result['n_without_abstract']}")
    print(f"Sources ok: {', '.join(result['sources_ok']) or 'none'} | failed: "
          f"{', '.join(result['sources_failed']) or 'none'}")
    div = result["query_diversity"]
    print(f"Query diversity: {div['distinct_terms']} distinct terms, mean pairwise overlap "
          f"{div['mean_pairwise_term_overlap']}" + (" (NEAR-PARAPHRASES)" if div["near_paraphrases"] else ""))
    print(f"Citation expansion: {result['n_from_citation_expansion']} paper(s) found only via citations"
          + (f" | seeds: {', '.join(s.get('title') or s['seed'] for s in result['seeds'])}" if result["seeds"] else "")
          + (f" | {len(result['expansion_errors'])} expansion error(s)" if result["expansion_errors"] else ""))
    if result["design_elements"]:
        print(f"Design elements checked: {len(result['design_elements'])} | papers matching "
              f"{novelty.DESIGN_MIN_ELEMENTS}+ elements: {result['n_possible_same_design']}")
    print(f"\nSIGNAL: {result['signal']}\nHighest novelty confidence this search can support: "
          f"{result['max_supported_novelty_confidence']}")
    for reason in result["ceiling_lowered_because"]:
        print(f"  ceiling limited: {reason}")
    print(f"{result['interpretation']}\nCAVEAT: {result['caveat']}")
    print("\nClosest retrieved work (read these before keeping the idea):")
    for i, s in enumerate(result["closest"], 1):
        tag = " | survey-like" if s["is_survey_like"] else ""
        tag += "" if s["has_abstract"] else " | NO ABSTRACT (title match only)"
        tag += " | via citations only" if s["found_only_via_citations"] else ""
        tag += f" | design: {'; '.join(s['design_elements_matched'])}" if s["design_elements_matched"] else ""
        print(paper_line(i, s["paper"], f" | overlap {s['term_overlap']} tfidf {s['tfidf_similarity']}{tag}"))
    if result["possible_same_design"]:
        print("\nPossibly the same experiment under other wording (read in full):")
        for i, s in enumerate(result["possible_same_design"][:8], 1):
            print(paper_line(i, s["paper"], f" | design: {'; '.join(s['design_elements_matched'])}"))
    print("\nMust read before deciding (full text where accessible):")
    for i, m in enumerate(result["must_read"][:10], 1):
        print(f"  {i}. {short(m['title'], 100)} ({m['year']}) | {m['why']}\n     next: {m['next']}")
    result["date"] = datetime.date.today().isoformat()
    write_out(args.out, result)
    return 0


def cmd_map(args, client) -> int:
    queries = list(args.query or [])
    if args.concept:
        expanded, _ = search.expand_concepts([c.split("|") for c in args.concept])
        queries += [q for q in expanded if q not in queries]
    if not queries:
        err("Give at least one --query or --concept.")
        return 2
    strategies = [s.strip() for s in args.strategies.split(",")] if args.strategies else None
    result = landscape.map_landscape(client, queries, pick_sources(args), design=args.design or [],
                                     seeds=args.seed or [], anchor=args.anchor, strategies=strategies,
                                     limit=args.limit, from_year=args.from_year, expand_top=args.expand,
                                     progress=progress)
    print(f"Topic queries: {len(queries)} | anchor: '{result['anchor']}' | design queries: "
          f"{len(result['design_queries'])} | papers mapped: {result['n_papers']}\n")
    print_source_status(result["sources_status"])
    for note in result["coverage_notes"]:
        print(f"  coverage: {note}")
    print("\nEvidence buckets (pattern matches on title and abstract; read before relying on them):")
    for t in landscape.PRIORITY + ["method_proposal"]:
        rows = result["buckets"][t]
        print(f"\n[{t}] {result['bucket_sizes'][t]} paper(s); top {min(args.top, len(rows))}:")
        for i, e in enumerate(rows[: args.top], 1):
            tag = "" if e["has_abstract"] else " | NO ABSTRACT"
            print(paper_line(i, e["paper"], f" | types: {','.join(e['evidence_types'])}{tag}"))
    print("\nRead first (full text where accessible):")
    for i, m in enumerate(result["must_read"], 1):
        print(f"  {i}. {short(m['title'], 100)} ({m['year']}) | {m['why']} | next: {m['next']}")
    print("\nRun these as ordinary web searches too (the toolkit cannot); add any paper found with `paper --id`:")
    for q in result["web_search_queries"]:
        print(f"  - {q}")
    print("\nNext: record what the literature establishes, disputes or leaves open as evidence_ledger entries "
          f"(types: {', '.join(report.LEDGER_TYPES)}), citing only papers you have read; derive questions from them.")
    write_out(args.out, {k: v for k, v in result.items() if k != "entries"})
    return 0


def cmd_retrieval_eval(args, client) -> int:
    fixtures = retrieval_eval.load_fixtures(args.fixtures)
    if args.split:
        fixtures = [f for f in fixtures if f["split"] == args.split]
    configs = [c.strip() for c in args.configs.split(",")]
    unknown = [c for c in configs if c not in retrieval_eval.CONFIGS]
    if unknown:
        err(f"Unknown configs {unknown}; choose from {retrieval_eval.CONFIGS}")
        return 2
    sources = search.normalize_sources(args.sources.split(","))
    if args.snapshot:
        # Every configuration sees identical responses for identical requests, and the run can be replayed.
        client = HttpClient(timeout=client.timeout, cache_dir=args.snapshot, cache_ttl=float("inf"))
        client.offline = bool(args.offline)
    elif args.offline:
        err("--offline needs --snapshot DIR")
        return 2
    if "challenge_hybrid" in configs:
        from . import semantic
        err(f"hybrid configuration: embedding backend {semantic.describe()}")
    results = []
    for fx in fixtures:
        err(f"== {fx['id']} ({fx['split']})")
        r = retrieval_eval.run_fixture(client, fx, sources, configs, args.limit, progress=progress)
        results.append(r)
        if args.out:  # save after every fixture so an interrupted live run keeps its results
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            Path(args.out).write_text(json.dumps(jsonable({"partial": True, "results": results}), indent=2,
                                                 ensure_ascii=False), encoding="utf-8")
        print(f"\n{fx['id']} [{fx['split']}] - {r['n_targets']} known relevant paper(s)", flush=True)
        for c in configs:
            x = r["configs"][c]
            print(f"  {c:<20} found {x['recall_any']:.2f} | R@{retrieval_eval.TOP_K} "
                  f"{x[f'recall_at_{retrieval_eval.TOP_K}']:.2f} | R@50 {x['recall_at_50']:.2f} | MRR {x['mrr']:.3f} | "
                  f"retrieved {x['n_retrieved']}" + (f" | {x['seconds']}s, {x['http_calls']} calls"
                                                     if x.get("seconds") is not None else "")
                  + (f" | failed: {','.join(x['failed'])}" if x.get("failed") else "")
                  + (f" | signal {x['signal']}" if x.get("signal") else ""))
        if r["missed_by_all"]:
            print("  missed by every configuration (check with web search):")
            for t in r["missed_by_all"]:
                print(f"    - {short(t, 110)}")
    summary = retrieval_eval.summarize(results, configs)
    print("\nPooled recall (known relevant papers found / targets):")
    print("\nChallenge signal 'close prior work found' (controls should not be flagged):")
    for split, by_cfg in summary.get("challenge_signal", {}).items():
        print("  " + split + ": " + "; ".join(f"{cfg} {v['flagged_prior_work']}/{v['fixtures']}" for cfg, v in by_cfg.items()))
    for split in ("dev", "heldout", "blind"):
        if split in summary:
            print(f"  {split}:")
            for c in configs:
                x = summary[split][c]
                print(f"    {c:<20} {x['found']}/{x['targets']} any rank, {x[f'in_top_{retrieval_eval.TOP_K}']}"
                      f"/{x['targets']} in top {retrieval_eval.TOP_K}, {x['in_top_50']}/{x['targets']} in top 50, "
                      f"MRR {x['mrr']} | misses by cause {x['miss_causes']} | {x['http_calls']} calls, "
                      f"{x['seconds']}s")
    print(f"\nCAVEAT: {summary['caveat']}")
    write_out(args.out, {"summary": summary, "results": results, "sources": sources, "configs": configs})
    return 0


def cmd_fulltext(args, client) -> int:
    paper = None
    kind, _ = parse_identifier(args.id)
    if kind != "arxiv":
        paper, _notes = search.resolve(client, args.id)
    result = fulltext.fetch(client, args.id, paper)
    print(f"Full text: {result['status']} via {result['source'] or 'none'} | arXiv {result['arxiv_id'] or 'n/a'}")
    for n in result["notes"]:
        print(f"  note: {n}")
    if result["status"] != "full_text":
        if result.get("oa_pdf"):
            print(f"  open-access PDF to read manually: {result['oa_pdf']}")
        print("Record read_level 'abstract' or 'not_accessible' for this paper until it is read.")
        write_out(args.out, result)
        return 1
    print("\nSections (roles are guessed from headings):")
    for s in result["sections"]:
        print(f"  {s['heading'][:70]:<70} {s['chars']:>7} chars  {', '.join(s['roles']) or ''}")
    if result.get("missing_roles"):
        print(f"  no section recognised as: {', '.join(result['missing_roles'])} (check the text manually)")
    print("\nSentences to check (pattern matches; read them in context):")
    for flag, hits in result["flags"].items():
        print(f"  [{flag}] {len(hits)} hit(s)")
        for h in hits[: args.show]:
            print(f"     - ({short(h['section'], 30)}) {short(h['sentence'], 220)}")
    if args.save_text:
        target = Path(args.save_text)
        target.parent.mkdir(parents=True, exist_ok=True)
        roles = [r.strip() for r in args.roles.split(",")] if args.roles else None
        target.write_text(fulltext.to_text(result, roles), encoding="utf-8")
        print(f"\nText written to {target}")
    write_out(args.out, result)
    return 0


def cmd_leakage(args, client) -> int:
    records = leakage.load_records(args.input)
    out = leakage.analyse(records, train=args.train.split(","), test=args.test.split(","),
                          entities_field=args.entities_field, label_field=args.label_field,
                          split_field=args.split_field, text_field=args.text_field,
                          scalar_fields=[f for f in (args.scalar or [])],
                          hub_thresholds=[int(t) for t in args.hub_thresholds.split(",") if t])
    print(f"Items: {out['n_items']} | splits: {out['split_sizes']}")
    e = out["entities"]
    print(f"Entities: {e['unique']} unique, {e['in_more_than_one_item']} in more than one item, "
          f"{e['share_of_occurrences_from_repeat_entities']} of occurrences from repeat entities, "
          f"{e['repeat_entities_with_a_single_label']} of repeat entities carry a single label")
    for v in out.get("entity_vote") or []:
        hub = v["dropped_entities_in_at_least_n_items"]
        print(f"Entity vote{f' (entities in >= {hub} items dropped)' if hub else ''}: accuracy "
              f"{v['entity_vote_accuracy']} vs majority {v['majority_class_accuracy']} | test items sharing an "
              f"entity with train {v['share_test_items_with_seen_entity']}")
    for c in out.get("disjoint_split_feasibility") or []:
        hub = c["dropped_entities_in_at_least_n_items"]
        print(f"Components{f' (hubs >= {hub} dropped)' if hub else ''}: {c['n_components']}, largest holds "
              f"{c['largest_component_share']} of items")
    if out.get("masking_seen_entities"):
        m = out["masking_seen_entities"]
        print(f"Masking seen entities: median per test item {m['median_entities_per_test_item_before']} -> "
              f"{m['median_entities_per_test_item_after']}, {m['test_items_left_without_entities']} items emptied")
    if out.get("duplicates"):
        print(f"Duplicates: {out['duplicates']}")
    for r in out.get("scalar_rules") or []:
        print(f"Scalar rule: {r}")
    print("\nRisks (diagnostics, not proof that a model exploits them):")
    for r in out["risks"] or [{"type": "none", "level": "-", "finding": "no threshold exceeded"}]:
        print(f"  {r['level'].upper():<7} {r['type']}: {r['finding']}")
    write_out(args.out, out)
    return 0


def cmd_repro(args, client) -> int:
    result = repro.assess(client, args.id, args.repo or [], args.max_repos)
    if not result["resolved"]:
        print(f"Could not resolve '{args.id}': {result['resolution_notes']}")
        return 1
    paper = result["paper"]
    print(paper_line(1, paper))
    print(f"\n{result['disclaimer']}\n")
    for item in result["checklist"].values():
        print(f"  {item['status']:<14} {item['label']}")
        for ev in item["evidence"][:3]:
            print(f"                 - {short(ev, 150)}")
        if item["note"]:
            print(f"                 ({item['note']})")
    print("\nCode candidates:")
    for r in result["code_candidates"] or []:
        print(f"  {r['url']} | {r['relationship']} | stars {r.get('stars')} | licence {r.get('license')} | "
              f"last push {(r.get('pushed_at') or '?')[:10]} | archived {r.get('archived')} | "
              f"repro issues {r.get('reproduction_issue_count', '?')}")
    if not result["code_candidates"]:
        print("  none found")
    hf = result["huggingface_linked"]
    print(f"\nHugging Face repos tagged with the paper: {len(hf['datasets'])} dataset(s) {hf['datasets'][:5]}, "
          f"{len(hf['models'])} model(s) {hf['models'][:5]}")
    for b in result["potential_blockers"]:
        print(f"POTENTIAL BLOCKER: {b}")
    for e in result["errors"]:
        print(f"  check failed ({e.get('step')}): {e['source']} {e['kind']} {e['message']}")
    write_out(args.out, result)
    return 0


def cmd_dataset_search(args, client) -> int:
    result = datasets.search(client, args.query, args.limit)
    for d in result["huggingface"]:
        print(f"HF     {d['id']} | licence {d['license'] or 'not reported'} | gated {d['gated']} | "
              f"downloads {d['downloads']} | size {d['size_category'] or 'not reported'} | "
              f"tasks {','.join(d['tasks']) or 'n/a'}\n       {d['url']}")
    for d in result["zenodo"]:
        print(f"Zenodo {short(d['name'], 90)} | licence {d['license'] or 'not reported'} | access "
              f"{d['access_right']} | {datasets.human_bytes(d['total_bytes']) or 'size not reported'}\n       {d['url']}")
    for e in result["errors"]:
        print(f"  search failed: {e['source']} {e['kind']} {e['message']}")
    if not (result["huggingface"] or result["zenodo"]):
        print("No datasets found. This does not show that none exist; try other terms or domain repositories.")
    write_out(args.out, result)
    return 0


def cmd_dataset_verify(args, client) -> int:
    results = [datasets.verify(client, ref) for ref in args.ref]
    for info in results:
        state = {True: "EXISTS", False: "NOT FOUND", None: "COULD NOT CHECK"}[info.get("exists")]
        print(f"{state}: {info.get('url') or info.get('ref')} ({info['source']})")
        for key in ("name", "license", "gated", "access_right", "num_rows", "size_category", "formats",
                    "modalities", "tasks", "configs", "storage_estimate", "last_modified", "publication_date",
                    "http_status"):
            if info.get(key) not in (None, [], ""):
                print(f"  {key}: {short(str(info[key]), 160)}")
        for s in (info.get("splits") or [])[:12]:
            print(f"  split {s['config']}/{s['split']}: {s['num_rows']} rows")
        for label, key in (("missing", "missing"), ("note", "notes"), ("BLOCKER", "blockers")):
            for item in info.get(key) or []:
                print(f"  {label}: {item}")
        if info.get("note"):
            print(f"  note: {info['note']}")
    write_out(args.out, results)
    return 0 if all(r.get("exists") for r in results) else 1


def cmd_score(args, client) -> int:
    try:
        result = scoring.rank(read_json(args.input))
    except ValueError as exc:
        err(str(exc))
        return 2
    print(result["method"] + "\n")
    for r in result["ranking"]:
        rank = f"#{r['rank']}" if r["rank"] else "BLOCKED"
        print(f"{rank:<8} {r['title'] or r['id']} | {r['score_percent']}% on scored criteria | range "
              f"{r['score_range'][0]}-{r['score_range'][1]} | scored weight {r['scored_weight_percent']}% | "
              f"verified weight {r['verified_weight_percent']}%")
        for b in r["blockers"]:
            print(f"         blocker: {b.get('description')}")
        if r["unscored_criteria"]:
            print(f"         unscored: {', '.join(r['unscored_criteria'])}")
        if r.get("question_type"):
            print(f"         question type: {r['question_type']} (value criterion scored as {r['value_basis']})")
        for c in r.get("caps_applied") or []:
            print(f"         capped {c['criterion']} {c['submitted_score']} -> {c['cap']}: {c['reason']}")
    write_out(args.out, result)
    return 0


def cmd_verify_refs(args, client) -> int:
    data = read_json(args.input)
    counts = verify.verify_report(
        client, data,
        lambda p: err(f"  {p['verification']['status']:<20} {p.get('key')}: {short(p.get('title'), 70)}"))
    print(f"Verification results: {counts or 'no papers'}")
    for p in data.get("papers") or []:
        v = p["verification"]
        if v["status"] != "verified":
            print(f"  {p.get('key')}: {v['status']} | resolved title: {v.get('resolved_title')} | {v.get('note', '')}")
    Path(args.out or args.input).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Verification written to {args.out or args.input}")
    bad = sum(n for s, n in counts.items() if s in ("title_mismatch", "unresolved", "no_identifier"))
    return 1 if bad else 0


def cmd_report(args, client) -> int:
    data = read_json(args.input)
    if args.ranking:
        data["ranking"] = read_json(args.ranking)
    errors, warnings = report.validate(data)
    for w in warnings:
        print(f"warning: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    if errors and not args.force:
        print(f"\n{len(errors)} integrity error(s); nothing was written. Fix them, or pass --force to render "
              "a draft that carries a warning banner.")
        return 2
    if args.check:
        print("Validation passed." if not errors else "Validation failed.")
        return 2 if errors else 0
    banner = ""
    if errors or warnings:
        banner = (f"> **DRAFT: {len(errors)} integrity error(s) and {len(warnings)} warning(s) were reported by "
                  "the validator.** Unverified references are marked in the reference list.")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = args.name or report.slugify(data.get("title"))
    formats = [f.strip() for f in args.format.split(",")]
    written = []
    if "md" in formats:
        (out_dir / f"{slug}.md").write_text(report.render_markdown(data, banner), encoding="utf-8")
        written.append(f"{slug}.md")
    if "latex" in formats:
        (out_dir / f"{slug}.tex").write_text(report.render_latex(data, banner), encoding="utf-8")
        (out_dir / "references.bib").write_text(report.render_bibtex(data), encoding="utf-8")
        written += [f"{slug}.tex", "references.bib"]
    if "json" in formats:
        (out_dir / f"{slug}.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        written.append(f"{slug}.json")
    print(f"Wrote {', '.join(written)} to {out_dir}")
    auto = os.environ.get("SRA_OBSIDIAN_AUTO", "").strip().lower() in ("1", "true", "yes")
    if args.obsidian or auto:
        from . import obsidian
        try:
            vault = obsidian.resolve_vault(args.vault)
            summary = obsidian.export([(data, Path(args.input).resolve())], vault, args.obsidian_folder)
        except obsidian.ExportError as exc:
            print(f"Obsidian export skipped: {exc}")
            return 0 if auto and not args.obsidian else 2
        _print_obsidian(summary)
    return 0


def _print_obsidian(summary: dict) -> None:
    counts: dict[str, int] = {}
    for a in summary["actions"]:
        counts[a["action"]] = counts.get(a["action"], 0) + 1
    head = "Obsidian export (dry run, nothing written)" if summary["dry_run"] else "Obsidian export"
    print(f"{head} to {summary['folder']}: " + ", ".join(f"{n} {k}" for k, n in sorted(counts.items())))
    for a in summary["actions"]:
        if a["action"] != "unchanged":
            print(f"  {a['action']:<9} {a['kind']:<9} {a['path']}")
    for w in summary["warnings"]:
        print(f"  warning: {w}")


def cmd_obsidian_export(args, client) -> int:
    from . import obsidian
    try:
        vault = obsidian.resolve_vault(args.vault, args.allow_plain_folder)
        reports = [obsidian.load_report(path) for path in args.input]
        summary = obsidian.export(reports, vault, args.folder, papers=not args.no_papers,
                                  status_override=args.status, overwrite_managed=args.overwrite_managed,
                                  dry_run=args.dry_run)
    except obsidian.ExportError as exc:
        err(f"Obsidian export failed: {exc}")
        return 2
    _print_obsidian(summary)
    return 0


# -- parser -----------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sra", description="Scientific research assistant toolkit.")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--no-cache", action="store_true", help="ignore and do not write the response cache")
    parser.add_argument("--timeout", type=float, default=30)
    sub = parser.add_subparsers(dest="command", required=True)

    def source_args(p):
        p.add_argument("--domain", choices=sorted(search.DOMAIN_SOURCES), default="cs",
                       help="picks default sources: cs, biomed or general")
        p.add_argument("--sources", help="comma list overriding --domain: " + ",".join(search.SEARCHERS))
        p.add_argument("--limit", type=int, default=15, help="results per query per source")
        p.add_argument("--from-year", type=int)
        p.add_argument("--top", type=int, default=20, help="rows to print")
        p.add_argument("--out", help="write full JSON here")

    p = sub.add_parser("sources", help="check which integrations respond and which keys are set")
    p.add_argument("--out")
    p.set_defaults(func=cmd_sources)

    p = sub.add_parser("search", help="multi-source literature search with deduplication")
    p.add_argument("--query", action="append", help="repeat for alternative phrasings")
    p.add_argument("--concept", action="append",
                   help="synonym group 'a|b|c'; repeat per concept to search every combination")
    p.add_argument("--strategies", default="keyword",
                   help="comma list of: " + ",".join(search.STRATEGIES))
    p.add_argument("--to-year", type=int)
    source_args(p)
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("paper", help="resolve one paper by arXiv ID, DOI, PMID, OpenAlex ID, URL or title")
    p.add_argument("--id", required=True)
    p.add_argument("--abstract", action="store_true")
    p.add_argument("--out")
    p.set_defaults(func=cmd_paper)

    p = sub.add_parser("related", help="references, citing works and related works of a paper")
    p.add_argument("--id", required=True)
    p.add_argument("--direction", choices=["all", "references", "citations", "related"], default="all")
    p.add_argument("--limit", type=int, default=25)
    p.add_argument("--top", type=int, default=10)
    p.add_argument("--out")
    p.set_defaults(func=cmd_related)

    p = sub.add_parser("challenge", help="try to disprove that a research idea is new")
    p.add_argument("--claim", required=True, help="one sentence stating what would be new")
    p.add_argument("--query", action="append", help="repeat: different wordings and synonyms of the idea")
    p.add_argument("--design", action="append",
                   help="repeat: one element of the experimental design in plain words, e.g. 'MLP baseline on the "
                        "same node features' or 'randomly rewired edges'; papers matching several are flagged")
    p.add_argument("--seed", action="append",
                   help="repeat: arXiv ID or DOI of a benchmark or method paper the idea builds on; its citing "
                        "works are searched for the queries")
    p.add_argument("--expand", type=int, default=3,
                   help="follow citations and references of this many closest papers (0 disables; lowers the "
                        "confidence ceiling)")
    source_args(p)
    p.set_defaults(func=cmd_challenge)

    p = sub.add_parser("map", help="literature-first landscape: comparisons, negative results, critiques, "
                                   "reproducibility studies and limitations for a topic")
    p.add_argument("--query", action="append", help="topic query (repeat)")
    p.add_argument("--concept", action="append", help="synonym group 'a|b|c' (repeat per concept)")
    p.add_argument("--design", action="append", help="experimental design element (repeat)")
    p.add_argument("--seed", action="append", help="benchmark or method paper the topic builds on (repeat)")
    p.add_argument("--anchor", help="short topic phrase used to anchor design queries (default: from first query)")
    p.add_argument("--strategies", help="comma list overriding " + ",".join(search.DISCOVERY_STRATEGIES))
    p.add_argument("--expand", type=int, default=3, help="follow citations of this many top papers")
    source_args(p)
    p.set_defaults(func=cmd_map, top=6, limit=10)

    p = sub.add_parser("retrieval-eval", help="recall of known relevant papers under each retrieval configuration")
    p.add_argument("--fixtures", required=True, help="fixture JSON file or glob, e.g. evals/retrieval/*.json")
    p.add_argument("--configs", default="baseline,challenge,landscape,full",
                   help="comma list from " + ",".join(retrieval_eval.CONFIGS))
    p.add_argument("--split", choices=list(retrieval_eval.SPLITS))
    p.add_argument("--sources", default="openalex,arxiv,crossref")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--snapshot", help="response store for this evaluation (never expires), so all configurations "
                                      "see the same responses and the run can be replayed")
    p.add_argument("--offline", action="store_true", help="replay from --snapshot only; no network")
    p.add_argument("--out")
    p.set_defaults(func=cmd_retrieval_eval)

    p = sub.add_parser("obsidian-export", help="export report JSON files to an Obsidian vault as linked notes")
    p.add_argument("--input", required=True, action="append", help="report JSON (repeat for several)")
    p.add_argument("--vault", help="vault folder (default: SRA_OBSIDIAN_VAULT)")
    p.add_argument("--folder", help="research folder inside the vault (default: SRA_OBSIDIAN_FOLDER or "
                   "'Scientific Research')")
    p.add_argument("--no-papers", action="store_true", help="do not create paper notes")
    p.add_argument("--status", help="research status to record instead of the one derived from the report")
    p.add_argument("--dry-run", action="store_true", help="show what would be created or updated; write nothing")
    p.add_argument("--overwrite-managed", action="store_true",
                   help="also replace generated sections that were edited by hand (user text outside them is kept)")
    p.add_argument("--allow-plain-folder", action="store_true", help="accept a folder without .obsidian")
    p.set_defaults(func=cmd_obsidian_export)

    p = sub.add_parser("fulltext", help="fetch accessible full text (arXiv source or HTML) and flag methodology")
    p.add_argument("--id", required=True)
    p.add_argument("--show", type=int, default=3, help="sentences to print per flag")
    p.add_argument("--save-text", help="write the section text here for reading")
    p.add_argument("--roles", help="with --save-text: only these roles, e.g. experiments,ablation,limitations")
    p.add_argument("--out")
    p.set_defaults(func=cmd_fulltext)

    p = sub.add_parser("leakage", help="train/test overlap, duplicate and shortcut diagnostics for a split")
    p.add_argument("--input", required=True, help="JSON list or .jsonl with one record per evaluation item")
    p.add_argument("--split-field", default="split")
    p.add_argument("--label-field", default="label")
    p.add_argument("--entities-field", default="entities", help="list of entity ids (users, authors, sources)")
    p.add_argument("--text-field", help="text to check for exact duplicates across splits")
    p.add_argument("--scalar", action="append", help="numeric field to test as a one-threshold shortcut")
    p.add_argument("--train", default="train", help="comma list of split names used for training")
    p.add_argument("--test", default="test", help="comma list of split names used for testing")
    p.add_argument("--hub-thresholds", default="50,10", help="also rerun dropping entities in >= N items")
    p.add_argument("--out")
    p.set_defaults(func=cmd_leakage)

    p = sub.add_parser("repro", help="reproducibility pre-assessment of one paper")
    p.add_argument("--id", required=True)
    p.add_argument("--repo", action="append", help="owner/name of a known implementation (repeatable)")
    p.add_argument("--max-repos", type=int, default=4)
    p.add_argument("--out")
    p.set_defaults(func=cmd_repro)

    p = sub.add_parser("dataset-search", help="find public datasets on Hugging Face and Zenodo")
    p.add_argument("--query", required=True)
    p.add_argument("--limit", type=int, default=8)
    p.add_argument("--out")
    p.set_defaults(func=cmd_dataset_search)

    p = sub.add_parser("dataset-verify", help="confirm datasets exist and report licence, size and access")
    p.add_argument("ref", nargs="+", help="Hugging Face id or URL, zenodo:<id> or Zenodo URL, or any URL")
    p.add_argument("--out")
    p.set_defaults(func=cmd_dataset_verify)

    p = sub.add_parser("score", help="rank candidate projects from a scoring JSON")
    p.add_argument("--input", required=True)
    p.add_argument("--out")
    p.set_defaults(func=cmd_score)

    p = sub.add_parser("verify-refs", help="check that every paper in a report JSON resolves")
    p.add_argument("--input", required=True)
    p.add_argument("--out", help="default: update the input file in place")
    p.set_defaults(func=cmd_verify_refs)

    p = sub.add_parser("report", help="validate a report JSON and render Markdown / LaTeX / JSON")
    p.add_argument("--input", required=True)
    p.add_argument("--out-dir", default="research-reports")
    p.add_argument("--format", default="md", help="comma list of md,latex,json")
    p.add_argument("--ranking", help="output of the score command, shown as the feasibility ranking")
    p.add_argument("--name", help="output file stem (default: slug of the title)")
    p.add_argument("--check", action="store_true", help="validate only")
    p.add_argument("--force", action="store_true", help="render despite integrity errors, with a banner")
    p.add_argument("--obsidian", action="store_true", help="also export to the Obsidian vault (see obsidian-export); "
                   "automatic when SRA_OBSIDIAN_AUTO=1")
    p.add_argument("--vault", help="Obsidian vault folder (default: SRA_OBSIDIAN_VAULT)")
    p.add_argument("--obsidian-folder", help="research folder inside the vault (default: SRA_OBSIDIAN_FOLDER or "
                   "'Scientific Research')")
    p.set_defaults(func=cmd_report)
    return parser


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    args = build_parser().parse_args(argv)
    client = HttpClient(timeout=args.timeout, cache_dir=None if args.no_cache else "default")
    try:
        return args.func(args, client)
    except (ValueError, FileNotFoundError) as exc:
        err(f"error: {exc}")
        return 2
