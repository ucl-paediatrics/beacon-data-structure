"""Functions to calculate and process date-related data."""

import polars as pl


def calculate_admission_age(df: pl.DataFrame) -> pl.DataFrame:
    """Calculates the age at admission in months for each record in the DataFrame."""
    days_per_month: float = 365.25 / 12

    return df.with_columns(
        age_at_admission=pl.col('visit_start_datetime') - pl.col('date_of_birth')
    ).with_columns(
        pl.col('age_at_admission').dt.total_days() // days_per_month
    ).with_columns(
        pl.col('age_at_admission').cast(pl.Int64)
    )
