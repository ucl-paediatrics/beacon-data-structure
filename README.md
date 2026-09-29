# BEACON DATA STRUCTURE

This project creates sample data to demonstrate the intended data structure to be provided by collaborating sites to the BEACON project. 

## Data Dictionary

This data dictionary defines the *output* dictionary intended to be provided to BEACON. 

### PERSON table
| Field name | Data type | Definition | Anonymisation Steps |
| ---------- | --------- | ---------- | ------------------- |
| `person_id` | string | Unique pseudonymous patient identifier | None |
| `gender` | string | Gender or sex as defined locally. <br>Preferred options are 'M', 'F', 'Other', null for unknown/not recorded. | None |
| `ethnicity` | string <br> (single character) | Ethnicity as defined by in MHS001 (16+1 categories)<br>Null/None for 'Not Known' (99) or missing data.<br>This is distinct from 'Not Stated' ('Z') which records a positive response to the question rather than missing data. <br> See [NHS Digital](https://digital.nhs.uk/data-and-information/data-collections-and-data-sets/data-sets/mental-health-services-data-set/submit-data/data-quality-of-protected-characteristics-and-other-vulnerable-groups/ethnicity) for definitions | Amalgamate rare categories in to 'Other' |
| `preferred_language` | string | As locally defined. <br>Null/None for unknown or missing data. | Amalgamate rare categories in to 'Other' |
| `religion` | string | As locally defined. <br>Null/None for unknown or missing data. | Amalgamate rare categories in to 'Other' |
| `imd_decile` | integer <br> (1-10) | Decile of index of multiple deprivation, based on patient postcode. | None |
| `imd_decile_version` | ['2019', '2025'] | Version of the IMD index used to generate `imd_decile`. <br> Should be either '2019' or '2025', please contact study team if other version used. | None |



## Pseudonymisation steps

### Amalgamation of rare categories

For real data, indicated fields will be amalgamated in to 'Other' for categories with fewer than 20 patients. In this example dataset, amalgamation occurs for categories with fewer than 5 patients, to keep the dataset relatively small whilst demonstrating the procedure.