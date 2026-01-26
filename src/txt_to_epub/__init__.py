"""
TXT to EPUB Converter

A powerful Python library for converting plain text files (.txt) to professional EPUB eBooks
with intelligent chapter detection and AI-enhanced structure analysis.
"""

__version__ = "0.1.1"
__author__ = "TXT to EPUB Converter Team"
__license__ = "MIT"

# Import core conversion functionality
from .core import txt_to_epub
from .parser_config import ParserConfig, DEFAULT_CONFIG
from .data_structures import Volume, Chapter, Section

# Export public API
__all__ = [
    'txt_to_epub',
    'ParserConfig',
    'DEFAULT_CONFIG',
    'Volume',
    'Chapter',
    'Section',
]
