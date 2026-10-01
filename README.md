# Currency Exchange Pipeline

A small data pipeline that pulls daily exchange rates from the [Frankfurter API](https://frankfurter.dev) (v2) and stores them in SQLite using a Medallion architecture:

| Layer  | Table(s)                                                | Contents                                            |
| ------ | ------------------------------------------------------- | --------------------------------------------------- |
| Bronze | `raw_rates`                                           | Raw API responses, stored as-is (JSON)              |
| Silver | `cleaned_rates`                                       | Validated, typed, de-duplicated rates               |
| Gold   | `aggregated_rates`, `dim_currencies`, `dim_dates` | Daily change %, 7-day average, and dimension tables |

Base currency is USD. Targets are UZS, RUB, EUR and GBP (configurable in `.env`).

## Project structure

```
.
├── pipeline/
│   ├── extract.py          # API call with retries (tenacity)
│   ├── load_bronze.py      # incremental load into Bronze
│   ├── transform_silver.py # cleaning and validation
│   ├── transform_gold.py   # aggregates and dimensions
│   └── scheduler.py        # runs the pipeline once or daily
├── sql/schema.sql          # table definitions
├── data/                   # SQLite database (git-ignored)
├── requirements.txt
└── .env                    # configuration (git-ignored)
```

## Setup

Requires Python 3.9 or newer. Run all commands from the project root.

1. Create and activate a virtual environment:
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   ```
2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
3. Create the data folder:
   ```powershell
   mkdir data
   ```
4. Create a `.env` file in the project root:
   ```
   DB_PATH=data/currency_exchange.db
   SCHEMA_PATH=sql/schema.sql
   API_URL=https://api.frankfurter.dev/v2/rates
   BASE_CURRENCY=USD
   TARGET_CURRENCIES=UZS,RUB,EUR,GBP
   BACKFILL_DAYS=730
   ```

The Frankfurter API needs no API key.

## Running the backfill

The backfill loads historical rates the first time, or after you reset Bronze. When Bronze is empty, the pipeline fetches the last `BACKFILL_DAYS` days (730 by default, about two years):

```powershell
python pipeline/scheduler.py --once
```

This creates the tables, loads the history into Bronze, and builds Silver and Gold.

To redo the backfill from scratch, empty Bronze first and run the command again:

```powershell
python -c "import sqlite3; c = sqlite3.connect('data/currency_exchange.db'); c.execute('DELETE FROM raw_rates'); c.commit()"
python pipeline/scheduler.py --once
```

## Running the daily pipeline

**Run once, right now:**

```powershell
python pipeline/scheduler.py --once
```

**Run on a schedule:**

```powershell
python pipeline/scheduler.py
```

This keeps running and triggers the pipeline every day at **08:00 Tashkent time (UTC+5), which is 03:00 UTC**. The timezone is set explicitly, so the schedule is correct regardless of the machine's local timezone. Leave the terminal open; if the process stops, no runs happen.

### Why the `schedule` library

I chose [`schedule`](https://schedule.readthedocs.io) over APScheduler because the job is a single daily task and `schedule` needs only a few readable lines and no extra services.

## How it works

- **Incremental loading:** before fetching, the pipeline reads the latest rate date already in Bronze and requests only newer dates. If nothing new exists (a weekend or holiday, or Bronze is already current), it logs the reason and skips without failing.
- **Error handling:** API calls retry up to 3 times with exponential backoff (`tenacity`). A failed run is logged with its traceback and does not stop the scheduler.
- **Data quality (Silver):** rows with missing values, rates of zero or below, and duplicates are dropped and counted in a warning. The run fails with an error if no valid rows remain.
- **Rebuilds:** Silver and Gold are rebuilt from Bronze on every run, so their row counts are the full table size. Bronze only appends new rows.

## Logging

Logs go to the console and to `pipeline.log` in the project root. Each run reports what was fetched, how many rows were written per layer, and any skipped or invalid records. A normal run ends with a line like:

```
2026-10-01 08:00:04 INFO scheduler: Pipeline complete: Bronze +4 new rows, Silver 32 rows, Gold 32 rows
```
