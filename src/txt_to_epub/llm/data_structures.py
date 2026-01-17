"""
Data structures for LLM-assisted parsing
"""
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ChapterCandidate:
    """Candidate chapter data structure"""
    text: str
    position: int
    line_number: int
    confidence: float
    context_before: str
    context_after: str
    pattern_type: str
    issues: List[str] = None

    def __post_init__(self):
        if self.issues is None:
            self.issues = []


@dataclass
class LLMDecision:
    """LLM decision result data structure"""
    is_chapter: bool
    confidence: float
    reason: str
    suggested_title: Optional[str] = None
    suggested_position: Optional[int] = None
