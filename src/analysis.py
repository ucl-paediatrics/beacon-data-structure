"""Functions to analyse the data."""
from pathlib import Path
from typing import Any

import polars as pl
from matplotlib import pyplot as plt
from matplotlib.patches import Patch

from src import import_data


def get_data_for_visit_timeline_plot() -> tuple[pl.DataFrame, pl.DataFrame]:
    """Gets the data for the visit timeline plot."""

    visit_details = import_data.visit_details().join(
        other=import_data.visits().join(
            other=import_data.patients(), on="person_id", how="left", coalesce=True
        ),
        on=["person_id", "visit_id"], how="left", coalesce=True
    )

    visit_details = visit_details.with_columns(
        (
            (pl.col("visit_detail_start_datetime") - pl.col("visit_start_datetime"))
            .dt.total_seconds() / 3600
        ).alias("start_hours"),
        (
            (pl.col("visit_detail_end_datetime") - pl.col("visit_start_datetime"))
            .dt.total_seconds() / 3600
        ).alias("end_hours"),
    )


    visit_summary = (
        visit_details.group_by("person_id", "visit_id")
        .agg(
            (pl.col("visit_end_datetime").min() - pl.col("visit_start_datetime").min())
            .alias("visit_length")
        ).with_columns(
            pl.col(
                "person_id"
            ).str.replace(
                r'^[a-zA-z].*_', ''
            ).cast(
                pl.Int8
            ).alias(
                "person_id_number"
            )
        )
        .sort("person_id_number", "visit_length")
    )

    return visit_summary, visit_details


def plot_visit_timeline(): #pylint: disable=too-many-locals
    """Plots each visit as a horizontal timeline bar, coloured by ward (care_site).

    Visits are aligned to a common start (elapsed time since admission), so the
    actual calendar date is ignored. Visits are grouped by person_id, and within
    each person ordered by total length.
    """
    visit_summary, visit_details = get_data_for_visit_timeline_plot()


    visit_order = visit_summary["visit_id"].to_list()
    person_order = visit_summary["person_id"].to_list()
    visit_index: dict[Any, int] = {visit_id: i for i, visit_id in enumerate(visit_order)}

    persons = visit_summary["person_id"].unique(maintain_order=True).sort().to_list()
    person_cmap = plt.get_cmap("Pastel1")
    person_band_colors = {
        person_id: person_cmap(i % person_cmap.N) for i, person_id in enumerate(persons)
    }

    wards = visit_details["care_site"].unique().sort().to_list()
    cmap = plt.get_cmap("tab10")
    ward_colors = {ward: cmap(i % 10) for i, ward in enumerate(wards)}

    fig, ax = plt.subplots(figsize=(12, max(4, len(visit_order) * 0.4)))

    for visit_id, person_id in zip(visit_order, person_order):
        ax.axhspan(
            visit_index[visit_id] - 0.5,
            visit_index[visit_id] + 0.5,
            color=person_band_colors[person_id],
            zorder=0,
        )

    for row in visit_details.iter_rows(named=True):
        y = visit_index[row["visit_id"]]
        start = row["start_hours"]
        end = row["end_hours"]
        ax.barh(
            y=y,
            width=end - start,
            left=start,
            height=0.6,
            color=ward_colors[row["care_site"]],
            edgecolor="white",
            zorder=2,
        )

    ax.set_yticks(list(visit_index.values()))
    ax.set_yticklabels(
        [f"{person_id} / {visit_id}" for visit_id, person_id in zip(visit_order, person_order)]
    )
    ax.set_xlabel("Hours since admission")
    ax.set_ylabel("Person / Visit")
    ax.set_title(
        "Visit Timeline by Ward (aligned to admission, grouped by person, sorted by length)"
    )

    ward_legend = ax.legend(
        handles=[Patch(color=color, label=ward) for ward, color in ward_colors.items()],
        title="Ward",
        bbox_to_anchor=(1.02, 1),
        loc="upper left",
    )
    ax.add_artist(ward_legend)
    ax.legend(
        handles=[
            Patch(color=color, label=person_id)
            for person_id, color in person_band_colors.items()
        ],
        title="Person",
        bbox_to_anchor=(1.02, 0),
        loc="lower left",
    )

    fig.tight_layout()
    return ax


def list_datatypes_of_measurements(data_dir: Path) -> pl.DataFrame:
    """Lists the data types of all available measurements."""


    available_measurements = [
        f.stem for f in (data_dir / 'measurements').iterdir()
        if f.suffix == ".csv"
        ]

    dtypes = {}

    for m in available_measurements:
        match m:
            case 'difficulty_breathing':
                output_type = pl.List(pl.String)
            case 'capillary_filling' | 'pain_score':
                output_type = pl.String
            case _:
                output_type = None
        this_measurement = import_data.measurement(m, output_type=output_type)
        dtypes[m] = this_measurement['value_source_value'].dtype


    return pl.DataFrame(data ={
        'Measurement Type': dtypes.keys(),
        'Value Type': [str(dtype) for dtype in dtypes.values()]
    }).sort('Measurement Type')
