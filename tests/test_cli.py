import json
import pytest
from chinese_clause_segmentation.cli import main


@pytest.mark.parametrize("format,payload", [
    ("txt", "产品很好。谢谢！"),
    ("csv", 'text,unused\n"产品很好。谢谢！",value\n'),
    ("jsonl", '{"text": "产品很好。谢谢！"}\n'),
])
def test_cli_roundtrip(tmp_path, format, payload):
    source, target = tmp_path/"input", tmp_path/"output"
    source.write_text(payload, encoding="utf-8")
    assert main([str(source), "--format", format, "--output", str(target)]) == 0
    row = json.loads(target.read_text(encoding="utf-8"))
    assert ''.join(c['text'] for c in row['segmentation']['clauses']) == "产品很好。谢谢！"
    assert main([str(source), "--output", str(target)]) == 2


def test_missing_column(tmp_path):
    source, target = tmp_path/"input.csv", tmp_path/"output"
    source.write_text("wrong\nvalue\n", encoding="utf-8")
    assert main([str(source), "--format", "csv", "--output", str(target)]) == 2
