# =============================================================================
# STREAMING ETL — OpenAlex JSON (delivered via Kinesis Data Firehose)
# =============================================================================
# This Glue job processes the STREAMING-ingested dataset. The OpenAlex JSON
# records were delivered to S3 (raw/openalex/) by Kinesis Data Firehose in
# near-real-time batches, triggered by the Lambda streaming ingestion function.
#
# Reads the nested JSON, flattens the structure (authors, institutions, etc.),
# and writes Parquet with Snappy compression to cleaned/openalex/.
#
# Deployed as: Glue job "openalex-etl"
# =============================================================================

import sys
import time
import boto3
import datetime
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import functions as F

args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

job_start_time = time.time()

# read all json files from openalex folder (firehose saves in nested date subfolders)
df_raw = spark.read.option("recursiveFileLookup", "true") \
                   .json("s3://ae1-data-lake/raw/openalex/")

print(f"Raw row count: {df_raw.count()}")
df_raw.printSchema()

# the openalex json is deeply nested (authors have institutions inside them etc.)
# so we need to pull out the bits we actually want into flat columns
df = df_raw.select(
    F.col("id").alias("work_id"),
    F.col("title"),
    F.col("publication_date"),
    F.col("cited_by_count"),
    F.col("open_access.is_oa").alias("is_open_access"),
    F.col("open_access.oa_status").alias("open_access_status"),

    # get author names as comma separated string
    F.array_join(
        F.transform(
            F.col("authorships"),
            lambda x: x["author"]["display_name"]
        ),
        ", "
    ).alias("author_names"),

    # get institution names
    F.array_join(
        F.array_distinct(
            F.flatten(
                F.transform(
                    F.col("authorships"),
                    lambda x: F.transform(
                        x["institutions"],
                        lambda inst: inst["display_name"]
                    )
                )
            )
        ),
        "; "
    ).alias("institution_names"),
)

# some records come back without a title or date, not useful for analysis
df = df.dropna(subset=["title", "publication_date"])

# make sure date is proper date type
df = df.withColumn(
    "publication_date",
    F.to_date(F.col("publication_date"), "yyyy-MM-dd")
)
df = df.dropna(subset=["publication_date"])

# cast to int
df = df.withColumn("cited_by_count", F.col("cited_by_count").cast("int"))

cleaned_df = df

print(f"Cleaned row count: {cleaned_df.count()}")
cleaned_df.printSchema()
cleaned_df.show(5, truncate=True)

# write parquet
cleaned_df.write.mode("overwrite") \
                .parquet("s3://ae1-data-lake/cleaned/openalex/")

print("done - output at cleaned/openalex/")

# log to dynamodb
job_end_time = time.time()
duration = round(job_end_time - job_start_time, 2)

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('pipeline-metadata')

table.put_item(
    Item={
        'job_id': 'glue-openalex-clean',
        'run_timestamp': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'source_file': 's3://ae1-data-lake/raw/openalex/',
        'records_processed': int(df_raw.count()),
        'records_cleaned': int(cleaned_df.count()),
        'processing_duration_seconds': str(duration),
        'status': 'SUCCESS'
    }
)

print(f"logged to dynamodb, took {duration}s")

job.commit()
