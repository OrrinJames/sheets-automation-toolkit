"""sheetkit: clean, merge, dedupe and report on Excel / CSV / Google Sheets data."""

from sheetkit.clean import clean_frame, normalise_header, parse_currency
from sheetkit.dedupe import dedupe_frame
from sheetkit.io import read_table, write_table
from sheetkit.merge import merge_files
from sheetkit.report import build_summary, write_report

__all__ = [
    "build_summary",
    "clean_frame",
    "dedupe_frame",
    "merge_files",
    "normalise_header",
    "parse_currency",
    "read_table",
    "write_report",
    "write_table",
]

__version__ = "0.1.0"
