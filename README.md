# Advanced Data Engineering AE1

Coursework for LDSCI7229. Serverless data pipeline on AWS that ingests two datasets (one batch, one streaming), cleans them, catalogues them, and queries them with Athena.

## Datasets

- **US DOT Border Crossing Data** - ~273k rows of border crossing counts going back to 1996, static CSV
- **OpenAlex** - academic papers from a REST API, nested JSON, pulled via Lambda + Firehose

## How it works

Both datasets land in an S3 data lake (`raw/`), get cleaned by Glue ETL into Parquet (`cleaned/`), then get registered in the Glue Data Catalog so Athena can query them. Step Functions runs the whole thing end to end with one click. DynamoDB logs every run.

Everything runs in the AWS Academy Learner Lab (us-east-1, LabRole).

## Repo structure

- `task1-ingestion/` - Lambda function, Glue ETL scripts, Step Functions definition
- `task2-warehouse/` - Athena SQL queries, Glue crawler configs
- `task3-visualisation/` - Extended workflow JSON, Athena export query
- `screenshots/` - All screenshots organised by task (task1-*, task2-*, task3-*)
- `docs/` - The report (markdown + docx)

> **Note on screenshots.** Some screenshots in `screenshots/` have small black rectangles covering identifying information (AWS Academy username, 12-digit Account ID, ARNs containing the account ID, the bucket suffix that included my GitHub username, and my email where it appears in code). The screenshots are otherwise unedited. Code and configuration in this repo do not contain any of the redacted values.

## Running the pipeline

Open Step Functions, select `data-pipeline`, click Start execution with `{}`, and wait for all states to go green (~4 min).

## Links

- Border Crossings: https://data.bts.gov/Research-and-Statistics/Border-Crossing-Entry-Data/keg4-3bc2
- OpenAlex: https://docs.openalex.org/
