from __future__ import annotations

import pytest

from sheetkit.io import write_table
from sheetkit.merge import merge_files


def test_merge_aligns_headers_and_tags_source(fixtures_dir) -> None:
    out = merge_files([fixtures_dir / "part_a.csv", fixtures_dir / "part_b.csv"])
    assert list(out.columns) == ["order_id", "region", "amount", "source_file", "rep"]
    assert len(out) == 3
    assert out["source_file"].tolist() == ["part_a.csv", "part_a.csv", "part_b.csv"]
    assert out["rep"].tolist() == ["", "", "Aroha"]


def test_merge_mixed_csv_and_excel(fixtures_dir, tmp_path) -> None:
    from sheetkit.io import read_table

    xlsx = write_table(read_table(fixtures_dir / "part_b.csv"), tmp_path / "part_b.xlsx")
    out = merge_files([fixtures_dir / "part_a.csv", xlsx], source_column=None)
    assert "source_file" not in out.columns
    assert out["order_id"].tolist() == ["1", "2", "3"]


def test_merge_requires_input() -> None:
    with pytest.raises(ValueError):
        merge_files([])
