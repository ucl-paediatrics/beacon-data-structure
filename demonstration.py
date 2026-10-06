#pylint: disable=function-redefined,import-outside-toplevel,invalid-name,reimported,useless-return,missing-module-docstring
#ruff: noqa: PLR1711
#type: ignore

import marimo

__generated_with = "0.24.2"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    This notebook demonstrates the intended data format of BEACON, along with suggested anonymisation methods as described in the HRA approved protocol. In this case, we use relative timestamps to remove exact dates and times. An alternate strategy that is also allowed is to randomly jitter the timestamps by a small amount, e.g. 1-2 days
    """)
    return


@app.cell
def _():
    import marimo as mo

    from src import analysis, anonymisation, import_data, processing



    return analysis, anonymisation, import_data, mo, processing


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Visits and visit details

    Each `visit` comprises one or more `visit_details`. Each `visit` is also associated with a `person`.
    """)
    return


@app.cell(hide_code=True)
def _(analysis, mo):
    mo.ui.matplotlib(axes=analysis.plot_visit_timeline())
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
def _(analysis, import_data, mo):

    mo.ui.table(
        analysis.list_datatypes_of_measurements(data_dir=import_data.RAW_DATA_DIR),
        selection=None,
        pagination=False
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Anonymising potentially identifiable information

    Potentially identifiable information includes:
    - [x] Date of Birth
    - [ ] All datetime fields:
        - [x] `vist_start_datetime`
        - [x] `visit_end_datetime`
        - [x] `visit_detail_start_datetime`
        - [x] `visit_detail_end_datetime`
        - [x] `measurement_datetime`
        - [x] `outcome_datetime`
    * Rare categorical values:
        - [x] `ethnicity`
        - [x] `religion`
        - [x] `preferred_language`
        - [ ] `background_diagnoses`: Note - the logic here is not yet developed. TBC.
    * Extreme continuous values:
        - [x] `height`
        - [x] `weight`
        - [x] `bmi`
    """)
    return


@app.cell
def _(import_data):
    patients = import_data.patients()
    visits = import_data.visits()

    # This is the timestamp we will use to anonymise datetime fields:
    timestamp_datum=visits.select(
        ['person_id', 'visit_id', 'visit_start_datetime']
    ).rename(
        {'visit_start_datetime': 'datum'}
    )

    return patients, timestamp_datum, visits


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Visits

    We do several steps for the visits data:
    1. Calculate age in months at the time of the visit, based on the person's date of birth and the visit start datetime.
    1. Anonymise by:
        1. Rounding age in months to the nearest whole month.
        2. Relativise timestamps [really it's only visit_end_datetime] to a datum (the first visit start datetime for each person).
        3. Truncate the visit start datetime to the month level, to reduce identifiability.
    """)
    return


@app.cell
def _(anonymisation, mo, patients, processing, timestamp_datum, visits):
    visits_relative_timestamps = visits.pipe(
        processing.calculate_age, 
        reference_date_column='visit_start_datetime',
        dates_of_birth=patients.select(['person_id', 'date_of_birth'])
    ).pipe(
        anonymisation.round_columns,
        columns_to_round=['age_months'],
        decimal_places=0
    ).pipe(
        anonymisation.relativise_timestamps,
        df_admission_datum=timestamp_datum,
        except_columns=['visit_start_datetime']
    ).pipe(
        anonymisation.truncate_timestamps,
        timestamp_columns='visit_start_datetime',
        resolution='month'

    ).rename(
        {'visit_end_datetime': 'visit_duration'}
    )

    mo.vstack([
        mo.md('### Raw visits data'),
        mo.ui.table(visits, selection=None, pagination=False),
        mo.md('### Visits data with age and anonymised timestamps'),
        mo.ui.table(visits_relative_timestamps, selection=None, pagination=False)
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Patients

    Now that we've used the date of birth to calculate age, we can remove it from the patients table.

    We also censor potentially identifiable information in the patients table, including rare categorical values.
    """)
    return


@app.cell
def _(anonymisation, mo, patients):
    patients_anonymised = patients.pipe(
        anonymisation.suppress_rare_categories,
        specifications=anonymisation.SUPPRESSION_CONFIG['person']
    ).drop(
        ['date_of_birth']
    )

    mo.vstack([
        mo.md('### Raw patients data'),
        mo.ui.table(
            patients, selection=None, pagination=False, 
            format_mapping={'imd_decile_version': '{:d}'.format}
        ),
        mo.md('### Anonymised patients data'),
        mo.ui.table(
            patients_anonymised, selection=None, pagination=False, 
            format_mapping={'imd_decile_version': '{:d}'.format}
        )
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Visit Details
    """)
    return


@app.cell
def _(anonymisation, import_data, mo, timestamp_datum):
    visit_details = import_data.visit_details()

    visit_details_relative_timestamps = visit_details.pipe(
        function=anonymisation.relativise_timestamps,
        df_admission_datum=timestamp_datum
    )

    mo.vstack([
        mo.md('### Raw underlying data'),
        mo.ui.table(
            visit_details,
            selection=None,
            pagination=False
        ),
        mo.md('### Relative timestamp anonymisation'),
        mo.ui.table(
            visit_details_relative_timestamps,
            selection=None,
            pagination=False
        ),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Outcomes
    """)
    return


@app.cell
def _(anonymisation, import_data, mo, timestamp_datum, visits):
    outcomes = import_data.outcomes()

    outcomes_relative_timestamps = outcomes.pipe(
        function=anonymisation.associate_visits_with_events,
        df_visits=visits,
        event_timestamp_column='event_datetime'
    ).pipe(
        function=anonymisation.relativise_timestamps,
        df_admission_datum=timestamp_datum
    )

    mo.vstack([
        mo.md('### Raw underlying data'),
        mo.ui.table(
            outcomes,
            selection=None,
            pagination=False
        ),
        mo.md('### Relative timestamp anonymisation'),
        mo.ui.table(
            outcomes_relative_timestamps,
            selection=None,
            pagination=False
        ),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Measurements

    ### General principles
    Here we only show the general principle for a single measurement type, but the same principles apply to all measurement types.
    """)
    return


@app.cell
def _(anonymisation, import_data, mo, timestamp_datum, visits):
    pulse_rate = import_data.measurement('pulse_rate')
    pulse_rate_relative_timestamps = pulse_rate.pipe(
        function=anonymisation.associate_visits_with_events,
        df_visits=visits,
        event_timestamp_column='measurement_datetime'
    ).pipe(
        function=anonymisation.relativise_timestamps,
        df_admission_datum=timestamp_datum
    )

    mo.vstack([
        mo.md('#### Raw underlying data'),
        mo.ui.table(
            pulse_rate,
            selection=None,
            pagination=False, 
            format_mapping={'measurement_concept_id': '{:d}'.format}
        ),
        mo.md('#### Relative timestamp anonymisation'),
        mo.ui.table(
            pulse_rate_relative_timestamps,
            selection=None,
            pagination=False, 
            format_mapping={'measurement_concept_id': '{:d}'.format}
        ),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Clipping extreme values

    * Height is set to a maximum of 1.9m
    * BMI is set to a maximum of 50
    * Weight is set to a maximum of 150kg
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Height
    """)
    return


@app.cell
def _(anonymisation, import_data, mo, timestamp_datum, visits):
    height = import_data.measurement('height')
    height_relative_timestamps = height.pipe(
        function=anonymisation.associate_visits_with_events,
        df_visits=visits,
        event_timestamp_column='measurement_datetime'
    ).pipe(
        function=anonymisation.relativise_timestamps,
        df_admission_datum=timestamp_datum
    ).pipe(
        function=anonymisation.clip, 
        column='value_source_value',
        max_value=1.9
    )

    mo.vstack([
        mo.md('#### Raw underlying data'),
        mo.ui.table(
            height,
            selection=None,
            pagination=False, 
            format_mapping={'measurement_concept_id': '{:d}'.format}, 
        ),
        mo.md('#### Relative timestamp anonymisation'),
        mo.ui.table(
            height_relative_timestamps,
            selection=None,
            pagination=False, 
            format_mapping={'measurement_concept_id': '{:d}'.format}
        ),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Weight
    """)
    return


@app.cell
def _(anonymisation, import_data, mo, timestamp_datum, visits):
    weight = import_data.measurement('weight')
    weight_relative_timestamps = weight.pipe(
        function=anonymisation.associate_visits_with_events,
        df_visits=visits,
        event_timestamp_column='measurement_datetime'
    ).pipe(
        function=anonymisation.relativise_timestamps,
        df_admission_datum=timestamp_datum
    ).pipe(
        function=anonymisation.clip,
        column='value_source_value',
        max_value=150
    )   

    mo.vstack([
        mo.md('#### Raw underlying data'),
        mo.ui.table(
            weight,
            selection=None,
            pagination=False, 
            format_mapping={'measurement_concept_id': '{:d}'.format}
        ),
        mo.md('#### Relative timestamp anonymisation'),
        mo.ui.table(
            weight_relative_timestamps,
            selection=None,
            pagination=False, 
            format_mapping={'measurement_concept_id': '{:d}'.format}
        ),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### BMI
    """)
    return


@app.cell
def _(anonymisation, import_data, mo, timestamp_datum, visits):
    bmi = import_data.measurement('body_mass_index')
    bmi_relative_timestamps = bmi.pipe(
        function=anonymisation.associate_visits_with_events,
        df_visits=visits,
        event_timestamp_column='measurement_datetime'
    ).pipe(
        function=anonymisation.relativise_timestamps,
        df_admission_datum=timestamp_datum
    ).pipe(
        function=anonymisation.clip,
        column='value_source_value',
        max_value=50
    )

    mo.vstack([
        mo.md('#### Raw underlying data'),
        mo.ui.table(
            bmi.drop('measurement_concept_id'),
            selection=None,
            pagination=False, 
            format_mapping={'measurement_concept_id': '{:d}'.format}
        ),
        mo.md('#### Relative timestamp anonymisation'),
        mo.ui.table(
            bmi_relative_timestamps.drop('measurement_concept_id'),
            selection=None,
            pagination=False, 
            format_mapping={'measurement_concept_id': '{:d}'.format}
        ),
    ])
    return


if __name__ == "__main__":
    app.run()
