"""
Table of contents detection and removal utilities
"""
import re
import logging
from typing import Optional
from .patterns import ChinesePatterns, EnglishPatterns
from .language_detector import detect_language
from ..parser_config import ParserConfig, DEFAULT_CONFIG

logger = logging.getLogger(__name__)


def remove_table_of_contents(content: str, language: str = None, llm_assistant=None, config: Optional[ParserConfig] = None) -> str:
    """
    Remove the table of contents section from the text to avoid interference with chapter recognition.
    Supports both Chinese and English table of contents recognition.

    Enhanced version: Detects TOC by identifying regions with dense chapter-like patterns.
    Optionally uses LLM for more accurate TOC identification.

    :param content: Original text content
    :param language: Language type, 'chinese' or 'english', auto-detect if None
    :param llm_assistant: Optional LLM assistant for intelligent TOC detection
    :param config: Parser configuration (optional, uses default if None)
    :return: Text content with table of contents removed
    """
    if config is None:
        config = DEFAULT_CONFIG

    if not content or not content.strip():
        return content

    # Auto-detect language
    if language is None:
        language = detect_language(content)

    # Try LLM-based TOC detection first if available
    if llm_assistant:
        try:
            logger.info("Attempting to use LLM to recognize table of contents...")
            toc_result = llm_assistant.identify_table_of_contents(content[:5000], language)

            if toc_result.get('has_toc') and toc_result.get('confidence', 0) > config.llm_toc_detection_threshold:
                logger.info(f"LLM confirmed table of contents exists (confidence: {toc_result['confidence']:.2f})")

                # Use rule-based method to find and remove TOC, but with LLM confirmation
                # This provides a good balance between accuracy and robustness
                pass  # Continue to rule-based detection below
            else:
                logger.info(f"LLM did not detect TOC or confidence low (has_toc={toc_result.get('has_toc')}, confidence={toc_result.get('confidence', 0):.2f})")
                # If LLM says no TOC with high confidence, skip TOC removal
                if not toc_result.get('has_toc') and toc_result.get('confidence', 0) > config.llm_no_toc_threshold:
                    logger.info("LLM high confidence judgment: no TOC, skipping TOC removal")
                    return content
        except Exception as e:
            logger.warning(f"LLM TOC recognition failed, falling back to rule method: {e}")

    # Select corresponding patterns
    if language == 'english':
        patterns = EnglishPatterns()
        toc_keywords = patterns.TOC_KEYWORDS
        preface_keywords = patterns.PREFACE_KEYWORDS
        chapter_patterns = [patterns.CHAPTER_PATTERN, patterns.VOLUME_PATTERN]
    else:
        patterns = ChinesePatterns()
        toc_keywords = patterns.TOC_KEYWORDS
        preface_keywords = patterns.PREFACE_KEYWORDS
        chapter_patterns = [patterns.CHAPTER_PATTERN, patterns.VOLUME_PATTERN]

    lines = content.split('\n')

    # Find table of contents start position
    toc_start = -1
    toc_end = -1

    # Method 1: Explicit TOC keyword detection
    for i, line in enumerate(lines):
        stripped_line = line.strip()

        # Identify table of contents start: standalone line with TOC keywords
        if stripped_line in toc_keywords or any(keyword.lower() == stripped_line.lower() for keyword in toc_keywords):
            toc_start = i
            logger.info(f"Detected TOC title at line {i+1}: {stripped_line}")
            break

    # Method 2: Detect dense chapter pattern region (TOC without explicit keyword)
    if toc_start == -1:
        # Scan for regions with abnormally high density of chapter-like patterns
        window_size = 20  # Check 20 lines at a time
        max_score = 0
        max_score_start = -1
        candidate_info = None

        for i in range(0, min(len(lines), 500), 3):  # Only check first 500 lines, step by 3
            window_end = min(i + window_size, len(lines))
            window_lines = lines[i:window_end]

            # Count chapter-like patterns in window
            chapter_count = 0
            short_line_count = 0  # Count of short lines (typical of TOC)
            total_chars = 0
            consecutive_chapters = 0  # Consecutive chapter-pattern lines
            max_consecutive = 0
            has_page_numbers = False  # Check for page number patterns

            for j, line in enumerate(window_lines):
                stripped = line.strip()
                total_chars += len(stripped)

                # Check for short lines (TOC characteristic)
                if 5 < len(stripped) < 80:
                    short_line_count += 1

                # Check if line matches chapter pattern
                is_chapter_line = False
                for pattern in chapter_patterns:
                    if pattern.search(stripped):
                        # Check if it's a short line (TOC entry, not actual chapter with content)
                        if len(stripped) < 80:  # TOC entries are usually short
                            chapter_count += 1
                            is_chapter_line = True
                        break

                # Track consecutive chapter patterns
                if is_chapter_line:
                    consecutive_chapters += 1
                    max_consecutive = max(max_consecutive, consecutive_chapters)
                else:
                    consecutive_chapters = 0

                # Check for page number patterns (common in TOC)
                if re.search(r'\d{1,4}\s*$', stripped):  # Ends with numbers (page numbers)
                    has_page_numbers = True

            # Calculate multiple scoring factors
            score = 0

            # Factor 1: Chapter density (chapters per 1000 characters)
            if total_chars > 100:  # Ensure sufficient text
                density = (chapter_count * 1000) / total_chars
                if density > 100:  # High density
                    score += density * 0.5  # Weight 0.5

            # Factor 2: Absolute chapter count (at least 5 chapters)
            if chapter_count >= 5:
                score += chapter_count * 2  # Weight 2

            # Factor 3: Consecutive chapter patterns (strong indicator)
            if max_consecutive >= 3:
                score += max_consecutive * 10  # Weight 10

            # Factor 4: High ratio of short lines
            if len(window_lines) > 0:
                short_ratio = short_line_count / len(window_lines)
                if short_ratio > 0.6:  # More than 60% short lines
                    score += short_ratio * 20  # Weight 20

            # Factor 5: Presence of page numbers
            if has_page_numbers:
                score += 15  # Bonus points

            # Factor 6: Early position in document (TOC usually at beginning)
            position_bonus = max(0, 50 - i)  # Earlier lines get higher bonus
            score += position_bonus * 0.2

            # Update best candidate
            if score > max_score and score > config.toc_detection_score_threshold:  # Use configured threshold
                max_score = score
                max_score_start = i
                candidate_info = {
                    'chapters': chapter_count,
                    'density': density if total_chars > 100 else 0,
                    'consecutive': max_consecutive,
                    'short_ratio': short_ratio if len(window_lines) > 0 else 0,
                    'has_page_nums': has_page_numbers
                }

        # If found high-score region, consider it as TOC
        if max_score > config.toc_detection_score_threshold:  # Use configured threshold
            toc_start = max_score_start
            logger.info(f"Detected suspected TOC region starting at line {toc_start+1}, comprehensive score: {max_score:.1f}")

    # Find TOC end
    if toc_start != -1:
        # Look for the end of TOC
        chapter_density_window = 10

        for i in range(toc_start + 1, len(lines)):
            stripped_line = lines[i].strip()

            # Check for long paragraph (main content)
            if len(stripped_line) > 100:
                # Check if it's NOT a chapter title
                is_chapter = False
                for pattern in chapter_patterns:
                    if pattern.search(stripped_line):
                        is_chapter = True
                        break

                if not is_chapter:
                    # Found long content paragraph
                    toc_end = i - 1
                    logger.info(f"TOC ends at line {toc_end+1} (detected long paragraph of main content)")
                    break

            # Check for consecutive empty lines followed by content
            if not stripped_line:
                # Look ahead for content
                next_content_idx = -1
                for j in range(i + 1, min(i + 5, len(lines))):
                    if lines[j].strip():
                        next_content_idx = j
                        break

                if next_content_idx != -1:
                    next_line = lines[next_content_idx].strip()
                    # If next is long content or preface
                    if len(next_line) > 50:
                        is_chapter = any(p.search(next_line) for p in chapter_patterns)
                        is_preface = any(keyword.lower() == next_line.lower() for keyword in preface_keywords)

                        if not is_chapter or is_preface:
                            toc_end = i
                            logger.info(f"TOC ends at line {toc_end+1} (empty line followed by main content)")
                            break

            # Safety: if scanned too far without finding end, limit TOC region
            if i - toc_start > config.toc_max_scan_lines:
                toc_end = i
                logger.warning(f"TOC region too long, forcing end at line {toc_end+1}")
                break

    # Remove TOC if found
    if toc_start != -1 and toc_end != -1 and toc_end > toc_start:
        removed_lines = toc_end - toc_start + 1
        logger.info(f"Removed TOC: line {toc_start+1} to line {toc_end+1}, total {removed_lines} lines")
        remaining_lines = lines[:toc_start] + lines[toc_end + 1:]
        return '\n'.join(remaining_lines)

    return content
