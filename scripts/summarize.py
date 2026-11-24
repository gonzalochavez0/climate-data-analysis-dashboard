"""Summarise the climate dataset that feeds the Power BI dashboard.

Reproduces the headline numbers quoted in the README so they can be verified
without opening Power BI.

Usage (from the project root)::

    python scripts/summarize.py
    python scripts/summarize.py --csv data/dataset.csv --by-month
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

DEFAULT_CSV = Path(__file__).resolve().parents[1] / "data" / "dataset.csv"

REQUIRED_COLUMNS = [
    "Fecha",
    "Hora",
    "Departamento",
    "Temperatura_C",
    "Humedad_%",
    "Lluvia_mm",
    "Recomendacion_Siembra",
]

TEMPERATURE = "Temperatura_C"
HUMIDITY = "Humedad_%"
RAIN = "Lluvia_mm"
DEPARTMENT = "Departamento"
RECOMMENDATION = "Recomendacion_Siembra"


def load(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise SystemExit(f"{path} is missing required columns: {missing}")
    frame["Fecha"] = pd.to_datetime(frame["Fecha"])
    return frame


def print_overview(frame: pd.DataFrame) -> None:
    days = frame["Fecha"].dt.date.nunique()
    readings_per_day = len(frame) / days
    good = (frame[RECOMMENDATION] == "Buena para Maíz/Frijol").sum()

    print("=== Overview ===")
    print(f"Rows                : {len(frame):,}")
    print(f"Period              : {frame['Fecha'].min():%Y-%m-%d} -> {frame['Fecha'].max():%Y-%m-%d}")
    print(f"Days                : {days:,}")
    print(f"Readings per day    : {readings_per_day:.0f}")
    print(f"Departments         : {frame[DEPARTMENT].nunique()} ({', '.join(sorted(frame[DEPARTMENT].unique()))})")
    print(f"Hours sampled       : {', '.join(str(h) for h in sorted(frame['Hora'].unique()))}")
    print(f"Missing values      : {int(frame[REQUIRED_COLUMNS].isna().sum().sum())}")
    print(f"Sowing-friendly    : {good / len(frame):.1%} of readings")
    print()


def print_metrics(frame: pd.DataFrame) -> None:
    print("=== Metrics ===")
    print(
        f"{'Metric':<14}{'Min':>8}{'Mean':>9}{'Max':>9}{'Std':>9}"
    )
    for label, column in (("Temperature C", TEMPERATURE), ("Humidity %", HUMIDITY), ("Rain mm", RAIN)):
        series = frame[column]
        print(
            f"{label:<14}{series.min():>8.1f}{series.mean():>9.1f}"
            f"{series.max():>9.1f}{series.std():>9.1f}"
        )
    print()


def print_by_department(frame: pd.DataFrame) -> None:
    table = (
        frame.groupby(DEPARTMENT)
        .agg(
            readings=(TEMPERATURE, "size"),
            temp_mean=(TEMPERATURE, "mean"),
            humidity_mean=(HUMIDITY, "mean"),
            rain_total=(RAIN, "sum"),
        )
        .sort_values("temp_mean", ascending=False)
        .round(2)
    )
    print("=== By department ===")
    print(table.to_string())
    print()


def print_by_month(frame: pd.DataFrame) -> None:
    monthly = frame.assign(month=frame["Fecha"].dt.month).groupby("month").agg(
        temp_mean=(TEMPERATURE, "mean"),
        humidity_mean=(HUMIDITY, "mean"),
        rain_total=(RAIN, "sum"),
    )
    print("=== Monthly ===")
    print(monthly.round(1).to_string())
    print()


def print_extremes(frame: pd.DataFrame) -> None:
    print("=== Extremes ===")
    for label, column, use_max in (
        ("Hottest", TEMPERATURE, True),
        ("Coldest", TEMPERATURE, False),
        ("Wettest", RAIN, True),
    ):
        index = frame[column].idxmax() if use_max else frame[column].idxmin()
        row = frame.loc[index]
        print(
            f"{label:<8}: {row[column]:>6.1f} on {row['Fecha']:%Y-%m-%d} "
            f"at {row['Hora']:02d}:00 in {row[DEPARTMENT]}"
        )
    print()


def print_recommendations(frame: pd.DataFrame) -> None:
    counts = frame[RECOMMENDATION].value_counts()
    print("=== Sowing recommendations ===")
    for label, count in counts.items():
        print(f"{label:<45}{count:>6,}  ({count / len(frame):.1%})")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarise the climate dataset.")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="dataset path")
    parser.add_argument("--by-month", action="store_true", help="include the monthly breakdown")
    args = parser.parse_args()

    frame = load(args.csv)
    print(f"Dataset: {args.csv}\n")
    print_overview(frame)
    print_metrics(frame)
    print_by_department(frame)
    print_extremes(frame)
    print_recommendations(frame)
    if args.by_month:
        print_by_month(frame)


if __name__ == "__main__":
    main()
