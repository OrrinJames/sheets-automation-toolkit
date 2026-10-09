"""Reading and writing tabular files (CSV and Excel)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

CSV_SUFFIXES = {".csv", ".txt"}
EXCEL_SUFFIXES = {".xlsx", ".xlsm", ".xls"}


class UnsupportedFileError(ValueError):
    """Raised when a file extension is not a supported spreadsheet format."""


def read_table(path: str | Path, sheet: str | int = 0) -> pd.DataFrame:
    """Load a CSV or Excel file into a DataFrame.

    All cells are read as strings so that cleaning rules (not pandas' guesses)
    decide how dates, currency and IDs with leading zeros are interpreted.

    Args:
        path: Path to a ``.csv`` or ``.xlsx`` file.
        sheet: Worksheet name or index for Excel files. Ignored for CSV.

    Returns:
        The loaded table.

    Raises:
        FileNotFoundError: If ``path`` does not exist.
        UnsupportedFileError: If the extension is not CSV or Excel.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    suffix = path.suffix.lower()
    if suffix in CSV_SUFFIXES:
        return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    if suffix in EXCEL_SUFFIXES:
        return pd.read_excel(path, sheet_name=sheet, dtype=str, keep_default_na=False)
    raise UnsupportedFileError(f"Unsupported file type: {path.suffix!r}")


def write_table(df: pd.DataFrame, path: str | Path, sheet_name: str = "Data") -> Path:
    """Write a DataFrame to CSV or Excel, chosen by the output file's extension.

    Args:
        df: Table to write.
        path: Destination path ending in ``.csv`` or ``.xlsx``.
        sheet_name: Worksheet name used for Excel output.

    Returns:
        The path written to.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower()
    if suffix in CSV_SUFFIXES:
        df.to_csv(path, index=False)
    elif suffix in EXCEL_SUFFIXES:
        df.to_excel(path, index=False, sheet_name=sheet_name)
    else:
        raise UnsupportedFileError(f"Unsupported file type: {path.suffix!r}")
    return path
