# =============================================================================
# STREAMING INGESTION — OpenAlex API → Kinesis Data Firehose → S3
# =============================================================================
# This Lambda function implements the STREAMING ingestion pattern.
# It calls the OpenAlex REST API, paginates through recent academic papers,
# and pushes each batch of JSON records to Kinesis Data Firehose. Firehose
# buffers the records and delivers them to S3 (raw/openalex/) in near-real-time.
#
# Deployed as: Lambda function "openalex-ingestion"
# Triggered by: Step Functions (StreamingIngest_OpenAlex state) or EventBridge schedule
# =============================================================================

import json
import boto3
import urllib.request
import urllib.parse
from datetime import datetime, timedelta

FIREHOSE_STREAM_NAME = "firehose-stream"
TARGET_RECORDS = 200
PAGE_SIZE = 50

# get works from last 30 days
today = datetime.utcnow().date()
from_date = (today - timedelta(days=30)).isoformat()
to_date = today.isoformat()


def fetch_page(cursor):
    """fetch a page of results from OpenAlex API"""
    params = {
        "filter": f"from_publication_date:{from_date},to_publication_date:{to_date}",
        "per-page": PAGE_SIZE,
        "cursor": cursor,
        "select": "id,title,publication_date,doi,authorships,concepts,open_access,cited_by_count",
        "mailto": "student@example.com",
    }
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)

    with urllib.request.urlopen(url, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def send_to_firehose(client, records):
    """send records to firehose in batches of 500"""
    sent = 0
    batch = []

    for record in records:
        payload = json.dumps(record) + "\n"
        batch.append({"Data": payload.encode("utf-8")})

        if len(batch) == 500:
            client.put_record_batch(
                DeliveryStreamName=FIREHOSE_STREAM_NAME,
                Records=batch
            )
            sent += len(batch)
            batch = []

    # send remaining
    if batch:
        client.put_record_batch(
            DeliveryStreamName=FIREHOSE_STREAM_NAME,
            Records=batch
        )
        sent += len(batch)

    return sent


def lambda_handler(event, context):
    firehose = boto3.client("firehose")
    all_records = []
    cursor = "*"

    print(f"Fetching works from {from_date} to {to_date}")

    # keep paginating until we hit 200 records or run out of results
    while len(all_records) < TARGET_RECORDS:
        data = fetch_page(cursor)
        works = data.get("results", [])

        if not works:
            break

        all_records.extend(works)
        print(f"Got {len(works)} works, total: {len(all_records)}")

        next_cursor = data.get("meta", {}).get("next_cursor")
        if not next_cursor:
            break
        cursor = next_cursor

    # trim in case the last page pushed us over 200
    all_records = all_records[:TARGET_RECORDS]

    total_sent = send_to_firehose(firehose, all_records)

    result = {
        "status": "success",
        "records_ingested": total_sent,
        "date_range": f"{from_date} to {to_date}",
    }
    print("Done:", json.dumps(result))
    return result
