"""Convenience entry point so you can run the pipeline without the -m syntax.

    python run_pipeline.py

It does exactly what `python -m weather_lake` does. Both exist because beginners
reach for `python run_pipeline.py` first, and that should just work.
"""

import logging
import sys

from weather_lake.pipeline import run


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )
    path = run()
    if path is None:
        print("No data collected — see the log above.")
        return 1
    print(f"\nDone. Latest partition file: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
