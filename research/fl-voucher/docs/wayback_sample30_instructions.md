> UPDATE 2026-10-12: the first 30-school sample (`wayback_sample30.xlsx`) was drawn at random without knowing which pages Wayback had saved, so many links say "No URL has been captured". Use `data/processed/wayback_sample_checked.xlsx` instead (15 schools, one per website). For these, an earlier check of the Wayback index (2026-10-11) showed saved copies of the same page in at least 3 of the years 2021-2026, including 2021, 2022 or 2023; the column `years_with_saved_copy_of_this_page` lists them. Instructions below apply to both files.

# Wayback sample (30 schools): how to fill in past-year tuition by hand

File: `data/processed/wayback_sample30.xlsx` (same content as `wayback_sample30.csv`).
Sample: 30 of the schools with a tuition page found for 2025-26 or 2026-27 (HTML page, not PDF), stratified by enrollment (10 with <100, 10 with 100-299, 10 with 300+ students; random seed 12).

For each school and each year 2021-2026:
1. Click the year link (columns `2021` ... `2026`). It opens the Wayback copy closest to 1 September of that year. The address bar shows the copy's date (14 digits, yyyymmddhhmmss).
2. If the page shows tuition, fill the yellow columns of that year:
   - `YYYY_page_year_printed`: the school year printed on the page (e.g. 2022-23). If no year is printed, leave empty and say so in `notes`.
   - `YYYY_elem` / `_mid` / `_high`: annual sticker tuition by grade band when the page gives bands (elementary K-5, middle 6-8, high 9-12); otherwise
   - `YYYY_overall`: one representative annual amount.
   - `YYYY_snapshot_date`: the copy's date from the address bar.
3. Annual amounts only (monthly x number of payments is fine, note it). Exclude fees, deposits, preschool/VPK, after-care, international rates, sibling or parish discounts.
4. If the copy shows no tuition or the page is missing, write `NA` in `YYYY_overall`. If the copy shows the wrong school year (for example next year's rates posted in spring), record the year printed on the page, not the year of the link.
5. If the page link says "The Wayback Machine has not archived that URL": that only means the exact current address was never saved (the page may have had another address earlier). Do not mark NA yet. Open the `YYYY home` link (the school's front page saved around that date) and follow its Admissions / Tuition menu; or open the `all` link, which lists every saved address of the school's site, and pick the tuition-like one. Mark `NA` only if the front page has no saved copy for that year or no tuition page can be reached from it.
6. If the tuition page moved, try the school's other pages from that copy (Admissions, Tuition & Fees) and note the address in `notes`.

When done, send the file back; the values will be merged into a school-by-year file (`fl_tuition_panel_sample.csv`) with the source address and snapshot date for each value.
