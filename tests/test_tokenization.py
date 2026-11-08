import sys
import pytest
from chinese_clause_segmentation import segment
from chinese_clause_segmentation.tokenization import tokenize


def test_core_without_optional_dependency(monkeypatch):
    monkeypatch.setitem(sys.modules, "jieba", None)
    assert segment("很好").clauses[0].text == "很好"
    with pytest.raises(ImportError, match="tokenize"):
        tokenize("很好")


def test_optional_tokenization():
    pytest.importorskip("jieba")
    tokens = tokenize("产品很好，谢谢", {"产品"})
    assert "产品" not in tokens
    assert "谢谢" in tokens
    assert all(any(c.isalnum() for c in t) for t in tokens)
