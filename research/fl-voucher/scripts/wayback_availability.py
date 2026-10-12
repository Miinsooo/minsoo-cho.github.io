"""For schools with a tuition page found, ask the Wayback availability API which saved copy is closest to 1 Sept of 2021..2026.

Input : data/processed/fl_directory_tuition_2026.csv (found, source_url)
Output: data/processed/wayback_availability.csv  (school_code, source_url, ts2021..ts2026 = timestamp of the closest copy or empty)
Only the availability endpoint (archive.org/wayback/available) is used: no page content is downloaded here. 1 request per second.
A copy counts as belonging to a school year only if it was taken between 1 Mar of the year before and 28 Feb of the following year
(that is how `year_ok` columns are computed later); here the raw closest timestamps are stored.
Usage: python3 -I scripts/wayback_availability.py [--n 150] [--seed 5]
"""
import argparse, csv, json, os, random, subprocess, time
from urllib.parse import quote

YEARS = range(2021, 2027)

def avail(url, ts):
    q = f"https://archive.org/wayback/available?url={quote(url, safe='')}&timestamp={ts}"
    for _ in range(3):
        p = subprocess.run(["curl", "-sS", "-m", "40", "-A", "FLVoucherTuitionResearch/0.1", q], capture_output=True, text=True)
        time.sleep(1.0)
        try:
            c = json.loads(p.stdout).get("archived_snapshots", {}).get("closest")
            return c["timestamp"] if c and c.get("status") == "200" else ""
        except Exception:
            time.sleep(3)
    return None

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=150); ap.add_argument("--seed", type=int, default=5)
    a = ap.parse_args()
    out = "data/processed/wayback_availability.csv"
    done = {r["school_code"] for r in csv.DictReader(open(out))} if os.path.exists(out) else set()
    rows = [r for r in csv.DictReader(open("data/processed/fl_directory_tuition_2026.csv")) if r["tuition_status"] == "found" and r["source_url"].startswith("http") and r["source_url"].lower().find(".pdf") < 0]
    random.Random(a.seed).shuffle(rows)
    new = not os.path.exists(out)
    f = open(out, "a", newline=""); w = csv.writer(f)
    if new: w.writerow(["school_code", "source_url"] + [f"ts{y}" for y in YEARS])
    for r in [x for x in rows if x["school_code"] not in done][: a.n]:
        ts = [avail(r["source_url"], f"{y}0901") for y in YEARS]
        w.writerow([r["school_code"], r["source_url"]] + ["" if t is None else t for t in ts]); f.flush()
