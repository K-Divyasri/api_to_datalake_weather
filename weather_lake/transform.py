"""Transform: flatten the nested JSON into one tidy row per reading.

The API hands back a nested object: a `current` block sitting inside a bunch of
metadata, with a parallel `current_units` block describing the units. A data lake
wants flat, typed rows — one row per city per reading, every value a proper
column. This module does that flattening and nothing else.
"""

from __future__ import annotations

import logging
from datetime import datetime

import pandas as pd

from . import config

log = logging.getLogger(__name__)


def flatten_payload(payload: dict) -> dict:
    """Turn one raw API response into one flat record (a plain dict).

    We pull the metadata we care about from the top level, then spread every
    variable inside `current` up to the top. Anything the API didn't return
    comes back as None, which becomes a proper null in Parquet.
    """
    current = payload.get("current", {}) or {}

    record = {
        "city": payload.get("_city"),
        "country": payload.get("_country"),
        "latitude": payload.get("latitude"),
        "longitude": payload.get("longitude"),
        "elevation": payload.get("elevation"),
        # When the weather was observed (API's clock) vs when we collected it.
        "observed_at": current.get("time"),
        "collected_at_utc": payload.get("_collected_at_utc"),
    }

    # Spread each requested current-variable up to the top level. Using the
    # configured list (not whatever happened to come back) keeps the schema
    # stable run to run, even if the API omits a value.
    for var in config.CURRENT_VARIABLES:
        record[var] = current.get(var)

    return record


def to_dataframe(payloads: list[dict], collected_at: datetime) -> pd.DataFrame:
    """Flatten a list of raw payloads into a single typed DataFrame.

    Also adds the partition columns (ingest_date and the hour) and forces the
    timestamp columns to real datetimes. Returning a DataFrame here means the
    load step is dead simple: hand it to Parquet.
    """
    records = [flatten_payload(p) for p in payloads]
    df = pd.DataFrame.from_records(records)

    if df.empty:
        log.warning("No records to transform — every city must have failed")
        return df

    # Real timestamps, not strings. errors="coerce" turns anything unparseable
    # into NaT (a null datetime) instead of crashing the run.
    df["observed_at"] = pd.to_datetime(df["observed_at"], errors="coerce", utc=True)
    df["collected_at_utc"] = pd.to_datetime(
        df["collected_at_utc"], errors="coerce", utc=True
    )

    # Partition key. Every row collected in this run shares one ingest_date, so
    # all rows land in the same date partition on disk.
    df["ingest_date"] = collected_at.strftime("%Y-%m-%d")
    df["ingest_hour"] = collected_at.strftime("%H")

    log.info("Transformed %d rows, %d columns", len(df), df.shape[1])
    return df
