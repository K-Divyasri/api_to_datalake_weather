"""Tests for the load step — partition layout and idempotency.

We write into a temporary lake (pytest's tmp_path), so these tests never touch
your real data folder. The key thing being proven is idempotency: writing the
same hour twice leaves exactly one file, not two.
"""

from datetime import datetime, timezone

import pandas as pd
import pytest

from weather_lake import load


def sample_df():
    return pd.DataFrame(
        {
            "city": ["London", "Tokyo"],
            "temperature_2m": [12.0, 24.5],
            "ingest_date": ["2026-06-29", "2026-06-29"],
            "ingest_hour": ["14", "14"],
        }
    )


def test_partition_path_is_hive_style(monkeypatch, tmp_path):
    monkeypatch.setattr(load.config, "LAKE_DIR", tmp_path)
    collected = datetime(2026, 6, 29, 14, 0, tzinfo=timezone.utc)
    p = load.partition_path(collected)
    # year=YYYY/month=MM/day=DD — the parts a query engine reads as columns
    assert p.parts[-3:] == ("year=2026", "month=06", "day=29")


def test_write_then_read_round_trips(monkeypatch, tmp_path):
    monkeypatch.setattr(load.config, "LAKE_DIR", tmp_path)
    collected = datetime(2026, 6, 29, 14, 0, tzinfo=timezone.utc)

    load.write_partition(sample_df(), collected)
    back = load.read_lake(tmp_path)

    assert len(back) == 2
    assert set(back["city"]) == {"London", "Tokyo"}


def test_rerunning_same_hour_is_idempotent(monkeypatch, tmp_path):
    monkeypatch.setattr(load.config, "LAKE_DIR", tmp_path)
    collected = datetime(2026, 6, 29, 14, 0, tzinfo=timezone.utc)

    p1 = load.write_partition(sample_df(), collected)
    p2 = load.write_partition(sample_df(), collected)  # same hour again

    assert p1 == p2  # same deterministic filename
    folder = load.partition_path(collected)
    parquet_files = list(folder.glob("*.parquet"))
    assert len(parquet_files) == 1  # not two — overwritten, not appended

    # and the data wasn't doubled
    assert len(load.read_lake(tmp_path)) == 2


def test_empty_dataframe_is_rejected(monkeypatch, tmp_path):
    monkeypatch.setattr(load.config, "LAKE_DIR", tmp_path)
    collected = datetime(2026, 6, 29, 14, 0, tzinfo=timezone.utc)
    with pytest.raises(ValueError):
        load.write_partition(pd.DataFrame(), collected)
