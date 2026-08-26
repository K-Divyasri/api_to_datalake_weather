"""Run the collector as a module:  python -m weather_lake

Sets up readable logging, then runs one collection cycle. Exit code is non-zero
if nothing could be collected, so a scheduler (or CI) can tell it failed.
"""

import logging
import sys

from .pipeline import run


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )
    path = run()
    return 0 if path is not None else 1


if __name__ == "__main__":
    sys.exit(main())
