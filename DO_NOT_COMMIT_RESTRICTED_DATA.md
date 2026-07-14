# Do not commit restricted facility data

Do not commit any file containing facility-level identifiers, addresses, coordinates, or non-aggregated Baxtel records.

Examples of local-only files that must remain outside git:

- `facility_central_total_output.csv`
- `facility_central_combustion_diagnostic.csv`
- raw 403-facility analytical CSVs
- raw 675-facility universe CSVs
- files containing `full_address`, `latitude`, or `longitude` for individual facilities

The committed public layer should include only aggregate BA/state tables, figures, code, schemas, and cleared notebooks.
