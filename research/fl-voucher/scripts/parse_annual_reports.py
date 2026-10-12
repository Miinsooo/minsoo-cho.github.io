"""Parse FLDOE Private School Annual Report PDFs into a district x year panel.

Input : data/raw/fldoe_annual_report/<date>/PS-AnnualReport<tag>.pdf
        tag 1819 = 2018-19, 1920 = 2019-20, 2021 = 2020-21, ..., 2025 = 2024-25
Output: data/processed/fl_private_district_panel.csv
Needs pdftotext (poppler). Aborts if parsed district sums differ from a report's state totals.
"""
import csv, re, subprocess, sys, glob

RAW = sorted(glob.glob("data/raw/fldoe_annual_report/*/"))[-1]
GRADES = ["pk", "k"] + [f"g{i}" for i in range(1, 13)]
ALIAS = {"MIAMI-DADE": "DADE"}
YEARS = {"1819": "2018-19", "1920": "2019-20", "2021": "2020-21", "2022": "2021-22",
         "2023": "2022-23", "2024": "2023-24", "2025": "2024-25"}

def text(path):
    return subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True, text=True, check=True).stdout

def num(s): return int(s.replace(",", ""))
def name(s): s = s.strip(); return ALIAS.get(s, s)

def section(t, heading, stop_re):
    a = re.search(heading, t, re.I).end()
    lines = t[a:].splitlines()
    out = []
    for line in lines:
        out.append(line)
        if re.match(stop_re, line.strip(), re.I): break
    return out

def enrollment(t):
    rows = {}
    for line in section(t, r"STUDENT ENROLLMENT BY GRADE LEVEL", r"TOTAL:"):
        m = re.match(r"^\s*([A-Z][A-Z. \-]+?)\s{1,}((?:[\d,]+\s+){14}[\d,]+)\s*$", line)
        if m: rows[name(m[1])] = [num(x) for x in m[2].split()]
    return rows

def schools(t):
    rows = {}
    for line in section(t, r"Number of Private Schools by District", r"TOTAL:?\s+\d+"):
        m = re.match(r"^\s*(\d+)\s+([A-Z][A-Z. \-]+?)\s+(\d+)\s*$", line)
        if m: rows[name(m[2])] = (int(m[1]), int(m[3]))
    return rows

def public(t):
    rows = {}
    hits = [m.end() for m in re.finditer(r"PUBLIC\s+PRIVATE\s+TOTAL", t)]
    if not hits: return rows  # some reports (2023-24, 2024-25) have no public/private table
    a = hits[-1]
    for line in t[a:].splitlines():
        m = re.match(r"^\s*([A-Z][A-Z. \-]+?)\s+([\d,]+)\s+[\d.]+%\s+([\d,]+)\s+[\d.]+%\s+([\d,]+)\s*$", line)
        if m: rows[name(m[1])] = (num(m[2]), num(m[3]))
        if line.strip().startswith("TOTAL:"): break
    return rows

out = []
for tag, sy in YEARS.items():
    t = text(f"{RAW}PS-AnnualReport{tag}.pdf")
    en, sc, pu = enrollment(t), schools(t), public(t)
    state = [num(x) for x in re.search(r"TOTAL:\s+((?:[\d,]+\s+){14}[\d,]+)", t)[1].split()]
    parsed = [sum(v[i] for v in en.values()) for i in range(15)]
    ok = parsed == state
    sc_state = int(re.search(r"TOTAL:?\s+\d+\s+([\d,]+)", t[re.search(r"Number of Private Schools by District", t, re.I).start():])[1].replace(",", ""))
    ok_sc = sum(v[1] for v in sc.values()) == sc_state
    pub_priv_ok = all(pu[d][1] == en[d][-1] for d in pu if d in en)
    print(f"{sy}: districts {len(en)} enrollment {parsed[-1]:,} {'OK' if ok else 'MISMATCH'} | "
          f"schools {sum(v[1] for v in sc.values()):,}/{sc_state:,} {'OK' if ok_sc else 'MISMATCH'} | "
          f"public rows {len(pu)}, private==enrollment {'OK' if pub_priv_ok else 'MISMATCH'}")
    if not (ok and pub_priv_ok): sys.exit(1)
    if not ok_sc:  # source inconsistency: district rows do not add to the report's own total
        print(f"  WARNING {sy}: district school counts sum to {sum(v[1] for v in sc.values())}, report states {sc_state}")
    for d, v in en.items():
        did, ns = sc.get(d, ("", ""))
        out.append([sy, did, d, *v, ns, pu.get(d, ("",))[0]])

with open("data/processed/fl_private_district_panel.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["school_year", "district_id", "district"] + [f"enr_{g}" for g in GRADES] + ["enr_total", "schools", "public_enr"])
    w.writerows(out)
print("rows", len(out))
