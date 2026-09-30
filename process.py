"""Script to generate sample data for BEACON."""
import argparse
import logging

import polars as pl

from src.export_data import load_visits

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate sample data for BEACON.")
    parser.add_argument("--log-level", default="INFO", help="Set the logging level (default: INFO)")
    args = parser.parse_args()

    logging.basicConfig(level=args.log_level.upper())

    joined: pl.DataFrame = load_visits()

    print(joined['background_diagnoses'].head(10))
