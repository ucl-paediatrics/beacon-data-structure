#pylint: disable=C0116
"""Tests for the main module."""
import polars as pl

from main import main


def test_main():
    result: pl.DataFrame = main()
    assert isinstance(result, pl.DataFrame)

def test_age_at_admission():
    result: pl.DataFrame = main()
    # Check that all ages are correctly calculated
    assert all(result["age_at_admission"] >= 0)

    precise_age: pl.Series = (
        result["visit_start_datetime"] - result["date_of_birth"]
    ).dt.total_seconds()

    assert all(precise_age >= 0)

    seconds_per_month: float = 60*60*24*365.25/12

    assert all(precise_age // seconds_per_month == result["age_at_admission"])

def test_visit_details():
    result: pl.DataFrame = main()
    # Check that the first visit detail starts at the same time as the visit
    assert result.group_by("visit_id").agg(
            pl.col("visit_detail_start_datetime").first().alias("first_visit_detail_start"),
            pl.col("visit_start_datetime").first().alias("visit_start"),
        ).with_columns(
            start_times_match = pl.col("first_visit_detail_start") == pl.col("visit_start")
        )['start_times_match'].all()

    # Check that the last visit detail ends at the same time as the visit
    assert result.group_by("visit_id").agg(
            pl.col("visit_detail_end_datetime").last().alias("last_visit_detail_end"),
            pl.col("visit_end_datetime").last().alias("visit_end"),
        ).with_columns(
            end_times_match = pl.col("last_visit_detail_end") == pl.col("visit_end")
        )['end_times_match'].all()
