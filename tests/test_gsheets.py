from __future__ import annotations

import pandas as pd
import pytest

from sheetkit import gsheets


class FakeWorksheet:
    def __init__(self, values: list[list[str]]) -> None:
        self.values = values
        self.updated: list[list[str]] | None = None

    def get_all_values(self) -> list[list[str]]:
        return self.values

    def clear(self) -> None:
        self.values = []

    def update(self, values: list[list[str]], start: str) -> None:
        self.updated = values


class FakeBook:
    def __init__(self, ws: FakeWorksheet) -> None:
        self.ws = ws

    def get_worksheet(self, index: int) -> FakeWorksheet:
        return self.ws

    def worksheet(self, title: str) -> FakeWorksheet:
        return self.ws


class FakeClient:
    def __init__(self, ws: FakeWorksheet) -> None:
        self.book = FakeBook(ws)
        self.opened_with: str | None = None

    def open_by_key(self, key: str) -> FakeBook:
        self.opened_with = key
        return self.book

    def open_by_url(self, url: str) -> FakeBook:
        self.opened_with = url
        return self.book


def test_read_sheet_uses_first_row_as_header() -> None:
    client = FakeClient(FakeWorksheet([["Name", "Amount"], ["Jo", "$5"]]))
    df = gsheets.read_sheet("abc123", client=client)
    assert list(df.columns) == ["Name", "Amount"]
    assert df.iloc[0].tolist() == ["Jo", "$5"]
    assert client.opened_with == "abc123"


def test_write_sheet_sends_header_and_rows() -> None:
    ws = FakeWorksheet([])
    client = FakeClient(ws)
    gsheets.write_sheet(
        pd.DataFrame({"a": [1, None]}), "https://docs.google.com/x", "Out", client=client
    )
    assert ws.updated == [["a"], ["1.0"], [""]]
    assert client.opened_with == "https://docs.google.com/x"


def test_credentials_path_from_env(tmp_path, monkeypatch) -> None:
    key = tmp_path / "sa.json"
    key.write_text("{}")
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    monkeypatch.setenv("SHEETKIT_GOOGLE_CREDENTIALS", str(key))
    assert gsheets.credentials_path() == key


def test_credentials_path_missing(monkeypatch) -> None:
    for var in gsheets.CREDENTIALS_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(gsheets.GoogleSheetsError):
        gsheets.credentials_path()
