"""Main module for generating sample data for BEACON."""
import argparse
import logging

import polars as pl

import data
from date_processing import calculate_admission_age

DAYS_PER_MONTH: float = 365.25 / 12


def main() -> pl.DataFrame:
    """Exports the suppressed person data."""
    person = data.load_person_data()
    visits = data.load_visits_data()

    return visits.join(
        other=person, on="person_id", how="left"
    ).pipe(
        calculate_admission_age
    )

def anonymise():
    """Anonymises the data, suppressing rare categories and removing identifiable information."""
    # person_suppressed: pl.DataFrame = suppression.suppress_rare_categories(
    #     df=person,
    #     specifications=suppression.SUPPRESSION_CONFIG["person"]
    # )

    # return person_suppressed

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate sample data for BEACON.")
    parser.add_argument("--log-level", default="INFO", help="Set the logging level (default: INFO)")
    args = parser.parse_args()

    logging.basicConfig(level=args.log_level.upper())

    joined: pl.DataFrame = main()

    print(joined["background_diagnoses"].head(10))
