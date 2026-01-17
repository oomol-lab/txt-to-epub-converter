"""Validator package for TXT to EPUB conversion integrity checking.

This package provides comprehensive validation and reporting for TXT to EPUB conversion,
including character counting, content analysis, and detailed reporting capabilities.
"""

from typing import List, Tuple

from .word_count_validator import WordCountValidator
from .counter import (
    clean_text_for_counting,
    count_characters,
    detect_primary_language
)
from .messages import get_messages
from .analyzer import (
    analyze_content_changes,
    compare_content
)
from .reporter import generate_validation_report

from ..data_structures import Volume

__all__ = [
    # Main validator class
    'WordCountValidator',

    # Counter functions
    'clean_text_for_counting',
    'count_characters',
    'detect_primary_language',

    # Message functions
    'get_messages',

    # Analyzer functions
    'analyze_content_changes',
    'compare_content',

    # Reporter functions
    'generate_validation_report',

    # Convenience function
    'validate_conversion_integrity'
]


def validate_conversion_integrity(original_content: str, volumes: List[Volume]) -> Tuple[bool, str]:
    """
    Validate content integrity for txt to epub conversion.

    This is a convenience function that wraps the WordCountValidator class
    for simple one-call validation.

    :param original_content: Original txt file content
    :param volumes: Converted volume structure
    :return: (validation_passed, validation_report)
    """
    validator = WordCountValidator()

    # Analyze original content
    validator.analyze_original_content(original_content)

    # Analyze converted content
    validator.analyze_converted_content(volumes)

    # Generate validation report
    report = validator.generate_validation_report()

    # Get validation result
    is_valid, _ = validator.compare_content()

    return is_valid, report
