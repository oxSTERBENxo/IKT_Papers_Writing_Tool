"""CVSS severity vs. CISA KEV listing: all statistics for the paper.

Follows ANALYSIS_PLAN.md. Run:  .venv/Scripts/python analysis.py
Writes results/results.json, results/tables.md and figures/*.png.
"""
import json

import matplotlib
import matplotlib.ticker
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats
from statsmodels.stats.contingency_tables import Table2x2
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.proportion import proportion_confint

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

SEED = 20261019
rng = np.random.default_rng(SEED)

# Chart colours (validated reference palette, light mode)
BLUE, ORANGE = "#2a78d6", "#eb6834"
INK, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED,
    "text.color": INK, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "font.size": 10,
    "axes.titlesize": 11, "axes.titleweight": "bold", "axes.titlelocation": "left",
})

SEV_ORDER = ["Low", "Medium", "High", "Critical"]


# ---------------------------------------------------------------- data
def load():
    n = pd.read_csv("data/nvd_cvss.csv", low_memory=False)
    kev = set(pd.read_csv("data/kev.csv").cveID)
    n["year"] = n.published.str[:4].astype(int)
    n["kev"] = n.cve.isin(kev).astype(int)
    return n


def cohort(n, y0=2017, y1=2024, nvd_only=False):
    c = n[(n.year >= y0) & (n.year <= y1) & (n.status != "Rejected") & n.v3_score.notna()]
    c = c[c.v3_score > 0]  # score 0.0 = "None" severity, not a vulnerability rating
    if nvd_only:
        c = c[c.v3_source == "nvd"]
    c = c.copy()
    c["sev"] = pd.cut(c.v3_score, [0, 3.95, 6.95, 8.95, 10], labels=SEV_ORDER)
    return c


# ---------------------------------------------------------------- helpers
def wilson(k, n):
    lo, hi = proportion_confint(k, n, method="wilson")
    return [float(lo), float(hi)]


def diag(test, truth):
    """Sensitivity, specificity, PPV, NPV with Wilson CIs."""
    tp = int(((test == 1) & (truth == 1)).sum()); fn = int(((test == 0) & (truth == 1)).sum())
    fp = int(((test == 1) & (truth == 0)).sum()); tn = int(((test == 0) & (truth == 0)).sum())
    out = {"tp": tp, "fn": fn, "fp": fp, "tn": tn}
    for name, k, m in [("sensitivity", tp, tp + fn), ("specificity", tn, tn + fp),
                       ("ppv", tp, tp + fp), ("npv", tn, tn + fn)]:
        out[name] = k / m if m else float("nan")
        out[name + "_ci"] = wilson(k, m) if m else [float("nan")] * 2
    return out


def auc(score, y):
    s1, s0 = score[y == 1], score[y == 0]
    u = stats.mannwhitneyu(s1, s0, alternative="two-sided").statistic
    return u / (len(s1) * len(s0))


# ---------------------------------------------------------------- analyses
def core(c, boot=True):
    r = {"n": int(len(c)), "n_kev": int(c.kev.sum()), "kev_rate": float(c.kev.mean())}

    # H1: KEV rate by severity
    tab = pd.crosstab(c.sev, c.kev).reindex(SEV_ORDER)
    chi2, p, dof, _ = stats.chi2_contingency(tab.values)
    v = np.sqrt(chi2 / (tab.values.sum() * (min(tab.shape) - 1)))
    r["H1"] = {"chi2": float(chi2), "dof": int(dof), "p": float(p), "cramers_v": float(v),
               "by_severity": {s: {"n": int(tab.loc[s].sum()), "kev": int(tab.loc[s, 1]),
                                   "rate": float(tab.loc[s, 1] / tab.loc[s].sum()),
                                   "ci": wilson(int(tab.loc[s, 1]), int(tab.loc[s].sum()))}
                               for s in SEV_ORDER}}

    # H2: score difference
    s1, s0 = c.v3_score[c.kev == 1], c.v3_score[c.kev == 0]
    mw = stats.mannwhitneyu(s1, s0, alternative="two-sided")
    r["H2"] = {"U": float(mw.statistic), "p": float(mw.pvalue),
               "rank_biserial": float(2 * mw.statistic / (len(s1) * len(s0)) - 1),
               "median_kev": float(s1.median()), "median_non": float(s0.median()),
               "mean_kev": float(s1.mean()), "mean_non": float(s0.mean())}

    # H3 + H4: thresholds
    r["H3"], r["H4"] = {}, {}
    for t in (7.0, 9.0):
        test = (c.v3_score >= t).astype(int)
        r["H3"][f">={t}"] = diag(test.values, c.kev.values)
        t2 = Table2x2(pd.crosstab(test, c.kev).reindex(index=[1, 0], columns=[1, 0]).values)
        _, pf = stats.fisher_exact(pd.crosstab(test, c.kev).values)
        lo, hi = t2.oddsratio_confint()
        r["H4"][f">={t}"] = {"odds_ratio": float(t2.oddsratio), "ci": [float(lo), float(hi)],
                             "p_fisher": float(pf)}

    # H6: AUC with stratified bootstrap
    sc, y = c.v3_score.values, c.kev.values
    r["H6"] = {"auc": float(auc(sc, y))}
    if boot:
        i1, i0 = np.where(y == 1)[0], np.where(y == 0)[0]
        bs = []
        for _ in range(1000):
            a = sc[rng.choice(i1, len(i1))]; b = sc[rng.choice(i0, len(i0))]
            bs.append(stats.mannwhitneyu(a, b).statistic / (len(a) * len(b)))
        r["H6"]["ci"] = [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]
    return r


def logistic(c):
    # PHYSICAL has 0 KEV cases (complete separation), so it is merged into LOCAL as the reference.
    c = c.assign(attackVector=c.attackVector.replace({"PHYSICAL": "LOCAL_OR_PHYSICAL", "LOCAL": "LOCAL_OR_PHYSICAL"}))
    ref = {"attackVector": "LOCAL_OR_PHYSICAL", "attackComplexity": "HIGH", "privilegesRequired": "HIGH",
           "userInteraction": "REQUIRED", "scope": "UNCHANGED", "confidentialityImpact": "NONE",
           "integrityImpact": "NONE", "availabilityImpact": "NONE"}
    terms = " + ".join(f"C({k}, Treatment('{v}'))" for k, v in ref.items())
    m = smf.logit(f"kev ~ {terms} + C(year)", data=c).fit(disp=0, maxiter=200)
    ci = m.conf_int()
    rows = []
    for name in m.params.index:
        if name == "Intercept" or name.startswith("C(year)"):
            continue
        var = name.split(",")[0][2:]
        level = name.split("[T.")[1].rstrip("]")
        rows.append({"variable": var, "level": level, "ref": ref[var],
                     "odds_ratio": float(np.exp(m.params[name])),
                     "ci": [float(np.exp(ci.loc[name, 0])), float(np.exp(ci.loc[name, 1]))],
                     "p": float(m.pvalues[name])})
    return {"n": int(m.nobs), "pseudo_r2": float(m.prsquared), "llr_p": float(m.llr_pvalue),
            "terms": rows}


def allodi_observational(n):
    """Their test: CVSS v2 >= 6 vs exploitation, on CVEs with a v2 score."""
    c = n[(n.year >= 2017) & (n.year <= 2024) & (n.status != "Rejected") & n.v2_score.notna()]
    d = diag((c.v2_score >= 6).astype(int).values, c.kev.values)
    d["n"], d["n_kev"] = int(len(c)), int(c.kev.sum())
    d["allodi_2014_nvd"] = {"sensitivity": 0.787, "specificity": 0.444}
    return d


def case_control(c, match, reps=400, ratio=10):
    cases = c[c.kev == 1]
    ctrl = c[c.kev == 0]
    groups = ctrl.groupby(match).indices
    ctrl_scores = ctrl.v3_score.values
    sens, spec, ors = [], [], []
    case_keys = [tuple(x) if len(match) > 1 else x[0] for x in cases[match].values]
    usable = [k in groups for k in case_keys]
    cs = cases.v3_score.values[usable]
    keys = [k for k, u in zip(case_keys, usable) if u]
    for _ in range(reps):
        idx = rng.choice(len(cs), len(cs))  # resample cases
        a = cs[idx]
        b = np.concatenate([ctrl_scores[rng.choice(groups[keys[i]], ratio)] for i in idx])
        tp = (a >= 7).sum(); fn = len(a) - tp; fp = (b >= 7).sum(); tn = len(b) - fp
        sens.append(tp / len(a)); spec.append(tn / len(b))
        ors.append((tp + .5) * (tn + .5) / ((fn + .5) * (fp + .5)))
    q = lambda v: {"median": float(np.median(v)), "p2.5": float(np.percentile(v, 2.5)),
                   "p97.5": float(np.percentile(v, 97.5))}
    return {"matched_on": match, "cases_used": int(len(cs)), "cases_dropped": int(len(cases) - len(cs)),
            "ratio": ratio, "reps": reps, "sensitivity_ge7": q(sens), "specificity_ge7": q(spec),
            "odds_ratio_ge7": q(ors)}


# ---------------------------------------------------------------- figures
def fig_rates(r, path):
    d = r["H1"]["by_severity"]
    x = np.arange(4)
    rate = [d[s]["rate"] * 100 for s in SEV_ORDER]
    lo = [rate[i] - d[s]["ci"][0] * 100 for i, s in enumerate(SEV_ORDER)]
    hi = [d[s]["ci"][1] * 100 - rate[i] for i, s in enumerate(SEV_ORDER)]
    fig, ax = plt.subplots(figsize=(6, 3.6))
    ax.bar(x, rate, width=0.55, color=BLUE, zorder=2)
    ax.errorbar(x, rate, yerr=[lo, hi], fmt="none", ecolor=INK, elinewidth=1.2, capsize=4, zorder=3)
    for i, s in enumerate(SEV_ORDER):
        ax.text(i, rate[i] + hi[i] + 0.05, f"{rate[i]:.2f}%\nn={d[s]['n']:,}", ha="center",
                va="bottom", fontsize=8.5, color=MUTED)
    ax.set_xticks(x, SEV_ORDER); ax.grid(axis="x", visible=False)
    ax.set_ylabel("CVEs listed in KEV (%)")
    ax.set_ylim(0, max(np.add(rate, hi)) * 1.35)
    ax.set_title("Share of CVEs later listed as exploited, by CVSS v3 severity")
    fig.text(0.01, 0.01, "Error bars: Wilson 95% CI. CVEs published 2017–2024.", fontsize=7.5, color=MUTED)
    fig.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig(path, dpi=200); plt.close(fig)


def fig_ecdf(c, path):
    fig, ax = plt.subplots(figsize=(6, 3.6))
    for val, col, lab in [(0, BLUE, "Not in KEV"), (1, ORANGE, "In KEV")]:
        s = np.sort(c.v3_score[c.kev == val].values)
        yv = np.arange(1, len(s) + 1) / len(s)
        ax.step(s, yv, where="post", color=col, lw=2, label=f"{lab} (n={len(s):,})")
    for t in (7, 9):
        ax.axvline(t, color=MUTED, lw=0.8, ls="--", zorder=1)
    ax.set_xlabel("CVSS v3 base score"); ax.set_ylabel("Cumulative share of CVEs")
    ax.set_xlim(0, 10); ax.set_ylim(0, 1.01)
    ax.legend(frameon=False, loc="upper left")
    ax.set_title("Exploited CVEs score higher, but the groups overlap")
    fig.tight_layout(); fig.savefig(path, dpi=200); plt.close(fig)


def fig_roc(c, r, path):
    y = c.kev.values; s = c.v3_score.values
    th = np.r_[np.inf, np.sort(np.unique(s))[::-1]]
    P, N = y.sum(), (1 - y).sum()
    tpr = [((s >= t) & (y == 1)).sum() / P for t in th]
    fpr = [((s >= t) & (y == 0)).sum() / N for t in th]
    fig, ax = plt.subplots(figsize=(4.6, 4.4))
    ax.plot([0, 1], [0, 1], color=MUTED, lw=0.8, ls="--")
    ax.plot(fpr, tpr, color=BLUE, lw=2)
    for t, lab in [(7.0, "≥ 7.0 (High)"), (9.0, "≥ 9.0 (Critical)")]:
        h = r["H3"][f">={t}"]
        ax.plot(1 - h["specificity"], h["sensitivity"], "o", ms=8, color=BLUE, mec=SURFACE, mew=2)
        ax.annotate(lab, (1 - h["specificity"], h["sensitivity"]), xytext=(8, -12),
                    textcoords="offset points", fontsize=8.5, color=INK)
    ci = r["H6"].get("ci", [np.nan, np.nan])
    ax.text(0.98, 0.04, f"AUC = {r['H6']['auc']:.3f}\n95% CI [{ci[0]:.3f}, {ci[1]:.3f}]",
            ha="right", va="bottom", transform=ax.transAxes, fontsize=9)
    ax.set_xlabel("False positive rate (1 − specificity)"); ax.set_ylabel("Sensitivity")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1.01); ax.set_aspect("equal")
    ax.set_title("ROC: CVSS v3 score vs KEV listing")
    fig.tight_layout(); fig.savefig(path, dpi=200); plt.close(fig)


def fig_forest(lg, path):
    nice = {"attackVector": "Attack vector", "attackComplexity": "Attack complexity",
            "privilegesRequired": "Privileges required", "userInteraction": "User interaction",
            "scope": "Scope", "confidentialityImpact": "Confidentiality", "integrityImpact": "Integrity",
            "availabilityImpact": "Availability"}
    rows = lg["terms"][::-1]
    lvl = lambda v: v.replace("_OR_", "/").replace("_", " ").capitalize()
    fig, ax = plt.subplots(figsize=(6.4, 0.32 * len(rows) + 1.2))
    for i, t in enumerate(rows):
        ax.plot(t["ci"], [i, i], color=BLUE, lw=2, solid_capstyle="round")
        ax.plot(t["odds_ratio"], i, "o", ms=8, color=BLUE, mec=SURFACE, mew=2)
    ax.set_yticks(range(len(rows)),
                  [f"{nice[t['variable']]}: {lvl(t['level'])} vs {lvl(t['ref'])}" for t in rows],
                  fontsize=8.5)
    ax.axvline(1, color=MUTED, lw=1)
    ax.set_xscale("log"); ax.set_xlabel("Odds ratio for KEV listing (log scale, 95% CI)")
    ax.set_xticks([0.25, 0.5, 1, 2, 4], ["0.25", "0.5", "1", "2", "4"])
    ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.set_xlim(0.25, 5)
    ax.grid(axis="y", visible=False)
    fig.suptitle("Which CVSS v3 base metrics go with exploitation?", x=0.01, ha="left",
                 fontsize=11, fontweight="bold")
    fig.text(0.01, 0.01, "Logistic regression, all metrics together plus publication-year dummies.",
             fontsize=7.5, color=MUTED)
    fig.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig(path, dpi=200); plt.close(fig)


# ---------------------------------------------------------------- report tables
def pct(x):
    return f"{100 * x:.1f}%"


def ci(c):
    return f"[{100 * c[0]:.1f}, {100 * c[1]:.1f}]"


def tables(R):
    m = R["main"]; L = []
    L.append(f"## Cohort\n\nn = {m['n']:,} CVEs, of which {m['n_kev']:,} in KEV ({pct(m['kev_rate'])}).\n")
    L.append("## Table 1. KEV rate by CVSS v3 severity (H1)\n\n| Severity | CVEs | In KEV | KEV rate | 95% CI |\n|---|---:|---:|---:|---|")
    for s in SEV_ORDER:
        d = m["H1"]["by_severity"][s]
        L.append(f"| {s} | {d['n']:,} | {d['kev']:,} | {100 * d['rate']:.2f}% | [{100 * d['ci'][0]:.2f}, {100 * d['ci'][1]:.2f}] |")
    h = m["H1"]
    L.append(f"\nχ²({h['dof']}) = {h['chi2']:.1f}, p = {h['p']:.2g} (Holm-adjusted {R['holm']['H1']:.2g}), Cramér's V = {h['cramers_v']:.3f}.\n")
    h = m["H2"]
    L.append(f"## H2. Score difference\n\nMedian score KEV = {h['median_kev']}, non-KEV = {h['median_non']} "
             f"(means {h['mean_kev']:.2f} vs {h['mean_non']:.2f}). Mann–Whitney U = {h['U']:.4g}, p = {h['p']:.2g} "
             f"(Holm {R['holm']['H2']:.2g}), rank-biserial r = {h['rank_biserial']:.3f}.\n")
    L.append("## Table 2. CVSS thresholds as a test for exploitation (H3, H4)\n\n| Test | Sensitivity | Specificity | PPV | NPV | Odds ratio [95% CI] | Fisher p (Holm) |\n|---|---|---|---|---|---|---|")
    for t in (">=7.0", ">=9.0"):
        d, o = m["H3"][t], m["H4"][t]
        L.append(f"| score {t} | {pct(d['sensitivity'])} {ci(d['sensitivity_ci'])} | {pct(d['specificity'])} {ci(d['specificity_ci'])} | "
                 f"{100 * d['ppv']:.2f}% | {pct(d['npv'])} | {o['odds_ratio']:.2f} [{o['ci'][0]:.2f}, {o['ci'][1]:.2f}] | {o['p_fisher']:.2g} ({R['holm']['H4 ' + t]:.2g}) |")
    L.append(f"\n## H6. AUC = {m['H6']['auc']:.3f}, 95% bootstrap CI [{m['H6']['ci'][0]:.3f}, {m['H6']['ci'][1]:.3f}]\n")
    a = R["allodi_observational"]
    L.append("## Table 3. Replication of Allodi & Massacci (2014): CVSS v2 ≥ 6\n\n| | Sensitivity | Specificity |\n|---|---|---|")
    L.append(f"| Allodi & Massacci 2014 (NVD vs Symantec) | 78.7% | 44.4% |")
    L.append(f"| This study (NVD vs KEV, n={a['n']:,}, KEV={a['n_kev']:,}) | {pct(a['sensitivity'])} {ci(a['sensitivity_ci'])} | {pct(a['specificity'])} {ci(a['specificity_ci'])} |\n")
    L.append("## Table 4. Case-control bootstrap (score ≥ 7.0; 1:10 controls; 400 resamples)\n\n| Matched on | Cases used | Sensitivity (median [2.5, 97.5]) | Specificity | Odds ratio |\n|---|---:|---|---|---|")
    for cc in R["case_control"]:
        s, p_, o = cc["sensitivity_ge7"], cc["specificity_ge7"], cc["odds_ratio_ge7"]
        L.append(f"| {' + '.join(cc['matched_on'])} | {cc['cases_used']:,} | {pct(s['median'])} [{pct(s['p2.5'])}, {pct(s['p97.5'])}] | "
                 f"{pct(p_['median'])} [{pct(p_['p2.5'])}, {pct(p_['p97.5'])}] | {o['median']:.2f} [{o['p2.5']:.2f}, {o['p97.5']:.2f}] |")
    lg = R["logistic"]
    L.append(f"\n## Table 5. Logistic regression (H5), n = {lg['n']:,}, McFadden pseudo-R² = {lg['pseudo_r2']:.3f}\n\n| Metric | Level vs reference | Odds ratio [95% CI] | p |\n|---|---|---|---|")
    for t in lg["terms"]:
        L.append(f"| {t['variable']} | {t['level']} vs {t['ref']} | {t['odds_ratio']:.2f} [{t['ci'][0]:.2f}, {t['ci'][1]:.2f}] | {t['p']:.2g} |")
    L.append("\n## Table 6. Robustness checks\n\n| Cohort | n | KEV | Cramér's V | Sens ≥7 | Spec ≥7 | OR ≥7 | AUC |\n|---|---:|---:|---:|---|---|---|---|")
    for name, r in [("Main (2017–2024, NVD or CNA score)", m)] + list(R["robustness"].items()):
        d, o = r["H3"][">=7.0"], r["H4"][">=7.0"]
        L.append(f"| {name} | {r['n']:,} | {r['n_kev']:,} | {r['H1']['cramers_v']:.3f} | {pct(d['sensitivity'])} | {pct(d['specificity'])} | {o['odds_ratio']:.2f} | {r['H6']['auc']:.3f} |")
    return "\n".join(L) + "\n"


def main():
    n = load()
    c = cohort(n)
    R = {"seed": SEED, "main": core(c)}
    R["logistic"] = logistic(c)
    R["allodi_observational"] = allodi_observational(n)
    c["cia"] = c.confidentialityImpact + "/" + c.integrityImpact + "/" + c.availabilityImpact
    R["case_control"] = [case_control(c, ["year"]), case_control(c, ["year", "cia"])]
    R["robustness"] = {"NVD-scored only": core(cohort(n, nvd_only=True), boot=False),
                       "2018–2023 only": core(cohort(n, 2018, 2023), boot=False)}
    m = R["main"]
    keys = ["H1", "H2", "H4 >=7.0", "H4 >=9.0"]
    ps = [m["H1"]["p"], m["H2"]["p"], m["H4"][">=7.0"]["p_fisher"], m["H4"][">=9.0"]["p_fisher"]]
    R["holm"] = dict(zip(keys, map(float, multipletests(ps, method="holm")[1])))

    json.dump(R, open("results/results.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    open("results/tables.md", "w", encoding="utf-8").write(tables(R))
    fig_rates(m, "figures/fig1_kev_rate_by_severity.png")
    fig_ecdf(c, "figures/fig2_score_ecdf.png")
    fig_roc(c, m, "figures/fig3_roc.png")
    fig_forest(R["logistic"], "figures/fig4_logistic_forest.png")
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    print(open("results/tables.md", encoding="utf-8").read())


if __name__ == "__main__":
    main()
