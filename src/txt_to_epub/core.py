import os
import logging
import chardet
from typing import Optional, Dict, Any
from ebooklib import epub

# Try to import tqdm, make it optional
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    # Create a dummy tqdm class
    class tqdm:
        def __init__(self, *args, **kwargs):
            self.total = kwargs.get('total', 0)
            self.n = 0
        def update(self, n=1):
            self.n += n
        def set_description(self, desc=None):
            """Dummy method to match tqdm interface."""
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass

from .data_structures import Volume
from .parser import parse_hierarchical_content
from .parser_config import ParserConfig, DEFAULT_CONFIG
from .css import add_css_style
from .html_generator import create_volume_page, create_chapter_page, create_section_page, create_chapter
from .validator import validate_conversion_integrity

# Configure logging
logger = logging.getLogger(__name__)

# Try to import LLM-related modules
try:
    from .llm_parser_assistant import HybridParser
    LLM_AVAILABLE = True
except ImportError as e:
    LLM_AVAILABLE = False
    logger.warning(f"LLM assistance feature unavailable: {e}")
except Exception as e:
    LLM_AVAILABLE = False
    logger.warning(f"LLM assistance feature failed to load: {e}")


def _create_epub_book(title: str, author: str, cover_image: Optional[str] = None, language: str = 'zh') -> epub.EpubBook:
    """Create a new EPUB book and set metadata."""
    book = epub.EpubBook()
    book.set_title(title)
    book.set_language(language)
    book.add_author(author)

    if cover_image:
        _set_cover_image(book, cover_image)

    return book


def _set_cover_image(book: epub.EpubBook, cover_image: str) -> None:
    """Set the cover image for the book."""
    try:
        with open(cover_image, 'rb') as cover_file:
            book.set_cover('cover.png', cover_file.read())
    except IOError as e:
        logger.error(f"Unable to read cover image {cover_image}: {e}")


def _read_txt_file(txt_file: str) -> str:
    """Read text file content with automatic encoding detection."""
    try:
        # Check if file exists
        if not os.path.exists(txt_file):
            raise FileNotFoundError(f"File does not exist: {txt_file}")
        
        # Check file size
        file_size = os.path.getsize(txt_file)
        if file_size == 0:
            logger.warning(f"File is empty: {txt_file}")
            return "This document is empty."
        
        # Detect file encoding
        with open(txt_file, 'rb') as f:
            # Read sufficient data for encoding detection, but not exceeding 1MB
            sample_size = min(file_size, 1024 * 1024)
            raw_data = f.read(sample_size)
            result = chardet.detect(raw_data)
            encoding = result.get('encoding') or 'gb18030'
            confidence = result.get('confidence', 0)
            
            logger.info(f"Detected file encoding: {encoding} (confidence: {confidence:.2f})")

        # Use GB18030 encoding to handle Chinese encoding issues
        if encoding and encoding.lower() in ['gb2312', 'gbk']:
            encoding = 'gb18030'
        
        # Try multiple encodings to read file
        encodings_to_try = [encoding, 'utf-8', 'gb18030', 'gbk', 'utf-16', 'latin1']
        
        for enc in encodings_to_try:
            if not enc:
                continue
            try:
                with open(txt_file, 'r', encoding=enc, errors='replace') as f:
                    content = f.read()
                    # Verify content is reasonable (not all replacement characters)
                    if content and content.count('�') / len(content) < 0.1:  # Less than 10% replacement characters
                        logger.info(f"Successfully read file using encoding {enc}")
                        return content
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        # If all encodings fail, use final fallback option
        logger.warning(f"All encoding attempts failed, using fallback to read file: {txt_file}")
        with open(txt_file, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()
            
    except FileNotFoundError as e:
        raise FileNotFoundError(str(e))
    except IOError as e:
        raise IOError(f"Unable to read file {txt_file}: {e}")
    except Exception as e:
        raise Exception(f"Error occurred while reading file {txt_file}: {e}")


def _write_epub_file(epub_file: str, book: epub.EpubBook) -> None:
    """Write EPUB file."""
    try:
        epub.write_epub(epub_file, book, {})
        logger.info(f"Successfully generated EPUB file: {epub_file}")
    except Exception as e:
        raise Exception(f"Unable to write EPUB file {epub_file}: {e}")


def txt_to_epub(txt_file: str, epub_file: str, title: str = 'My Book',
                author: str = 'Unknown', cover_image: Optional[str] = None,
                config: Optional[ParserConfig] = None, show_progress: bool = True,
                context=None, enable_resume: bool = False) -> Dict[str, Any]:
    """
    Convert text file to EPUB format e-book, supports Chinese content.

    :param txt_file: Input text file path
    :param epub_file: Output EPUB file path
    :param title: Book title
    :param author: Author name
    :param cover_image: Cover image path (optional)
    :param config: Parser configuration (optional)
    :param show_progress: Show progress bar (optional, default True)
    :param context: OOMOL Context object for progress reporting (optional)
    :param enable_resume: Enable checkpoint resume feature (optional, default False)
    """
    if config is None:
        config = DEFAULT_CONFIG

    # Validate input parameters
    if not txt_file or not txt_file.strip():
        raise ValueError("Input file path cannot be empty")

    if not epub_file or not epub_file.strip():
        raise ValueError("Output file path cannot be empty")

    if not txt_file.lower().endswith('.txt'):
        raise ValueError("Input file must be .txt format")

    if not epub_file.lower().endswith('.epub'):
        raise ValueError("Output file must be .epub format")

    logger.info(f"Starting conversion: {txt_file} -> {epub_file}")

    # Initialize checkpoint resume state
    resume_state = None
    if enable_resume:
        from .resume_state import ResumeState, get_state_file_path
        epub_dir = os.path.dirname(epub_file)
        state_file = get_state_file_path(txt_file, epub_dir)
        resume_state = ResumeState(state_file)

        # Verify if source file has changed
        if resume_state.verify_source_file(txt_file):
            logger.info(f"Resume: Continuing from last interruption (processed {resume_state.get_processed_count()} chapters)")
            print(f">>> Resume enabled: {resume_state.get_processed_count()} chapters already processed")
        else:
            logger.info("Resume: Source file changed or first run, starting fresh")
            print(">>> Resume: Source file changed or first run, starting fresh")
            resume_state.reset()
            resume_state.set_source_hash(txt_file)

    # Report initial progress (already at 0% from __init__.py)
    if context:
        context.report_progress(1)  # Start conversion

    # Disable progress bar if tqdm not available
    if not TQDM_AVAILABLE and show_progress:
        logger.warning("tqdm not installed, progress bar disabled")
        show_progress = False

    try:
        with tqdm(total=5, desc="Conversion Progress", disable=not show_progress, ncols=80) as pbar:
            # Step 1: Create EPUB book
            pbar.set_description("Creating EPUB file")
            book = _create_epub_book(title, author, cover_image)
            pbar.update(1)

            if context:
                context.report_progress(2)  # EPUB creation completed

            # Step 2: Read and analyze text content
            pbar.set_description("Reading text file")
            content = _read_txt_file(txt_file)

            # Verify content is not empty
            if not content or not content.strip():
                logger.warning("File content is empty, creating default content")
                content = "This document content is empty or cannot be parsed."

            logger.info(f"File content length: {len(content)} characters")
            pbar.update(1)

            if context:
                context.report_progress(5)  # File reading completed (before TOC generation 5%)

            # Step 3: Parse hierarchical content
            pbar.set_description("Parsing document structure")

            logger.debug(f"Parser config: enable_llm={config.enable_llm_assistance}, LLM_AVAILABLE={LLM_AVAILABLE}")

            # Preprocessing: Remove table of contents once before all parsing
            from .parser import remove_table_of_contents, detect_language
            language = detect_language(content)

            # Update book language based on detected content language
            book.set_language('zh' if language == 'chinese' else 'en')

            # Create LLM assistant if needed for TOC detection
            llm_assistant = None
            if config.enable_llm_assistance and LLM_AVAILABLE:
                from .llm_parser_assistant import LLMParserAssistant
                llm_assistant = LLMParserAssistant(
                    api_key=config.llm_api_key,
                    base_url=config.llm_base_url,
                    model=config.llm_model
                )

            # Remove table of contents once
            content = remove_table_of_contents(content, language, llm_assistant, config)

            # Use hybrid parser (if LLM is enabled and available)
            if config.enable_llm_assistance and LLM_AVAILABLE:
                logger.info("Using hybrid parser (rules + LLM)")
                try:
                    parser = HybridParser(
                        llm_api_key=config.llm_api_key,
                        llm_base_url=config.llm_base_url,
                        llm_model=config.llm_model,
                        config=config
                    )
                    # Skip TOC removal since we already did it
                    volumes = parser.parse(content, skip_toc_removal=True, context=context, resume_state=resume_state)
                    logger.info(f"Parsing completed, generated {len(volumes)} volumes")

                    # Output LLM statistics
                    llm_stats = parser.get_stats()
                    if llm_stats['total_calls'] > 0:
                        logger.info(f"LLM stats: {llm_stats['total_calls']} calls, "
                                  f"${llm_stats['total_cost']:.4f} cost, "
                                  f"{llm_stats['total_input_tokens']} + {llm_stats['total_output_tokens']} tokens")
                except Exception as e:
                    logger.warning(f"Hybrid parser failed, falling back to rule-based parsing: {e}")
                    # Skip TOC removal since we already did it
                    # Even when falling back, pass llm_assistant for title generation
                    volumes = parse_hierarchical_content(content, config, llm_assistant, skip_toc_removal=True, context=context, resume_state=resume_state)
            else:
                # Use traditional rule-based parsing
                if config.enable_llm_assistance and not LLM_AVAILABLE:
                    logger.warning("User enabled intelligent analysis, but LLM module is unavailable, falling back to rule-based parsing")
                else:
                    logger.info("Using traditional rule-based parsing")
                # Skip TOC removal since we already did it
                # If llm_assistant is available, also pass it to rule-based parser for title generation
                volumes = parse_hierarchical_content(content, config, llm_assistant, skip_toc_removal=True, context=context, resume_state=resume_state)

            # Validate parsing results
            if not volumes:
                logger.error("Parsing failed, no volumes generated")
                raise Exception("Document parsing failed, unable to generate EPUB")

            logger.info(f"Parsing completed, generated {len(volumes)} volumes")
            pbar.update(1)

            # Chapter parsing completed, report 95% progress
            if context:
                context.report_progress(95)

            # Step 4: Add volumes, chapters and sections to book
            pbar.set_description("Generating EPUB file")

            # Prepare watermark text from config
            watermark = config.watermark_text if config.enable_watermark else None

            chapter_items = []
            toc_structure = []
            chapter_counter = 1
            volume_counter = 1

            # Calculate total chapters for sub-progress
            total_chapters = sum(len(volume.chapters) for volume in volumes)

            # Track progress for context reporting (5% to 95% = 90% range)
            processed_chapters = 0

            with tqdm(total=total_chapters, desc="  Processing chapters", disable=not show_progress,
                     leave=False, ncols=80) as chapter_pbar:
                for volume in volumes:
                    if volume.title:  # If has volume title
                        # Create a page for the volume
                        volume_file_name = f"volume_{volume_counter}.xhtml"
                        volume_page = create_volume_page(volume.title, volume_file_name, len(volume.chapters), watermark)
                        book.add_item(volume_page)
                        chapter_items.append(volume_page)

                        # Create volume table of contents link (top level, not indented)
                        volume_link = epub.Link(volume_file_name, volume.title, f"volume_{volume_counter}")
                        volume_chapters = []

                        for chapter in volume.chapters:
                            chapter_pbar.set_description(f"  Processing: {chapter.title[:20]}")
                            if chapter.sections:  # Chapter has sections
                                # Create chapter page
                                chapter_file_name = f"chap_{chapter_counter}.xhtml"
                                chapter_page = create_chapter_page(chapter.title, chapter.content, chapter_file_name, len(chapter.sections), watermark)
                                book.add_item(chapter_page)
                                chapter_items.append(chapter_page)

                                # Create chapter table of contents link (indented one level relative to volume)
                                chapter_link = epub.Link(chapter_file_name, chapter.title, f"chap_{chapter_counter}")
                                section_links = []
                                section_counter = 1

                                # Handle sections under chapter
                                for section in chapter.sections:
                                    section_file_name = f"chap_{chapter_counter}_sec_{section_counter}.xhtml"
                                    section_page = create_section_page(section.title, section.content, section_file_name)
                                    book.add_item(section_page)
                                    chapter_items.append(section_page)
                                    # Create section table of contents link (indented one more level relative to chapter)
                                    section_links.append(epub.Link(section_file_name, section.title, f"chap_{chapter_counter}_sec_{section_counter}"))
                                    section_counter += 1

                                # Add chapter and its sections as nested structure
                                volume_chapters.append((chapter_link, section_links))
                            else:  # Chapter has no sections, add chapter content directly
                                chapter_page = create_chapter(chapter.title, chapter.content, f"chap_{chapter_counter}.xhtml")
                                book.add_item(chapter_page)
                                chapter_items.append(chapter_page)
                                # Chapter directly as volume sub-item (indented one level relative to volume)
                                volume_chapters.append(epub.Link(f"chap_{chapter_counter}.xhtml", chapter.title, f"chap_{chapter_counter}"))

                            chapter_counter += 1
                            chapter_pbar.update(1)

                            # Report progress to context (5% to 95% range)
                            processed_chapters += 1
                            if context and total_chapters > 0:
                                progress = 5 + int((processed_chapters / total_chapters) * 90)
                                context.report_progress(progress)

                        # Add volume to table of contents structure: volume title + hierarchical structure of chapters and sections below it
                        toc_structure.append((volume_link, volume_chapters))
                        volume_counter += 1
                    else:  # No volumes, add chapters directly
                        for chapter in volume.chapters:
                            chapter_pbar.set_description(f"  Processing: {chapter.title[:20]}")
                            if chapter.sections:  # Chapter has sections
                                # Create chapter page
                                chapter_file_name = f"chap_{chapter_counter}.xhtml"
                                chapter_page = create_chapter_page(chapter.title, chapter.content, chapter_file_name, len(chapter.sections), watermark)
                                book.add_item(chapter_page)
                                chapter_items.append(chapter_page)

                                # Create chapter table of contents link (top level)
                                chapter_link = epub.Link(chapter_file_name, chapter.title, f"chap_{chapter_counter}")
                                section_links = []
                                section_counter = 1

                                # Handle sections under chapter
                                for section in chapter.sections:
                                    section_file_name = f"chap_{chapter_counter}_sec_{section_counter}.xhtml"
                                    section_page = create_section_page(section.title, section.content, section_file_name)
                                    book.add_item(section_page)
                                    chapter_items.append(section_page)
                                    # Create section table of contents link (indented one level relative to chapter)
                                    section_links.append(epub.Link(section_file_name, section.title, f"chap_{chapter_counter}_sec_{section_counter}"))
                                    section_counter += 1

                                # Add chapter and its sections as nested structure
                                toc_structure.append((chapter_link, section_links))
                            else:  # Chapter has no sections, add chapter content directly
                                chapter_page = create_chapter(chapter.title, chapter.content, f"chap_{chapter_counter}.xhtml")
                                book.add_item(chapter_page)
                                chapter_items.append(chapter_page)
                                # Chapter as top-level item
                                toc_structure.append(epub.Link(f"chap_{chapter_counter}.xhtml", chapter.title, f"chap_{chapter_counter}"))

                            chapter_counter += 1
                            chapter_pbar.update(1)

                            # Report progress to context (5% to 95% range)
                            processed_chapters += 1
                            if context and total_chapters > 0:
                                progress = 5 + int((processed_chapters / total_chapters) * 90)
                                context.report_progress(progress)

            pbar.update(1)

            # Step 5: Set book structure and write file
            pbar.set_description("Writing EPUB file")
            # Set book structure
            book.toc = toc_structure
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())

            # Add style and set spine
            add_css_style(book)
            book.spine = ['nav'] + chapter_items

            # Ensure output directory exists and write file
            epub_dir = os.path.dirname(epub_file)
            if epub_dir:  # Only create directory if path has a directory component
                os.makedirs(epub_dir, exist_ok=True)
            _write_epub_file(epub_file, book)
            pbar.update(1)

            # EPUB file writing completed, report 100% progress
            if context:
                context.report_progress(100)

        # Verify conversion content integrity
        logger.info("Starting conversion content integrity verification...")
        is_valid, validation_report = validate_conversion_integrity(content, volumes)

        # Output verification report
        print("\n" + validation_report)

        if not is_valid:
            logger.warning("Content integrity verification failed, possible content loss")
        else:
            logger.info("Content integrity verification passed, good conversion quality")

        logger.info(f"EPUB conversion completed: {epub_file}")

        # Mark checkpoint resume as completed and clean up state file
        if resume_state:
            resume_state.flush()  # Ensure all unsaved changes are persisted
            resume_state.mark_completed()
            resume_state.cleanup()
            logger.info("Resume: Conversion completed, state file cleaned up")

        return {
            "success": True,
            "output_file": epub_file,
            "validation_passed": is_valid,
            "validation_report": validation_report,
            "volumes_count": len(volumes),
            "chapters_count": sum(len(volume.chapters) for volume in volumes)
        }

    except Exception as e:
        logger.error(f"Error occurred during conversion: {e}")
        raise Exception(f"EPUB conversion failed: {e}")
