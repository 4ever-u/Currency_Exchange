import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL")
BASE_CURRENCY = os.getenv("BASE_CURRENCY")
TARGET_CURRENCIES = os.getenv("TARGET_CURRENCIES")

def fetch_rates(start_date = None):
    parameters = {
        "base": BASE_CURRENCY,
        "quotes": TARGET_CURRENCIES
    }

    if start_date:
        parameters["from"] = start_date

    response = requests.get(url=API_URL, params=parameters)
    content = response.json()
    return content