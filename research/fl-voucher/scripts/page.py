"""Show the part of a school's best saved page around its tuition amounts, with surrounding labels.

Usage: python3 -I scripts/page.py CODE [BEFORE=4] [AFTER=30]
"""
import re, sys
sys.path.insert(0, "scripts")
import evidence_lib as E

code = sys.argv[1]
before = int(sys.argv[2]) if len(sys.argv) > 2 else 4
after = int(sys.argv[3]) if len(sys.argv) > 3 else 30
sc, url, body = E.best_page(code)
lines = [re.sub(r"\s+", " ", l).strip() for l in body.split("\n")]
lines = [l for l in lines if l]
first = next((i for i, l in enumerate(lines) if E.AMT.search(l) and re.search("tuition", " ".join(lines[max(0, i-2):i+2]), re.I)), None)
print(f"{code} {url}")
if first is None: print("(no tuition + amount region)")
else:
    for l in lines[max(0, first - before): first + after]: print("  " + l[:200])
