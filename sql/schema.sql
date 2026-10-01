-- =========================================
-- BRONZE LAYER — raw, immutable API responses
-- =========================================

CREATE TABLE IF NOT EXISTS raw_rates (
    fetch_date TEXT NOT NULL,
    base_currency TEXT NOT NULL,
    raw_json TEXT NOT NULL,
    inserted_at TEXT NOT NULL DEFAULT (datetime('now'))
);


-- =========================================
-- SILVER LAYER — cleaned, validated, typed
-- =========================================
CREATE TABLE IF NOT EXISTS cleaned_rates (
    date TEXT NOT NULL,
    base_currency TEXT NOT NULL,
    target_currency TEXT NOT NULL,
    exchange_rate REAL NOT NULL CHECK (exchange_rate > 0),
    load_timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(date, base_currency, target_currency)
);


-- =========================================
-- GOLD LAYER — dimensions
-- =========================================
CREATE TABLE IF NOT EXISTS dim_currencies (
    currency_code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    symbol TEXT,
    country TEXT
);

CREATE TABLE IF NOT EXISTS dim_dates (
    date TEXT PRIMARY KEY,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    day INTEGER NOT NULL,
    is_weekday INTEGER NOT NULL
);

-- =========================================
-- GOLD LAYER — fact table
-- =========================================
CREATE TABLE IF NOT EXISTS aggregated_rates (
    date TEXT NOT NULL,
    base_currency TEXT NOT NULL,
    target_currency TEXT NOT NULL,
    exchange_rate REAL NOT NULL,
    rate_change_pct REAL,
    avg_7day REAL,
    FOREIGN KEY (target_currency) REFERENCES dim_currencies(currency_code),
    FOREIGN KEY (date) REFERENCES dim_dates(date)
);