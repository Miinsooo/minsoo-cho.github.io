"""Parse FLDOE FTC quarterly report PDFs (2018-19 to 2022-23) into a district-level file.

Input : data/raw/fldoe_ftc_quarterly/<date>/FTC-<Mon>-<Year>-Q-Report.pdf
        June reports cover the whole school year (payment periods through April/June);
        Sept 2022, Nov 2022, Feb 2023 are earlier cumulative reports of 2022-23.
Output: data/processed/fl_ftc_district.csv
Aborts if parsed district sums differ from a report's printed totals.
"""
import csv, glob, re, subprocess, sys

RAW = sorted(glob.glob("data/raw/fldoe_ftc_quarterly/*/"))[-1]
REPORTS = [("Jun-2019", "2019-06", "2018-19"), ("Jun-2020", "2020-06", "2019-20"), ("Jun-2021", "2021-06", "2020-21"),
           ("Jun-2022", "2022-06", "2021-22"), ("Sept-2022", "2022-09", "2022-23"), ("Nov-2022", "2022-11", "2022-23"),
           ("Feb-2023", "2023-02", "2022-23"), ("Jun-2023", "2023-06", "2022-23")]
num = lambda s: int(s.replace(",", ""))

def text(path):
    return subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True, text=True, check=True).stdout

rows = []
for tag, rep, sy in REPORTS:
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
    print(f"{sy} {rep}: students {sum(v[1] for v in stu.values()):,} funded ${sum(v[2] for v in stu.values()):,} "
          f"schools {sum(sch.values()):,} districts {len(stu)}/{len(sch)} -> {'OK' if ok else 'MISMATCH'}")
    if not ok: sys.exit(1)
    if fund_diff: print(f"  note {rep}: district funding sums differ from printed total by ${fund_diff}")
    for k in range(1, 68):
        n = stu.get(k)
        rows.append([sy, rep, k, n[0] if n else "", n[1] if n else "", n[2] if n else "", sch.get(k, "")])

with open("data/processed/fl_ftc_district.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["school_year", "report", "district_id", "district", "ftc_students", "ftc_total_funded", "private_schools_serving_ftc"])
    w.writerows(rows)
print("rows", len(rows))
