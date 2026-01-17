"""
Text parser package for hierarchical document structure
"""
from .core import parse_hierarchical_content, parse_chapters_from_content, parse_sections_from_content
from .patterns import ChinesePatterns, EnglishPatterns
from .language_detector import detect_language
from .title_enhancer import enhance_chapter_title, is_simple_chapter_title, extract_meaningful_title
from .validator import validate_and_merge_chapters, is_valid_chapter_title, estimate_chapter_confidence
from .toc_remover import remove_table_of_contents

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
    'estimate_chapter_confidence',
    'remove_table_of_contents',
]
