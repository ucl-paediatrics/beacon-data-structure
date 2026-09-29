"""Module for loading data from CSV files.

Notes:
* Datetimes are represented in millisecond resolution, as this is the coarsest available for Polars.
  Clearly, this is overly precise for date of birth etc!

"""

from pathlib import Path

import polars as pl

# Don't include "None" as this might be a valid value in some columns, e.g. religion
_NULL_VALUES = ["null", "NULL", ""]
_RAW_DATA_DIR = Path(__file__).parent / "raw_data"


def load_person_data() -> pl.DataFrame:
    """Loads the person data from a CSV file."""
    return pl.read_csv(
        source=_RAW_DATA_DIR / "person.csv",
        null_values=_NULL_VALUES,
    ).with_columns(
        pl.col(name="date_of_birth").str.to_datetime(time_unit="ms")
    )

def load_visits_data() -> pl.DataFrame:
    """Loads the visits data from a CSV file."""
    return pl.read_csv(
        source=_RAW_DATA_DIR / "visits.csv",
        null_values=_NULL_VALUES,
        schema_overrides={
            "visit_start_datetime": pl.Datetime,
            "visit_end_datetime": pl.Datetime,
            "background_diagnoses": pl.String,
        },
        separator=","  # Ensure that the separator is a comma
    ).with_columns(
        pl.col(
            name="background_diagnoses"
        ).str.replace(
            pattern=';', value=','
        ).str.json_decode(
            dtype=pl.List(inner=pl.Int64)
        )
    )

def load_visit_details_data() -> pl.DataFrame:
    """Loads the visit details data from a CSV file."""
    return pl.read_csv(
        source=_RAW_DATA_DIR / "visit_details.csv",
        null_values=_NULL_VALUES,
        schema_overrides={
            "visit_detail_start_datetime": pl.Datetime,
            "visit_detail_end_datetime": pl.Datetime,
        }
    )
