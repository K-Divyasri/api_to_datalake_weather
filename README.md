# Weather Data Lake

A Python package with separate extract, transform, and load modules, config,
logging, tests, and a SQL file to query the result.

It pulls current weather for ten cities from the free
[Open-Meteo API](https://open-meteo.com/) (no API key) and writes it into a
date-partitioned Parquet **data lake**. Run it on a schedule and the lake grows
one slice every hour.

## What it produces

```
data/
├── raw/weather/date=2026-06-29/hour=14/london.json   <- every API response, untouched
└── lake/weather/year=2026/month=06/day=29/           <- cleaned, columnar, queryable
        weather_20260629T14.parquet
```

Two layers on purpose: `raw/` is the data exactly as it arrived, so it can
always be re-processed. `lake/` is the clean Parquet people actually query.
That split is the "medallion" idea (bronze to silver) in miniature.

## Run it

```powershell
python -m venv .venv ; .\.venv\Scripts\Activate.ps1   # Windows PowerShell
pip install -r requirements.txt

python run_pipeline.py        # one collection cycle
pytest                        # the tests pass without touching the network
```

On macOS/Linux the only difference is activating the venv:
`source .venv/bin/activate`.

Run `python run_pipeline.py` a few times (or wait for the hourly schedule) to
build up some history, then query it:

```powershell
duckdb
.read sql/analysis.sql
```

## How the code is laid out

```
weather_lake/           the package, one job per file
├── cities.py           the 10 cities (name, country, lat, lon) as data
├── config.py           every setting in one place (paths, API, timeouts)
├── extract.py          call the API (with retries), save the raw JSON
├── transform.py        flatten nested JSON into flat, typed rows (a DataFrame)
├── load.py             write Hive-partitioned Parquet; idempotent
├── pipeline.py         extract -> transform -> load, with per-city error isolation
└── __main__.py         `python -m weather_lake`
run_pipeline.py         `python run_pipeline.py` (same thing, friendlier)
sql/analysis.sql        DuckDB queries over the lake (window functions, pruning)
tests/                  pytest, transform logic and load idempotency
requirements.txt
.env.example            copy to .env to override settings (no secrets needed)
.gitignore
```

## The three ideas this project proves

1. **Ingesting from a REST API**: `requests`, JSON, retries, timeouts. Real
   sources are flaky, so the code treats a failed city as a warning, not a crash.
2. **Data-lake layout**: Hive-style `year=/month=/day=` partitions. A query that
   filters on a date only reads the folders it needs ("partition pruning").
3. **Parquet over CSV**: columnar, compressed, typed. `load.py` writes it,
   `sql/analysis.sql` shows DuckDB querying it in place with no database server.

And quietly, a fourth: **idempotency**. The Parquet filename is keyed to the
collection hour, so re-running an hour overwrites rather than duplicates. The
test `test_rerunning_same_hour_is_idempotent` proves it.

## Resume line

> "Built an automated API-ingestion pipeline storing partitioned Parquet in a
> data-lake layout, scheduled hourly on GitHub Actions, with retry handling,
> idempotent writes, and DuckDB SQL access."

Every word of that is in this repo. The `hosting/` guide turns the last
clause (the schedule) on.
