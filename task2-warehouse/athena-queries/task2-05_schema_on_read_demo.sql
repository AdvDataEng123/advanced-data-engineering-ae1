-- Demonstrates schema-on-read — Athena reads schema from Glue Catalog at query time
-- The data sits as raw Parquet files in S3, schema applied on read
DESCRIBE border_crossing;

-- Full table definition including S3 location, format, compression
SHOW CREATE TABLE border_crossing;
