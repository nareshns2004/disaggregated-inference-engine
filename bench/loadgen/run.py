"""`make bench SCENARIO=...` entry point. Writes bench/results/<run_id>/ with config, env
manifest, raw timelines. Refuses to run without an env manifest."""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--out", required=True)
    ap.parse_args(argv)
    raise NotImplementedError("M1: OpenAI-compatible async client + timeline capture")


if __name__ == "__main__":
    sys.exit(main())
