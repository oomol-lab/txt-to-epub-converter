"""Edge-case tests for the word count validator (empty input)."""

from txt_to_epub.validator.analyzer import analyze_content_changes
from txt_to_epub.validator.counter import count_characters


def _zero_stats():
    return {
        "chinese_chars": 0,
        "english_chars": 0,
        "punctuation": 0,
        "total_chars": 0,
        "original_length": 0,
    }


def test_analyze_empty_content_does_not_crash():
    """Analyzing an empty original must not raise ZeroDivisionError."""
    analysis = analyze_content_changes(_zero_stats(), _zero_stats())
    assert "overall_reason" in analysis
    assert "overall_concern" in analysis


def test_count_characters_empty_string():
    """Counting an empty string must report all zeros."""
    stats = count_characters("")
    assert stats["total_chars"] == 0
    assert stats["original_length"] == 0
