"""
Text parser for hierarchical document structure (Backward Compatibility Wrapper)

This module provides backward compatibility with the old parser API.
The implementation has been refactored into multiple modules under the parser package.
"""

# Re-export everything from the new modular structure
from .parser import (
    parse_hierarchical_content,
    parse_chapters_from_content,
    parse_sections_from_content,
    ChinesePatterns,
    EnglishPatterns,
    detect_language,
    enhance_chapter_title,
    is_simple_chapter_title,
    extract_meaningful_title,
    validate_and_merge_chapters,
    is_valid_chapter_title,
    remove_table_of_contents
)

# For backward compatibility, also export these at module level
__all__ = [
    'parse_hierarchical_content',
    'parse_chapters_from_content',
    'parse_sections_from_content',
    'ChinesePatterns',
    'EnglishPatterns',
    'detect_language',
    'enhance_chapter_title',
    'is_simple_chapter_title',
    'extract_meaningful_title',
    'validate_and_merge_chapters',
    'is_valid_chapter_title',
    'remove_table_of_contents',
]
