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
| Status | planned |
| Source | FLDOE Private School Directory (annual) |
| URL | _to fill in when retrieved_ |
| Years | target 2018-19 to 2024-25 |
| Unit | one row per school per year |
| Used for | master list of private schools; entry/exit tracking |
| Known issues | _to fill in_ |

## 2. School covariates
| Item | Value |
|---|---|
| Status | planned |
| Source | NCES Private School Universe Survey (PSS), biennial |
| Years | 2017-18, 2019-20, 2021-22, 2023-24 (availability to verify) |
| Used for | enrollment, grade range, religious affiliation. Whether PSS contains tuition is to be verified; assumed not. |
| Linkage to frame | _matching rule (name + address / PSS ID) to fill in_ |

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
