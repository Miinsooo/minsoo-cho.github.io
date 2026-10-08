"""Probe the Wayback Machine CDX index: for schools with a tuition page found, which years have a saved copy?

Input : data/processed/fl_directory_tuition_2026.csv (status found, source_url)
Output: data/processed/wayback_probe.csv (school_code, url, years_with_snapshot per page and per site)
Only the CDX index is queried (no page downloads). 1 request per second.
Usage: python3 -I scripts/wayback_probe.py [--n 100] [--seed 1]
"""
import argparse, csv, json, random, subprocess, time
from urllib.parse import quote, urlparse

def cdx(url, match="exact"):
    q = f"https://web.archive.org/cdx/search/cdx?url={quote(url, safe='')}&matchType={match}&output=json&fl=timestamp,original&filter=statuscode:200&collapse=timestamp:6&limit=400"
    for _ in range(3):
        p = subprocess.run(["curl", "-sS", "-m", "40", "-A", "FLVoucherTuitionResearch/0.1", q], capture_output=True, text=True)
        time.sleep(1.0)
        try: return json.loads(p.stdout)[1:]
        except Exception: time.sleep(3)
    return None

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=100); ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    rows = [r for r in csv.DictReader(open("data/processed/fl_directory_tuition_2026.csv")) if r["tuition_status"] == "found" and r["source_url"].startswith("http")]
    random.Random(a.seed).shuffle(rows)
    out = csv.writer(open("data/processed/wayback_probe.csv", "w", newline=""))
    out.writerow(["school_code", "page_url", "page_years", "site_years", "ok"])
    for r in rows[: a.n]:
        u = r["source_url"].split("#")[0]
        pg = cdx(u); host = urlparse(u).netloc
        site = cdx(host + "/*", "prefix") if False else cdx(host, "host")
        def yrs(x): return sorted({s[0][:4] for s in x}) if x is not None else None
        out.writerow([r["school_code"], u, " ".join(yrs(pg) or []), " ".join(yrs(site) or []), "1" if pg is not None and site is not None else "0"])
        print(r["school_code"], yrs(pg), flush=True)
