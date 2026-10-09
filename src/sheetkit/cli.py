"""Command-line interface: ``sheetkit clean | merge | dedupe | report``."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, cast

import typer

from sheetkit.clean import clean_frame
from sheetkit.dedupe import Keep, dedupe_frame
from sheetkit.io import read_table, write_table
from sheetkit.merge import merge_files
from sheetkit.report import AggFunc, write_report

app = typer.Typer(
    help="Clean, merge, dedupe and report on Excel / CSV data.",
    no_args_is_help=True,
    add_completion=False,
)

InputFile = Annotated[
    Path, typer.Argument(exists=True, dir_okay=False, readable=True, help="Input CSV or .xlsx")
]
OutputFile = Annotated[Path, typer.Option("--output", "-o", help="Output path (.csv or .xlsx)")]


def _split(values: list[str] | None) -> list[str]:
    """Accept both repeated options and comma-separated lists."""
    result: list[str] = []
    for value in values or []:
        result.extend(v.strip() for v in value.split(",") if v.strip())
    return result


@app.command()
def clean(
    input_file: InputFile,
    output: OutputFile,
    date: Annotated[
        list[str] | None, typer.Option("--date", "-d", help="Date column(s) to parse")
    ] = None,
    currency: Annotated[
        list[str] | None, typer.Option("--currency", "-c", help="NZD column(s) to parse")
    ] = None,
    monthfirst: Annotated[
        bool, typer.Option("--monthfirst", help="Read dates as MM/DD (default is NZ DD/MM)")
    ] = False,
    sheet: Annotated[str, typer.Option(help="Worksheet name for Excel input")] = "0",
) -> None:
    """Trim whitespace, normalise headers, and parse dates and NZD currency."""
    df = read_table(input_file, sheet=_sheet(sheet))
    try:
        cleaned = clean_frame(
            df,
            date_columns=_split(date),
            currency_columns=_split(currency),
            dayfirst=not monthfirst,
        )
    except (KeyError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    write_table(cleaned, output)
    typer.echo(f"Cleaned {len(df)} rows -> {len(cleaned)} rows: {output}")


@app.command()
def dedupe(
    input_file: InputFile,
    output: OutputFile,
    key: Annotated[
        list[str] | None,
        typer.Option("--key", "-k", help="Key column(s); default is all columns"),
    ] = None,
    keep: Annotated[str, typer.Option(help="Keep 'first' or 'last' duplicate")] = "first",
    case_sensitive: Annotated[
        bool, typer.Option("--case-sensitive", help="Treat 'ACME' and 'acme' as different")
    ] = False,
) -> None:
    """Remove duplicate rows, matching on key columns."""
    if keep not in {"first", "last"}:
        raise typer.BadParameter("--keep must be 'first' or 'last'")
    df = read_table(input_file)
    try:
        result, removed = dedupe_frame(
            df, keys=_split(key), keep=cast(Keep, keep), case_insensitive=not case_sensitive
        )
    except KeyError as exc:
        raise typer.BadParameter(str(exc)) from exc
    write_table(result, output)
    typer.echo(f"Removed {removed} duplicate row(s); {len(result)} remain: {output}")


@app.command()
def merge(
    input_files: Annotated[
        list[Path], typer.Argument(exists=True, dir_okay=False, help="Files to merge")
    ],
    output: OutputFile,
    no_source: Annotated[
        bool, typer.Option("--no-source", help="Don't add a source_file column")
    ] = False,
) -> None:
    """Stack several CSV / Excel files into one, aligning columns by name."""
    merged = merge_files(input_files, source_column=None if no_source else "source_file")
    write_table(merged, output)
    typer.echo(f"Merged {len(input_files)} file(s), {len(merged)} rows: {output}")


@app.command()
def report(
    input_file: InputFile,
    output: OutputFile,
    index: Annotated[str, typer.Option("--index", "-i", help="Pivot row column")],
    values: Annotated[str, typer.Option("--values", "-v", help="Column to aggregate")],
    columns: Annotated[str | None, typer.Option("--columns", help="Optional pivot column")] = None,
    agg: Annotated[str, typer.Option(help="sum, mean, count, min or max")] = "sum",
    currency: Annotated[
        list[str] | None,
        typer.Option("--currency", "-c", help="Parse these columns as NZD before pivoting"),
    ] = None,
    date: Annotated[
        list[str] | None, typer.Option("--date", "-d", help="Date column(s) to parse")
    ] = None,
    title: Annotated[str, typer.Option(help="Summary sheet name")] = "Summary",
) -> None:
    """Build a formatted Excel summary: pivot, styled header, autofit columns."""
    if agg not in {"sum", "mean", "count", "min", "max"}:
        raise typer.BadParameter("--agg must be one of sum, mean, count, min, max")
    if output.suffix.lower() != ".xlsx":
        raise typer.BadParameter("--output must end in .xlsx")
    try:
        df = clean_frame(
            read_table(input_file),
            currency_columns=_split(currency),
            date_columns=_split(date),
        )
        write_report(
            df,
            output,
            index=index,
            values=values,
            columns=columns,
            aggfunc=cast(AggFunc, agg),
            title=title,
        )
    except (KeyError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(f"Report written: {output}")


def _sheet(value: str) -> str | int:
    """Interpret a numeric ``--sheet`` value as an index."""
    return int(value) if value.isdigit() else value


if __name__ == "__main__":  # pragma: no cover
    app()
