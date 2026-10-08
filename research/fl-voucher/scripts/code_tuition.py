"""Merge hand-coded tuition rows into data/processed/fl_tuition_2026.csv.

Coding files: data/processed/tuition_coding/*.txt, one school per line, fields separated by '|':
  school_code | tuition_year | elem | mid | high | overall | is_range(0/1) | confidence | status | note
status: found | no_tuition_listed | network_site_only | unclear
Amounts are USD per year, blank if absent. source_url is filled from the page the evidence was read from.
"""
import csv, glob, os, sys
sys.path.insert(0, "scripts")
import evidence_lib as E

OUT = "data/processed/fl_tuition_2026.csv"
COLS = ["school_code", "tuition_year", "tuition_elem", "tuition_mid", "tuition_high", "tuition_overall", "tuition_is_range",
        "source_url", "source_date", "source_type", "tuition_note", "confidence", "status"]
rows, seen, errs = [], set(), []
for f in sorted(glob.glob("data/processed/tuition_coding/*.txt")):
    for n, line in enumerate(open(f), 1):
        line = line.strip()
        if not line or line.startswith("#"): continue
        p = [x.strip() for x in line.split("|")]
        if len(p) != 10: errs.append(f"{f}:{n} expected 10 fields, got {len(p)}"); continue
        code, year, el, mi, hi, ov, rng, conf, st, note = p
        if code in seen: errs.append(f"{f}:{n} duplicate {code}"); continue
        seen.add(code)
        if st not in ("found", "no_tuition_listed", "network_site_only", "unclear"): errs.append(f"{f}:{n} bad status {st}")
        if conf not in ("high", "medium", "low", ""): errs.append(f"{f}:{n} bad confidence {conf}")
        amts = [a for a in (el, mi, hi, ov) if a]
        for a in amts:
            if not a.isdigit() or not (500 <= int(a) <= 100000): errs.append(f"{f}:{n} amount out of range {a}")
        if st == "found" and not amts: errs.append(f"{f}:{n} found without amount")
        if st != "found" and amts: errs.append(f"{f}:{n} amount with status {st}")
        _, url, _ = E.best_page(code)
        rows.append([code, year, el, mi, hi, ov, rng or "0", url, "2026-10-08", "live", note, conf, st])
if errs:
    print("\n".join(errs[:30])); sys.exit(1)
with open(OUT, "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(COLS); w.writerows(rows)
import collections
print(len(rows), "coded;", dict(collections.Counter(r[-1] for r in rows)))
