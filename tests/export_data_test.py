#pylint: disable=C0116
"""Tests for the main module."""
import polars as pl

from src.export_data import load_visits


def test_main():
    visits: pl.DataFrame = load_visits()
    assert isinstance(visits, pl.DataFrame)

def test_age_at_admission():
    visits: pl.DataFrame = load_visits()
    # Check that all ages are correctly calculated
    assert all(visits["age_at_admission"] >= 0)

    precise_age: pl.Series = (
        visits["visit_start_datetime"] - visits["date_of_birth"]
    ).dt.total_seconds()

    assert all(precise_age >= 0)

    seconds_per_month: float = 60*60*24*365.25/12

    assert all(precise_age // seconds_per_month == visits["age_at_admission"])

def test_visit_details():
    visits: pl.DataFrame = load_visits()
    # Check that the first visit detail starts at the same time as the visit
    assert visits.group_by("visit_id").agg(
            pl.col("visit_detail_start_datetime").first().alias("first_visit_detail_start"),
            pl.col("visit_start_datetime").first().alias("visit_start"),
        ).with_columns(
            start_times_match = pl.col("first_visit_detail_start") == pl.col("visit_start")
        )['start_times_match'].all()

    # Check that the last visit detail ends at the same time as the visit
    assert visits.group_by("visit_id").agg(
            pl.col("visit_detail_end_datetime").last().alias("last_visit_detail_end"),
            pl.col("visit_end_datetime").last().alias("visit_end"),
        ).with_columns(
            end_times_match = pl.col("last_visit_detail_end") == pl.col("visit_end")
        )['end_times_match'].all()
