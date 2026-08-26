"""The ten cities we collect weather for.

Open-Meteo takes coordinates, not city names, so each city is a (lat, lon) pair
plus a country code we keep around for grouping later. Latitude is north/south,
longitude is east/west, both in plain decimal degrees (WGS84) — the same numbers
Google Maps shows you when you right-click a place.

Keeping the list here, as data, means the pipeline code never hard-codes a city.
Want to track Lagos instead of Lima? Add a line. Nothing else changes.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class City:
    name: str
    country: str
    latitude: float
    longitude: float


# A deliberately spread-out set: different continents, hemispheres and time
# zones, so when you look at the collected data the numbers actually differ.
CITIES = [
    City("London",        "GB", 51.5074,  -0.1278),
    City("New York",      "US", 40.7128, -74.0060),
    City("Tokyo",         "JP", 35.6762, 139.6503),
    City("Sydney",        "AU", -33.8688, 151.2093),
    City("Sao Paulo",     "BR", -23.5505, -46.6333),
    City("Mumbai",        "IN", 19.0760,  72.8777),
    City("Cairo",         "EG", 30.0444,  31.2357),
    City("Moscow",        "RU", 55.7558,  37.6173),
    City("Nairobi",       "KE", -1.2921,  36.8219),
    City("Reykjavik",     "IS", 64.1466, -21.9426),
]
