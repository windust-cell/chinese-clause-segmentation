"""Streaming UTF-8 batch I/O. Output is always JSONL, one input record per line."""
import argparse
import csv
import json
import sys
from pathlib import Path
from .core import segment


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--format", choices=("txt", "csv", "jsonl"), default="txt")
    parser.add_argument("--text-column", default="text")
    parser.add_argument("--mode", choices=("general", "medical"), default="general")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.input.resolve() == args.output.resolve():
        parser.error("input and output must differ")
    try:
        with args.input.open(encoding="utf-8-sig", newline="") as source, args.output.open("x", encoding="utf-8", newline="\n") as target:
            if args.format == "txt":
                records = iter(({args.text_column: source.read()},))
            elif args.format == "csv":
                records = csv.DictReader(source)
                if args.text_column not in (records.fieldnames or []):
                    raise ValueError("missing text column")
            else:
                records = (json.loads(line) for line in source if line.strip())
            for row_id, record in enumerate(records, 1):
                if not isinstance(record, dict) or args.text_column not in record:
                    raise ValueError(f"record {row_id}: missing text column")
                result = segment(record[args.text_column], args.mode)
                target.write(json.dumps({"row_id": row_id, "segmentation": result.to_dict()}, ensure_ascii=False)+"\n")
    except (OSError, ValueError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0
