from __future__ import annotations

import pandas as pd
import pytest

from sheetkit.clean import clean_frame, normalise_header, parse_currency, parse_dates
from sheetkit.io import read_table


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("  Order Date ", "order_date"),
        ("Amount (NZD)", "amount_nzd"),
        ("Customer-Name", "customer_name"),
        ("%%%", "column"),
        (2026, "2026"),
    ],
)
def test_normalise_header(raw: object, expected: str) -> None:
    assert normalise_header(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("$1,250.00", 1250.0),
        ("NZ$89.90", 89.9),
        ("NZD 410", 410.0),
        ("($20.00)", -20.0),
        ("-$5", -5.0),
        ("7", 7.0),
        ("", None),
        ("   ", None),
        (None, None),
    ],
)
def test_parse_currency(raw: object, expected: float | None) -> None:
    assert parse_currency(raw) == expected


def test_parse_currency_rejects_text() -> None:
    with pytest.raises(ValueError, match="Not a currency value"):
        parse_currency("twelve dollars")


def test_parse_dates_is_day_first_and_handles_iso() -> None:
    parsed = parse_dates(pd.Series(["03/04/2026", "2026-04-05", "", "not a date"]))
    assert parsed[0] == pd.Timestamp("2026-04-03")
    assert parsed[1] == pd.Timestamp("2026-04-05")
    assert pd.isna(parsed[2])
    assert pd.isna(parsed[3])


def test_parse_dates_month_first() -> None:
    parsed = parse_dates(pd.Series(["03/04/2026"]), dayfirst=False)
    assert parsed[0] == pd.Timestamp("2026-03-04")


def test_clean_frame_end_to_end(fixtures_dir) -> None:
    df = read_table(fixtures_dir / "messy.csv")
    out = clean_frame(df, date_columns=["Order Date"], currency_columns=["amount_nzd"])

    assert list(out.columns) == ["order_id", "customer_name", "order_date", "amount_nzd", "region"]
    assert len(out) == 4  # blank row dropped
    assert out.loc[0, "customer_name"] == "Kiwi Coffee Co"
    assert out.loc[2, "customer_name"] == "Tui Plumbing"  # internal spaces collapsed
    assert out["order_date"].tolist() == [
        pd.Timestamp("2026-04-03"),
        pd.Timestamp("2026-04-05"),
        pd.Timestamp("2026-04-15"),
        pd.Timestamp("2026-04-30"),
    ]
    assert out["amount_nzd"].tolist() == [1250.0, 89.9, -20.0, 410.0]


def test_clean_frame_does_not_mutate_input(fixtures_dir) -> None:
    df = read_table(fixtures_dir / "messy.csv")
    before = df.copy()
    clean_frame(df)
    pd.testing.assert_frame_equal(df, before)


def test_clean_frame_makes_duplicate_headers_unique() -> None:
    df = pd.DataFrame([["a", "b"]], columns=["Name", " name "])
    assert list(clean_frame(df).columns) == ["name", "name_2"]


def test_clean_frame_unknown_column() -> None:
    with pytest.raises(KeyError, match="not found"):
        clean_frame(pd.DataFrame({"a": ["1"]}), date_columns=["missing"])
