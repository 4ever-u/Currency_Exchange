import requests
import os
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH")
SCHEMA_PATH = os.getenv("SCHEMA_PATH")
API_URL = os.getenv("API_URL")
BASE_CURRENCY = os.getenv("BASE_CURRENCY")
TARGET_CURRENCIES = os.getenv("TARGET_CURRENCIES")

def fetch_rates():
    parameters = {
        "base": BASE_CURRENCY,
        "quotes": TARGET_CURRENCIES
    }

    response = requests.get(url=API_URL, params=parameters)
    content = response.json()
    return content