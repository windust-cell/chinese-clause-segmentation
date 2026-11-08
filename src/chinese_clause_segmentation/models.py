"""Offsets are zero-based Python Unicode code-point indexes, end exclusive."""
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Sentence:
    text: str
    start: int
    end: int
    sentence_id: int
    reason: str


@dataclass(frozen=True)
class Clause:
    text: str
    start: int
    end: int
    sentence_id: int
    clause_id: int
    reason: str


@dataclass(frozen=True)
class Segmentation:
    sentences: tuple[Sentence, ...]
    clauses: tuple[Clause, ...]
    mode: str

    def to_dict(self) -> dict:
        return asdict(self)
