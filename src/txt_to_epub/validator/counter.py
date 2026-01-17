"""Character counting module for text analysis."""

import re
from typing import Dict


def clean_text_for_counting(text: str) -> str:
    """
    Clean text for counting, remove extra whitespace and punctuation.

    :param text: Original text
    :return: Cleaned text
    """
    if not text:
        return ""

    # Remove extra whitespace (spaces, tabs, newlines, etc.)
    cleaned = re.sub(r'\s+', '', text)

    # Remove common punctuation and special characters (but keep Chinese characters)
    # Only remove obvious separators, keep potentially meaningful punctuation
    cleaned = re.sub(r'[　\u3000]+', '', cleaned)  # Remove Chinese spaces

    return cleaned


def count_characters(text: str) -> Dict[str, int]:
    """
    Count characters in text.

    :param text: Text content
    :return: Character statistics dictionary
    """
    cleaned_text = clean_text_for_counting(text)

    # Count Chinese characters (including Chinese punctuation)
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf]', cleaned_text))

    # Count English letters and numbers
    english_chars = len(re.findall(r'[a-zA-Z0-9]', cleaned_text))

    # Count punctuation - use Unicode ranges to avoid encoding issues
    chinese_punctuation = len(re.findall(r'[\u3000-\u303f\uff00-\uffef]', cleaned_text))  # Chinese punctuation
    english_punctuation = len(re.findall(r'[.,!?;:()\[\]<>"\'\\-]', cleaned_text))  # English punctuation
    punctuation = chinese_punctuation + english_punctuation

    # Total characters (excluding whitespace)
    total_chars = len(cleaned_text)

    # Original text total length (including whitespace)
    original_length = len(text) if text else 0

    return {
        'chinese_chars': chinese_chars,
        'english_chars': english_chars,
        'punctuation': punctuation,
        'total_chars': total_chars,
        'original_length': original_length
    }


def detect_primary_language(text: str) -> str:
    """
    Detect the primary language of the text based on character composition.

    :param text: Text content to analyze
    :return: 'chinese' for primarily Chinese text, 'english' for primarily English text
    """
    if not text:
        return 'english'

    cleaned_text = clean_text_for_counting(text)

    # Count Chinese characters
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf]', cleaned_text))
    # Count English letters
    english_chars = len(re.findall(r'[a-zA-Z]', cleaned_text))

    total_meaningful_chars = chinese_chars + english_chars

    if total_meaningful_chars == 0:
        return 'english'

    # If Chinese characters make up more than 30% of meaningful characters, consider it Chinese
    chinese_ratio = chinese_chars / total_meaningful_chars

    return 'chinese' if chinese_ratio > 0.3 else 'english'
