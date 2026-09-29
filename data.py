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
        }
    ).with_columns(
        pl.col(name="background_diagnoses").str.json_decode(pl.List(pl.Int64))
    )
