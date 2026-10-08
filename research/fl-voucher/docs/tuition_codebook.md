# Tuition variable: codebook (draft v0.1)

Goal: attach a published annual tuition to each school in the FLDOE Private School Directory
(`data/processed/fl_directory_2026.csv`, key `school_code`). Outcome of interest: whether schools raised tuition
after the 2023 scholarship expansion. Net tuition (what scholarship families actually pay) is out of scope for now.

## What counts as "published annual tuition"
The amount the school publishes on its own website (or a linked PDF) as the yearly price of full-time
attendance for one child at the standard rate.

Include: base tuition for the stated academic year.
Exclude: registration/application fees, deposits, books, uniforms, technology and activity fees, lunch,
before/after care, sibling or staff discounts, financial aid, scholarship-specific rates, part-time or
half-day rates, summer programs.

Rules for common cases
- Quoted per month: multiply by the number of payments the school states (10 or 12). If the number is not
  stated, leave `tuition_annual` missing and keep the raw monthly figure.
- Quoted per semester or quarter: multiply by the number of terms.
- Several payment plans: use the pay-in-full annual amount if it is listed, otherwise the plan with the
  most payments multiplied out. Record which one in `tuition_note`.
- Quoted as a range or "starting at": record the lower figure and set `tuition_is_range = 1`.
- Different rates by grade: fill the grade-band variables below.
- Different rates for members vs non-members (for example church members): use the non-member rate, note it.
- Pre-K and nursery are out of scope. K-12 only.
- If the school lists one tuition for all grades, copy it into every band the school serves.

## Variables (one row per school and academic year)
| Variable | Meaning |
|---|---|
| `school_code` | FLDOE school code (key) |
| `tuition_year` | Academic year the amount applies to, e.g. 2025-26. Never guess; leave missing if the page does not say |
| `tuition_elem` | Annual tuition, grades K-5 (USD) |
| `tuition_mid` | Annual tuition, grades 6-8 |
| `tuition_high` | Annual tuition, grades 9-12 |
| `tuition_overall` | Single representative annual tuition if no grade breakdown is given |
| `tuition_is_range` | 1 if the figure is a "from" or range value |
| `source_url` | Page or PDF the amount was read from |
| `source_date` | Date the page was retrieved (or the Wayback snapshot date) |
| `source_type` | `live` or `wayback` |
| `tuition_note` | Free text: payment plan used, discounts seen, anything odd |
| `confidence` | `high` (clear annual figure, year stated), `medium` (derived, e.g. monthly x 10), `low` (ambiguous) |
| `status` | `found`, `no_website`, `no_tuition_listed` (for example "call for tuition"), `blocked`, `not_reached` |

Missing is kept as missing. A school with `no_tuition_listed` or `not_reached` is not the same as a school
with no tuition.

## Design choices to confirm
1. Current year first (the directory is a current snapshot): tuition for 2025-26 or 2026-27, whichever the
   websites show. Earlier years come later from Wayback snapshots of the same pages.
2. Whether to use all schools or priority schools first (see plan).
3. Grade bands: elementary / middle / high, as above.
