from __future__ import annotations

import pytest

from sheetkit.dedupe import dedupe_frame
from sheetkit.io import read_table


def test_dedupe_on_key_case_insensitive(fixtures_dir) -> None:
    df = read_table(fixtures_dir / "dupes.csv")
    out, removed = dedupe_frame(df, keys=["email"])
    assert removed == 2
    assert out["plan"].tolist() == ["Basic", "Basic"]


def test_dedupe_keep_last(fixtures_dir) -> None:
    df = read_table(fixtures_dir / "dupes.csv")
    out, _ = dedupe_frame(df, keys=["Email"], keep="last")
    assert out["plan"].tolist() == ["Pro", "Basic"]


def test_dedupe_case_sensitive(fixtures_dir) -> None:
    df = read_table(fixtures_dir / "dupes.csv")
    _, removed = dedupe_frame(df, keys=["email"], case_insensitive=False)
    assert removed == 1  # only the exact sam@ duplicate


def test_dedupe_all_columns(fixtures_dir) -> None:
    df = read_table(fixtures_dir / "dupes.csv")
    _, removed = dedupe_frame(df)
    assert removed == 1


def test_dedupe_missing_key(fixtures_dir) -> None:
    df = read_table(fixtures_dir / "dupes.csv")
    with pytest.raises(KeyError):
        dedupe_frame(df, keys=["phone"])
