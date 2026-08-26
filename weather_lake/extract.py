"""Extract: call the weather API and bring back the raw JSON, untouched.

The golden rule of extraction is *don't fix anything yet*. Pull the response in
exactly as the API gives it to you, save a copy of it, and hand it on. All the
cleaning happens in transform. Keeping extract "dumb" is what lets you re-run the
whole pipeline from saved raw files later without hitting the network again.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from . import config
from .cities import City

log = logging.getLogger(__name__)


def fetch_city(city: City, collected_at: datetime) -> dict:
    """Call Open-Meteo for one city and return the parsed JSON as a dict.

    Retries on network errors with a short backoff. Raises if every attempt
    fails — the caller decides whether one dead city should kill the whole run
    (it shouldn't; see pipeline.py).
    """
    params = {
        "latitude": city.latitude,
        "longitude": city.longitude,
        "current": ",".join(config.CURRENT_VARIABLES),
        "timezone": config.TIMEZONE,
    }

    last_error: Exception | None = None
    for attempt in range(1, config.MAX_RETRIES + 1):
        try:
            resp = requests.get(
                config.API_URL, params=params, timeout=config.REQUEST_TIMEOUT
            )
            resp.raise_for_status()  # turn a 4xx/5xx into an exception
            payload = resp.json()
            # Stamp the moment we collected it. The API tells us when the weather
            # was observed; we record when *we* asked. Both matter later.
            payload["_city"] = city.name
            payload["_country"] = city.country
            payload["_collected_at_utc"] = collected_at.isoformat()
            log.info("Fetched %s (%d attempt[s])", city.name, attempt)
            return payload
        except requests.RequestException as exc:
            last_error = exc
            wait = attempt * 2  # 2s, 4s, 6s — simple linear backoff
            log.warning(
                "Attempt %d for %s failed: %s. Retrying in %ds",
                attempt, city.name, exc, wait,
            )
            time.sleep(wait)

    raise RuntimeError(f"All {config.MAX_RETRIES} attempts failed for {city.name}") from last_error


def save_raw(payload: dict, collected_at: datetime) -> Path:
    """Write the raw JSON to the raw layer, partitioned by collection hour.

    Layout: data/raw/weather/date=YYYY-MM-DD/hour=HH/<city>.json

    The filename is deterministic (city + hour), so re-running the same hour
    overwrites the same file instead of piling up duplicates — that's the raw
    layer being idempotent too.
    """
    city = payload["_city"].lower().replace(" ", "_")
    folder = (
        config.RAW_DIR
        / f"date={collected_at:%Y-%m-%d}"
        / f"hour={collected_at:%H}"
    )
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{city}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    log.debug("Saved raw JSON -> %s", path)
    return path
