import sqlite3
import os
from dotenv import load_dotenv
from extract import fetch_rates
import json
from datetime import date, timedelta
import logging
logger = logging.getLogger(__name__)


def create_table(db_path, schema_path):
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        with open(schema_path, 'r') as f:
            cursor.executescript(f.read())


def get_latest_bronze_date(db_path):
    with sqlite3.connect(db_path) as conn:
        result = conn.execute(
            "SELECT MAX(json_extract(raw_json, '$.date')) FROM raw_rates"
        ).fetchone()[0]
    return result


def load_bronze(db_path, base_curr):
    latest = get_latest_bronze_date(db_path)
    if latest:
        start = date.fromisoformat(latest) + timedelta(days=1)
    else:
        start = date.today() - timedelta(days=int(os.getenv("BACKFILL_DAYS")))

    if start > date.today():
        print(f"Bronze is up to date (latest: {latest}). Nothing to fetch.")
        return 0
    
    content = fetch_rates(str(start))

    if not content:
        print(f"No new rates since {latest} (current date, weekend or holiday). Skipping.")
        return 0

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        for data in content:
            query = ''' INSERT INTO raw_rates (fetch_date, base_currency, raw_json)
                VALUES(?, ?, ?) '''
            cursor.execute(query, (str(date.today()), base_curr, json.dumps(data)))

    logger.info("Bronze: fetched %d records, wrote %d rows", len(content), len(content))
    return len(content)


if __name__ == "__main__":
    load_dotenv()
    DB_PATH = os.getenv("DB_PATH")
    SCHEMA_PATH = os.getenv("SCHEMA_PATH")
    BASE_CURRENCY = os.getenv("BASE_CURRENCY")
    create_table(DB_PATH, SCHEMA_PATH)
    load_bronze(DB_PATH, BASE_CURRENCY)