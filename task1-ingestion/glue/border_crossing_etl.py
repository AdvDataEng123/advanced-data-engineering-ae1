# =============================================================================
# BATCH ETL — Border Crossing CSV (static dataset)
# =============================================================================
# This Glue job processes the BATCH-ingested dataset. The border crossing CSV
# was uploaded directly to S3 (raw/border_crossing_data.csv) as a one-time
# batch upload — no streaming, no API calls, no Firehose.
#
# Reads the raw CSV, cleans it (date parsing, type casting, null removal),
# and writes Parquet with Snappy compression to cleaned/border_crossing/.
#
# Deployed as: Glue job "border-crossing-etl"
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
from pyspark.sql.types import IntegerType

args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

job_start_time = time.time()

# read raw csv
raw_df = spark.read.option("header", "true") \
                   .option("inferSchema", "true") \
                   .csv("s3://ae1-data-lake/raw/border_crossing_data.csv")

print(f"Raw row count: {raw_df.count()}")

df = raw_df

# drop rows missing important columns
df = df.dropna(subset=["Port Name", "Date", "Value"])

# the csv has dates in different formats depending on the row,
# so we try a few and take whichever one works
df = df.withColumn(
    "Date",
    F.coalesce(
        F.to_date(F.col("Date"), "MM/yyyy"),
        F.to_date(F.col("Date"), "MMMM yyyy"),
        F.to_date(F.col("Date"), "yyyy-MM-dd"),
    )
)
df = df.dropna(subset=["Date"])

# cast value to int
df = df.withColumn("Value", F.col("Value").cast(IntegerType()))

# drop point column since we already have lat/long
if "Point" in df.columns:
    df = df.drop("Point")

cleaned_df = df

print(f"Cleaned row count: {cleaned_df.count()}")
cleaned_df.printSchema()

# write as parquet with snappy compression (default).
# overwrite mode so reruns don't create duplicates
cleaned_df.write.mode("overwrite") \
                .parquet("s3://ae1-data-lake/cleaned/border_crossing/")

print("done - output at cleaned/border_crossing/")

# log to dynamodb
job_end_time = time.time()
duration = round(job_end_time - job_start_time, 2)

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('pipeline-metadata')

table.put_item(
    Item={
        'job_id': 'glue-border-clean',
        'run_timestamp': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'source_file': 's3://ae1-data-lake/raw/border_crossing_data.csv',
        'records_processed': int(raw_df.count()),
        'records_cleaned': int(cleaned_df.count()),
        'processing_duration_seconds': str(duration),
        'status': 'SUCCESS'
    }
)

print(f"logged to dynamodb, took {duration}s")

job.commit()
