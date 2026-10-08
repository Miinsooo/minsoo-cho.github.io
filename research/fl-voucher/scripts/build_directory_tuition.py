"""Join the FLDOE directory (3,540 schools) with crawl status and hand-coded tuition.

Input : data/processed/fl_directory_2026.csv, data/processed/tuition_evidence.jsonl, data/processed/fl_tuition_2026.csv
Output: data/processed/fl_directory_tuition_2026.csv  (one row per directory school)
`tuition_status` explains every school without a tuition value:
  found                 coded annual tuition (see docs/tuition_codebook.md)
  unclear               pages read, no usable amount
  network_site_only     only a diocese/network site was found
  tuition_word_no_amount, not_reached, no_website, blocked   crawl outcomes for schools that were tried and not coded
  not_attempted_no_enrollment      directory shows zero enrollment
  not_attempted_no_own_domain      no email on its own domain, so no website guess
"""
import csv, json
FREE = {"gmail.com","yahoo.com","aol.com","hotmail.com","outlook.com","icloud.com","comcast.net","bellsouth.net","att.net","msn.com","live.com","me.com","sbcglobal.net","verizon.net","earthlink.net","mac.com","protonmail.com","cox.net","windstream.net","embarqmail.com","centurylink.net","charter.net","frontier.com","netzero.net","juno.com","ymail.com","gmx.com","mail.com","optonline.net","roadrunner.com","tampabay.rr.com","yahoo.co.uk","rocketmail.com"}
dirx = list(csv.DictReader(open("data/processed/fl_directory_2026.csv")))
crawl = {}
for f in ("data/processed/tuition_evidence.jsonl", "data/processed/tuition_evidence2.jsonl"):  # later file overrides
    try:
        for l in open(f):
            r = json.loads(l); crawl[r["school_code"]] = r["status"]
    except FileNotFoundError: pass
coded = {r["school_code"]: r for r in csv.DictReader(open("data/processed/fl_tuition_2026.csv"))}
cols = ["tuition_year","tuition_elem","tuition_mid","tuition_high","tuition_overall","tuition_is_range","source_url","source_date","source_type","tuition_note","confidence"]
out = []
for s in dirx:
    c = s["school_code"]; row = {k: s[k] for k in ("school_code","district","school_name","city","zip","religious","fes_eo","ftc","grade_levels","enroll_total","last_survey_year")}
    t = coded.get(c)
    if t: st = t["status"]
    elif c in crawl: st = crawl[c]
    elif int(s["enroll_total"]) == 0: st = "not_attempted_no_enrollment"
    else: st = "not_attempted_no_own_domain"
    row["tuition_status"] = st
    for k in cols: row[k] = t[k] if t else ""
    out.append(row)
with open("data/processed/fl_directory_tuition_2026.csv","w",newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
import collections
cnt = collections.Counter(r["tuition_status"] for r in out)
for k,v in cnt.most_common(): print(f"{v:5d}  {k}")
print(len(out), "schools")
