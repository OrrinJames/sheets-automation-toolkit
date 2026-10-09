"""Duplicate removal on one or more key columns."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

import pandas as pd

from sheetkit.clean import normalise_header

Keep = Literal["first", "last"]


def dedupe_frame(
    df: pd.DataFrame,
    keys: Sequence[str] | None = None,
    keep: Keep = "first",
    case_insensitive: bool = True,
) -> tuple[pd.DataFrame, int]:
    """Drop duplicate rows, matching on ``keys`` (or all columns if none given).

    Matching ignores surrounding whitespace and, by default, letter case, so
    ``"ACME Ltd "`` and ``"acme ltd"`` count as the same key. The kept row's
    original values are left untouched.

    Args:
        df: Input table.
        keys: Column names to match on. Accepts original or normalised names.
        keep: Keep the ``"first"`` or ``"last"`` occurrence of each key.
        case_insensitive: Compare text keys without regard to case.

    Returns:
        A tuple of ``(deduplicated_frame, number_of_rows_removed)``.

    Raises:
        KeyError: If a key column is missing.
    """
    if keys:
        lookup = {normalise_header(c): c for c in df.columns}
        columns = []
        for key in keys:
            if key in df.columns:
                columns.append(key)
            elif normalise_header(key) in lookup:
                columns.append(lookup[normalise_header(key)])
            else:
                raise KeyError(f"Key column {key!r} not found")
    else:
        columns = list(df.columns)

    comparable = df[columns].astype("string").apply(lambda s: s.str.strip())
    if case_insensitive:
        comparable = comparable.apply(lambda s: s.str.casefold())

    mask = comparable.duplicated(keep=keep)
    result = df.loc[~mask].reset_index(drop=True)
    return result, int(mask.sum())
