"""Print tuition evidence for a batch of schools, for reading and coding.

Usage: python3 -I scripts/show_evidence.py START COUNT [--status tuition_evidence] [--chars 700]
Only schools without a coded row in data/processed/fl_tuition_2026.csv are shown.
"""
import csv, json, os, sys

start, count = int(sys.argv[1]), int(sys.argv[2])
status = "tuition_evidence"; chars = 700
if "--status" in sys.argv: status = sys.argv[sys.argv.index("--status") + 1]
if "--chars" in sys.argv: chars = int(sys.argv[sys.argv.index("--chars") + 1])
coded = set()
if os.path.exists("data/processed/fl_tuition_2026.csv"):
    coded = {r["school_code"] for r in csv.DictReader(open("data/processed/fl_tuition_2026.csv"))}
rows = [json.loads(l) for l in open("data/processed/tuition_evidence.jsonl")]
rows = sorted([r for r in rows if r["status"] == status and r["school_code"] not in coded], key=lambda r: int(r["school_code"]))
print(f"[{status}] uncoded {len(rows)}; showing {start}..{start+count-1}")
for r in rows[start:start + count]:
    print(f"\n### {r['school_code']} | {r['school_name']} | years {','.join(r['years']) or '-'} | no_price_hint={r['no_price_hint']}")
    for w in r["windows"][:2]:
        print(f"- {w['url']}\n  {w['text'][:chars]}")
