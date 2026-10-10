"""Write the per-school source log: where each school's website and tuition value came from.

Output: data/processed/tuition_source_log.csv with columns
  school_code, school_name, tuition_status, website_found_by, website, tuition_source_url, source_type, tuition_year, coding_batch
website_found_by: email_domain (school's own email domain) | name_guess (find_websites.py) | name_guess_ext (second pass)
                  | web_search (candidate from a web search, verified) 
coding_batch: the hand-coding file that holds the school's row (data/processed/tuition_coding/batch_NNN.txt)
Usage: python3 -I scripts/build_source_log.py
"""
import csv, glob, os, re
P = "data/processed/"
d = {r["school_code"]: r for r in csv.DictReader(open(P + "fl_directory_tuition_2026.csv"))}
how = {}
for f, label in (("website_guess.csv", "name_guess"), ("website_guess_ext.csv", "name_guess_ext")):
    if os.path.exists(P + f):
        for r in csv.DictReader(open(P + f)):
            how[r["school_code"]] = ("web_search" if r.get("matched") == "websearch" else label, r["url"])
batch = {}
for fn in sorted(glob.glob(P + "tuition_coding/batch_*.txt")):
    for l in open(fn):
        if l.strip() and not l.startswith("#"): batch[l.split(" | ")[0].strip()] = os.path.basename(fn)
with open(P + "tuition_source_log.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["school_code", "school_name", "tuition_status", "website_found_by", "website", "tuition_source_url", "source_type", "tuition_year", "coding_batch"])
    for c, r in d.items():
        if r["tuition_status"] in ("not_attempted_no_enrollment", "not_attempted_no_own_domain", "no_website") and c not in how: continue
        by, site = how.get(c, ("email_domain", ""))
        w.writerow([c, r["school_name"], r["tuition_status"], by, site, r["source_url"], r["source_type"], r["tuition_year"], batch.get(c, "")])
print("rows", sum(1 for _ in open(P + "tuition_source_log.csv")) - 1)
