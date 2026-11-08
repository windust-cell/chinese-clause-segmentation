"""Optional domain vocabulary, kept out of the general algorithm."""
from dataclasses import replace
from .rules import GENERAL, Rules

MEDICAL = replace(
    GENERAL,
    subjects=GENERAL.subjects + ("医生", "护士", "患者", "医院", "治疗", "费用", "疗效", "态度"),
    predicates=GENERAL.predicates + ("耐心", "恢复", "改善", "解释", "沟通", "治疗", "复查", "疼痛", "出院"),
    shifts=GENERAL.shifts + ("术后", "出院后", "复查后"),
)


def get_rules(mode: str) -> Rules:
    if mode == "general":
        return GENERAL
    if mode == "medical":
        return MEDICAL
    raise ValueError("mode must be 'general' or 'medical'")
