#pylint: disable=function-redefined,import-outside-toplevel,invalid-name,reimported,useless-return,missing-module-docstring
#ruff: noqa: PLR1711,F821
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

    from src.export_data import load_visits

    return Patch, load_visits, mo, pl, plt


@app.cell
def _(load_visits, pl):
    visits: pl.DataFrame = load_visits()
    return (visits,)


@app.cell(hide_code=True)
def _(Patch, mo, pl, plt, visits: "pl.DataFrame"):
    def plot_visit_timeline(visit_details: pl.DataFrame) -> plt.Axes:
        """Plots each visit as a horizontal timeline bar, coloured by ward (care_site).

        Visits are aligned to a common start (elapsed time since admission), so the
        actual calendar date is ignored. Visits are ordered by total length.
        """
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

        visit_order = (
            visit_details.group_by("visit_id")
            .agg(
                (pl.col("visit_end_datetime").min() - pl.col("visit_start_datetime").min())
                .alias("visit_length")
            )
            .sort("visit_length")["visit_id"]
            .to_list()
        )
        visit_index = {visit_id: i for i, visit_id in enumerate(visit_order)}

        wards = visit_details["care_site"].unique().sort().to_list()
        cmap = plt.get_cmap("tab10")
        ward_colors = {ward: cmap(i % 10) for i, ward in enumerate(wards)}

        fig, ax = plt.subplots(figsize=(12, max(4, len(visit_order) * 0.4)))

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
            )

        ax.set_yticks(list(visit_index.values()))
        ax.set_yticklabels(visit_order)
        ax.set_xlabel("Hours since admission")
        ax.set_ylabel("Visit")
        ax.set_title("Visit Timeline by Ward (aligned to admission, sorted by length)")

        ax.legend(
            handles=[Patch(color=color, label=ward) for ward, color in ward_colors.items()],
            title="Ward",
            bbox_to_anchor=(1.02, 1),
            loc="upper left",
        )

        fig.tight_layout()
        return ax


    mo.ui.matplotlib(axes=plot_visit_timeline(visits))
    return


if __name__ == "__main__":
    app.run()
