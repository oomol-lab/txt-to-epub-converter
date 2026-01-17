"""
Language detection for text content
"""
import re


def detect_language(content: str) -> str:
    """
    Detect the main language of the text (Chinese or English)

    :param content: Text content
    :return: 'chinese' or 'english'
    """
    if not content or not content.strip():
        return 'chinese'  # Default to Chinese

    # Count Chinese characters
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
    # Count English letters
    english_chars = len(re.findall(r'[a-zA-Z]', content))

    # Check common Chinese chapter keywords
    chinese_keywords = ['第', '章', '节', '卷', '部', '篇', '序言', '前言', '目录']
    chinese_keyword_count = sum(content.count(kw) for kw in chinese_keywords)

    # Check common English chapter keywords
    english_keywords = ['Chapter', 'Section', 'Part', 'Book', 'Volume', 'Contents', 'Preface', 'Introduction']
    english_keyword_count = sum(content.lower().count(kw.lower()) for kw in english_keywords)

    # Decision logic
    if chinese_chars > english_chars * 0.5 or chinese_keyword_count > english_keyword_count:
        return 'chinese'
    else:
        return 'english'
