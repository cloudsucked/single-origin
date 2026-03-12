#!/usr/bin/env python3
# pyright: reportMissingImports=false
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export OpenAPI spec for Single Origin backend")
    parser.add_argument(
        "--output",
        default="docs/openapi/single-origin.openapi.json",
        help="Output path relative to repository root",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if exported spec differs from committed file",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    os.chdir(root / "backend")
    sys.path.insert(0, str(root / "backend"))

    from app.main import app  # pylint: disable=import-outside-toplevel

    output_path = root / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    spec = app.openapi()
    rendered = json.dumps(spec, indent=2, sort_keys=True) + "\n"

    if args.check:
        if not output_path.exists():
            print(f"OpenAPI spec not found: {output_path}")
            return 1
        current = output_path.read_text(encoding="utf-8")
        if current != rendered:
            print(f"OpenAPI spec drift detected: {output_path}")
            print("Run scripts/export-openapi.py to update the committed spec.")
            return 1
        print(f"OpenAPI spec is up to date: {output_path}")
        return 0

    output_path.write_text(rendered, encoding="utf-8")
    print(f"Wrote OpenAPI spec to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
