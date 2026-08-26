"""The pipeline: tie extract -> transform -> load into one runnable job.

This is the function GitHub Actions calls every hour. It loops the cities, pulls
each one (saving the raw JSON), flattens the whole batch into a DataFrame, and
writes one Parquet file into today's date partition.

One design choice worth noticing: a single city failing does NOT kill the run.
We collect what we can and load that. A weather lake with nine of ten cities is
far more useful than no lake at all because one API call timed out.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from . import extract, transform, load
from .cities import CITIES

log = logging.getLogger(__name__)


def run(collected_at: datetime | None = None) -> Path | None:
    """Run one full collection cycle. Returns the Parquet path written, or None.

    `collected_at` is injectable so tests can pin the timestamp. In production it
    defaults to "now, in UTC".
    """
    collected_at = collected_at or datetime.now(timezone.utc)
    log.info("=== Weather collection run @ %s ===", collected_at.isoformat())

    payloads = []
    for city in CITIES:
        try:
            payload = extract.fetch_city(city, collected_at)
            extract.save_raw(payload, collected_at)
            payloads.append(payload)
        except Exception as exc:  # noqa: BLE001 - one bad city must not stop the run
            log.error("Skipping %s: %s", city.name, exc)

    if not payloads:
        log.error("Every city failed — nothing to load. Aborting.")
        return None

    df = transform.to_dataframe(payloads, collected_at)
    path = load.write_partition(df, collected_at)

    log.info(
        "Run complete: %d/%d cities -> %s", len(payloads), len(CITIES), path
    )
    return path
