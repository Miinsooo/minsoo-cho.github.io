#!/usr/bin/env bash
# Download NCES PSS public-use CSVs and documentation into data/raw/nces_pss/<date>/
# Source page: https://nces.ed.gov/surveys/pss/pssdata.asp
set -euo pipefail
cd "$(dirname "$0")/../data/raw"
D=nces_pss/$(date +%F)
mkdir -p "$D"
cd "$D"
for f in pss2324_pu_csv pss2122_pu_csv pss1920_pu_csv pss1718_pu_csv layout2021-22 layout2019-20 codebook2021_22; do
  curl -sSLf -o "$f.zip" "https://nces.ed.gov/surveys/pss/zip/$f.zip"
done
for z in pss2324_pu_csv pss2122_pu_csv pss1920_pu_csv pss1718_pu_csv; do
  mkdir -p "x_$z" && unzip -q -o "$z.zip" -d "x_$z"
done
