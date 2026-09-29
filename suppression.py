"""Configuration and utility functions for suppressing rare categories in a DataFrame."""
import logging
from typing import Any

import polars as pl

SUPPRESSION_CONFIG = {
    "person": {
        "ethnicity": (5, "Other"),
        "preferred_language": (5, "Other"),
        "religion": (5, "Other"),
    }
}

LOGGER = logging.getLogger(__name__)


def suppress_rare_category(
    df: pl.DataFrame,
    column: str,
    threshold: int = 20,
    new_value: str = "Other"
) -> pl.DataFrame:
    """Suppresses rare categories in a specified column of a DataFrame."""
    counts = df[column].value_counts()
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
