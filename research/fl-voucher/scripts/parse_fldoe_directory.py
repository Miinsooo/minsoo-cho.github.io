"""Parse the FLDOE Private School Directory xlsx into a school-level CSV.

Input : data/raw/fldoe_directory/<date>/PrivateSchools_All.xlsx (openpyxl cannot read this file's styles, so the
        sheet XML is read directly)
Output: data/processed/fl_directory_2026.csv
Contact names and personal email addresses are NOT written out; only the email domain is kept, as a hint for
finding the school's website.
"""
import csv, glob, html, re, zipfile

SRC = sorted(glob.glob("data/raw/fldoe_directory/*/PrivateSchools_All.xlsx"))[-1]
z = zipfile.ZipFile(SRC)
sheet = z.read("xl/worksheets/sheet1.xml").decode("utf8", "ignore")
rows = []
for r in re.findall(r"<x:row[^>]*>(.*?)</x:row>", sheet, re.S):
    vals = []
    for c in re.findall(r"<x:c[^>]*?(?:/>|>.*?</x:c>)", r, re.S):
        m = re.search(r"<x:v>(.*?)</x:v>", c, re.S)
        vals.append(html.unescape(m.group(1)) if m else "")
    rows.append(vals)
hdr, data = rows[0], rows[1:]
ix = {h: i for i, h in enumerate(hdr)}
get = lambda r, k: r[ix[k]].strip() if ix[k] < len(r) else ""
GRADES = ["Pre-K", "Kindergarten"] + [f"Grade {i}" for i in range(1, 13)]
domain = lambda e: e.split("@")[-1].lower() if "@" in e else ""

out = []
for r in data:
    enr = sum(int(get(r, g) or 0) for g in GRADES)
    out.append({
        "school_code": get(r, "School Code"), "district": get(r, "District"), "school_name": get(r, "School Name"),
        "address1": get(r, "Address 1"), "city": get(r, "City"), "zip": get(r, "Zip"),
        "fes_eo": get(r, "FES Educational Options Participant"), "ftc": get(r, "FTC Participant"),
        "fes_ua": get(r, "FES Unique Abilities Participant"), "pep": get(r, "PEP Participant"),
        "non_profit": get(r, "Non-Profit"), "religious": get(r, "Religious"), "denomination": get(r, "Denomination"),
        "grade_levels": get(r, "Grade Levels"), "accreditation": get(r, "Accreditation"),
        "last_survey_year": get(r, "Last Annual Survey Year"), "enroll_total": enr,
        "email_domain": domain(get(r, "Director Email")) or domain(get(r, "Contact Email")),
    })
with open("data/processed/fl_directory_2026.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
print(len(out), "schools;", sum(1 for o in out if o["enroll_total"] > 0), "with enrollment;",
      sum(1 for o in out if o["email_domain"]), "with email domain")
