"""Explainable, lossless Chinese sentence and clause segmentation."""
from .core import segment, split_clauses, split_sentences
from .models import Clause, Segmentation, Sentence
from .rules import Rules

__version__ = "0.1.0"
__all__ = ["segment", "split_sentences", "split_clauses", "Clause", "Sentence", "Segmentation", "Rules"]
