"""Tests for the transform step — the part with real logic worth pinning down.

These don't touch the network. We feed in a fake API payload (the same shape
Open-Meteo returns) and check the flattening, typing and partition columns. Fast,
deterministic, and exactly what CI runs on every push.
"""

from datetime import datetime, timezone

import pandas as pd
import pytest

from weather_lake import transform


def fake_payload(city="London", country="GB", temp=12.3):
    """A minimal payload shaped like a real Open-Meteo response."""
    return {
        "latitude": 51.5,
        "longitude": -0.12,
        "elevation": 25.0,
        "current": {
            "time": "2026-06-29T14:00",
            "temperature_2m": temp,
            "relative_humidity_2m": 71,
            "apparent_temperature": 11.8,
            "precipitation": 0.0,
            "weather_code": 3,
            "cloud_cover": 75,
            "pressure_msl": 1013.2,
            "wind_speed_10m": 14.0,
            "wind_direction_10m": 230,
        },
        "_city": city,
        "_country": country,
        "_collected_at_utc": "2026-06-29T14:05:00+00:00",
    }


def test_flatten_pulls_current_up_to_top_level():
    rec = transform.flatten_payload(fake_payload(temp=9.9))
    assert rec["city"] == "London"
    assert rec["temperature_2m"] == 9.9
    assert rec["wind_speed_10m"] == 14.0
    # nested 'current' must be gone; values live at the top now
    assert "current" not in rec


def test_missing_variable_becomes_none():
    payload = fake_payload()
    del payload["current"]["pressure_msl"]
    rec = transform.flatten_payload(payload)
    # the column still exists (stable schema), just null
    assert rec["pressure_msl"] is None


def test_to_dataframe_adds_partition_columns_and_types():
    collected = datetime(2026, 6, 29, 14, 5, tzinfo=timezone.utc)
    df = transform.to_dataframe([fake_payload("London"), fake_payload("Tokyo")], collected)

    assert len(df) == 2
    assert {"ingest_date", "ingest_hour"} <= set(df.columns)
    assert df["ingest_date"].iloc[0] == "2026-06-29"
    assert df["ingest_hour"].iloc[0] == "14"
    # timestamps were parsed to real datetimes, not left as strings
    assert pd.api.types.is_datetime64_any_dtype(df["observed_at"])


def test_empty_input_returns_empty_frame():
    collected = datetime(2026, 6, 29, 14, 5, tzinfo=timezone.utc)
    df = transform.to_dataframe([], collected)
    assert df.empty
