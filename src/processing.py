"""Functions to process dataframes to obtain derived fields."""
import polars as pl

DAYS_PER_MONTH: float = 365.25 / 12


def calculate_age(
    df: pl.DataFrame,
    reference_date_column: str,
    dates_of_birth: pl.DataFrame
) -> pl.DataFrame:
    """Calculates the age of each person in a dataframe based on their date of birth 
    and a reference date.

    Args:
        df: The dataframe containing the reference dates for age calculation. This must include a
          'person_id' column and a column containing the reference dates.
        reference_date_column: The name of the column in df that contains the reference dates.
        dates_of_birth: A dictionary mapping person_id to their date of birth.
        
    Returns:
        A copy of df with an additional column 'age' containing the age of each person in years at 
          the reference date.
    """

    expected_dob_columns = {'person_id', 'date_of_birth'}
    if set(dates_of_birth.columns) != expected_dob_columns:
        raise ValueError(
            f"dates_of_birth must contain the following columns: {expected_dob_columns}"
        )

    # Join the input dataframe with the dates of birth dataframe on 'person_id'
    joined_df = df.join(dates_of_birth, on='person_id', how='left')

    # Calculate age in years
    age_df = joined_df.with_columns(
        (
            (pl.col(reference_date_column) - pl.col('date_of_birth')).dt.total_days() / DAYS_PER_MONTH
        ).alias('age_months')
    )

    # Drop the date_of_birth column as it's no longer needed
    return age_df.drop('date_of_birth')
