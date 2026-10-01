#pylint: disable=function-redefined,import-outside-toplevel,invalid-name,reimported,useless-return,missing-module-docstring
#ruff: noqa: PLR1711
#type: ignore

import marimo

__generated_with = "0.24.2"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    import polars as pl
    from matplotlib import pyplot as plt
    from matplotlib.patches import Patch

    from src.data import _RAW_DATA_DIR as raw_data_dir
    from src.data import load_measurement_data, load_person_data, load_visit_data, load_outcome_data, load_visit_details_data
    from src.export_data import load_visits



    return (
        Patch,
        load_measurement_data,
        load_outcome_data,
        load_person_data,
        load_visit_data,
        load_visit_details_data,
        load_visits,
        mo,
        pl,
        plt,
        raw_data_dir,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Visits and visit details

    Each `visit` comprises one or more `visit_details`. Each `visit` is also associated with a `person`.
    """)
    return


@app.cell
def _(Patch, load_visits, pl, plt):
    def plot_visit_timeline() -> plt.Axes:
        """Plots each visit as a horizontal timeline bar, coloured by ward (care_site).

        Visits are aligned to a common start (elapsed time since admission), so the
        actual calendar date is ignored. Visits are grouped by person_id, and within
        each person ordered by total length.
        """
        visit_details = load_visits()
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
        visit_order = visit_summary["visit_id"].to_list()
        person_order = visit_summary["person_id"].to_list()
        visit_index = {visit_id: i for i, visit_id in enumerate(visit_order)}

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

    return (plot_visit_timeline,)


@app.cell(hide_code=True)
def _(mo, plot_visit_timeline):
    mo.ui.matplotlib(axes=plot_visit_timeline())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Measurements

    Measurements are stored in separate files, one for each measurement type. Each measurement is associated with a `person` (via `person_id`).

    Different measurement types are represented as different data types. Here is the list of measurement types and their corresponding data types:
    """)
    return


@app.cell
def _(load_measurement_data, mo, pl, raw_data_dir):
    def list_datatypes_of_measurements():
        """Lists the data types of all available measurements."""


        available_measurements = [
            f.stem for f in (raw_data_dir / 'measurements').iterdir()
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
            data = load_measurement_data(m, output_type=output_type)
            dtypes[m] = data['value_source_value'].dtype


        return pl.DataFrame(data ={
            'Measurement Type': dtypes.keys(),
            'Value Type': [str(dtype) for dtype in dtypes.values()]
        }).sort('Measurement Type')

    mo.ui.table(
        list_datatypes_of_measurements(),
        selection=None,
        pagination=False
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Anonymising potentially identifiable information

    Potentially identifiable information includes:
    * Date of Birth
    * All datetime fields:
        * `vist_start_datetime`
        * `visit_end_datetime`
        * `visit_detail_start_datetime`
        * `visit_detail_end_datetime`
        * `measurement_datetime`
    * Rare categorical values:
        * `ethnicity`
        * `religion`
        * `preferred_language`
        * `background_diagnoses`
    * Extreme continuous values:
        * `height`
        * `weight`
        * `bmi`
    """)
    return


@app.cell
def _(
    load_outcome_data,
    load_person_data,
    load_visit_data,
    load_visit_details_data,
):
    patients = load_person_data()
    visits = load_visit_data()
    visit_details = load_visit_details_data()
    outcomes = load_outcome_data()


    return


app._unparsable_cell(
    """
    def censor_datetimes(
        df: pl.DataFrame,
        reference_datetimes: pl.DataFrame,
        columns_to_preserve: list[str] | None = None,
        left_on: str | list[str] | None = None,
        right_on: str | list[]
    

    ) -> pl.DataFrame:
        \"\"\"Censors datetime columns in a DataFrame based on reference datetimes.

        Args:
            df (pl.DataFrame): The input DataFrame containing datetime columns.
            reference_datetimes (pl.DataFrame): A DataFrame containing reference datetimes for 
              censoring. This should include two columns: 'person_id' and another column with 
              the reference datetime values.
            columns_to_preserve (list[str], optional): A list of column names to preserve uncensored 
              in the output DataFrame. If not provided, all columns will be censored.

        Returns:
            pl.DataFrame: A new DataFrame with censored datetime columns.
        \"\"\"

        if 'person_id' not in reference_datetimes.columns:
            raise ValueError(\"Reference datetimes DataFrame must contain a 'person_id' column.\")

        datum_column: str = next(col for col in reference_datetimes.columns if col != 'person_id')

        columns_to_censor: list[str] = [
            col for col in df.columns if df[col].dtype == pl.Datetime
            if col not in (columns_to_preserve or [])
        ]

        censored_df: pl.DataFrame = df.join(reference_datetimes, on='person_id', how='left')

        if len(censored_df) != len(df):
            raise ValueError(
                f\"Join operation returned {len(censored_df)} rows; expected {len(df)}.\" + \\
                \"Check for missing person_id values.\"
            )

        for col in columns_to_censor:
            censored_df = censored_df.with_columns(
                pl.col(col)-pl.col(datum_column)
            )
        return censored_df.drop(datum_column)


    censor_datetimes(
        df=visits,
        reference_datetimes=visits.select(['person_id', 'visit_start_datetime']),
        columns_to_preserve=['visit_start_datetime']
    )

    visits.join(
        other=visits.with_columns(
            datum=pl.col('visit_start_datetime')
        ).select(['datum', 'person_id', 'visit_start_datetime']),
        on=['person_id', 'visit_start_datetime']
    ).with_columns(
        visit_duration=pl.col('visit_end_datetime')-pl.col('datum')
    ).drop([
        'datum',
        'visit_start_datetime',
        'visit_end_datetime'
    ])
    """,
    name="_"
)


if __name__ == "__main__":
    app.run()
