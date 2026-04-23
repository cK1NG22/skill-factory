# Client Skill Spec — csv-to-parquet

## Company
acme

## Skill slug
csv-to-parquet

## One-line description
Converts a .csv file to a Parquet file preserving column types.

## Trigger phrases
- "csv to parquet"
- "convert this csv to parquet"
- "make a parquet from csv"
- "render csv as parquet"
- "export as parquet"

## Inputs
A path to a `.csv` file.

## Outputs
A `.parquet` file at `~/Claude/csv-to-parquet/<input-stem>.parquet`.

## Happy-path walkthrough
Read the input CSV and write it back out as Parquet.

## Success signals
- The output parquet file exists at the expected path.
- `file <output-path>` reports a Parquet document.

## Failure modes
- **Input file missing** → fail-fast with exit code 1.
- **Malformed CSV** → fail-fast with a specific error naming the bad row.

## Existing skills to reuse
None
