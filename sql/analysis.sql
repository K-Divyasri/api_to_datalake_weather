-- Querying the weather data lake with DuckDB
-- ---------------------------------------------------------------------------
-- DuckDB reads partitioned Parquet straight off disk — no server, no load step.
-- Run these after you've collected some data (run_pipeline.py a few times).
--
-- From the build_from_scratch/ folder:
--     duckdb
--     .read sql/analysis.sql
-- or just paste queries one at a time into the duckdb shell.
--
-- The glob '**/*.parquet' walks every partition folder. hive_partitioning=true
-- tells DuckDB to read year=/month=/day= from the folder names as real columns,
-- so you can filter on them without them being inside the files at all.

-- 1. Sanity check: how many readings are in the lake, across how many cities?
SELECT
    count(*)               AS total_readings,
    count(DISTINCT city)   AS cities,
    min(observed_at)       AS earliest,
    max(observed_at)       AS latest
FROM read_parquet('data/lake/weather/**/*.parquet', hive_partitioning = true);

-- 2. Latest temperature per city (the newest reading we have for each).
--    ROW_NUMBER() is a window function — ranks rows within each city by time.
WITH ranked AS (
    SELECT
        city,
        temperature_2m,
        observed_at,
        ROW_NUMBER() OVER (PARTITION BY city ORDER BY observed_at DESC) AS rn
    FROM read_parquet('data/lake/weather/**/*.parquet', hive_partitioning = true)
)
SELECT city, temperature_2m, observed_at
FROM ranked
WHERE rn = 1
ORDER BY temperature_2m DESC;

-- 3. Average temperature per city per day — the kind of roll-up a dashboard shows.
SELECT
    city,
    ingest_date,
    round(avg(temperature_2m), 1) AS avg_temp,
    round(min(temperature_2m), 1) AS min_temp,
    round(max(temperature_2m), 1) AS max_temp,
    count(*)                      AS readings
FROM read_parquet('data/lake/weather/**/*.parquet', hive_partitioning = true)
GROUP BY city, ingest_date
ORDER BY ingest_date, city;

-- 4. Partition pruning in action: only read June 2026.
--    Because year/month come from the folder names, DuckDB never opens the
--    folders for other months. On a big lake that's the difference between
--    scanning gigabytes and scanning megabytes.
SELECT city, observed_at, temperature_2m, wind_speed_10m
FROM read_parquet('data/lake/weather/**/*.parquet', hive_partitioning = true)
WHERE year = 2026 AND month = 6
ORDER BY observed_at DESC
LIMIT 20;

-- 5. Windiest reading we've ever recorded, and where.
SELECT city, observed_at, wind_speed_10m, wind_direction_10m
FROM read_parquet('data/lake/weather/**/*.parquet', hive_partitioning = true)
ORDER BY wind_speed_10m DESC
LIMIT 5;
