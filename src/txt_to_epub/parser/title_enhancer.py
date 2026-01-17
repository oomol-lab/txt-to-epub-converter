"""
Chapter title enhancement utilities
"""
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def is_simple_chapter_title(title: str, language: str = 'chinese') -> bool:
    """
    Determine if chapter title is too simple (only chapter number, no substantial content)

    :param title: Chapter title
    :param language: Language type
    :return: True if simple chapter number, False if has substantial content
    """
    if not title:
        return True

    title = title.strip()

    if language == 'chinese':
        # Match titles with only "第X章" or "第X章 "
        simple_patterns = [
            r'^第[一二三四五六七八九十百千万\d]+章\s*$',
            r'^第[一二三四五六七八九十百千万\d]+章\s+[\s\u3000]*$',  # Including full-width space
            r'^\d+[\s\u3000]*$',  # Only numbers
            r'^第\d+章\s*$',
            r'^第\d+章\s+[\s\u3000]*$'
        ]

        for pattern in simple_patterns:
            if re.match(pattern, title):
                return True

        # If title length is <= 5 characters and contains "第" and "章", consider it simple
        if len(title) <= 5 and '第' in title and '章' in title:
            return True

    else:
        # English simple title patterns
        simple_patterns = [
            r'^Chapter\s+\d+\s*$',
            r'^Ch\.?\s+\d+\s*$',
            r'^Chapter\s+[IVXivx]+\s*$',
            r'^\d+\s*$'
        ]

        for pattern in simple_patterns:
            if re.match(pattern, title, re.IGNORECASE):
                return True

    return False


def extract_meaningful_title(chapter_content: str, language: str = 'chinese', max_length: int = 20) -> str:
    """
    Extract meaningful title from chapter content

    :param chapter_content: Chapter content
    :param language: Language type
    :param max_length: Maximum title length
    :return: Extracted title
    """
    if not chapter_content or not chapter_content.strip():
        return ""

    content = chapter_content.strip()

    # Remove common opening phrases
    if language == 'chinese':
        # Remove opening phrases like "话说", "且说", "却说"
        content = re.sub(r'^(话说|且说|却说|却说|正是|正所谓|古人云|俗语说)\s*', '', content)

        # Find first complete sentence
        sentences = re.split(r'[。！？；]', content)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) >= 5 and len(sentence) <= max_length * 2:  # Chinese characters
                # Check if contains meaningful content
                if re.search(r'[的之在了是]', sentence):  # Contains meaningful connectors
                    # Extract first max_length characters
                    title = sentence[:max_length]
                    # Ensure not ending with incomplete word
                    if len(title) < len(sentence):
                        # Try to end at punctuation or natural break point
                        break_points = [',', '，', ':', '：', ' ', '\u3000']
                        for bp in break_points:
                            if bp in title:
                                title = title.rsplit(bp, 1)[0]
                                break
                    return title.strip()

        # If no suitable sentence found, take first few characters
        if len(content) >= 5:
            title = content[:max_length]
            # Avoid cutting words
            if len(title) < len(content):
                # Find last space or punctuation
                for i in range(len(title)-1, 0, -1):
                    if title[i] in ' ，。！？；：':
                        title = title[:i]
                        break
            return title.strip()

    else:
        # English processing
        sentences = re.split(r'[.!?;]', content)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) >= 10 and len(sentence) <= max_length * 2:
                # Contains meaningful words
                if re.search(r'\b(the|a|an|is|are|was|were|in|on|at|to|for)\b', sentence, re.IGNORECASE):
                    title = sentence[:max_length]
                    # Truncate at appropriate position
                    words = title.split()
                    if len(words) > 1:
                        title = ' '.join(words[:-1]) if len(' '.join(words)) > max_length else ' '.join(words)
                    return title.strip()

        # fallback
        if len(content) >= 10:
            title = content[:max_length]
            words = title.split()
            if len(words) > 1:
                title = ' '.join(words[:-1])
            return title.strip()

    return ""


def enhance_chapter_title(chapter_title: str, chapter_content: str, language: str = 'chinese', llm_assistant=None) -> str:
    """
    Enhance chapter title: if title is too simple, try using LLM or extract meaningful title from content

    :param chapter_title: Original chapter title
    :param chapter_content: Chapter content
    :param language: Language type
    :param llm_assistant: LLM assistant instance (optional)
    :return: Enhanced title
    """
    # If title already has substantial content, return directly
    if not is_simple_chapter_title(chapter_title, language):
        return chapter_title

    # Extract chapter number
    if language == 'chinese':
        chapter_num_match = re.search(r'(第[一二三四五六七八九十百千万\d]+章)', chapter_title)
        chapter_number = chapter_num_match.group(1) if chapter_num_match else chapter_title
    else:
        chapter_num_match = re.search(r'(Chapter\s+[\dIVXivx]+)', chapter_title, re.IGNORECASE)
        chapter_number = chapter_num_match.group(1) if chapter_num_match else chapter_title

    # Prioritize using LLM to generate title
    if llm_assistant:
        try:
            logger.info(f"Using LLM to generate chapter title: {chapter_number}")
            result = llm_assistant.generate_chapter_title(
                chapter_number=chapter_number,
                chapter_content=chapter_content,
                language=language,
                max_content_length=1000
            )

            # If LLM generation successful and confidence high enough
            if result.get('title') and result.get('confidence', 0) > 0.5:
                generated_title = result['title'].strip()
                if generated_title:
                    # Combine chapter number and generated title
                    if language == 'chinese':
                        return f"{chapter_number} {generated_title}"
                    else:
                        return f"{chapter_number}: {generated_title}"
            else:
                logger.warning(f"LLM generated title confidence too low or empty: {result.get('confidence', 0):.2f}")
        except Exception as e:
            logger.warning(f"LLM title generation failed, falling back to rule extraction: {e}")

    # Fallback: extract meaningful title from content
    meaningful_title = extract_meaningful_title(chapter_content, language)

    if meaningful_title:
        # Keep original chapter number, add substantial content
        if language == 'chinese':
            return f"{chapter_number} {meaningful_title}"
        else:
            return f"{chapter_number}: {meaningful_title}"

    # If unable to extract meaningful content, return original title
    return chapter_title
