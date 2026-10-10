"""Verify website candidates found by web search (school_code,url) with the same test as find_websites.py.
Output: data/processed/website_guess.csv gets the verified rows appended (score, matched='websearch').
Usage: python3 -I scripts/verify_candidates.py data/processed/website_search_candidates.csv
"""
import csv, sys, os
sys.path.insert(0, "scripts")
import find_websites as F
schools = {r["school_code"]: r for r in csv.DictReader(open("data/processed/fl_directory_2026.csv"))}
have = {r["school_code"] for r in csv.DictReader(open(F.OUT))} if os.path.exists(F.OUT) else set()
new = []
for r in csv.DictReader(open(sys.argv[1])):
    c = r["school_code"]
    if c in have: continue
    code, final, body = F.curl(r["url"], 15)
    sc = F.verify(schools[c], F.clean(body)) if code == 200 else 0.0
    print(c, schools[c]["school_name"], "->", final, code, sc)
    if sc >= 0.7: new.append({"school_code": c, "url": final, "score": sc, "matched": "websearch"})
with open(F.OUT, "a", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["school_code", "url", "score", "matched"])
    for x in new: w.writerow(x)
print(len(new), "verified")
