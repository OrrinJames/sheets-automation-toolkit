"""Combine several spreadsheet files into one table."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from sheetkit.clean import _dedupe_headers, normalise_header
from sheetkit.io import read_table


def merge_files(
    paths: Sequence[str | Path],
    source_column: str | None = "source_file",
    sheet: str | int = 0,
) -> pd.DataFrame:
    """Stack multiple CSV/Excel files into a single DataFrame.

    Headers are normalised before stacking so ``"Order ID"`` in one file lines up
    with ``"order_id"`` in another. Columns missing from a file are filled with
    blanks rather than dropped.

    Args:
        paths: Files to merge, in order.
        source_column: Name of a column recording each row's source file name,
            or ``None`` to omit it.
        sheet: Worksheet name or index to read from Excel files.

    Returns:
        The combined table.

    Raises:
        ValueError: If ``paths`` is empty.
    """
    if not paths:
        raise ValueError("merge_files needs at least one input file")

    frames: list[pd.DataFrame] = []
    for path in paths:
        frame = read_table(path, sheet=sheet)
        frame.columns = _dedupe_headers(normalise_header(c) for c in frame.columns)
        if source_column:
            frame[source_column] = Path(path).name
        frames.append(frame)

    merged = pd.concat(frames, ignore_index=True, sort=False)
    return merged.fillna("")
