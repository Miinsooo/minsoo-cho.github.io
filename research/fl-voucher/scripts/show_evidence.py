"""Print compact tuition evidence (dollar lines near tuition cues) for uncoded schools.

Usage: python3 -I scripts/show_evidence.py START COUNT [--status tuition_evidence]
Schools already present in data/processed/fl_tuition_2026.csv are skipped.
"""
import csv, json, os, sys
sys.path.insert(0, "scripts")
import evidence_lib as E

start, count = int(sys.argv[1]), int(sys.argv[2])
status = sys.argv[sys.argv.index("--status") + 1] if "--status" in sys.argv else "tuition_evidence"
coded = set()
if os.path.exists("data/processed/fl_tuition_2026.csv"):
    coded = {r["school_code"] for r in csv.DictReader(open("data/processed/fl_tuition_2026.csv"))}
rows = [json.loads(l) for l in open(E.EVID)]
if "--codes" in sys.argv:
    want = set(sys.argv[sys.argv.index("--codes") + 1].split(","))
    rows = sorted([r for r in rows if r["school_code"] in want], key=lambda r: int(r["school_code"]))
else:
    rows = sorted([r for r in rows if r["status"] == status and r["school_code"] not in coded], key=lambda r: int(r["school_code"]))
print(f"[{status}] uncoded {len(rows)}; showing {start}..{start+count-1}")
for r in rows[start:start + count]:
    sc, url, body = E.best_page(r["school_code"])
    ln = E.dollar_lines(body) if body else []
    print(f"\n## {r['school_code']} {r['school_name'][:40]} | {','.join(E.years_in(body)) or '-'} | {url.split('//')[-1][:60]}")
    for l in ln: print("  " + l)
