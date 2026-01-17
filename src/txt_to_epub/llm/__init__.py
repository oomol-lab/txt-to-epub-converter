"""
LLM-assisted parser package
"""
from .client import LLMClient
from .data_structures import ChapterCandidate, LLMDecision
from .chapter_assistant import ChapterAssistant
from .title_generator import TitleGenerator
from .toc_assistant import TOCAssistant
from .format_identifier import FormatIdentifier
from .disambiguation import Disambiguator
from .structure_inferrer import StructureInferrer

__all__ = [
    'LLMClient',
    'ChapterCandidate',
    'LLMDecision',
    'ChapterAssistant',
    'TitleGenerator',
    'TOCAssistant',
    'FormatIdentifier',
    'Disambiguator',
    'StructureInferrer',
]
