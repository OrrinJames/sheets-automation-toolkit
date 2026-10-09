"""Cleaning rules: whitespace, headers, dates and NZD currency values."""

from __future__ import annotations

import re
from collections.abc import Iterable
from decimal import Decimal, InvalidOperation

import pandas as pd

_NON_ALNUM = re.compile(r"[^0-9a-z]+")
_CURRENCY_STRIP = re.compile(r"(?i)\s|nzd|nz\$|\$|,")


def normalise_header(name: object) -> str:
    """Convert a column header to ``snake_case``.

    Examples:
        >>> normalise_header("  Order Date ")
        'order_date'
        >>> normalise_header("Amount (NZD)")
        'amount_nzd'
    """
    text = str(name).strip().lower()
    text = _NON_ALNUM.sub("_", text).strip("_")
    return text or "column"


def _dedupe_headers(headers: Iterable[str]) -> list[str]:
    """Suffix repeated header names with ``_2``, ``_3`` ... so every column is unique."""
    seen: dict[str, int] = {}
    result: list[str] = []
    for header in headers:
        count = seen.get(header, 0) + 1
        seen[header] = count
        result.append(header if count == 1 else f"{header}_{count}")
    return result


def parse_currency(value: object) -> float | None:
    """Parse an NZD-style money string into a float.

    Handles ``$``, ``NZ$``, ``NZD``, thousands separators, and negatives written
    as ``-$5`` or in accounting brackets ``($5.00)``. Blank values return ``None``.

    Raises:
        ValueError: If the value is not blank and cannot be read as money.

    Examples:
        >>> parse_currency("NZ$1,234.50")
        1234.5
        >>> parse_currency("($20.00)")
        -20.0
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    if not text:
        return None
    negative = text.startswith("(") and text.endswith(")")
    if negative:
        text = text[1:-1]
    text = _CURRENCY_STRIP.sub("", text)
    if text.startswith("-"):
        negative = not negative
        text = text[1:]
    try:
        amount = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"Not a currency value: {value!r}") from exc
    return float(-amount if negative else amount)


def parse_dates(series: pd.Series, dayfirst: bool = True) -> pd.Series:
    """Parse a column of date strings into ``datetime64`` values.

    NZ convention is day-first (``03/04/2026`` is 3 April). ISO strings such as
    ``2026-04-03`` parse correctly either way. Unparseable values become ``NaT``.
    """
    cleaned = series.astype("string").str.strip().replace("", pd.NA)
    iso_mask = cleaned.str.match(r"^\d{4}-\d{2}-\d{2}", na=False)
    result = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")
    if iso_mask.any():
        result[iso_mask] = pd.to_datetime(cleaned[iso_mask], errors="coerce", format="ISO8601")
    other = ~iso_mask & cleaned.notna()
    if other.any():
        result[other] = pd.to_datetime(
            cleaned[other], errors="coerce", dayfirst=dayfirst, format="mixed"
        )
    return result


def clean_frame(
    df: pd.DataFrame,
    date_columns: Iterable[str] = (),
    currency_columns: Iterable[str] = (),
    dayfirst: bool = True,
    drop_empty_rows: bool = True,
) -> pd.DataFrame:
    """Return a cleaned copy of ``df``.

    Steps, in order:

    1. Normalise headers to unique ``snake_case`` names.
    2. Trim surrounding whitespace and collapse internal runs of spaces in text cells.
    3. Optionally drop rows where every cell is blank.
    4. Parse the named date columns (day-first by default).
    5. Parse the named currency columns as NZD amounts.

    Column names in ``date_columns`` / ``currency_columns`` may be given in either
    their original or normalised form.

    Raises:
        KeyError: If a requested date or currency column does not exist.
    """
    out = df.copy()
    out.columns = _dedupe_headers(normalise_header(c) for c in out.columns)

    for col in out.columns:
        if out[col].dtype == object or pd.api.types.is_string_dtype(out[col]):
            out[col] = (
                out[col]
                .astype("string")
                .str.strip()
                .str.replace(r"\s+", " ", regex=True)
                .fillna("")
                .astype(object)
            )

    if drop_empty_rows:
        blank = out.apply(lambda row: all(str(v) == "" for v in row), axis=1)
        out = out.loc[~blank].reset_index(drop=True)

    for col in _resolve(out, date_columns):
        out[col] = parse_dates(out[col], dayfirst=dayfirst)

    for col in _resolve(out, currency_columns):
        out[col] = out[col].map(parse_currency).astype("Float64")

    return out


def _resolve(df: pd.DataFrame, names: Iterable[str]) -> list[str]:
    """Map user-supplied column names onto normalised column names in ``df``."""
    resolved = []
    for name in names:
        key = normalise_header(name)
        if key not in df.columns:
            raise KeyError(f"Column {name!r} not found. Available: {', '.join(df.columns)}")
        resolved.append(key)
    return resolved
