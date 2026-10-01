import os
from dotenv import load_dotenv
import time
import schedule

from load_bronze import load_bronze
from transform_silver import extract_from_bronze, clean_rates, load_silver
from transform_gold import build_dim_currencies, build_dim_dates, compute_aggregated_rates, load_gold

load_dotenv()
DB_PATH = os.getenv("DB_PATH")
BASE_CURRENCY = os.getenv("BASE_CURRENCY")


def run_pipeline():

    print("Step 1/4: Extracting and loading Bronze...")
    load_bronze(DB_PATH, BASE_CURRENCY)

    print("Step 2/4: Transforming Silver...")
    raw_df = extract_from_bronze(DB_PATH)
    cleaned_df = clean_rates(raw_df)
    load_silver(cleaned_df, DB_PATH)

    print("Step 3/4: Transforming Gold...")
    dim_currencies_df = build_dim_currencies()
    dim_dates_df = build_dim_dates(cleaned_df["date"])
    aggregated_df = compute_aggregated_rates(cleaned_df)
    load_gold(aggregated_df, dim_currencies_df, dim_dates_df, DB_PATH)

    print("Step 4/4: Pipeline complete.")


def main():
    schedule.every().day.at("08:00", "Asia/Tashkent").do(run_pipeline)
    # schedule.every(10).seconds.do(run_pipeline)       # to test whether the scheduler is working fine or not.
    print("Scheduler started. Next run:", schedule.next_run())
    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()