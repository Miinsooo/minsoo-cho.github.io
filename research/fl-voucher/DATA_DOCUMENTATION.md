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
| Known issues | (1) Cross-section: no past years, so closed schools and pre-policy status are missing. (2) FES-EO, FTC and FES-UA flags are identical for all 2,712 "Yes" schools, so they appear to describe current (post-2023) participation and cannot serve as pre-policy exposure. (3) 432 rows have zero enrollment and blank grade levels (some look like home-education or non-operating entries); 76 have no ZIP. (4) FLDOE states it does not verify the survey data. (5) Page URL for the directory still to be recorded. |

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
