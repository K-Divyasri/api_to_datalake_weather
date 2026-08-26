"""Load: write the flattened rows into the lake as partitioned Parquet.

This is where the project earns its name. Instead of one big file, we write
Hive-style partitions:

    data/lake/weather/year=2026/month=06/day=29/weather_20260629T14.parquet

Each folder level is `key=value`. Query engines (DuckDB, Athena, Spark) read the
folder names as columns for free, so a query like `WHERE year = 2026 AND month = 6`
only opens the folders it needs and skips the rest. That's "partition pruning",
and it's the whole point of laying data out this way.

The filename carries the collection hour, so re-running the same hour overwrites
the same file rather than creating a second copy. That makes the load idempotent:
run it once or ten times, the partition holds exactly one file for that hour.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

from . import config

log = logging.getLogger(__name__)


def partition_path(collected_at: datetime) -> Path:
    """Build the year=/month=/day= folder for a given collection time."""
    return (
        config.LAKE_DIR
        / f"year={collected_at:%Y}"
        / f"month={collected_at:%m}"
        / f"day={collected_at:%d}"
    )


def write_partition(df: pd.DataFrame, collected_at: datetime) -> Path:
    """Write one DataFrame into its date partition as a single Parquet file.

    Returns the path written. Overwrites deterministically on re-run.
    """
    if df.empty:
        raise ValueError("Refusing to write an empty DataFrame to the lake")

    folder = partition_path(collected_at)
    folder.mkdir(parents=True, exist_ok=True)

    # Deterministic name keyed to the hour => idempotent overwrite.
    filename = f"weather_{collected_at:%Y%m%dT%H}.parquet"
    path = folder / filename

    # pyarrow is the engine that actually writes the columnar file. Snappy
    # compression is the sensible default: fast, and shrinks the file a lot.
    df.to_parquet(path, engine="pyarrow", compression="snappy", index=False)

    log.info("Wrote %d rows -> %s", len(df), path)
    return path


def read_lake(lake_dir: Path | None = None) -> pd.DataFrame:
    """Read the whole lake back into one DataFrame.

    pandas + pyarrow can read a directory of partitioned Parquet in one call and
    reconstruct the year/month/day partition columns from the folder names. This
    is the "prove it worked" round trip — write data, then read it all back.
    """
    lake_dir = lake_dir or config.LAKE_DIR
    if not lake_dir.exists():
        log.warning("Lake directory %s does not exist yet", lake_dir)
        return pd.DataFrame()

    df = pd.read_parquet(lake_dir, engine="pyarrow")
    log.info("Read %d rows back from the lake", len(df))
    return df
