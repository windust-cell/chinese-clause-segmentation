"""Lossless segmentation with explicit punctuation and relation guards.

Whitespace and punctuation belong to a span. No normalisation or trimming is
performed, so concatenating spans reconstructs the input byte-for-byte after
encoding with the same codec. No statistical syntactic parsing is claimed.
"""
import re
from .domains import get_rules
from .models import Clause, Segmentation, Sentence
from .rules import Rules

PAIRS = {"(": ")", "（": "）", "[": "]", "【": "】", "{": "}", "《": "》", "“": "”", "‘": "’", "「": "」", "『": "』"}
CLOSERS = set(PAIRS.values()) | {'"', "'"}
TERMINALS = set("。！？!?")
ABBREVIATIONS = frozenset(("mr", "mrs", "ms", "dr", "prof", "sr", "jr", "vs", "etc", "e.g", "i.e"))


def _protected(text: str) -> list[bool]:
    """Protect matched, type-correct brackets/quotes; unmatched openers recover.

    A conservative quoted utterance stays intact, including its internal stops.
    Apostrophes between letters are not quote delimiters.
    """
    stack: list[tuple[str, int]] = []
    intervals = []
    for i, char in enumerate(text):
        if char in {'"', "'"}:
            if char == "'" and 0 < i < len(text)-1 and text[i-1].isalnum() and text[i+1].isalnum():
                continue
            if stack and stack[-1][0] == char:
                _, start = stack.pop()
                intervals.append((start, i))
            else:
                stack.append((char, i))
        elif char in PAIRS:
            stack.append((char, i))
        elif stack and PAIRS.get(stack[-1][0]) == char:
            _, start = stack.pop()
            intervals.append((start, i))
    delta = [0] * (len(text)+1)
    for start, end in intervals:
        delta[start+1] += 1
        delta[end] -= 1
    depth = 0
    result = []
    for change in delta[:-1]:
        depth += change
        result.append(depth > 0)
    return result


def _period(text: str, i: int) -> bool:
    before, after = text[i-1:i], text[i+1:i+2]
    if before.isdigit() and after.isdigit():
        return False
    if before.isascii() and before.isalpha() and after.isascii() and after.isalpha():
        return False
    prefix = re.search(r"([A-Za-z][A-Za-z.]*)$", text[:i])
    if prefix and (prefix[1].lower() in ABBREVIATIONS or re.fullmatch(r"(?:[A-Za-z]\.)*[A-Za-z]", prefix[1])):
        return False
    # A domain, email or URL is an opaque unit, even if followed by punctuation.
    token_start = max(text.rfind(" ", 0, i), text.rfind("\n", 0, i)) + 1
    token = text[token_start:i+1]
    if "://" in token and after and not after.isspace():
        return False
    return True


def _validate(text: str) -> None:
    if not isinstance(text, str):
        raise TypeError("text must be str")


def split_sentences(text: str) -> list[Sentence]:
    _validate(text)
    protected = _protected(text)
    cuts: dict[int, str] = {}
    i = 0
    while i < len(text):
        char = text[i]
        # A stop immediately before closing quotes ends the quoted sentence
        # only if no reporting continuation follows (e.g. “好！”他说).
        terminal = char in TERMINALS or (char == "." and _period(text, i)) or char == "…"
        quoted_end = False
        end = i+1
        if terminal:
            while end < len(text) and (text[end] in TERMINALS | {".", "…"}):
                end += 1
            while end < len(text) and text[end] in CLOSERS:
                end += 1
            quoted_end = protected[i] and end == len(text)
        if terminal and (not protected[i] or quoted_end):
            # Keep following whitespace attached to the preceding unit.
            while end < len(text) and text[end].isspace():
                end += 1
            cuts[end] = "terminal"
            i = end
            continue
        if char == "\n" and not protected[i] and text[:i].strip():
            cuts[i+1] = "newline"
        i += 1
    if text:
        cuts.setdefault(len(text), "end")
    result = []
    start = 0
    for end, reason in sorted(cuts.items()):
        if end > start:
            result.append(Sentence(text[start:end], start, end, len(result)+1, reason))
            start = end
    return result


def _core(text: str) -> str:
    return text.strip(" \t\r\n,，;；。.!?！？…")


def _proposition(value: str, rules: Rules) -> bool:
    return bool(value) and any(cue in value for cue in rules.predicates)


def _boundary(left: str, right: str, kind: str, rules: Rules) -> str | None:
    left, right = _core(left), _core(right)
    if not left or not right:
        return None
    # Negation/degree and evaluative target fragments must retain their content.
    if left in {"不", "没", "未", "很", "非常", "比较", "太"} or left.endswith(rules.dependent_endings):
        return None
    if any(left.startswith(opener) and right.startswith(closers) for opener, closers in rules.pairs):
        return None
    if left.startswith(rules.dependent_starts) and not re.search("[,，;；]", left):
        return None
    if right.startswith(rules.continuations):
        return None
    if not (_proposition(left, rules) and _proposition(right, rules)):
        return None
    if kind == "semicolon":
        return "semicolon_propositions"
    if kind == "implicit" and min(len(left), len(right)) < rules.min_unpunctuated_side:
        return None
    if right.startswith(rules.shifts):
        return "discourse_shift"
    if right.startswith(rules.subjects):
        return "subject_or_target_shift"
    if kind == "comma" and min(len(left), len(right)) >= 6:
        return "two_propositions"
    return None


def _clauses(text: str, sentence: Sentence, rules: Rules) -> list[Clause]:
    protected = _protected(sentence.text)
    candidates: dict[int, str] = {}
    for local, char in enumerate(sentence.text):
        if protected[local]:
            continue
        pos = sentence.start + local
        if char in ",，;；":
            # Thousands separators are numeric content.
            if char == "," and text[pos-1:pos].isdigit() and text[pos+1:pos+2].isdigit():
                continue
            candidates[pos+1] = "semicolon" if char in ";；" else "comma"
        elif char.isspace():
            candidates[pos+1] = "whitespace"
    # Unpunctuated text: consider only explicit discourse shifts, with two
    # proposition/length guards. Never infer boundaries from length alone.
    for cue in rules.shifts:
        start = 0
        while True:
            local = sentence.text.find(cue, start)
            if local < 0:
                break
            if local > 0 and not protected[local] and not sentence.text[local-1].isspace() and sentence.text[local-1] not in ",，;；":
                candidates.setdefault(sentence.start+local, "implicit")
            start = local+len(cue)
    result = []
    start = sentence.start
    for pos, kind in sorted(candidates.items()):
        reason = _boundary(text[start:pos], text[pos:sentence.end], kind, rules)
        if reason:
            result.append(Clause(text[start:pos], start, pos, sentence.sentence_id, len(result)+1, reason))
            start = pos
    if start < sentence.end:
        result.append(Clause(text[start:sentence.end], start, sentence.end, sentence.sentence_id, len(result)+1, "sentence_end"))
    return result


def segment(text: str, mode: str = "general", *, rules: Rules | None = None) -> Segmentation:
    _validate(text)
    selected = get_rules(mode) if rules is None else rules
    sentences = split_sentences(text)
    clauses = [clause for sentence in sentences for clause in _clauses(text, sentence, selected)]
    return Segmentation(tuple(sentences), tuple(clauses), mode)


def split_clauses(text: str, mode: str = "general", *, rules: Rules | None = None) -> list[Clause]:
    return list(segment(text, mode, rules=rules).clauses)
