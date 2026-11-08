"""Opt-in segmentation-independent tokenizer; no dictionaries are bundled."""
from collections.abc import Iterable


def tokenize(text: str, stopwords: Iterable[str] = ()) -> list[str]:
    try:
        import jieba
    except ImportError as exc:
        raise ImportError("Install chinese-clause-segmentation[tokenize]") from exc
    excluded = set(stopwords)
    return [token for token in jieba.cut(text) if token.strip() and token not in excluded and any(c.isalnum() for c in token)]
