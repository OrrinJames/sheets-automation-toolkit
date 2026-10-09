# sheets-automation-toolkit

[![CI](https://github.com/OrrinJames/sheets-automation-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/OrrinJames/sheets-automation-toolkit/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Python toolkit for cleaning, merging and reporting on Excel and Google Sheets data.

`sheetkit` is a small, tested library and command-line tool for the spreadsheet chores
that eat up an afternoon: tidying exported data, combining monthly files, removing
duplicates, and turning the result into a clean Excel summary someone can actually read.

## Features

- **`clean`** – trims whitespace, collapses double spaces, normalises headers to
  `snake_case` (`" Amount (NZD) "` → `amount_nzd`), drops fully blank rows, parses dates
  (NZ day-first by default, ISO dates always safe) and NZD currency values
  (`$1,250.00`, `NZ$89.90`, `NZD 410`, accounting negatives like `($20.00)`).
- **`dedupe`** – removes duplicate rows on one or more key columns, ignoring case and
  stray whitespace by default; keep the first or last occurrence.
- **`merge`** – stacks any mix of CSV and `.xlsx` files, lining columns up by normalised
  name and tagging each row with its source file.
- **`report`** – builds a formatted Excel workbook: pivot summary with totals, styled and
  frozen header row, NZD number format, bold total row, auto-fitted column widths, plus
  the underlying data on a second sheet.
- **Google Sheets** (optional extra) – read a worksheet into pandas or write a DataFrame
  back, authenticated with a service account.
- Typed, documented functions you can import directly into your own scripts.

## Install

Requires Python 3.11+.

```bash
git clone https://github.com/OrrinJames/sheets-automation-toolkit.git
cd sheets-automation-toolkit
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .                 # core: pandas, openpyxl, typer
pip install -e ".[gsheets]"      # + Google Sheets support
pip install -e ".[dev]"          # + pytest and ruff
```

## Usage

The `sample_data/` folder has two fictional monthly sales exports with typical mess
(inconsistent headers, `$` amounts, a negative in brackets, and one order present in both
files). The commands below run against it.

```bash
# 1. Combine the monthly files into one
sheetkit merge sample_data/sales_2026_03.csv sample_data/sales_2026_04.csv -o out/merged.csv

# 2. Remove the order that appears in both months
sheetkit dedupe out/merged.csv -o out/unique.csv --key order_id

# 3. Tidy text, parse dates (DD/MM/YYYY) and NZD amounts
sheetkit clean out/unique.csv -o out/clean.xlsx --date order_date --currency amount_nzd

# 4. Excel summary: revenue by region, with totals
sheetkit report out/unique.csv -o out/report.xlsx \
    --index region --values amount_nzd --currency amount_nzd --title "Sales by region"
```

Add `--columns product` to `report` for a two-way pivot, or `--agg count|mean|min|max`
to change the aggregation. Run `sheetkit --help` or `sheetkit <command> --help` for all
options. Column names can be given as they appear in the file or in `snake_case`.

### As a library

```python
from sheetkit import clean_frame, dedupe_frame, merge_files, write_report

df = merge_files(["sales_2026_03.csv", "sales_2026_04.csv"])
df, removed = dedupe_frame(df, keys=["order_id"])
df = clean_frame(df, date_columns=["order_date"], currency_columns=["amount_nzd"])
write_report(df, "report.xlsx", index="region", values="amount_nzd", columns="product")
```

## Google Sheets setup

1. In [Google Cloud Console](https://console.cloud.google.com/), create a project and
   enable the **Google Sheets API** (and **Google Drive API** if you open sheets by URL).
2. Create a **service account**, then add a JSON key and download it.
3. Share the spreadsheet with the service account's email (`...@...iam.gserviceaccount.com`)
   as Viewer (read) or Editor (write).
4. Point sheetkit at the key with an environment variable. Keep the file outside the repo;
   `.gitignore` also excludes common key file names as a safety net.

```bash
pip install -e ".[gsheets]"
export SHEETKIT_GOOGLE_CREDENTIALS="$HOME/.config/sheetkit/service-account.json"
```

```python
from sheetkit import clean_frame
from sheetkit.gsheets import read_sheet, write_sheet

raw = read_sheet("https://docs.google.com/spreadsheets/d/<id>/edit", worksheet="Orders")
tidy = clean_frame(raw, date_columns=["Order Date"], currency_columns=["Total"])
write_sheet(tidy, "<spreadsheet-id>", worksheet="Orders (clean)")
```

`GOOGLE_APPLICATION_CREDENTIALS` is used as a fallback if `SHEETKIT_GOOGLE_CREDENTIALS`
is not set.

## Development

```bash
pip install -e ".[dev,gsheets]"
ruff check . && ruff format --check .
pytest
```

CI runs ruff and pytest on Python 3.11 and 3.12 for every push and pull request.

## Project layout

```
src/sheetkit/
  cli.py       Typer CLI (clean, merge, dedupe, report)
  clean.py     header, whitespace, date and NZD currency cleaning
  dedupe.py    key-based duplicate removal
  merge.py     multi-file merge with column alignment
  report.py    pivot summary + openpyxl formatting
  gsheets.py   optional Google Sheets read/write
  io.py        CSV / Excel read and write
tests/         pytest suite with small fixture CSVs
sample_data/   fictional example inputs
```

## License

[MIT](LICENSE) © 2026 Tyrel Orrin
