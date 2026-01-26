"""
Chapter validation and merging utilities
"""
import re
import logging
from typing import List
from ..data_structures import Chapter

logger = logging.getLogger(__name__)


def is_valid_chapter_title(match, content: str, language: str = 'chinese') -> bool:
    """
    Validate if a regex match is a genuine chapter title, not an inline reference.
    Enhanced with better context checking to reduce false positives.

    :param match: Regex match object
    :param content: Full text content
    :param language: Language type, 'chinese' or 'english'
    :return: True if valid chapter title, False if likely a reference
    """
    match_text = match.group(0).strip()
    match_start = match.start()
    match_end = match.end()

    # 0. Enhanced: Check if in TOC region (first 15% of file with short content)
    # This is a strong indicator of TOC entries
    file_position_ratio = match_start / len(content) if len(content) > 0 else 0
    if file_position_ratio < 0.15:  # In first 15% of file
        # Check if next chapter is very close (TOC pattern)
        # Use proper chapter pattern instead of just "第"
        next_chapter_match = re.search(r'第[一二三四五六七八九十百千万壹贰叁肆伍陆柒捌玖拾佰仟萬\d]{1,4}章',
                                      content[match_end:match_end + 200])
        if next_chapter_match:
            distance = next_chapter_match.start()
            if distance < 150:  # Next chapter within 150 chars
                logger.debug(f"Rejected chapter title (TOC region, next chapter at {distance} chars): {match_text}")
                return False

    # 1. Check if title is too long (likely not a real chapter title)
    if len(match_text) > 100:
        logger.debug(f"Rejected chapter title (too long): {match_text[:50]}...")
        return False

    # 2. Check context before the match
    context_before_start = max(0, match_start - 50)
    context_before = content[context_before_start:match_start]

    # Check if it's in the middle of a sentence (preceded by comma, etc.)
    if language == 'chinese':
        # Chinese: check for patterns like "在第X章", "如第X章", "见第X章"
        if re.search(r'[在如见到自从正前后于从到至]第.{0,5}章', context_before[-20:] + match_text[:10]):
            logger.debug(f"Rejected chapter title (inline reference): {match_text}")
            return False

        # Check if preceded by punctuation that suggests inline reference
        if re.search(r'[，,、；;]第.{0,5}章', context_before[-10:] + match_text[:10]):
            logger.debug(f"Rejected chapter title (after punctuation): {match_text}")
            return False
    else:
        # English: check for patterns like "in Chapter X", "see Chapter X"
        if re.search(r'(?:in|see|from|at|to|of|for)\s+Chapter\s+\w+', context_before[-30:] + match_text[:20], re.IGNORECASE):
            logger.debug(f"Rejected chapter title (inline reference): {match_text}")
            return False

    # 3. Check context after the match
    context_after_end = min(len(content), match_end + 300)  # Increased from 150 to 300
    context_after = content[match_end:context_after_end]

    if language == 'chinese':
        # Check for continuation phrases like "结束时", "中", "里"
        if re.match(r'^\s*[结结束时中里]', context_after):
            logger.debug(f"Rejected chapter title (continuation): {match_text}")
            return False

        # Check if followed by comma (inline reference pattern)
        if re.match(r'^\s*[，,]', context_after):
            logger.debug(f"Rejected chapter title (followed by comma): {match_text}")
            return False

        # Enhanced: Check if followed immediately by another chapter title (likely TOC)
        # Look for another chapter pattern within 100 chars (increased from 20)
        if re.search(r'^\s{0,50}.{0,50}第.{1,8}章', context_after[:100]):
            logger.debug(f"Rejected chapter title (consecutive titles, likely TOC): {match_text}")
            return False

        # Additional check: Count chapter titles in next 300 chars
        # If 2+ chapters found, likely TOC
        chapter_pattern = r'第[一二三四五六七八九十百千万壹贰叁肆伍陆柒捌玖拾佰仟萬\d]{1,4}章'
        chapters_nearby = re.findall(chapter_pattern, context_after[:300])
        if len(chapters_nearby) >= 2:
            logger.debug(f"Rejected chapter title (high density {len(chapters_nearby)} chapters in 300 chars, likely TOC): {match_text}")
            return False
    else:
        # English: check for continuation like "ends", "of the book"
        if re.match(r'^\s*(?:ends?|of|in|at)\s', context_after, re.IGNORECASE):
            logger.debug(f"Rejected chapter title (continuation): {match_text}")
            return False

        # Enhanced: Check if followed immediately by another chapter title (likely TOC)
        if re.search(r'^\s{0,10}Chapter\s+[\dIVXivx]+', context_after[:30], re.IGNORECASE):
            logger.debug(f"Rejected chapter title (consecutive titles, likely TOC): {match_text}")
            return False

    # 4. Check if the match is at the beginning of a line (real chapter titles usually are)
    # Allow some whitespace before the match
    line_start = content.rfind('\n', 0, match_start)
    if line_start == -1:
        line_start = 0
    else:
        line_start += 1

    text_before_match = content[line_start:match_start]
    if text_before_match.strip():  # Non-whitespace characters before match on same line
        # There's text before the chapter marker on the same line
        # This suggests it's not a standalone chapter title
        logger.debug(f"Rejected chapter title (not at line start): {match_text}")
        return False

    # 5. Enhanced: Check if preceded by blank line(s) (true titles often have space before)
    # Only check if not at the very beginning of the document
    if match_start > 10:
        context_before_extended = content[max(0, match_start - 30):match_start]
        # Check if there's a blank line (double newline) before the title
        # Real chapter titles usually have at least one blank line before them
        if not re.search(r'\n\s*\n\s*$', context_before_extended) and match_start > 30:
            # No blank line found, but allow exception for first chapter
            # Check if there's substantial content before (more than 100 chars)
            if match_start > 100:
                logger.debug(f"Warning: Chapter title without preceding blank line: {match_text}")
                # Don't reject, but this is a warning sign

    # 6. Enhanced: Check if followed by actual content (not immediately another title or empty)
    # Real chapter titles should have content after them
    content_after_stripped = context_after.strip()
    if content_after_stripped:
        # Check if the content starts with actual text, not another structural element
        first_line = content_after_stripped.split('\n')[0][:50]
        if len(first_line) < 5:  # Very short first line might be problematic
            logger.debug(f"Warning: Very short content after title: {match_text}")

    return True


def validate_and_merge_chapters(chapters: List[Chapter], language: str = 'chinese', min_length: int = 500) -> List[Chapter]:
    """
    Validate chapter structure and merge chapters that are too short (likely misidentified).

    :param chapters: List of chapters to validate
    :param language: Language type, 'chinese' or 'english'
    :param min_length: Minimum chapter length in characters
    :return: Validated and merged chapter list
    """
    if not chapters:
        return chapters

    valid_chapters = []
    accumulated_content = ""
    accumulated_title = None

    for i, chapter in enumerate(chapters):
        # Calculate total content length (chapter content + all sections)
        total_content = chapter.content
        for section in chapter.sections:
            total_content += section.content

        content_length = len(total_content.strip())

        # Check if chapter is too short
        if content_length < min_length:
            logger.warning(f"Chapter '{chapter.title}' is too short ({content_length} chars), may be misidentified")

            # First chapter or no previous accumulated content
            if not valid_chapters and not accumulated_content:
                # Store this chapter for potential merging
                accumulated_title = chapter.title
                accumulated_content = f"{chapter.title}\n\n{chapter.content}"
            else:
                # Merge into previous chapter or accumulated content
                if valid_chapters:
                    # Merge into last valid chapter
                    last_chapter = valid_chapters[-1]
                    merged_content = last_chapter.content
                    if merged_content:
                        merged_content += f"\n\n{chapter.title}\n{chapter.content}"
                    else:
                        merged_content = f"{chapter.title}\n{chapter.content}"

                    # Keep the original chapter structure but update content
                    valid_chapters[-1] = Chapter(
                        title=last_chapter.title,
                        content=merged_content,
                        sections=last_chapter.sections
                    )
                    logger.info(f"Merged short chapter '{chapter.title}' into '{last_chapter.title}'")
                else:
                    # Add to accumulated content
                    accumulated_content += f"\n\n{chapter.title}\n{chapter.content}"
        else:
            # Chapter is long enough, it's valid
            if accumulated_content:
                # First, add the accumulated content as a chapter
                preface_title = accumulated_title or ("前言" if language == 'chinese' else "Preface")
                valid_chapters.append(Chapter(
                    title=preface_title,
                    content=accumulated_content.strip(),
                    sections=[]
                ))
                accumulated_content = ""
                accumulated_title = None

            # Then add current chapter
            valid_chapters.append(chapter)

    # Handle any remaining accumulated content
    if accumulated_content:
        preface_title = accumulated_title or ("前言" if language == 'chinese' else "Preface")
        valid_chapters.append(Chapter(
            title=preface_title,
            content=accumulated_content.strip(),
            sections=[]
        ))

    logger.info(f"Chapter validation complete: {len(chapters)} -> {len(valid_chapters)} chapters")
    return valid_chapters


def estimate_chapter_confidence(chapter_title: str, chapter_content: str, language: str = 'chinese') -> float:
    """
    Estimate confidence score for a detected chapter (for RuleBasedParserWithConfidence).

    :param chapter_title: Chapter title
    :param chapter_content: Chapter content
    :param language: Language type, 'chinese' or 'english'
    :return: Confidence score between 0.0 and 1.0
    """
    confidence = 0.5  # Base confidence

    # Factor 1: Title structure validation
    if language == 'chinese':
        # Check for standard chapter patterns
        if re.match(r'^第[一二三四五六七八九十百千万\d]+章', chapter_title):
            confidence += 0.2
        # Check for special chapter types
        if re.match(r'^(?:番外|番外篇|外传|特别篇|插话|后记|尾声|终章|楔子|序章)', chapter_title):
            confidence += 0.15
    else:
        # English chapter patterns
        if re.match(r'^Chapter\s+[\dIVXivx]+', chapter_title, re.IGNORECASE):
            confidence += 0.2

    # Factor 2: Content length validation
    content_length = len(chapter_content.strip())
    if content_length > 1000:
        confidence += 0.15
    elif content_length > 500:
        confidence += 0.1
    elif content_length < 100:
        confidence -= 0.2

    # Factor 3: Title complexity (not too simple)
    from .title_enhancer import is_simple_chapter_title
    if not is_simple_chapter_title(chapter_title, language):
        confidence += 0.1

    # Factor 4: Content quality indicators
    if language == 'chinese':
        # Check for narrative indicators
        if re.search(r'[。！？；]', chapter_content):
            confidence += 0.05
    else:
        # Check for English sentences
        if re.search(r'[.!?]\s+[A-Z]', chapter_content):
            confidence += 0.05

    # Clamp confidence to [0.0, 1.0]
    return max(0.0, min(1.0, confidence))
