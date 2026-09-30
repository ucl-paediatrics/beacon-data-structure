"""Main module for generating sample data for BEACON."""

import polars as pl

from src import data
from src.date_processing import calculate_admission_age

DAYS_PER_MONTH: float = 365.25 / 12


def load_visits() -> pl.DataFrame:
    """Loads the visit detail, visit, and person data."""
    person = data.load_person_data()
    visits = data.load_visits_data()
    visit_details = data.load_visit_details_data()

    return visit_details.join(
        other=visits.join(
            other=person, on="person_id", how="left", coalesce=True
        ).pipe(
            calculate_admission_age
        ),
        on=["person_id", "visit_id"], how="left", coalesce=True
    )

def anonymise():
    """Anonymises the data, suppressing rare categories and removing identifiable information."""
    # TODO: Implement anonymisation logic here. This function is currently a placeholder
    # person_suppressed: pl.DataFrame = suppression.suppress_rare_categories(
    #     df=person,
    #     specifications=suppression.SUPPRESSION_CONFIG["person"]
    # )

    # return person_suppressed
