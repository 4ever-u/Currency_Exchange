import requests
import os
from dotenv import load_dotenv
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_sleep_log

logger = logging.getLogger(__name__)

load_dotenv()

API_URL = os.getenv("API_URL")
BASE_CURRENCY = os.getenv("BASE_CURRENCY")
TARGET_CURRENCIES = os.getenv("TARGET_CURRENCIES")

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=30),
    retry=retry_if_exception_type(requests.RequestException),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)

def fetch_rates(start_date = None):
    parameters = {
        "base": BASE_CURRENCY,
        "quotes": TARGET_CURRENCIES
    }

    if start_date:
        parameters["from"] = start_date

    response = requests.get(url=API_URL, params=parameters, timeout=30)
    response.raise_for_status()
    content = response.json()
    return content