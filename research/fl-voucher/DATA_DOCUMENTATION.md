# Data Documentation

How each dataset in this project was built and where it came from.
Update this file **whenever a dataset is added or changed**. Never describe a source as collected until it is.

## Conventions
- Raw downloads and scrapes go in `data/raw/<source>/<YYYY-MM-DD>/` and are never edited.
- Every raw file gets one row in `data/raw/SOURCE_LOG.csv`
  (columns: `file, source_name, url, retrieved_on, script, notes`).
- Processed datasets in `data/processed/` list their input files and the script that built them below.
- School-year is the academic year start (2022 = 2022-23).

## Status legend
`planned` = not yet collected · `collected` = raw files exist · `built` = processed dataset exists

## 1. School universe (sampling frame)
| Item | Value |
|---|---|
| Status | collected (current snapshot only; historical years not yet obtained) |
| Source | FLDOE K-12 Private Schools > Directory of Private Schools, "Download School Contact List" (xlsx) |
| Retrieved | 2026-10-08, downloaded manually by the project owner (site blocks automated access); `data/raw/fldoe_directory/2026-10-08/PrivateSchools_All.xlsx`, git-ignored, logged in `data/raw/SOURCE_LOG.csv` |
| Contents | 3,540 schools, 39 columns: district, school name, FLDOE school code (unique), address, contact, scholarship participation flags (FES-EO, FTC, FES-UA, PEP), non-profit, religious, denomination, grade levels, accreditation, student type, last annual survey year, enrollment by grade (Pre-K to 12) |
| Unit | one row per school, one time point |
| Survey year | 2,714 schools last surveyed 2025, 826 last surveyed 2026 |
| Used for | master list of current schools; link key to PSS and to school websites |
| Known issues | (1) Cross-section: no past years, so closed schools and pre-policy status are missing. (2) FES-EO, FTC and FES-UA flags are identical for all 2,712 "Yes" schools, so they appear to describe current (post-2023) participation and cannot serve as pre-policy exposure. (3) 432 rows have zero enrollment and blank grade levels (some look like home-education or non-operating entries); 76 have no ZIP. (4) FLDOE states it does not verify the survey data. (5) Page URL for the directory still to be recorded. (6) Wayback Machine checked 2026-10-08: the directory page is archived often (609 captures, 2007-2026), but captures hold no school lists for 2018 onward. The 2019 `DownloadExcelFile.aspx` capture is only the download form (select district; fields include FTC and McKay participant, religious, denomination, total enrollment), because the file is produced by a form submission that archiving cannot replay. Only 2008 and 2012 captures of one district's search results (`Default.aspx?id=13&submit=GO`) were found. |

## 2. School covariates
| Item | Value |
|---|---|
| Status | collected (raw only; not yet cleaned) |
| Source | NCES Private School Universe Survey (PSS), public-use CSVs, biennial |
| URL | https://nces.ed.gov/surveys/pss/pssdata.asp (files under `/surveys/pss/zip/`) |
| Retrieved | 2026-10-08 via `scripts/download_pss.sh` (raw files in `data/raw/nces_pss/2026-10-08/`, git-ignored; listed in `data/raw/SOURCE_LOG.csv`) |
| Waves | 2017-18, 2019-20, 2021-22, 2023-24 |
| Florida schools (`PSTABB == FL`) | 1,850 / 1,724 / 1,937 / 2,003 |
| Useful variables | `NUMSTUDS` enrollment, `LEVEL` grade level, `RELIG` religion, `PCNTY` county, latitude/longitude, `PPIN` school ID |
| Tuition | No tuition variable found in the 2021-22 codebook text or layout. Other waves' codebooks not checked. |
| Linkage to frame | _matching rule (name + address / PSS ID) to fill in_ |
| Known issues | Biennial only; no wave between the pre-period years or for 2022-23. Variable names are coded (`P135` etc.); decode with the codebook before use. The 2023-24 layout file link on the PSS page returned 404. |

## 3. Scholarship participation
| Item | Value |
|---|---|
| Status | planned |
| Source | FLDOE / Step Up For Students participating-school lists |
| Used for | pre-policy scholarship dependence (exposure intensity); participation status |
| Known issues | _to fill in_ |

## 4. Tuition (outcome)
| Item | Value |
|---|---|
| Status | planned |
| Source | School websites, current pages and Wayback Machine snapshots for earlier years |
| Years | pre-period back to at least 2021-22; longer is better |
| Definition | published (sticker) tuition, annual, by grade band (elementary / middle / high). Fees and discounts recorded separately. |
| Missing data | kept as missing, not dropped, to avoid survival bias |
| Known issues | _snapshot date vs academic year mapping; to fill in_ |

## 5. Local exposure measures
| Item | Value |
|---|---|
| Status | planned |
| Source | _e.g. ACS income distribution by county/ZIP; to decide_ |
| Used for | share of households newly eligible after the 2023 expansion |

## Build log
_Add entries as: date · dataset · inputs · script · what changed._

## 6. State and district aggregates (private school annual reports)
| Item | Value |
|---|---|
| Status | built (district x year panel, 2018-19 to 2024-25) |
| Source | FLDOE Office of Independent Education and Parental Choice, "Florida's Private Schools Annual Report" PDFs, from K-12 Private Schools > Private School Annual Reports |
| Retrieved | 2026-10-08, downloaded manually by the project owner; `data/raw/fldoe_annual_report/2026-10-08/PS-AnnualReport{1819,1920,2021,2022,2023,2024,2025}.pdf` (git-ignored). File tag = school year end, e.g. 2025 is 2024-25; 1819 is 2018-19 |
| Contents | Enrollment by grade (PK-12) and district; number of private schools by district; for 2018-19 to 2022-23 also public school enrollment by district; state totals 2015-16 to 2024-25 |
| Processed | `data/processed/fl_private_district_panel.csv` (458 rows: district x year, built by `scripts/parse_annual_reports.py`); `data/processed/fl_private_state_totals.csv` (hand-transcribed from the 2024-25 report p.2) |
| Checks | For every year, summed district enrollment equals the report's state total by grade and in total; summed school counts equal the stated total except 2023-24 (see below); where the report gives public enrollment, its private column equals the district enrollment |
| Used for | district-level private enrollment (denominator for scholarship exposure) and, 2018-19 to 2022-23, private share of PK-12 enrollment |
| Known issues | (1) No school-level data. (2) Districts with no private schools are absent from a year's table (64 to 66 of 67 districts appear), not zero-filled. (3) 2023-24: district school counts sum to 3,013 but the report states 3,016; the district rows are kept as printed. (4) Public enrollment is blank for 2023-24 and 2024-25 because those reports have no such table. (5) School counts here count schools that submitted enrollment data, fewer than the 3,540 rows in the 2026 directory snapshot. (6) 2020-21 enrollment dips to 364,420, likely pandemic-related. (7) FLDOE does not verify survey data. |

## 7. Pre-policy scholarship exposure by district (FTC quarterly reports)
| Item | Value |
|---|---|
| Status | built, 2018-19 to 2022-23 (FTC only; FES-EO not yet obtained) |
| Source | FLDOE, "Florida Tax Credit Scholarship Program Quarterly Report" PDFs, from K-12 Scholarship Programs > Florida Tax Credit > Quarterly Reports. June 2019, 2020, 2021, 2022, 2023 reports (one per school year, payment periods through April or June) plus Sept 2022, Nov 2022, Feb 2023 (earlier cumulative reports of 2022-23) |
| Retrieved | 2026-10-08, downloaded manually by the project owner; `data/raw/fldoe_ftc_quarterly/2026-10-08/FTC-<Mon>-<Year>-Q-Report.pdf` (git-ignored) |
| Contents | By district: FTC students, total funded, private schools serving FTC students |
| State totals (June reports) | 2018-19: 104,091 students, 1,825 schools. 2019-20: 111,219, 1,870. 2020-21: 106,112, 1,945. 2021-22: 85,612, 1,990. 2022-23: 100,025, 2,083. |
| Processed | `data/processed/fl_ftc_district.csv` (536 rows: school year x report x district), built by `scripts/parse_ftc_quarterly.py` |
| Checks | Summed district students and school counts equal each report's printed totals. Summed district funding differs from the printed total by up to $10 in seven of eight reports (rounding in the source). |
| Used for | candidate pre-policy exposure at the district level: scholarship students per private-school student, using district enrollment in section 6 |
| Known issues | (1) District level only; no school-level data. (2) **FTC alone is not total exposure.** FTC students fall from 106,112 (2020-21) to 85,612 (2021-22) while private enrollment rises (section 6), which suggests students moved to other programs such as FES-EO. Exposure must add FES-EO before use; the reason for the drop is not yet verified. (3) The school-count table lists fewer than 67 districts in seven of the eight reports (61 to 66), so missing districts are not zero-filled. (4) Counts include only students who received funding. |

## 8. FES-EO participation, state aggregates (FES research reports)
| Item | Value |
|---|---|
| Status | collected; state aggregates only. Not usable for district exposure. |
| Source | FES Research Reports 2020-21, 2021-22, 2022-23 (Learning Systems Institute for FLDOE), from K-12 Scholarship Programs > Family Empowerment Scholarship |
| Retrieved | 2026-10-08, downloaded manually by the project owner; `data/raw/fldoe_fes/2026-10-08/FES-Report{2021,2022,2023}.pdf` (git-ignored) |
| Processed | `data/processed/fl_fes_state_aggregates.csv`, hand-transcribed from the report text |
| Contents | Participating schools with FES students in grades 3-10: 1,385 (2020-21), 1,682 (2021-22), 1,777 (2022-23). FES students in grades 3-10: 11,710, 36,348, 47,036. Students with valid test scores: 10,466, 32,693, 44,112. |
| Known issues | (1) Grades 3-10 only (the tested grades), so these are not total FES participants. (2) No district-level counts. (3) The 2022-23 report has an appendix listing about 208 schools with 30 or more students with gain scores (school name and city, no school code). This is a large-school subset, not a full participant list; not yet parsed or linked. (4) The sharp rise from 2020-21 to 2021-22 alongside the fall in FTC students (section 7) suggests students moved from FTC to FES-EO; not verified. |
