# Analysis plan (fixed before running any outcome statistics)

**Working title:** Does CVSS severity predict real-world exploitation? A replication of Allodi & Massacci (2014) using the CISA Known Exploited Vulnerabilities catalog.

**Type:** replication with updated data (not a novelty claim).

## Data
- NVD records: fkie-cad/nvd-json-data-feeds, `CVE-all.json.xz`, feed timestamp 2026-10-19 (409,838 CVEs).
- CISA KEV catalog: cisagov/kev-data `known_exploited_vulnerabilities.csv`, downloaded 2026-10-19 (1,748 CVEs, added 2021-11-03 to 2026-10-16).

## Cohort
- CVEs published 2017-01-01 to 2024-12-31, so each one has had at least ~22 months to be added to KEV.
- Status not `Rejected`, and a CVSS v3.x base score present.
- Score source: NVD's own score (nvd@nist.gov) when present, otherwise the first CNA score.

**Outcome:** `kev = 1` if the CVE is in the KEV catalog.

## Hypotheses and tests (alpha = 0.05; Holm correction across H1–H4)
| # | Question | Test | Effect size |
|---|---|---|---|
| H1 | Does the KEV rate differ across severity categories (Low/Medium/High/Critical)? | Chi-square test of independence | Cramér's V; KEV rate per category with Wilson 95% CI |
| H2 | Do KEV CVEs have higher base scores? | Mann–Whitney U | Rank-biserial r; medians |
| H3 | How good is "score ≥ 7.0" (High+) and "≥ 9.0" (Critical) as a test for exploitation? | — | Sensitivity, specificity, PPV, NPV, each with Wilson 95% CI |
| H4 | Odds of KEV listing above vs below each threshold | Fisher's exact test | Odds ratio with 95% CI |
| H5 | Which CVSS v3 base metrics are associated with KEV listing, holding the others fixed? | Logistic regression (8 base metrics + publication-year dummies) | Odds ratios with 95% CI |
| H6 | Overall discrimination of the base score | ROC AUC | 1,000-sample bootstrap 95% CI |

Because n is large, almost any difference will be "significant", so conclusions rest on effect sizes and intervals, not p-values alone.

## Direct replication of Allodi & Massacci (2014)
- **Observational:** sensitivity and specificity of the CVSS v2 test "score ≥ 6" (their threshold), on CVEs that also have a v2 score. Compared side by side with their NVD row (sensitivity 78.7%, specificity 44.4%).
- **Case-control:** all KEV CVEs are cases. Controls are random non-KEV CVEs at 1:10, matched on (a) publication year and (b) year plus the C/I/A impact triple, following their "controlled by Impact" design. 400 bootstrap resamples, as in the original. Report the median sensitivity and specificity with 2.5–97.5 percentile intervals.

## Robustness checks (pre-specified)
1. NVD-scored CVEs only (drops CNA fallback scores).
2. Cohort 2018–2023 only.

## Known limitations (stated up front)
- KEV is a lower bound on exploitation: it lists only confirmed exploitation that CISA has acted on, so some "controls" are exploited.
- KEV inclusion criteria (a clear remediation action is required) may favour certain vendors and product types.
- The CVSS scores used are the current values, which may have been revised after publication or after exploitation became known (possible look-ahead).
- EPSS is deliberately left out: current EPSS scores already use exploitation evidence, which would leak the outcome.

## Deviations from the plan (recorded after running)
1. **H5 reference level.** No CVE with attack vector PHYSICAL is in KEV (0 of 1,753), so the logistic model could not be estimated (complete separation). PHYSICAL was merged with LOCAL into one reference level, `LOCAL_OR_PHYSICAL`. Nothing else was changed.
