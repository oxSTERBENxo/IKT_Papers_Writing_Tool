"""All statistics and figures for the memorisation paper (follows ANALYSIS_PLAN.md).

Run after run_llms.py and gcn_baseline.py:  .venv/Scripts/python analyze.py
Writes results/results.json, results/tables.md and figures/*.png.
"""
import glob
import json
import os
import sys

import matplotlib
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats
from statsmodels.stats.contingency_tables import mcnemar
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.proportion import proportion_confint

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
rng = np.random.default_rng(20261020)
B = 2000

MODELS = {"llama2_7b-chat": "Llama-2-7B", "llama3.2_latest": "Llama-3.2-3B",
          "qwen2.5_7b": "Qwen2.5-7B", "gemma3_4b": "Gemma-3-4B"}
ORDER = list(MODELS.values())
OLD = "Llama-2-7B"
SETS = ["S2019", "S2023", "S2026"]

# chart style (validated reference palette, light mode)
COL = {"Llama-2-7B": "#2a78d6", "Llama-3.2-3B": "#eb6834", "Qwen2.5-7B": "#1baf7a",
       "Gemma-3-4B": "#eda100", "GCN (no text)": "#52514e"}
INK, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
plt.rcParams.update({
    "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF, "axes.edgecolor": GRID,
    "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.8, "font.size": 10, "axes.titlesize": 11, "axes.titleweight": "bold",
    "axes.titlelocation": "left"})


# ------------------------------------------------------------------ loading
def load():
    meta = pd.concat([pd.read_json(f"data/{s}.jsonl", lines=True, dtype={"id": str}) for s in SETS])
    meta = meta[["set", "id", "label", "homophily", "degree"]]
    rows = []
    for f in glob.glob("results/raw/*.jsonl"):
        m, task, s = os.path.basename(f)[:-6].split("__")
        d = pd.read_json(f, lines=True, dtype={"id": str})
        d["model"], d["task"], d["set"] = MODELS[m], task, s
        rows.append(d)
    raw = pd.concat(rows, ignore_index=True)
    cls = raw[raw.task.isin(["P0", "P1"])].drop(columns=["label"]).merge(meta, on=["set", "id"])
    probe = raw[raw.task == "PROBE"].merge(meta, on=["set", "id"])
    return cls, probe


def wilson(k, n):
    lo, hi = proportion_confint(k, n, method="wilson")
    return [float(lo), float(hi)]


def acc_table(cls, gcn):
    out = {}
    for (task, model, s), g in cls.groupby(["task", "model", "set"]):
        k, n = int(g.correct.sum()), len(g)
        out.setdefault(task, {}).setdefault(model, {})[s] = {
            "n": n, "acc": k / n, "ci": wilson(k, n), "invalid": float(g.pred.isna().mean())}
    for s, d in gcn.items():
        accs = [r["test_acc"] for r in d["runs"]]
        out.setdefault("GCN", {})[s] = {"n": len(d["ids"]), "acc": float(np.mean(accs)),
                                        "sd_over_seeds": float(np.std(accs, ddof=1)), "seeds": len(accs)}
    return out


def boot_p(samples):
    samples = np.asarray(samples)
    return float(min(1.0, 2 * min((samples <= 0).mean(), (samples >= 0).mean())))


# ------------------------------------------------------------------ H1
def h1(cls, gcn):
    """Llama-2 drop S2019 -> S2023 minus GCN drop, node bootstrap."""
    res = {}
    gcn_node = {s: pd.Series(np.mean([r["correct"] for r in d["runs"]], axis=0), index=d["ids"])
                for s, d in gcn.items()}
    for model in ORDER:
        p0 = cls[(cls.task == "P0") & (cls.model == model)]
        a = {s: p0[p0.set == s].set_index("id").correct for s in ["S2019", "S2023"]}
        g = {s: gcn_node[s].reindex(a[s].index) for s in a}
        did = (a["S2019"].mean() - a["S2023"].mean()) - (g["S2019"].mean() - g["S2023"].mean())
        bs = []
        for _ in range(B):
            i19 = rng.integers(0, len(a["S2019"]), len(a["S2019"]))
            i23 = rng.integers(0, len(a["S2023"]), len(a["S2023"]))
            bs.append((a["S2019"].values[i19].mean() - a["S2023"].values[i23].mean())
                      - (g["S2019"].values[i19].mean() - g["S2023"].values[i23].mean()))
        res[model] = {"llm_drop": float(a["S2019"].mean() - a["S2023"].mean()),
                      "gcn_drop": float(g["S2019"].mean() - g["S2023"].mean()),
                      "did": float(did), "ci": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))],
                      "p_boot": boot_p(bs)}
    return res


# ------------------------------------------------------------------ H2
def collapse_labels(d, min_n=15):
    """Pool categories with fewer than min_n *papers* (not rows: each paper has one row per model)."""
    vc = d.drop_duplicates(["set", "id"]).label.value_counts()
    return d.label.where(d.label.map(vc) >= min_n, "other")


def h2(cls):
    d = cls[(cls.task == "P0") & cls.set.isin(["S2023", "S2026"])].copy()
    d["s23"] = (d.set == "S2023").astype(int)
    d["new"] = (d.model != OLD).astype(int)
    d["cat"] = collapse_labels(d)
    d["model"] = pd.Categorical(d.model, ORDER)
    fam = sm.families.Binomial()
    cov = sm.cov_struct.Exchangeable()
    # `new` main effect is omitted: it is a sum of the C(model) dummies (collinear)
    pooled = smf.gee("correct ~ new:s23 + s23 + C(model) + C(cat)", groups="id", data=d, family=fam,
                     cov_struct=cov).fit()
    per = smf.gee("correct ~ C(model) * s23 + C(cat)", groups="id", data=d, family=fam,
                  cov_struct=cov).fit()
    terms = {}
    for name in per.params.index:
        if ":s23" in name:
            mdl = name.split("[T.")[1].split("]")[0]
            ci = per.conf_int().loc[name]
            terms[mdl] = {"or": float(np.exp(per.params[name])), "ci": [float(np.exp(ci[0])), float(np.exp(ci[1]))],
                          "p": float(per.pvalues[name])}
    pi = "new:s23"
    pci = pooled.conf_int().loc[pi]
    # accuracy DiD with paired-by-paper bootstrap (papers are shared across models)
    wide = d.pivot_table(index=["set", "id"], columns="model", values="correct", observed=False)
    did, did_rw = {}, {}
    w = reweights(d)
    for m in ORDER[1:]:
        def stat(t, weights=None):
            x23, x26 = t.loc["S2023"], t.loc["S2026"]
            if weights is None:
                return (x23[m].mean() - x26[m].mean()) - (x23[OLD].mean() - x26[OLD].mean())
            w26 = weights.reindex(x26.index)
            return ((x23[m].mean() - np.average(x26[m], weights=w26))
                    - (x23[OLD].mean() - np.average(x26[OLD], weights=w26)))
        t23, t26 = wide.loc["S2023"], wide.loc["S2026"]
        bs, bsw = [], []
        for _ in range(B):
            s23 = t23.iloc[rng.integers(0, len(t23), len(t23))]
            s26 = t26.iloc[rng.integers(0, len(t26), len(t26))]
            s23 = s23.set_index(pd.RangeIndex(len(s23)))
            ww = w.reindex(s26.index).values
            s26 = s26.set_index(pd.RangeIndex(len(s26)))
            bt = pd.concat({"S2023": s23, "S2026": s26})
            bs.append(stat(bt))
            bsw.append(stat(bt, pd.Series(ww, index=s26.index)))
        did[m] = {"did": float(stat(wide)), "ci": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))],
                  "p_boot": boot_p(bs)}
        did_rw[m] = {"did": float(stat(wide, w)), "ci": [float(np.percentile(bsw, 2.5)), float(np.percentile(bsw, 97.5))]}
    return {"pooled": {"or": float(np.exp(pooled.params[pi])), "ci": [float(np.exp(pci[0])), float(np.exp(pci[1]))],
                       "p": float(pooled.pvalues[pi]), "n_obs": int(pooled.nobs)},
            "per_model_interaction": terms, "accuracy_did": did, "accuracy_did_category_reweighted": did_rw}


def reweights(d):
    """Weights that give S2026 the S2023 category mix (post-stratification), indexed by S2026 paper id."""
    one = d[d.model == OLD]
    p23 = one[one.set == "S2023"].cat.value_counts(normalize=True)
    s26 = one[one.set == "S2026"].set_index("id").cat
    p26 = s26.value_counts(normalize=True)
    return s26.map(lambda c: p23.get(c, 0) / p26[c])


# ------------------------------------------------------------------ H3
def h3(probe):
    res = {"by_model": {}}
    for m in ORDER:
        g = probe[probe.model == m]
        r = {}
        for s in ["S2023", "S2026"]:
            x = g[g.set == s]
            r[s] = {"n": len(x), "exact": int(x.exact.sum()), "exact_rate": float(x.exact.mean()),
                    "exact_ci": wilson(int(x.exact.sum()), len(x)), "f1_mean": float(x.f1.mean())}
        tab = [[r["S2023"]["exact"], r["S2023"]["n"] - r["S2023"]["exact"]],
               [r["S2026"]["exact"], r["S2026"]["n"] - r["S2026"]["exact"]]]
        odds, p = stats.fisher_exact(tab)
        u = stats.mannwhitneyu(g[g.set == "S2023"].f1, g[g.set == "S2026"].f1)
        r["fisher_or"], r["fisher_p"], r["f1_mwu_p"] = float(odds), float(p), float(u.pvalue)
        res["by_model"][m] = r
    # pooled difference-in-differences on exact-match rate (new models vs Llama-2), paper bootstrap
    wide = probe.pivot_table(index=["set", "id"], columns="model", values="exact")
    def stat(t):
        new = [m for m in ORDER[1:]]
        d_new = t.loc["S2023"][new].values.mean() - t.loc["S2026"][new].values.mean()
        d_old = t.loc["S2023"][OLD].mean() - t.loc["S2026"][OLD].mean()
        return d_new - d_old
    t23, t26 = wide.loc["S2023"], wide.loc["S2026"]
    bs = []
    for _ in range(B):
        a = t23.iloc[rng.integers(0, len(t23), len(t23))].reset_index(drop=True)
        b = t26.iloc[rng.integers(0, len(t26), len(t26))].reset_index(drop=True)
        bs.append(stat(pd.concat({"S2023": a, "S2026": b})))
    res["pooled_did"] = {"did": float(stat(wide)), "ci": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))],
                         "p_boot": boot_p(bs)}
    return res


# ------------------------------------------------------------------ H4
def h4(cls):
    res = {"mcnemar": {}}
    both = cls[cls.set.isin(["S2019", "S2023"])]
    wide = both.pivot_table(index=["model", "set", "id"], columns="task", values="correct").dropna()
    for (m, s), g in wide.groupby(level=[0, 1]):
        b = int(((g.P0 == 1) & (g.P1 == 0)).sum()); c = int(((g.P0 == 0) & (g.P1 == 1)).sum())
        t = mcnemar([[0, b], [c, 0]], exact=True)
        res["mcnemar"].setdefault(m, {})[s] = {"n": len(g), "acc_p0": float(g.P0.mean()), "acc_p1": float(g.P1.mean()),
                                               "gain": float(g.P1.mean() - g.P0.mean()), "p0_only": b, "p1_only": c,
                                               "p": float(t.pvalue)}
    d = both.copy()
    d["p1"] = (d.task == "P1").astype(int)
    d["hom"] = d.homophily
    d["cluster"] = d.set + "_" + d.id
    fit = smf.gee("correct ~ p1 * hom + C(model) + C(set)", groups="cluster", data=d,
                  family=sm.families.Binomial(), cov_struct=sm.cov_struct.Exchangeable()).fit()
    ci = fit.conf_int()
    res["gee"] = {k: {"coef": float(fit.params[k]), "or": float(np.exp(fit.params[k])),
                      "ci_or": [float(np.exp(ci.loc[k, 0])), float(np.exp(ci.loc[k, 1]))], "p": float(fit.pvalues[k])}
                  for k in ["p1", "hom", "p1:hom"]}
    # gain by homophily band (for the figure)
    d["band"] = pd.cut(d.hom, [-0.01, 0.25, 0.5, 0.75, 1.0], labels=["0–0.25", "0.25–0.5", "0.5–0.75", "0.75–1"])
    gb = d.pivot_table(index=["model", "set", "id", "band"], columns="task", values="correct", observed=True).dropna()
    gb = (gb.P1 - gb.P0).groupby(level=[0, 3], observed=True).agg(["mean", "count"])
    res["gain_by_band"] = {m: {str(b): {"gain": float(r["mean"]), "n": int(r["count"])}
                               for b, r in gb.loc[m].iterrows()} for m in ORDER}
    return res


# ------------------------------------------------------------------ figures
def fig_acc(T, path):
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    x = np.arange(3)
    for i, m in enumerate(ORDER):
        acc = [T["P0"][m][s]["acc"] * 100 for s in SETS]
        lo = [acc[j] - T["P0"][m][s]["ci"][0] * 100 for j, s in enumerate(SETS)]
        hi = [T["P0"][m][s]["ci"][1] * 100 - acc[j] for j, s in enumerate(SETS)]
        off = (i - 1.5) * 0.06
        ax.errorbar(x + off, acc, yerr=[lo, hi], color=COL[m], lw=2, marker="o", ms=7, mec=SURF, mew=1.5,
                    capsize=3, label=m)
    g = [T["GCN"][s]["acc"] * 100 for s in ["S2019", "S2023"]]
    ax.plot([0, 1], g, color=COL["GCN (no text)"], lw=2, ls="--", marker="s", ms=6, label="GCN (no text)")
    ax.axvspan(0.5, 1.5, color="#eb6834", alpha=0.06, lw=0)
    ax.set_xticks(x, ["2019\n(seen by all)", "2023\n(seen by new models only)", "2026\n(seen by none)"])
    ax.set_ylabel("Accuracy (%)"); ax.grid(axis="x", visible=False)
    ax.set_title("Zero-shot category accuracy by publication year")
    ax.legend(frameon=False, fontsize=8.5, ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.2),
              handlelength=1.6, columnspacing=1.0)
    fig.text(0.01, 0.01, "Text-only prompt (P0). Error bars: Wilson 95% CI. GCN: mean of 5 seeds.",
             fontsize=7.5, color=MUTED)
    fig.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig(path, dpi=200); plt.close(fig)


def fig_did(R, path):
    fig, ax = plt.subplots(figsize=(6.8, 2.8))
    ms = ORDER[1:]
    for i, m in enumerate(ms):
        d = R["H2"]["accuracy_did"][m]
        ax.plot([d["ci"][0] * 100, d["ci"][1] * 100], [i, i], color="#2a78d6", lw=2, solid_capstyle="round")
        ax.plot(d["did"] * 100, i, "o", ms=8, color="#2a78d6", mec=SURF, mew=2)
        ax.annotate(f"{d['did'] * 100:+.1f} pp", (d["ci"][1] * 100, i), xytext=(6, -3),
                    textcoords="offset points", fontsize=8.5)
    ax.axvline(0, color=MUTED, lw=1)
    ax.set_yticks(range(len(ms)), [f"{m} vs Llama-2" for m in ms]); ax.grid(axis="y", visible=False)
    ax.set_ylim(-0.6, len(ms) - 0.4)
    ax.set_xlabel("Extra 2023-vs-2026 advantage (pp, 95% bootstrap CI)")
    ax.set_title("Extra advantage on papers the model may have seen")
    fig.tight_layout(); fig.savefig(path, dpi=200); plt.close(fig)


def fig_probe(R, path):
    fig, ax = plt.subplots(figsize=(6.2, 3.4))
    x = np.arange(len(ORDER)); w = 0.36
    for j, (s, col, lab) in enumerate([("S2023", "#2a78d6", "2023 papers"), ("S2026", "#eb6834", "2026 papers")]):
        v = [R["H3"]["by_model"][m][s]["f1_mean"] * 100 for m in ORDER]
        ax.bar(x + (j - 0.5) * w * 1.06, v, w, color=col, label=lab, zorder=2)
        for i, m in enumerate(ORDER):
            e = R["H3"]["by_model"][m][s]
            ax.text(x[i] + (j - 0.5) * w * 1.06, v[i] + 0.4, f"{e['exact']}/{e['n']}", ha="center",
                    va="bottom", fontsize=7.5, color=MUTED)
    ax.set_xticks(x, ORDER); ax.grid(axis="x", visible=False)
    ax.set_ylabel("Word overlap with true ending (F1, %)")
    ax.set_title("Title completion from the first half of the title")
    ax.set_ylim(0, ax.get_ylim()[1] * 1.25)
    ax.legend(frameon=False, fontsize=8.5, ncol=2, loc="upper right")
    fig.text(0.01, 0.01, "Numbers above bars: exact completions / papers.", fontsize=7.5, color=MUTED)
    fig.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig(path, dpi=200); plt.close(fig)


def fig_hom(R, path):
    bands = ["0–0.25", "0.25–0.5", "0.5–0.75", "0.75–1"]
    fig, ax = plt.subplots(figsize=(6.6, 4.0))
    for m in ORDER:
        gb = R["H4"]["gain_by_band"][m]
        ax.plot(range(4), [gb.get(b, {}).get("gain", np.nan) * 100 for b in bands], color=COL[m], lw=2,
                marker="o", ms=7, mec=SURF, mew=1.5, label=m)
    ax.axhline(0, color=MUTED, lw=1)
    ax.set_xticks(range(4), bands); ax.set_xlabel("Label homophily of the paper's citation neighbourhood")
    ax.set_ylabel("Accuracy gain from neighbour titles (pp)")
    ax.set_title("Gain from neighbour titles by homophily")
    ax.legend(frameon=False, fontsize=8.5, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.2))
    fig.tight_layout(); fig.savefig(path, dpi=200); plt.close(fig)


# ------------------------------------------------------------------ tables
def pct(x, d=1):
    return f"{100 * x:.{d}f}"


def tables(R):
    T = R["acc"]; L = []
    L.append("## Table 1. Accuracy (%) by model, prompt and test set [Wilson 95% CI]\n")
    L.append("| Model | Prompt | S2019 | S2023 | S2026 | Invalid answers |\n|---|---|---|---|---|---|")
    for task in ["P0", "P1"]:
        for m in ORDER:
            cells = []
            for s in SETS:
                e = T.get(task, {}).get(m, {}).get(s)
                cells.append(f"{pct(e['acc'])} [{pct(e['ci'][0])}, {pct(e['ci'][1])}]" if e else "—")
            inv = np.mean([e["invalid"] for e in T[task][m].values()])
            L.append(f"| {m} | {task} | {' | '.join(cells)} | {pct(inv)}% |")
    L.append(f"| GCN (no text, 5 seeds) | — | {pct(T['GCN']['S2019']['acc'])} ± {pct(T['GCN']['S2019']['sd_over_seeds'])} | "
             f"{pct(T['GCN']['S2023']['acc'])} ± {pct(T['GCN']['S2023']['sd_over_seeds'])} | — | — |\n")
    L.append("## Table 2. H1: drop from S2019 to S2023, LLM (P0) vs GCN\n\n| Model | LLM drop (pp) | GCN drop (pp) | Difference [95% CI] | p (bootstrap) |\n|---|---|---|---|---|")
    for m in ORDER:
        e = R["H1"][m]
        L.append(f"| {m} | {pct(e['llm_drop'])} | {pct(e['gcn_drop'])} | {pct(e['did'])} [{pct(e['ci'][0])}, {pct(e['ci'][1])}] | {e['p_boot']:.3g} |")
    h = R["H2"]
    L.append(f"\n## Table 3. H2: extra 2023-vs-2026 advantage of new models over Llama-2 (P0)\n\nPooled GEE interaction (new model × 2023, category-adjusted): OR = {h['pooled']['or']:.2f} "
             f"[{h['pooled']['ci'][0]:.2f}, {h['pooled']['ci'][1]:.2f}], p = {h['pooled']['p']:.3g} (Holm {R['holm']['H2']:.3g}).\n")
    L.append("| Model | Accuracy DiD (pp) [95% CI] | Category-reweighted DiD (pp) [95% CI] | GEE interaction OR [95% CI] | p |\n|---|---|---|---|---|")
    for m in ORDER[1:]:
        a, b, c = h["accuracy_did"][m], h["accuracy_did_category_reweighted"][m], h["per_model_interaction"][m]
        L.append(f"| {m} | {pct(a['did'])} [{pct(a['ci'][0])}, {pct(a['ci'][1])}] | {pct(b['did'])} [{pct(b['ci'][0])}, {pct(b['ci'][1])}] | "
                 f"{c['or']:.2f} [{c['ci'][0]:.2f}, {c['ci'][1]:.2f}] | {c['p']:.3g} |")
    L.append("\n## Table 4. H3: title-completion probe\n\n| Model | Exact 2023 | Exact 2026 | Fisher p | Mean F1 2023 | Mean F1 2026 | F1 Mann–Whitney p |\n|---|---|---|---|---|---|---|")
    for m in ORDER:
        e = R["H3"]["by_model"][m]
        L.append(f"| {m} | {e['S2023']['exact']}/{e['S2023']['n']} ({pct(e['S2023']['exact_rate'])}%) | {e['S2026']['exact']}/{e['S2026']['n']} ({pct(e['S2026']['exact_rate'])}%) | "
                 f"{e['fisher_p']:.3g} | {pct(e['S2023']['f1_mean'])} | {pct(e['S2026']['f1_mean'])} | {e['f1_mwu_p']:.3g} |")
    p = R["H3"]["pooled_did"]
    L.append(f"\nPooled DiD in exact-match rate (new models minus Llama-2, 2023 minus 2026): {pct(p['did'], 2)} pp [{pct(p['ci'][0], 2)}, {pct(p['ci'][1], 2)}], bootstrap p = {p['p_boot']:.3g} (Holm {R['holm']['H3']:.3g}).\n")
    L.append("## Table 5. H4: effect of citation-neighbour titles (P1 vs P0), McNemar exact tests\n\n| Model | Set | Acc P0 | Acc P1 | Gain (pp) | Only P0 right | Only P1 right | p |\n|---|---|---|---|---|---|---|---|")
    for m in ORDER:
        for s in ["S2019", "S2023"]:
            e = R["H4"]["mcnemar"][m][s]
            L.append(f"| {m} | {s} | {pct(e['acc_p0'])} | {pct(e['acc_p1'])} | {pct(e['gain'])} | {e['p0_only']} | {e['p1_only']} | {e['p']:.3g} |")
    g = R["H4"]["gee"]
    L.append(f"\nGEE (all models, both sets): neighbour prompt OR = {g['p1']['or']:.2f} [{g['p1']['ci_or'][0]:.2f}, {g['p1']['ci_or'][1]:.2f}]; "
             f"prompt × homophily OR = {g['p1:hom']['or']:.2f} [{g['p1:hom']['ci_or'][0]:.2f}, {g['p1:hom']['ci_or'][1]:.2f}], p = {g['p1:hom']['p']:.3g} (Holm {R['holm']['H4']:.3g}).\n")
    return "\n".join(L) + "\n"


def main():
    cls, probe = load()
    gcn = json.load(open("results/gcn.json"))
    R = {"acc": acc_table(cls, gcn)}
    R["H1"] = h1(cls, gcn)
    R["H2"] = h2(cls)
    R["H3"] = h3(probe)
    R["H4"] = h4(cls)
    keys = ["H1", "H2", "H3", "H4"]
    ps = [R["H1"][OLD]["p_boot"], R["H2"]["pooled"]["p"], R["H3"]["pooled_did"]["p_boot"], R["H4"]["gee"]["p1:hom"]["p"]]
    R["holm"] = dict(zip(keys, map(float, multipletests(ps, method="holm")[1])))
    json.dump(R, open("results/results.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    md = tables(R)
    open("results/tables.md", "w", encoding="utf-8").write(md)
    fig_acc(R["acc"], "figures/fig1_accuracy_by_year.png")
    fig_did(R, "figures/fig2_memorisation_did.png")
    fig_probe(R, "figures/fig3_title_probe.png")
    fig_hom(R, "figures/fig4_neighbours_homophily.png")
    print(md)


if __name__ == "__main__":
    main()
