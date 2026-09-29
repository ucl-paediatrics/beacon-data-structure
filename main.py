"""Main module for generating sample data for BEACON."""
import argparse
import logging

import polars as pl

import suppression

PERSON = pl.read_csv("person_raw.csv")

def export():
    """Exports the suppressed person data."""
    person_suppressed: pl.DataFrame = suppression.suppress_rare_categories(
        df=PERSON,
        specifications=suppression.SUPPRESSION_CONFIG["person"]
    )

    return person_suppressed

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate sample data for BEACON.")
    parser.add_argument("--log-level", default="INFO", help="Set the logging level (default: INFO)")
    args = parser.parse_args()

    logging.basicConfig(level=args.log_level.upper())

    suppressed = export()
