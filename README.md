# BEACON DATA STRUCTURE

This project creates sample data to demonstrate the intended data structure to be provided by collaborating sites to the BEACON project. 

For an interactive version of the loading and anonymisation of the data, see the [demonstration notebook](https://molab.marimo.io/github/ucl-paediatrics/beacon-data-structure/blob/main/demonstration.py).

## Data Dictionary

This data dictionary defines the *output* dictionary intended to be provided to BEACON. 

### PERSON table
| Field name | Data type | Definition | Anonymisation Steps |
| ---------- | --------- | ---------- | ------------------- |
| `person_id` | string | Unique pseudonymous patient identifier | None |
| `gender` | string | Gender or sex as defined locally. <br>Preferred options are 'M', 'F', 'Other', null for unknown/not recorded. | None |
| `ethnicity` | string <br> (single character) | Ethnicity as defined by in MHS001 (16+1 categories)<br>Null/None for 'Not Known' (99) or missing data.<br>This is distinct from 'Not Stated' ('Z') which records a positive response to the question rather than missing data. <br> See [NHS Digital](https://digital.nhs.uk/data-and-information/data-collections-and-data-sets/data-sets/mental-health-services-data-set/submit-data/data-quality-of-protected-characteristics-and-other-vulnerable-groups/ethnicity) for definitions | Amalgamate rare categories in to 'Y' <br>(unused symbol in underlying ontology) |
| `preferred_language` | string | As locally defined. <br>Null/None for unknown or missing data. | Amalgamate rare categories in to 'Other' |
| `religion` | string | As locally defined. <br>Null/None for unknown or missing data. | Amalgamate rare categories in to 'Other' |
| `imd_decile` | integer <br> (1-10) | Decile of index of multiple deprivation, based on patient postcode. | None |
| `imd_decile_version` | ['2019', '2025'] | Version of the IMD index used to generate `imd_decile`. <br> Should be either '2019' or '2025', please contact study team if other version used. | None |

### Visits Table
| Field name | Data type | Definition | Anonymisation Steps |
| ---------- | --------- | ---------- | ------------------- |
| `visit_id` | string    | Unique identifier for this visit | None |
| `person_id`| string    | Foreign Key to Person table | None |
| `age_at_presentation` | integer | Age in months on `visit_start_datetime` | Round down |
| `visit_start_datetime` | datetime | Start of the period of care: presentation to emergency department or admission to ward | Censor to midnight on 1st of month, once used as datum for timings |
| `visit_end_datetime`| integer | Timestamp of discharge, transferred out, or mortality (seconds since `visit_start_datetime`). | Converted to duration; original timestamp discarded  |
| `admission_type` | ['Elective', 'Emergency'] | Category of admission | None |
| `visit_type` | ['Inpatient', 'Day Case'] | Type of visit. Note that outpatient visits should not be included | None |
| `background_diagnoses` | list[int] | Existing diagnoses at the point of admission (coded SNOMED diagnoses) | Amalgamation of rare diagnoses with < 20 entries in to higher SNOMED category. |

Discussion with contributing centres regarding diagnosis, specifically:
* Provision in ICD-10 format if SNOMED not available
* Precise anonymisation strategy based on prevalent demographics

### Visit Details Table
Each visit (see above) comprises one or more ward stays. Each ward stay is defined by a start and end time, and the ward in which the patient was located.

| Field name | Data type | Definition | Anonymisation Steps |
| ---------- | --------- | ---------- | ------------------- |
| `person_id` | string | Foreign Key to Person table | None |
| `visit_id` | string | Foreign Key to Visits table | None |
| `care_site` | string | Ward name or other identifier | None |
| `visit_detail_start_datetime` | integer | Timestamp of the start of the stay on the particular ward (seconds since `visit_start_datetime`) | Converted to duration; original timestamp discarded |
| `visit_detail_end_datetime` | integer | Timestamp of the end of the stay on the particular ward (seconds since `visit_start_datetime`) | Converted to duration; original timestamp discarded |
 
### Measurements Tables

Unlike the previous tables, measurements are not defined in a single table. Instead, each measurement type is defined in a separate table, with the table name indicating the measurement type. Each table contains the following fields:

| Field name | Data type | Definition |
| ---------- | --------- | ---------- |
| `person_id` | string | Foreign Key to Person table |
| `measurement_datetime` | integer | Timestamp of the measurement (seconds relative to `visit_start_datetime`) |
| `measurement_concept_id` | integer | Concept ID of the measurement type (OMOP standard if available) |
| `measurement_concept_name` | string | Concept name of the measurement type (human-readable) |
| `value_source_value` | variable, depending on measurement | Value of the measurement, as recorded in the source data |

#### Measurement Types

Concept ID is the OMOP standard concept ID for the measurement type, if available.

None of the measurements in the table below require any anonymisation steps, as they are either numerical or categorical with no identifiable information considered to be possible. Care should, however, be taken with string values to ensure that PII is not inadvertently included in the source data. It is considered that a quick manual review is sufficient to ensure that this is the case.

| Measurement Type | Concept ID | Data Type | Definition |
| ---------------- | ---------- | --------- | ---------- |
| Body Temperature | 4302666 | float | Body temperature in degrees Celsius |
| Capillary Filling | 4048731 | string | Capillary refill time in seconds, as recorded in the source data. Likely to be non-numerical (e.g. '2-3' or '>5') |
| Delivered Oxygen Flow Rate | 4141684 | float | Oxygen flow rate in litres per minute |
| Difficulty Breathing | 4041664 | string | Difficulty breathing as recorded in the source data. Expected to be a list of signs present, separated by semicolons e.g. "Nasal Flaring;Head Bobbing". <br>May be empty, indicating assessment done with no signs present |
| Hemoglobin Saturation With Oxygen | 4011919 | integer | Oxygen saturation in percentage (0-100) |
| Inspired Oxygen Concentration | 4353936 | float | Inspired oxygen concentration as a fraction (0-1) |
| Ventilatory Support | 44791135 | string | Ventilatory support mode e.g. 'Low Flow' |
| Pulse Rate | 4301868 | integer | Heart rate in beats per minute |
| Respiratory Rate | 4313591 | integer | Respiratory rate in breaths per minute |
| Systolic Blood Pressure | 4152194 | integer | Systolic blood pressure in mmHg |
| Diastolic Blood Pressure | 4154790 | integer | Diastolic blood pressure in mmHg |
| Mean Blood Pressure | 4239021 | integer | Mean blood pressure in mmHg. If not available, will be imputed from SBP and DBP |
| Blood Pressure Derogation Reason | <none> | string | Reason for derogation of blood pressure measurement, if applicable. <br>Expected options are: <br>'Not Attempted (no concern)' ('NCO') <br>'Unsuccessful (no concern)' ('U0') <br>"Unsuccessful (concern)' ('U0')|
| Glasgow Coma Scale Motor Response Subscore | 4083352 | integer | Glasgow Coma Scale motor score (1-6); null for letter scores (derogations) |
| Glasgow Coma Scale Verbal Response Subscore | 4084912 | integer | Glasgow Coma Scale verbal score (1-5); null for letter scores (derogations) |
| Glasgow Coma Scale Eye Opening Subscore | 4084277 | integer | Glasgow Coma Scale eye opening score (1-4); null for letter scores (derogations) |
| Pain Score | 4022240 | string | Pain score. Several options - check with local team |
| State of Consciousness and Awareness | 449159002 | string | Several options, including AVPU - check with local team |
| Patient Unavailable | 4136469 | string | Reason for patient being unavailable for a missed set of observations e.g. “Away from Ward”|
| Blood Glucose Level | 40329577 | float | Blood glucose level in mmol/L |
| C-Reactive Protein | 3035320 | float | C-reactive protein level in mg/L |
| New Suspicion of Clinical Shock | <none> | binary | Binary indicator of whether there is a new suspicion of clinical shock as defined in NPEWS |
| Clinical Concern | <none> | binary | Binary indicator of whether there is a new clinical concern as defined in NPEWS |
| Parental Concern | <none> | binary | Binary indicator of whether there is a new parental concern as defined in NPEWS: {Worse, Same, Better, Parent/Carer Asleep, Unavailable} |


The following anthropometric measurements are also included in the dataset. For some of these measurements, extreme values may be considered to be identifiable, and so these measurements are subject to additional anonymisation steps.

| Measurement Type | Concept ID | Data Type | Definition | Anonymisation Steps |
| ---------------- | ---------- | --------- | ---------- | ------------------- |
| Height | 4302666 | float | Height in metres. Length considered synonymous for babies. | Clip to 1.9m if larger |
| Weight | 4099154 | float | Weight in kilograms | Clip to 150kg if larger |
| Body Mass Index | 4245997 | float | Body mass index in kg/m^2 | Clip to 50kg/m^2 if larger |


## Pseudonymisation steps

### Amalgamation of rare categories

For real data, indicated fields will be amalgamated in to 'Other' for categories with fewer than 20 patients. In this example dataset, amalgamation occurs for categories with fewer than 5 patients, to keep the dataset relatively small whilst demonstrating the procedure.

## Items to check with contributing centres

* Background diagnoses: Are these available in SNOMED format, or only ICD-10?
    * Is the timing of when the diagnosis was made available? If so, how is this recorded?
* Measurements:
    * Capillary Filling: How is this recorded? Is it a numerical value, a semi-numerical string, or a categorical value (e.g. 'Normal', 'Delayed')?
    * Difficulty Breathing: How is this recorded? Is it a list of signs? Which signs are recorded?
    * Ventilatory support: What modes are used and how are they recorded?
    * Pain score in local use
