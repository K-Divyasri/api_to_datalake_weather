"""All the knobs in one place, so nothing important is buried in the code.

Anything you might reasonably want to change without editing logic lives here:
where the data lake goes, which weather variables to ask for, the API URL,
how long to wait on the network. Values can be overridden with environment
variables (loaded from a local .env file if you have python-dotenv installed),
which is how the GitHub Actions schedule configures it without touching code.
"""

from __future__ import annotations

import os
from pathlib import Path

# Load a local .env if python-dotenv is available. It's optional: this project
# needs no secrets (Open-Meteo has no API key), but using .env from day one is a
# good habit, and lets you flip settings per machine.
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


# --- Where data lives -------------------------------------------------------
# The project root is two levels up from this file:
#   build_from_scratch/weather_lake/config.py  ->  build_from_scratch/
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.getenv("DATA_DIR", PROJECT_ROOT / "data"))

# The "raw" layer: every API response saved untouched, exactly as it arrived.
RAW_DIR = DATA_DIR / "raw" / "weather"

# The "lake" layer: cleaned, flattened, columnar Parquet, partitioned by date.
LAKE_DIR = DATA_DIR / "lake" / "weather"


# --- The API ----------------------------------------------------------------
API_URL = os.getenv("OPEN_METEO_URL", "https://api.open-meteo.com/v1/forecast")

# Which "current conditions" variables to pull. Order doesn't matter; Open-Meteo
# returns whatever you list under `current`. These nine give a rounded picture.
CURRENT_VARIABLES = [
    "temperature_2m",
    "relative_humidity_2m",
    "apparent_temperature",
    "precipitation",
    "weather_code",
    "cloud_cover",
    "pressure_msl",
    "wind_speed_10m",
    "wind_direction_10m",
]

# Ask the API to return timestamps in UTC. A data lake that mixes local times is
# a debugging nightmare; store everything in UTC and convert on the way out.
TIMEZONE = os.getenv("OPEN_METEO_TIMEZONE", "UTC")

# Network timeout in seconds. Without this, one hung connection freezes the whole
# run forever. Always set a timeout on requests in a pipeline.
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "15"))

# How many times to retry a failed call before giving up on that city.
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
