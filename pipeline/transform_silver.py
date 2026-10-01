import sqlite3
import json
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DB_PATH")

def extract_from_bronze(db_path):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        data = cursor.execute("SELECT * FROM raw_rates")
        content = data.fetchall()

    list_of_dicts = []
    for item in content:
        dict_data = {}
        dict_data["date"] = item[0]
        dict_data["base_currency"] = item[1]
        item_dict = json.loads(item[2])
        dict_data["target_currency"] = item_dict["quote"]
        dict_data["exchange_rate"] = item_dict["rate"]
        list_of_dicts.append(dict_data)

    return pd.DataFrame(list_of_dicts)


def clean_rates(df):
    df = df.dropna()
    df = df.drop_duplicates(subset=["date", "base_currency", "target_currency"])    
    df['date'] = df['date'].astype("datetime64[us]")
    df['exchange_rate'] = df['exchange_rate'].astype("float64").round(2)
    df = df[df["exchange_rate"] > 0]
    return df

def load_silver(df, db_path):
    df_to_write = df.copy()
    df_to_write["date"] = df_to_write["date"].dt.strftime("%Y-%m-%d")

    with sqlite3.connect(db_path) as conn:
        df_to_write.to_sql("cleaned_rates", conn, if_exists="replace", index=False)


    
if __name__ == "__main__":
    raw_df = extract_from_bronze(DB_PATH)
    cleaned_df = clean_rates(raw_df)
    load_silver(cleaned_df, DB_PATH)