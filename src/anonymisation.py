"""Functions for anonymising tables."""
import logging
from typing import Any

import polars as pl

SUPPRESSION_CONFIG = {
    "person": {
        "ethnicity": (5, 'Y'),
        "preferred_language": (5, "Other"),
        "religion": (5, "Other"),
    }
}

LOGGER = logging.getLogger(__name__)


def relativise_timestamps(
    df: pl.DataFrame,
    df_admission_datum: pl.DataFrame,
    admission_datum_field_name: str = 'datum', 
    except_columns: list[str] | None = None
) -> pl.DataFrame:
    """Converts timestamps in a dataframe to be relative to a timestamp datum.
    
    This datum is set up in this workflow as the start of the most recent visit for that patient.

    Args:
        df: The dataframe containing the timestamps to be relativised. This must include a
          'person_id' column and one or more columns containing timestamps.
        df_admission_datum: The dataframe containing the timestamp datum for each person. 
          This must include a 'person_id' column and a column containing the timestamp datum.
        admission_datum_field_name: The name of the column in df_admission_datum that contains 
          the timestamp datum. Defaults to 'datum'.
    
    Returns:
        A copy of df with all timestamp columns converted to be relative to the timestamp datum for 
          that person and visit. 
    
    
    """
    joined =  df.join(
        other=df_admission_datum,
        on=['person_id', 'visit_id'],
        how='left'
    )

    # Get a list of columns to anonymise - all date columns
    cols_to_anonymise = [
        col for col,type in zip(joined.columns, joined.dtypes)
        if (type==pl.Datetime) and \
            col != admission_datum_field_name and \
            col not in (except_columns or [])
    ]

    # Start with a copy of the dataframe
    censored = joined.select(pl.all())

    # Loop over all columns to anonymise - and do the anonymisation
    for col in cols_to_anonymise:
        censored = censored.with_columns(
            pl.col(col)-pl.col(admission_datum_field_name)
        )

    # Drop the identifiable timestamp datum
    return censored.drop(admission_datum_field_name)


def truncate_timestamps(
    df: pl.DataFrame,
    timestamp_columns: str | list[str] | None = None,
    resolution: str = 'month'

) -> pl.DataFrame:
    """Truncates timestamps in a dataframe to the specified resolution.
    
    Args:
        df: The dataframe containing the timestamps to be truncated. This must include a
          'person_id' column and one or more columns containing timestamps.
        timestamp_columns: A single column, or a list of column names in df that contain timestamps 
          to be truncated. If None, all columns of type Datetime will be truncated. 
          Defaults to None.
        resolution: The resolution to which the timestamps should be truncated.
            Must be one of 'year', 'month', 'day'.
    
    Returns:
        A copy of df with all specified timestamp columns truncated to the specified resolution.
    """

    if timestamp_columns is not None and isinstance(timestamp_columns, str):
        timestamp_columns = [timestamp_columns]

    if timestamp_columns is None:
        timestamp_columns = [
            col for col, type in zip(df.columns, df.dtypes) if type == pl.Datetime
        ]

    truncated = df.select(pl.all())

    match resolution:
        case 'year':
            resolution = '1y'
        case 'month':
            resolution = '1mo'
        case 'day':
            resolution = '1d'
        case _:
            raise ValueError(
                f"Invalid resolution '{resolution}'. Must be one of 'year', 'month', 'day'."
            )

    for col in timestamp_columns:
        truncated = truncated.with_columns(
            pl.col(col).dt.truncate(every=resolution).alias(col)
        )

    return truncated


def round_columns(
    df: pl.DataFrame,
    columns_to_round: str | list[str],
    decimal_places: int = 2
) -> pl.DataFrame:
    """Rounds specified columns in a dataframe to the specified number of decimal places.
    
    Args:
        df: The dataframe containing the columns to be rounded.
        columns_to_round: A single column, or a list of column names in df that should be rounded.
        decimal_places: The number of decimal places to which the columns should be rounded. 
          Defaults to 2.
    
    Returns:
        A copy of df with all specified columns rounded to the specified number of decimal places.
    """

    if isinstance(columns_to_round, str):
        columns_to_round = [columns_to_round]

    rounded = df.select(pl.all())

    for col in columns_to_round:
        rounded = rounded.with_columns(
            pl.col(col).round(decimal_places).alias(col)
        )

    return rounded


def associate_visits_with_events(
    df: pl.DataFrame,
    df_visits: pl.DataFrame,
    event_timestamp_column: str,
    visit_start_field_name: str = 'visit_start_datetime'
) -> pl.DataFrame:
    """Associates events with visits based on the event timestamp and visit start timestamp.
    This function performs an asof join between the events dataframe and the visits dataframe,
    matching each event to the most recent visit that started before the event occurred.
    
    Note that events may end up being associated with visits that finished before the event 
    occurred, as the join is based on the visit start timestamp; end timestamp is ignored.
    However, if a subsequent visit started before the event, the event will be associated with 
    that subsequent visit instead. This prevents events from being left unassociated with any 
    visit if they occur after a visit has ended but before the next visit starts, as may happen 
    if time signals are slightly misaligned (e.g. mortality)

    Args:
        df: The dataframe containing the events to be associated with visits.
          This must include a 'person_id' column and a column containing the event timestamps.
        df_visits: The dataframe containing the visits to be associated with events.
        event_timestamp_column: The name of the column in df that contains the event timestamps.
        visit_start_field_name: The name of the column in df_visits that contains the visit 
          start timestamps. Defaults to 'visit_start_datetime'.

    Returns:
        A copy of df with an additional column 'visit_id' indicating the visit associated 
          with each event. Columns are ordered as follows: 'person_id', 'visit_id', 
          event_timestamp_column, followed by all other columns in df.
    
    """

    df_sorted = df.sort(['person_id', event_timestamp_column])
    df_visits_sorted = df_visits.sort(['person_id', visit_start_field_name])

    associated = df_sorted.join_asof(
        other=df_visits_sorted[visit_start_field_name, 'person_id', 'visit_id'],
        by=['person_id'],
        left_on=event_timestamp_column,
        right_on=visit_start_field_name,
        strategy='backward',
        check_sortedness=False
    ).drop(visit_start_field_name)

    columns_ordered = ['person_id', 'visit_id', event_timestamp_column] + \
    [col for col in df.columns if col not in ['person_id', 'visit_id', event_timestamp_column]]

    return associated.select(columns_ordered)


def suppress_rare_category(
    df: pl.DataFrame,
    column: str,
    threshold: int = 20,
    new_value: str = "Other"
) -> pl.DataFrame:
    """Suppresses rare categories in a specified column of a DataFrame."""
    counts = df[column].value_counts().drop_nulls()
    rare_categories = counts.filter(pl.col("count") < threshold)[column].to_list()
    LOGGER.info(
        f"Rare categories in column '{column}': {rare_categories} suppressed to '{new_value}'"
    )
    return df.with_columns(
        pl.when(pl.col(column).is_in(rare_categories))
        .then(pl.lit(new_value))
        .otherwise(pl.col(column))
        .alias(column)
    )


def suppress_rare_categories(
    df: pl.DataFrame,
    specifications: dict[str, tuple[int, Any]],
) -> pl.DataFrame:
    """Suppresses rare categories in multiple columns based on provided specifications.
    Arguments:
        df: The DataFrame to process.
        specifications: A dictionary where keys are column names and values are tuples containing 
          the threshold and the new value to replace rare categories with.
    Returns:
        A DataFrame with rare categories suppressed according to the specifications.
    
    """
    for column, (threshold, new_value) in specifications.items():
        df = suppress_rare_category(df, column, threshold, new_value)
    return df


def clip(
    df: pl.DataFrame,
    column: str,
    max_value: float | None = None,
    min_value: float | None = None,
) -> pl.DataFrame:
    """Clips extreme values in a specified column of a DataFrame."""
    return df.with_columns(
        pl.col(column).clip(lower_bound=min_value, upper_bound=max_value).alias(column)
    )
