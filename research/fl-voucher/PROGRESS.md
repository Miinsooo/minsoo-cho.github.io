# Progress overview (2026-10-11)

Goal: effect of Florida's 2023 universal scholarship expansion (HB 1) on private K-12 tuition. Florida first; current-year tuition first; past years after the FLDOE roster arrives.

## 1. Datasets in hand
| Dataset | Unit | Period | Status |
|---|---|---|---|
| FLDOE private school directory | 3,540 schools | current snapshot | collected |
| NCES PSS | schools | 2017-18, 2019-20, 2021-22, 2023-24 | collected (no tuition variable) |
| FLDOE annual reports | district x year | 2018-19 to 2024-25 | collected |
| FTC quarterly reports | district x year | 2018-19 to 2022-23 | collected |
| FES research reports | state totals | 2020-21 to 2022-23 | collected |
| School-level tuition (own collection) | school | current year (mostly 2026-27) | in progress: 541 found |
| Earlier rosters and scholarship participation | school x year | 2017-18 on | public records request sent, awaiting reply |

## 2. Current-year tuition collection: steps and yield
| Step | Method | Result |
|---|---|---|
| 1 | crawl sites from school email domains (2,050) | 426 found after hand coding |
| 2 | name-based website guess (1,401 tried) | 187 sites, 39 more found |
| 3 | re-read `unclear` schools | +23 found |
| 4 | follow tuition links and PDFs from saved pages | +45 found |
| 5 | deeper recrawl of `not_reached` (639) | +5 found |
| 6 | web search for 20 large schools without a site | 1 found (not scaled up) |
| 7 | diocesan sites | no tuition published; not used |
| 8 | second name guess (parish/church patterns) | 29 sites, 7 found |

## 3. Coverage now (schools with enrollment: 3,108)
found 541 (17.4%; about 31% of students) | unclear 344 | word but no amount ~350 | site opened, no tuition page ~600 | no website ~900 not searched successfully.

## 4. Where everything is
- `DATA_DOCUMENTATION.md`: provenance log (sections 1-10, 9a-9f for tuition steps)
- `data/processed/fl_directory_tuition_2026.csv`: one row per school with status and tuition values
- `data/processed/tuition_source_log.csv`: how each website and value was found
- `docs/tuition_codebook.md`: variable definitions and coding rules
- `scripts/`: parsers, crawlers, coding and logging tools

## 5. Open items
- FLDOE public records reply (directory files 2017-18 to 2024-25).
- Next option for current year: headless-browser rendering for about 970 JavaScript/image pages (test 20-30 first).
- Comparison group and identification (out-of-state data) still to decide; advisor update drafted.
- Past-year tuition (Wayback) deferred; probe showed about 25% of tuition pages have a 2021-22 copy.
