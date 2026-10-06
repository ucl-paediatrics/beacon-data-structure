"""Module for loading data from CSV files.

Notes:
* Datetimes are represented in millisecond resolution, as this is the coarsest available for Polars.
  Clearly, this is overly precise for date of birth etc!

"""

from pathlib import Path

import polars as pl

# Don't include "None" as this might be a valid value in some columns, e.g. religion
_NULL_VALUES = ["null", "NULL", ""]
RAW_DATA_DIR = Path(__file__).parent.parent / "raw_data"


def patients() -> pl.DataFrame:
    """Loads the person data from a CSV file."""
    return pl.read_csv(
        source=RAW_DATA_DIR / "person.csv",
        null_values=_NULL_VALUES,
        schema_overrides={
            'date_of_birth': pl.Datetime(time_unit='ms')
        }
    )

def visits() -> pl.DataFrame:
    """Loads the visits data from a CSV file."""
    return pl.read_csv(
        source=RAW_DATA_DIR / "visits.csv",
        null_values=_NULL_VALUES,
        schema_overrides={
            "visit_start_datetime": pl.Datetime('ms'),
            "visit_end_datetime": pl.Datetime('ms'),
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

def visit_details() -> pl.DataFrame:
    """Loads the visit details data from a CSV file."""
    return pl.read_csv(
        source=RAW_DATA_DIR / "visit_details.csv",
        null_values=_NULL_VALUES,
        schema_overrides={
            "visit_detail_start_datetime": pl.Datetime('ms'),
            "visit_detail_end_datetime": pl.Datetime('ms'),
        }
    )

def measurement(measurement_type: str, output_type=None) -> pl.DataFrame:
    """Loads the measurement data from a CSV file.

    Args:
        measurement_type: The type of measurement to load. This must correspond to a CSV file in
          the measurements subdirectory of the raw_data directory.

    Returns:
        A Polars DataFrame containing the measurement data.

    Raises:
        ValueError: If the measurement_type is not one of the expected values.
    """
    try:
        data = pl.read_csv(
            source=RAW_DATA_DIR / "measurements" / f"{measurement_type}.csv",
            null_values=_NULL_VALUES,
            schema_overrides={
                "measurement_datetime": pl.Datetime('ms'),
            }
        )
    except FileNotFoundError as exc:
        valid_measurements: list[str] = sorted([
            path.stem for path in (RAW_DATA_DIR / "measurements").glob("*.csv")
        ])
        raise ValueError(
            f"Measurement '{measurement_type}' is not valid. Choose one of: {valid_measurements}"
        ) from exc

    if output_type is not None:
        match output_type:
            case pl.List(inner=pl.String):
                data = data.with_columns(
                    pl.col(
                        'value_source_value'
                    ).str.replace(
                        r'\[', ''
                    ).str.replace(
                        r'\]', ''
                    ).str.split(';')
                )
            case pl.String | pl.Int64 | pl.Float64:
                data = data.with_columns(
                    pl.col('value_source_value').cast(output_type)
                )
            case _:
                raise ValueError(f"Output type '{output_type}' is not valid.")

    return data

def outcomes() -> pl.DataFrame:
    """Loads the outcome data"""
    return pl.read_csv(
        source=RAW_DATA_DIR / "outcomes.csv",
        null_values=_NULL_VALUES,
        schema_overrides={
            'event_type': pl.String,
            'event_datetime': pl.Datetime(time_unit='ms')
        }
    )
