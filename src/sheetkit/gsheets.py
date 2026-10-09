"""Optional Google Sheets support via gspread and a service account.

Install with ``pip install "sheetkit[gsheets]"``. Credentials are read from the
path in the ``SHEETKIT_GOOGLE_CREDENTIALS`` environment variable (falling back to
``GOOGLE_APPLICATION_CREDENTIALS``). Never commit the JSON key file.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pandas as pd

if TYPE_CHECKING:  # pragma: no cover
    import gspread

CREDENTIALS_ENV_VARS = ("SHEETKIT_GOOGLE_CREDENTIALS", "GOOGLE_APPLICATION_CREDENTIALS")


class GoogleSheetsError(RuntimeError):
    """Raised for missing dependencies or credentials."""


def credentials_path() -> Path:
    """Return the service-account key path from the environment.

    Raises:
        GoogleSheetsError: If no variable is set or the file does not exist.
    """
    for var in CREDENTIALS_ENV_VARS:
        value = os.environ.get(var)
        if value:
            path = Path(value).expanduser()
            if not path.is_file():
                raise GoogleSheetsError(f"{var} points to a missing file: {path}")
            return path
    raise GoogleSheetsError(
        "Set SHEETKIT_GOOGLE_CREDENTIALS to the path of your service-account JSON key."
    )


def get_client() -> gspread.Client:
    """Create an authorised gspread client from the service-account key."""
    try:
        import gspread
    except ImportError as exc:  # pragma: no cover - depends on optional extra
        raise GoogleSheetsError(
            'Google Sheets support needs the extra: pip install "sheetkit[gsheets]"'
        ) from exc
    return gspread.service_account(filename=str(credentials_path()))


def read_sheet(
    spreadsheet: str, worksheet: str | int = 0, client: Any | None = None
) -> pd.DataFrame:
    """Read a worksheet into a DataFrame (all values as strings).

    Args:
        spreadsheet: Spreadsheet key, or a full ``docs.google.com`` URL.
        worksheet: Worksheet title or zero-based index.
        client: Optional pre-built gspread client (useful for testing).
    """
    client = client or get_client()
    book = _open(client, spreadsheet)
    ws = book.get_worksheet(worksheet) if isinstance(worksheet, int) else book.worksheet(worksheet)
    rows = ws.get_all_values()
    if not rows:
        return pd.DataFrame()
    header, *body = rows
    return pd.DataFrame(body, columns=header)


def write_sheet(
    df: pd.DataFrame,
    spreadsheet: str,
    worksheet: str,
    client: Any | None = None,
) -> None:
    """Replace a worksheet's contents with ``df``, creating the worksheet if needed."""
    client = client or get_client()
    book = _open(client, spreadsheet)
    try:
        ws = book.worksheet(worksheet)
        ws.clear()
    except Exception:  # gspread.WorksheetNotFound; kept generic so the extra stays optional
        ws = book.add_worksheet(title=worksheet, rows=len(df) + 1, cols=max(len(df.columns), 1))
    values = [[str(c) for c in df.columns]]
    values += [[_cell(v) for v in row] for row in df.itertuples(index=False)]
    ws.update(values, "A1")


def _cell(value: object) -> str:
    """Render one value as text for Sheets: blanks for missing, ISO for dates."""
    if value is None or (not isinstance(value, str) and pd.isna(value)):
        return ""
    if isinstance(value, pd.Timestamp):
        return value.date().isoformat() if value == value.normalize() else value.isoformat()
    return str(value)


def _open(client: Any, spreadsheet: str) -> Any:
    """Open a spreadsheet by URL or key."""
    if spreadsheet.startswith("http"):
        return client.open_by_url(spreadsheet)
    return client.open_by_key(spreadsheet)
