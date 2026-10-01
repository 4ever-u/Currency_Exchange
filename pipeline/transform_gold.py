import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import os
import logging
logger = logging.getLogger(__name__)

load_dotenv()
DB_PATH = os.getenv("DB_PATH")


def build_dim_currencies():
    return pd.DataFrame([
        {"currency_code": "USD", "name": "US Dollar", "symbol": "$", "country": "United States"},
        {"currency_code": "EUR", "name": "Euro", "symbol": "€", "country": "Eurozone"},
        {"currency_code": "GBP", "name": "British Pound", "symbol": "£", "country": "United Kingdom"},
        {"currency_code": "RUB", "name": "Russian Ruble", "symbol": "₽", "country": "Russia"},
        {"currency_code": "UZS", "name": "Uzbekistani Som", "symbol": "so'm", "country": "Uzbekistan"},
    ])


def build_dim_dates(dates):

    unique_dates = pd.to_datetime(pd.Series(dates).unique())

    dim = pd.DataFrame({"date": unique_dates})
    dim["year"] = dim["date"].dt.year
    dim["month"] = dim["date"].dt.month
    dim["day"] = dim["date"].dt.day
    dim["is_weekday"] = dim["date"].dt.dayofweek < 5
    dim["is_weekday"] = dim["is_weekday"].astype(int)

    return dim


def compute_aggregated_rates(silver_df):
    df = silver_df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["base_currency", "target_currency", "date"])
    grouped = df.groupby(["base_currency", "target_currency"])["exchange_rate"]
    df["rate_change_pct"] = round(grouped.pct_change() * 100, 2)
    df["avg_7day"] = grouped.transform(lambda x: x.rolling(7, min_periods=1).mean()).round(2)

    return df


def load_gold(aggregated_df, dim_currencies_df, dim_dates_df, db_path):
    """
    Writes all three Gold tables to the database.
    if_exists='replace' means Gold is fully rebuilt each run, not appended to —
    this is intentional: Gold should always reflect a fresh recompute from
    Silver, not accumulate stale duplicate calculations over time.
    """
    with sqlite3.connect(db_path) as conn:
        aggregated_to_write = aggregated_df.copy()
        aggregated_to_write["date"] = aggregated_to_write["date"].dt.strftime("%Y-%m-%d")
        aggregated_to_write.to_sql("aggregated_rates", conn, if_exists="replace", index=False)
    
        dim_currencies_df.to_sql("dim_currencies", conn, if_exists="replace", index=False)

        dim_dates_to_write = dim_dates_df.copy()
        dim_dates_to_write["date"] = dim_dates_to_write["date"].dt.strftime("%Y-%m-%d")
        dim_dates_to_write.to_sql("dim_dates", conn, if_exists="replace", index=False)

    logger.info(
        "Gold: wrote %d aggregated_rates, %d dim_currencies, %d dim_dates rows",
        len(aggregated_df), len(dim_currencies_df), len(dim_dates_df),
    )
    return len(aggregated_df)


if __name__ == "__main__":
    from transform_silver import extract_from_bronze, clean_rates

    raw_df = extract_from_bronze(DB_PATH)
    silver_df = clean_rates(raw_df)

    dim_currencies_df = build_dim_currencies()
    dim_dates_df = build_dim_dates(silver_df["date"])
    aggregated_df = compute_aggregated_rates(silver_df)

    load_gold(aggregated_df, dim_currencies_df, dim_dates_df, DB_PATH)