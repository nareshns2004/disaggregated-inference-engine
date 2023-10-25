#!/usr/bin/env python3
"""Pre-commit guard for CLAUDE.md rule 3 (no fabricated numbers).

Flags lines in the given markdown files that contain a performance unit next to a digit but none
of the provenance markers below. Heuristic by design: false positives are fixed by adding the
run id or an explicit label, which is the point.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

UNIT = re.compile(r"\d[\d.,]*\s*(Gb/s|Gbps|GB/s|MB/s|µs|us|ms|req/s|tok/s|Mpps)\b")
OK = re.compile(
    "|".join(
        [
            r"run[_ ]?id",
            r"bench/results/",
            r"calculation",
            r"target",
            r"hypothes",
            r"spec",
            r"\u00d7",  # multiplication sign: a formula, not a measurement
            r"\u2265",
            r"\u2264",
            r">=",
            r"<=",
            r"cite",
            r"\[\d+\]",
            r"TODO",
            r"e\.g\.",
        ]
    ),
    re.I,
)


def main(paths: list[str]) -> int:
    bad = 0
    for p in paths:
        in_code = False
        for n, line in enumerate(Path(p).read_text().splitlines(), 1):
            if line.lstrip().startswith("```"):
                in_code = not in_code
                continue
            if not in_code and UNIT.search(line) and not OK.search(line):
                print(f"{p}:{n}: number without provenance: {line.strip()}")
                bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
