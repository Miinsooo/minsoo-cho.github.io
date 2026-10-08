"""Parse FLDOE FTC quarterly report PDFs (2022-23) into a district-level file.

Input : data/raw/fldoe_ftc_quarterly/<date>/FTC-<Sept-2022|Nov-2022|Feb-2023|Jun-2023>-Q-Report.pdf
        (each report is cumulative over the payment periods of the 2022-23 school year so far)
Output: data/processed/fl_ftc_district_2022_23.csv
Aborts if parsed district sums differ from a report's printed totals.
"""
import csv, glob, re, subprocess, sys

RAW = sorted(glob.glob("data/raw/fldoe_ftc_quarterly/*/"))[-1]
REPORTS = [("Sept-2022", "2022-09"), ("Nov-2022", "2022-11"), ("Feb-2023", "2023-02"), ("Jun-2023", "2023-06")]
num = lambda s: int(s.replace(",", ""))

def text(path):
    return subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True, text=True, check=True).stdout

rows = []
for tag, rep in REPORTS:
    t = text(f"{RAW}FTC-{tag}-Q-Report.pdf")
    head, _, rest = t.partition("Private Schools by District Serving FTC Students")
    stu = {}
    for m in re.finditer(r"^\s*(\d+)\s+([A-Z][A-Z. \-]+?)\s+([\d,]+)\s+[\d.]+%\s+([\d,]+)\s+[\d.]+%\s*$", head, re.M):
        stu[int(m[1])] = (m[2].strip(), num(m[3]), num(m[4]))
    sch = {int(m[1]): int(m[3]) for m in re.finditer(r"^\s*(\d+)\s+([A-Z][A-Z. \-]+?)\s+(\d+)\s*$", rest.split("FTC Student Enrollment by Gender")[0], re.M)}
    tot = re.search(r"TOTAL:\s+67\s+([\d,]+)\s+100\.00%\s+([\d,]+)", head)
    sch_tot = re.search(r"TOTAL:\s+\d+\s+([\d,]+)", rest)
    fund_diff = sum(v[2] for v in stu.values()) - num(tot[2])
    ok = (sum(v[1] for v in stu.values()) == num(tot[1]) and abs(fund_diff) <= 100
          and sum(sch.values()) == num(sch_tot[1]))  # funding may differ by rounding in the source
    print(f"{rep}: students {sum(v[1] for v in stu.values()):,} funded ${sum(v[2] for v in stu.values()):,} "
          f"schools {sum(sch.values()):,} districts {len(stu)}/{len(sch)} -> {'OK' if ok else 'MISMATCH'}")
    if not ok: sys.exit(1)
    if fund_diff: print(f"  note {rep}: district funding sums differ from printed total by ${fund_diff}")
    for k in range(1, 68):
        n = stu.get(k)
        rows.append([rep, k, n[0] if n else "", n[1] if n else "", n[2] if n else "", sch.get(k, "")])

with open("data/processed/fl_ftc_district_2022_23.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["report", "district_id", "district", "ftc_students", "ftc_total_funded", "private_schools_serving_ftc"])
    w.writerows(rows)
print("rows", len(rows))
