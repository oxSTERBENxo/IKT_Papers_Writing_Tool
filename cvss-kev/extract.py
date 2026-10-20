"""Stream the NVD feed (CVE-all.json.xz) into a compact CSV of CVSS fields.

Output: data/nvd_cvss.csv with one row per CVE.
"""
import csv
import lzma

import ijson

SRC = "data/CVE-all.json.xz"
OUT = "data/nvd_cvss.csv"

V3_FIELDS = ["attackVector", "attackComplexity", "privilegesRequired", "userInteraction",
             "scope", "confidentialityImpact", "integrityImpact", "availabilityImpact"]


def pick(metrics):
    """Prefer NVD's own score (nvd@nist.gov); otherwise the first (CNA) score."""
    if not metrics:
        return None, None
    for m in metrics:
        if m.get("source") == "nvd@nist.gov":
            return m, "nvd"
    return metrics[0], "cna"


def main():
    cols = ["cve", "published", "status", "v3_version", "v3_source", "v3_score", "v3_severity",
            "v3_exploitability", "v3_impact", *V3_FIELDS, "v2_score", "has_v4", "cwe"]
    n = 0
    with lzma.open(SRC, "rb") as f, open(OUT, "w", newline="", encoding="utf-8") as out:
        w = csv.writer(out)
        w.writerow(cols)
        for item in ijson.items(f, "cve_items.item", use_float=True):
            met = item.get("metrics") or {}
            v3, src = pick((met.get("cvssMetricV31") or []) + (met.get("cvssMetricV30") or []))
            v2, _ = pick(met.get("cvssMetricV2") or [])
            d = (v3 or {}).get("cvssData", {})
            cwe = ""
            for wk in item.get("weaknesses") or []:
                for desc in wk.get("description") or []:
                    if desc.get("value", "").startswith("CWE-"):
                        cwe = desc["value"]
                        break
                if cwe:
                    break
            w.writerow([
                item["id"], item.get("published", "")[:10], item.get("vulnStatus", ""),
                d.get("version", ""), src or "", d.get("baseScore", ""), d.get("baseSeverity", ""),
                (v3 or {}).get("exploitabilityScore", ""), (v3 or {}).get("impactScore", ""),
                *[d.get(k, "") for k in V3_FIELDS],
                (v2 or {}).get("cvssData", {}).get("baseScore", ""),
                int(bool(met.get("cvssMetricV40"))), cwe,
            ])
            n += 1
            if n % 50000 == 0:
                print(n, "records", flush=True)
    print("done:", n, "records ->", OUT)


if __name__ == "__main__":
    main()
