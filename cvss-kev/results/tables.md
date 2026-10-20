## Cohort

n = 180,432 CVEs, of which 1,112 in KEV (0.6%).

## Table 1. KEV rate by CVSS v3 severity (H1)

| Severity | CVEs | In KEV | KEV rate | 95% CI |
|---|---:|---:|---:|---|
| Low | 3,277 | 3 | 0.09% | [0.03, 0.27] |
| Medium | 77,474 | 117 | 0.15% | [0.13, 0.18] |
| High | 73,115 | 596 | 0.82% | [0.75, 0.88] |
| Critical | 26,566 | 396 | 1.49% | [1.35, 1.64] |

χ²(3) = 667.3, p = 2.5e-144 (Holm-adjusted 7.6e-144), Cramér's V = 0.061.

## H2. Score difference

Median score KEV = 8.8, non-KEV = 7.5 (means 8.41 vs 7.12). Mann–Whitney U = 1.441e+08, p = 8e-146 (Holm 3.2e-145), rank-biserial r = 0.445.

## Table 2. CVSS thresholds as a test for exploitation (H3, H4)

| Test | Sensitivity | Specificity | PPV | NPV | Odds ratio [95% CI] | Fisher p (Holm) |
|---|---|---|---|---|---|---|
| score >=7.0 | 89.2% [87.2, 90.9] | 45.0% [44.7, 45.2] | 1.00% | 99.9% | 6.75 [5.59, 8.16] | 8.5e-135 (1.7e-134) |
| score >=9.0 | 35.6% [32.9, 38.5] | 85.4% [85.2, 85.6] | 1.49% | 99.5% | 3.24 [2.86, 3.66] | 3.4e-67 (3.4e-67) |

## H6. AUC = 0.723, 95% bootstrap CI [0.710, 0.735]

## Table 3. Replication of Allodi & Massacci (2014): CVSS v2 ≥ 6

| | Sensitivity | Specificity |
|---|---|---|
| Allodi & Massacci 2014 (NVD vs Symantec) | 78.7% | 44.4% |
| This study (NVD vs KEV, n=105,050, KEV=735) | 78.6% [75.5, 81.4] | 58.2% [57.9, 58.5] |

## Table 4. Case-control bootstrap (score ≥ 7.0; 1:10 controls; 400 resamples)

| Matched on | Cases used | Sensitivity (median [2.5, 97.5]) | Specificity | Odds ratio |
|---|---:|---|---|---|
| year | 1,112 | 89.1% [87.4%, 91.0%] | 44.6% [43.5%, 45.4%] | 6.55 [5.42, 7.94] |
| year + cia | 1,112 | 89.3% [87.1%, 90.8%] | 17.0% [15.2%, 18.6%] | 1.69 [1.49, 1.92] |

## Table 5. Logistic regression (H5), n = 180,432, McFadden pseudo-R² = 0.069

| Metric | Level vs reference | Odds ratio [95% CI] | p |
|---|---|---|---|
| attackVector | ADJACENT_NETWORK vs LOCAL_OR_PHYSICAL | 0.63 [0.40, 1.01] | 0.056 |
| attackVector | NETWORK vs LOCAL_OR_PHYSICAL | 1.17 [1.00, 1.37] | 0.058 |
| attackComplexity | LOW vs HIGH | 1.24 [0.96, 1.61] | 0.1 |
| privilegesRequired | LOW vs HIGH | 1.43 [1.09, 1.89] | 0.011 |
| privilegesRequired | NONE vs HIGH | 2.14 [1.63, 2.79] | 2.9e-08 |
| userInteraction | NONE vs REQUIRED | 1.45 [1.23, 1.71] | 9.1e-06 |
| scope | CHANGED vs UNCHANGED | 1.65 [1.28, 2.12] | 9.3e-05 |
| confidentialityImpact | HIGH vs NONE | 3.14 [2.41, 4.10] | 3.5e-17 |
| confidentialityImpact | LOW vs NONE | 0.88 [0.53, 1.45] | 0.62 |
| integrityImpact | HIGH vs NONE | 2.27 [1.77, 2.91] | 7.3e-11 |
| integrityImpact | LOW vs NONE | 0.91 [0.56, 1.49] | 0.72 |
| availabilityImpact | HIGH vs NONE | 1.50 [1.19, 1.90] | 0.00062 |
| availabilityImpact | LOW vs NONE | 1.55 [0.89, 2.70] | 0.12 |

## Table 6. Robustness checks

| Cohort | n | KEV | Cramér's V | Sens ≥7 | Spec ≥7 | OR ≥7 | AUC |
|---|---:|---:|---:|---|---|---|---|
| Main (2017–2024, NVD or CNA score) | 180,432 | 1,112 | 0.061 | 89.2% | 45.0% | 6.75 | 0.723 |
| NVD-scored only | 159,044 | 1,015 | 0.062 | 89.1% | 44.3% | 6.47 | 0.722 |
| 2018–2023 only | 126,162 | 863 | 0.059 | 88.4% | 43.4% | 5.86 | 0.711 |
