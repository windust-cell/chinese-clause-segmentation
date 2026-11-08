"""Reproducible boundary micro P/R/F1; final document boundary excluded."""
import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from chinese_clause_segmentation import segment
from .cases import CASES


def boundaries(parts):
    offset = 0
    result = set()
    for part in parts[:-1]:
        offset += len(part)
        result.add(offset)
    return result


def score(tp, fp, fn):
    p = tp/(tp+fp) if tp+fp else 1.0
    r = tp/(tp+fn) if tp+fn else 1.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": p, "recall": r, "f1": 2*p*r/(p+r) if p+r else 0.0}


def evaluate():
    totals = defaultdict(lambda: [0, 0, 0])
    errors = []
    for index, (domain, sentences, clauses, _) in enumerate(CASES):
        text = "".join(sentences)
        assert text == "".join(clauses)
        output = segment(text, "medical" if domain == "medical" else "general")
        for level, gold, predicted, pattern in (
            ("sentence", sentences, [s.text for s in output.sentences], r"(?<=[。！？!?\.])"),
            ("clause", clauses, [c.text for c in output.clauses], r"(?<=[。！？!?\.,，;；])"),
        ):
            truth = boundaries(gold)
            for method, parts in (("tool", predicted), ("punctuation_baseline", [p for p in re.split(pattern, text) if p])):
                actual = boundaries(parts)
                counts = [len(actual & truth), len(actual-truth), len(truth-actual)]
                for group in ("all", domain):
                    key = f"{group}/{level}/{method}"
                    totals[key] = [a+b for a, b in zip(totals[key], counts)]
                if method == "tool" and actual != truth:
                    errors.append({"case": index, "domain": domain, "level": level, "text": text, "expected": gold, "actual": predicted, "extra_boundaries": sorted(actual-truth), "missed_boundaries": sorted(truth-actual)})
    return {"scope": "Invented developer-authored cases; not independent generalization validation", "cases": len(CASES), "metrics": {key: score(*value) for key, value in sorted(totals.items())}, "errors": errors}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = evaluate()
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload+"\n", encoding="utf-8")
    else:
        print(payload)


if __name__ == "__main__":
    main()
