"""
Core parsing functions for hierarchical content structure
"""
import re
import logging
from typing import List, Optional
from ..data_structures import Section, Chapter, Volume
from ..parser_config import ParserConfig, DEFAULT_CONFIG
from .patterns import ChinesePatterns, EnglishPatterns
from .language_detector import detect_language
from .toc_remover import remove_table_of_contents
from .validator import is_valid_chapter_title, validate_and_merge_chapters
from .title_enhancer import is_simple_chapter_title, extract_meaningful_title

logger = logging.getLogger(__name__)


def parse_hierarchical_content(content: str, config: Optional[ParserConfig] = None, llm_assistant=None, skip_toc_removal: bool = False, context=None, resume_state=None) -> List[Volume]:
    """
    Split text content into three-level hierarchical structure: volumes, chapters, sections.
    Supports both Chinese and English book formats.
    Optimized version using finditer() for better performance.

    :param content: Text content
    :param config: Parser configuration (optional, uses default if None)
    :param llm_assistant: Optional LLM assistant for intelligent TOC detection
    :param skip_toc_removal: If True, skip table of contents removal (useful when content already processed)
    :return: List of volumes containing complete hierarchical structure
    """
    if config is None:
        config = DEFAULT_CONFIG

    if not content or not content.strip():
        # If content is empty, return a volume with empty chapter
        return [Volume(title=None, chapters=[Chapter(title="Empty Content", content="This document is empty or cannot be parsed.", sections=[])])]

    # Detect language
    language = detect_language(content)

    # Preprocessing: remove table of contents to avoid interference with content parsing
    if not skip_toc_removal:
        content = remove_table_of_contents(content, language, llm_assistant, config)

    # Select corresponding patterns based on language
    if language == 'english':
        patterns = EnglishPatterns()
        volume_pattern = patterns.VOLUME_PATTERN
    else:
        patterns = ChinesePatterns()
        volume_pattern = patterns.VOLUME_PATTERN

    # Optimized: Use finditer() instead of split() for better performance
    volume_matches = list(volume_pattern.finditer(content))

    volumes = []

    if not volume_matches:
        # No volumes, only chapters
        chapters = parse_chapters_from_content(content, language, config, llm_assistant, context, resume_state)
        # Validate and merge short chapters if enabled
        if config.enable_length_validation:
            chapters = validate_and_merge_chapters(chapters, language, config.min_chapter_length)
        if chapters:
            volumes.append(Volume(title=None, chapters=chapters))
        else:
            # If no chapters detected, treat entire content as one chapter
            default_title = "正文" if language == 'chinese' else "Content"
            volumes.append(Volume(title=None, chapters=[Chapter(title=default_title, content=content.strip(), sections=[])]))
    else:
        # Handle first part (possibly preface, content without volume title)
        first_volume_start = volume_matches[0].start()
        if first_volume_start > 0 and content[:first_volume_start].strip():
            pre_content = content[:first_volume_start]
            pre_chapters = parse_chapters_from_content(pre_content, language, config, llm_assistant, context, resume_state)
            # Validate and merge short chapters if enabled
            if config.enable_length_validation:
                pre_chapters = validate_and_merge_chapters(pre_chapters, language, config.min_chapter_length)
            if pre_chapters:
                volumes.append(Volume(title=None, chapters=pre_chapters))
            else:
                # If first part has no chapter structure, treat as preface chapter
                preface_title = "序言" if language == 'chinese' else "Preface"
                volumes.append(Volume(title=None, chapters=[Chapter(title=preface_title, content=pre_content.strip(), sections=[])]))

        # Handle parts with volume titles
        seen_volume_titles = set()  # Track seen volume titles
        for i, match in enumerate(volume_matches):
            volume_title = match.group(1).strip()

            # Get volume content (from end of current match to start of next match, or end of text)
            volume_start = match.end()
            volume_end = volume_matches[i + 1].start() if i + 1 < len(volume_matches) else len(content)
            volume_content = content[volume_start:volume_end]

            # Check for duplicate volume titles, skip if duplicate
            if volume_title and volume_title not in seen_volume_titles:
                seen_volume_titles.add(volume_title)
                chapters = parse_chapters_from_content(volume_content, language, config, llm_assistant, context, resume_state)
                # Validate and merge short chapters if enabled
                if config.enable_length_validation:
                    chapters = validate_and_merge_chapters(chapters, language, config.min_chapter_length)
                if chapters:
                    volumes.append(Volume(title=volume_title, chapters=chapters))
                elif volume_content.strip():  # If has content but no chapter structure
                    # Treat entire volume content as one chapter
                    default_title = "正文" if language == 'chinese' else "Content"
                    volumes.append(Volume(title=volume_title, chapters=[Chapter(title=default_title, content=volume_content.strip(), sections=[])]))

    # Ensure at least one volume
    if not volumes:
        error_title = "未知内容" if language == 'chinese' else "Unknown Content"
        error_content = "无法解析文档结构，请检查文档格式。" if language == 'chinese' else "Unable to parse document structure. Please check document format."
        volumes.append(Volume(title=None, chapters=[Chapter(title=error_title, content=error_content, sections=[])]))

    return volumes


def parse_chapters_from_content(content: str, language: str = 'chinese', config: Optional[ParserConfig] = None, llm_assistant=None, context=None, resume_state=None) -> List[Chapter]:
    """
    Split chapters and sections from given content.
    Supports both Chinese and English chapter formats.
    Optimized version using finditer() for better performance.
    Validates chapter titles to filter out inline references.

    :param content: Text content
    :param language: Language type, 'chinese' or 'english'
    :param config: Parser configuration (optional)
    :param llm_assistant: LLM assistant for title enhancement
    :param context: Context for progress reporting
    :param resume_state: Resume state for checkpoint resume
    :return: Chapter list, each chapter contains title, content and section list
    """
    if config is None:
        config = DEFAULT_CONFIG

    if not content or not content.strip():
        return []

    # Select corresponding patterns based on language
    if language == 'english':
        patterns = EnglishPatterns()
        chapter_pattern = patterns.CHAPTER_PATTERN
        preface_keywords = patterns.PREFACE_KEYWORDS
    else:
        patterns = ChinesePatterns()
        chapter_pattern = patterns.CHAPTER_PATTERN
        preface_keywords = patterns.PREFACE_KEYWORDS

    # Optimized: Use finditer() instead of split()
    all_matches = list(chapter_pattern.finditer(content))

    # Validate matches to filter out inline references (if enabled)
    if config.enable_chapter_validation:
        chapter_matches = [match for match in all_matches if is_valid_chapter_title(match, content, language)]
        if len(all_matches) != len(chapter_matches):
            logger.info(f"Filtered out {len(all_matches) - len(chapter_matches)} inline chapter references")
    else:
        chapter_matches = all_matches

    chapter_list = []

    # If no chapter titles found, return empty list (let parent function handle)
    if not chapter_matches:
        return chapter_list

    # Process first part (possibly preface content without chapter title)
    first_chapter_start = chapter_matches[0].start()
    if first_chapter_start > 0 and content[:first_chapter_start].strip():
        preface_content = content[:first_chapter_start].strip()
        sections = parse_sections_from_content(preface_content, language)
        preface_title = "前言" if language == 'chinese' else "Preface"
        if sections:
            chapter_list.append(Chapter(title=preface_title, content="", sections=sections))
        else:
            chapter_list.append(Chapter(title=preface_title, content=preface_content, sections=[]))

    # Process each matched chapter
    seen_titles = set()  # Track seen chapter titles
    total_chapters = len(chapter_matches)

    # Set total chapters for resume checkpoint
    if resume_state:
        resume_state.set_total_chapters(total_chapters)

    # Log start of chapter processing
    if llm_assistant:
        logger.info(f"Starting to use LLM to generate chapter titles, total {total_chapters} chapters")
        print(f"\n{'='*60}")
        print(f"Starting intelligent chapter title generation (total {total_chapters} chapters)")
        if resume_state and resume_state.get_processed_count() > 0:
            print(f"Resume from checkpoint: Already processed {resume_state.get_processed_count()} chapters, continuing...")
        print(f"{'='*60}")

    # 【Optimization】Batch collect chapters that need LLM enhancement
    chapters_to_enhance = []
    chapter_data = []  # Store chapter metadata

    for i, match in enumerate(chapter_matches):
        chapter_title = match.group(1).strip()

        # Resume checkpoint: skip already processed chapters (using index)
        if resume_state and resume_state.is_chapter_processed(i):
            if llm_assistant:
                print(f"[{i+1}/{total_chapters}] Skipping already processed chapter: {chapter_title[:20]}...")
            continue

        # Get chapter content (from end of current match to start of next match, or end of text)
        chapter_start = match.end()
        chapter_end = chapter_matches[i + 1].start() if i + 1 < len(chapter_matches) else len(content)
        chapter_content = content[chapter_start:chapter_end].strip('\n\r')

        if chapter_title and chapter_title not in seen_titles:  # Ensure title is not empty and not duplicate
            # Store chapter data
            chapter_data.append({
                'index': i,
                'title': chapter_title,
                'content': chapter_content,
                'is_simple': is_simple_chapter_title(chapter_title, language)
            })

            # Collect chapters that need enhancement
            if is_simple_chapter_title(chapter_title, language):
                # Extract chapter number
                if language == 'chinese':
                    chapter_num_match = re.search(r'(第[一二三四五六七八九十百千万\d]+章)', chapter_title)
                    chapter_number = chapter_num_match.group(1) if chapter_num_match else chapter_title
                else:
                    chapter_num_match = re.search(r'(Chapter\s+[\dIVXivx]+)', chapter_title, re.IGNORECASE)
                    chapter_number = chapter_num_match.group(1) if chapter_num_match else chapter_title

                chapters_to_enhance.append({
                    'index': i,
                    'number': chapter_number,
                    'content': chapter_content
                })

    # 【Optimization】Batch call LLM to generate titles
    enhanced_titles = {}
    if llm_assistant and chapters_to_enhance:
        try:
            logger.info(f"Batch generating titles for {len(chapters_to_enhance)} simple chapters...")
            print(f"\nBatch generating {len(chapters_to_enhance)} chapter titles...")

            batch_results = llm_assistant.generate_chapter_titles_batch(
                chapters_to_enhance,
                language=language,
                max_content_length=400
            )

            # Build index to title mapping
            for result in batch_results:
                idx = result.get('index')
                if idx is not None:
                    idx = idx - 1  # Convert to 0-based index
                    if result.get('title') and result.get('confidence', 0) > 0.5:
                        enhanced_titles[idx] = result['title']
                        logger.info(f"[{idx+1}] Generated title: {result['title']} (confidence: {result['confidence']:.2f})")

            print(f"✓ Batch generation complete: {len(enhanced_titles)}/{len(chapters_to_enhance)} titles successful")

        except Exception as e:
            logger.warning(f"Batch title generation failed, falling back to rule extraction: {e}")
            print(f"⚠ Batch generation failed, using rule extraction: {e}")

    # Process all chapters, apply enhanced titles
    for ch_data in chapter_data:
        i = ch_data['index']
        chapter_title = ch_data['title']
        chapter_content = ch_data['content']

        # Calculate and report progress: between 5% to 95% (chapter generation stage accounts for 90%)
        progress_percent = int((i + 1) / total_chapters * 100)
        if context:
            # Map chapter processing progress to 5% - 95% range
            mapped_progress = 5 + int((i + 1) / total_chapters * 90)
            context.report_progress(mapped_progress)

        # Print progress
        print(f"[{i+1}/{total_chapters}] ({progress_percent}%) Processing chapter: {chapter_title[:20]}...")

        # Apply enhanced title (if available)
        if i in enhanced_titles:
            # Extract chapter number
            if language == 'chinese':
                chapter_num_match = re.search(r'(第[一二三四五六七八九十百千万\d]+章)', chapter_title)
                chapter_number = chapter_num_match.group(1) if chapter_num_match else chapter_title
                enhanced_title = f"{chapter_number} {enhanced_titles[i]}"
            else:
                chapter_num_match = re.search(r'(Chapter\s+[\dIVXivx]+)', chapter_title, re.IGNORECASE)
                chapter_number = chapter_num_match.group(1) if chapter_num_match else chapter_title
                enhanced_title = f"{chapter_number}: {enhanced_titles[i]}"

            logger.info(f"[{i+1}/{total_chapters}] Enhanced: '{chapter_title}' -> '{enhanced_title}'")
            print(f"  ✓ Applied title: {enhanced_title}")
            final_title = enhanced_title
        elif ch_data['is_simple'] and not llm_assistant:
            # If no LLM, fall back to rule extraction
            meaningful_title = extract_meaningful_title(chapter_content, language)
            if meaningful_title:
                if language == 'chinese':
                    chapter_num_match = re.search(r'(第[一二三四五六七八九十百千万\d]+章)', chapter_title)
                    chapter_number = chapter_num_match.group(1) if chapter_num_match else chapter_title
                    final_title = f"{chapter_number} {meaningful_title}"
                else:
                    chapter_num_match = re.search(r'(Chapter\s+[\dIVXivx]+)', chapter_title, re.IGNORECASE)
                    chapter_number = chapter_num_match.group(1) if chapter_num_match else chapter_title
                    final_title = f"{chapter_number}: {meaningful_title}"
                print(f"  - Rule-extracted title: {meaningful_title}")
            else:
                final_title = chapter_title
                print(f"  - Keeping original title")
        else:
            final_title = chapter_title
            print(f"  - Keeping original title")

        seen_titles.add(final_title)

        # Further analyze chapter content for sections
        sections = parse_sections_from_content(chapter_content, language)
        if sections:
            # If has sections, chapter content is empty (all content is in sections)
            chapter_list.append(Chapter(title=final_title, content="", sections=sections))
        else:
            # If no sections, chapter directly contains content
            if not chapter_content.strip():
                empty_content = "此章节内容为空。" if language == 'chinese' else "This chapter is empty."
                chapter_content = empty_content
            chapter_list.append(Chapter(title=final_title, content=chapter_content, sections=[]))

        # Resume checkpoint: mark chapter processed (using index)
        if resume_state:
            resume_state.mark_chapter_processed(i)

    # Completion log
    if llm_assistant:
        print(f"{'='*60}")
        print(f"✓ Chapter title generation complete! Processed {total_chapters} chapters total")
        print(f"{'='*60}\n")
        logger.info(f"Chapter title generation complete, processed {total_chapters} chapters total")

    return chapter_list


def parse_sections_from_content(content: str, language: str = 'chinese') -> List[Section]:
    """
    Split sections from given chapter content.
    Supports both Chinese and English section formats.
    Optimized version using finditer() for better performance.

    :param content: Chapter content
    :param language: Language type, 'chinese' or 'english'
    :return: Section list, each section contains title and content
    """
    if not content or not content.strip():
        return []

    # Select corresponding patterns based on language
    if language == 'english':
        patterns = EnglishPatterns()
        # Try multiple section patterns for English
        section_patterns = [patterns.SECTION_PATTERN, patterns.NUMBERED_SECTION_PATTERN]
    else:
        patterns = ChinesePatterns()
        section_patterns = [patterns.SECTION_PATTERN]

    section_list = []
    section_matches = None
    active_pattern = None

    # Try different section patterns
    for pattern in section_patterns:
        matches = list(pattern.finditer(content))
        if matches:  # Found matching pattern
            section_matches = matches
            active_pattern = pattern
            break

    # If no section pattern found, return empty list
    if not section_matches:
        return section_list

    # Handle first part (chapter preface, content without section title)
    first_section_start = section_matches[0].start()
    if first_section_start > 0 and content[:first_section_start].strip():
        preface_title = "章节序言" if language == 'chinese' else "Chapter Preface"
        section_list.append(Section(title=preface_title, content=content[:first_section_start].strip()))

    # Process each matched section
    seen_titles = set()  # Track seen section titles
    for i, match in enumerate(section_matches):
        section_title = match.group(1).strip()

        # Get section content (from end of current match to start of next match, or end of text)
        section_start = match.end()
        section_end = section_matches[i + 1].start() if i + 1 < len(section_matches) else len(content)
        section_content = content[section_start:section_end].strip('\n\r')

        if section_title and section_title not in seen_titles:  # Ensure title is not empty and not duplicate
            seen_titles.add(section_title)
            # Ensure section content is not empty
            if not section_content.strip():
                empty_content = "此节内容为空。" if language == 'chinese' else "This section is empty."
                section_content = empty_content
            section_list.append(Section(title=section_title, content=section_content))

    return section_list
