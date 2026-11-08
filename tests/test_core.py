import random
import pytest
from chinese_clause_segmentation import Rules, segment, split_clauses, split_sentences
from benchmarks.cases import CASES


@pytest.mark.parametrize("domain,sentences,clauses,_", [c for c in CASES if c[3]])
def test_confirmed_development_boundaries(domain, sentences, clauses, _):
    text = "".join(sentences)
    result = segment(text, "medical" if domain == "medical" else "general")
    assert [s.text for s in result.sentences] == sentences
    assert [c.text for c in result.clauses] == clauses


@pytest.mark.parametrize("text", ["", " ", "\n\t", "不", "很好", "谢谢", "不行", "😂", "！？", "a\x00b", "（未闭合。继续。", "【错配）测试。", "𠮷你好👨‍👩‍👧‍👦。"])
def test_lossless_edge_cases(text):
    result = segment(text)
    assert "".join(s.text for s in result.sentences) == text
    assert "".join(c.text for c in result.clauses) == text
    for unit in (*result.sentences, *result.clauses):
        assert text[unit.start:unit.end] == unit.text
        assert unit.end > unit.start
    for sentence in result.sentences:
        children = [c for c in result.clauses if c.sentence_id == sentence.sentence_id]
        assert "".join(c.text for c in children) == sentence.text
        assert [c.clause_id for c in children] == list(range(1, len(children)+1))


def test_random_unicode_reconstruction():
    rng = random.Random(42)
    alphabet = '你我很好因为但是。!?，;；\n\t ()（【】）“”a3.😂'
    for _ in range(400):
        text = ''.join(rng.choice(alphabet) for _ in range(rng.randrange(180)))
        result = segment(text)
        assert ''.join(c.text for c in result.clauses) == text
        assert all(text[c.start:c.end] == c.text for c in result.clauses)


@pytest.mark.parametrize("bad", [None, 1, [], b"text"])
def test_invalid_types(bad):
    with pytest.raises(TypeError):
        segment(bad)


def test_api_and_config():
    assert split_sentences("") == []
    assert split_clauses("") == []
    assert segment("很好", rules=Rules()).to_dict()["clauses"][0]["text"] == "很好"
    with pytest.raises(ValueError):
        segment("很好", "unknown")
