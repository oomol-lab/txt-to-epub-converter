import os
import logging
import json
import re
import chardet
from typing import Optional, Dict, Any, List, Tuple
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

from .data_structures import Volume, Chapter
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


class _MonotonicProgressContext:
    """Wrap a context object so reported progress never moves backward."""

    def __init__(self, context):
        self._context = context
        self._last_progress = -1

    def report_progress(self, value: int) -> None:
        progress = max(0, min(100, int(value)))
        if progress <= self._last_progress:
            return

        self._last_progress = progress
        self._context.report_progress(progress)


def _create_epub_book(
    title: str,
    author: str,
    cover_image: Optional[str] = None,
    language: str = 'zh',
    metadata: Optional[Dict[str, Any]] = None
) -> epub.EpubBook:
    """Create a new EPUB book and set metadata."""
    book = epub.EpubBook()
    book.set_title(title)
    book.set_language(language)
    if author:
        book.add_author(author)

    if metadata:
        _apply_epub_metadata(book, metadata)

    if cover_image:
        _set_cover_image(book, cover_image)

    return book


def _set_cover_image(book: epub.EpubBook, cover_image: str) -> None:
    """Set the cover image for the book."""
    try:
        with open(cover_image, 'rb') as cover_file:
            data = cover_file.read()

            cover_name = 'cover.png'
            if data.startswith(b'\xff\xd8\xff'):
                cover_name = 'cover.jpg'
            elif data.startswith(b'RIFF') and b'WEBP' in data[:16]:
                cover_name = 'cover.webp'

            book.set_cover(cover_name, data)
    except IOError as e:
        logger.error(f"Unable to read cover image {cover_image}: {e}")


def _apply_epub_metadata(book: epub.EpubBook, metadata: Dict[str, Any]) -> None:
    """Apply extra metadata fields to the EPUB book."""
    description = metadata.get('description')
    if description:
        book.add_metadata('DC', 'description', description)

    publisher = metadata.get('publisher')
    if publisher:
        book.add_metadata('DC', 'publisher', publisher)

    published_date = metadata.get('date')
    if published_date:
        book.add_metadata('DC', 'date', published_date)

    subjects = metadata.get('subjects') or []
    for subject in subjects:
        if subject:
            book.add_metadata('DC', 'subject', subject)

    identifier = metadata.get('identifier')
    if identifier:
        book.set_identifier(identifier)


def _normalize_subjects(raw_subjects: Any, max_tags: int = 8) -> List[str]:
    """Normalize subjects to a clean list of unique strings."""
    if isinstance(raw_subjects, str):
        candidates = [s.strip() for s in raw_subjects.replace('，', ',').replace('、', ',').split(',') if s.strip()]
    elif isinstance(raw_subjects, list):
        candidates = [str(s).strip() for s in raw_subjects if str(s).strip()]
    else:
        return []

    deduped = []
    seen = set()
    for item in candidates:
        lowered = item.lower()
        if lowered in seen:
            continue
        deduped.append(item[:40])
        seen.add(lowered)
        if len(deduped) >= max_tags:
            break
    return deduped


def _is_unknown_author(author: Optional[str]) -> bool:
    """Check whether author should be treated as unknown/placeholder."""
    if author is None:
        return True

    normalized = str(author).strip().lower()
    if not normalized:
        return True

    unknown_values = {
        'unknown',
        'unknown author',
        'n/a',
        'na',
        'none',
        'null',
        '未知',
        '未知作者',
        '佚名',
        '匿名',
    }
    return normalized in unknown_values


def _is_probable_filename_title(title: Optional[str]) -> bool:
    """Detect weak title hints that look like filesystem names instead of real book titles."""
    if title is None:
        return False

    raw = str(title).strip()
    if not raw:
        return False

    lowered = raw.lower()
    placeholders = {
        "my book",
        "book",
        "untitled",
        "unknown",
        "new text document",
        "document",
        "未命名",
        "未知标题",
    }
    if lowered in placeholders:
        return True

    # Paths and common file extensions are strong filename signals.
    if re.search(r"[\\/]", raw):
        return True
    if re.search(r"\.(txt|md|markdown|doc|docx|pdf|epub|rtf|html?)$", lowered):
        return True

    # Typical release/version file naming patterns.
    if re.search(r"\b(?:v|ver|version)[\s._-]?\d+(?:\.\d+)*\b", lowered):
        return True

    quality_tokens = {
        "final",
        "draft",
        "clean",
        "edited",
        "完整版",
        "修订版",
        "校对版",
        "精校版",
        "完结版",
    }
    has_quality_token = any(token in lowered for token in quality_tokens)
    if has_quality_token and (re.search(r"[_-]", raw) or re.search(r"\d{4,}", raw)):
        return True

    separator_count = raw.count("_") + raw.count("-")
    if separator_count >= 2 and re.search(r"\d{4,}", raw):
        return True

    if re.fullmatch(r"[A-Za-z0-9._-]+", raw):
        if re.search(r"\d", raw) and ("_" in raw or "-" in raw):
            return True
        if len(raw) > 24 and ("_" in raw or "-" in raw):
            return True

    return False


def _is_probable_source_slug(title: Optional[str]) -> bool:
    """Detect short slug-like titles commonly derived from filenames."""
    if title is None:
        return False

    text = str(title).strip()
    if not text:
        return False

    if not re.fullmatch(r"[A-Za-z0-9._-]+", text):
        return False

    if len(text) <= 3:
        return True

    if len(text) <= 12 and re.search(r"[_\-.]", text):
        return True

    if len(text) <= 12 and re.search(r"\d", text) and not text.isdigit():
        return True

    return False


def _normalize_title_hint_for_ai(title_hint: str, source_hint: Optional[str] = None) -> str:
    """Keep title hint only when it looks like a meaningful book title."""
    text = (title_hint or "").strip()
    if not text:
        return ""
    if _is_probable_filename_title(text):
        return ""
    source_text = (source_hint or "").strip()
    if source_text and text == source_text and _is_probable_source_slug(text):
        return ""
    return text


def _normalize_author_hint_for_ai(author_hint: Optional[str]) -> str:
    """Keep author hint only when it's not an unknown placeholder."""
    text = (author_hint or "").strip()
    if not text:
        return ""
    if _is_unknown_author(text):
        return ""
    return text


def _resolve_book_metadata(
    title: Optional[str],
    author: Optional[str],
    detected_language: str,
    metadata_overrides: Optional[Dict[str, Any]],
    ai_metadata: Optional[Dict[str, Any]],
    source_hint: Optional[str] = None,
    max_tags: int = 8
) -> Tuple[str, str, str, Dict[str, Any]]:
    """Resolve final title/author/language and extra metadata payload."""
    overrides = metadata_overrides or {}
    generated = ai_metadata or {}

    input_title = (title or '').strip()
    source_text = (source_hint or '').strip()
    source_slug_title = (
        bool(input_title and source_text)
        and input_title == source_text
        and _is_probable_source_slug(input_title)
    )
    weak_title_hint = (not input_title) or _is_probable_filename_title(input_title) or source_slug_title
    if weak_title_hint:
        resolved_title = overrides.get('title') or generated.get('title') or input_title
    else:
        resolved_title = overrides.get('title') or input_title
    resolved_title = str(resolved_title or '').strip()

    input_author = (author or '').strip()
    weak_author_hint = _is_unknown_author(input_author)
    if weak_author_hint:
        resolved_author = overrides.get('author') or generated.get('author') or ''
    else:
        resolved_author = overrides.get('author') or input_author
    resolved_author = str(resolved_author or '').strip()

    resolved_language = overrides.get('language') or generated.get('language')
    if resolved_language not in {'zh', 'en'}:
        resolved_language = 'zh' if detected_language == 'chinese' else 'en'

    description = overrides.get('description') or generated.get('description') or ''
    publisher = overrides.get('publisher') or generated.get('publisher') or ''
    published_date = overrides.get('date') or generated.get('date') or ''
    identifier = overrides.get('identifier') or generated.get('identifier') or ''
    subjects = overrides.get('tags')
    if subjects is None:
        subjects = generated.get('tags', [])
    subjects = _normalize_subjects(subjects, max_tags=max_tags)

    metadata_payload = {
        'description': description,
        'publisher': publisher,
        'date': published_date,
        'identifier': identifier,
        'subjects': subjects,
    }
    return resolved_title, resolved_author, resolved_language, metadata_payload


def _generate_ai_book_metadata(
    content: str,
    language: str,
    title_hint: Optional[str],
    author_hint: Optional[str],
    config: ParserConfig,
    source_hint: Optional[str] = None
) -> Tuple[Dict[str, Any], bool, Dict[str, Any], List[str]]:
    """Generate metadata using AI, returning metadata/generated/stats/warnings."""
    warnings: List[str] = []
    if not config.enable_ai_metadata:
        return {}, False, {}, warnings

    try:
        from .ai import BookMetadataGenerator

        generator = BookMetadataGenerator(
            api_key=config.llm_api_key,
            model=config.ai_metadata_model or config.llm_model,
            base_url=config.llm_base_url,
            max_sample_chars=config.ai_metadata_sample_chars,
            max_tags=config.ai_metadata_max_tags,
        )
        result = generator.generate(
            content=content,
            language=language,
            title_hint=_normalize_title_hint_for_ai(title_hint, source_hint=source_hint),
            author_hint=_normalize_author_hint_for_ai(author_hint),
        )
        stats = generator.get_stats()

        if result.get('success'):
            return result.get('metadata', {}), True, stats, warnings

        warnings.append(f"AI metadata not applied: {result.get('reason', 'unknown_error')}")
        return {}, False, stats, warnings

    except Exception as e:
        warnings.append(f"AI metadata generation failed: {e}")
        logger.warning(warnings[-1])
        return {}, False, {}, warnings


def _merge_ai_usage(base: Dict[str, Any], extra: Dict[str, Any]) -> Dict[str, Any]:
    """Merge numeric usage counters from two dictionaries."""
    if not extra:
        return base
    if not base:
        return dict(extra)

    merged = dict(base)
    for key, value in extra.items():
        if isinstance(value, (int, float)) and isinstance(merged.get(key), (int, float)):
            merged[key] = merged[key] + value
        elif key not in merged:
            merged[key] = value
    return merged


def _generate_ai_cover_image(
    content: str,
    language: str,
    title: str,
    author: str,
    metadata_payload: Dict[str, Any],
    config: ParserConfig,
    cover_prompt_hint: str = "",
    source_hint: str = ""
) -> Tuple[Optional[str], bool, Dict[str, Any], List[str]]:
    """Generate cover image using AI, returning cover_path/generated/stats/warnings."""
    warnings: List[str] = []
    if not config.enable_ai_cover:
        return None, False, {}, warnings

    try:
        from .ai import CoverGenerator

        context_chars = max(1000, int(getattr(config, 'ai_cover_context_chars', 2000)))

        generator = CoverGenerator(
            api_key=config.llm_api_key,
            model=config.ai_cover_model,
            base_url=config.llm_base_url,
            size=config.ai_cover_size,
            quality=config.ai_cover_quality
        )

        cover_author = author
        if getattr(config, 'hide_unknown_author', True) and _is_unknown_author(author):
            cover_author = ''

        result = generator.generate_cover(
            title=title,
            author=cover_author,
            description=metadata_payload.get('description', ''),
            tags=metadata_payload.get('subjects', []),
            language=language,
            style_hint=cover_prompt_hint or (config.ai_cover_style_hint or ''),
            content_sample=content[:context_chars],
            source_hint=source_hint
        )
        stats = generator.get_stats()

        if result.get('success') and result.get('cover_path'):
            return result.get('cover_path'), True, stats, warnings

        warnings.append(f"AI cover not applied: {result.get('reason', 'unknown_error')}")
        return None, False, stats, warnings
    except Exception as e:
        warnings.append(f"AI cover generation failed: {e}")
        logger.warning(warnings[-1])
        return None, False, {}, warnings


def _extract_chapter_illustration_text(chapter: Chapter, max_chars: int = 4000) -> str:
    """Build a compact text sample from chapter/section content for illustration prompts."""
    chunks: List[str] = []
    chapter_text = (chapter.content or "").strip()
    if chapter_text:
        chunks.append(chapter_text)

    for section in chapter.sections[:3]:
        section_text = (section.content or "").strip()
        if not section_text:
            continue
        if section.title:
            chunks.append(f"{section.title}\n{section_text}")
        else:
            chunks.append(section_text)

    merged = "\n\n".join(chunks).strip()
    if len(merged) <= max_chars:
        return merged
    return merged[:max_chars]


def _resolve_ai_illustration_policy(config: ParserConfig) -> Dict[str, int]:
    """Resolve effective chapter-illustration policy, with compatibility fallback."""
    resolver = getattr(config, "get_ai_illustration_policy", None)
    if callable(resolver):
        return resolver()
    return {
        "max_images_per_book": max(0, int(getattr(config, "ai_illustration_max_images_per_book", 0))),
        "chapter_interval": max(1, int(getattr(config, "ai_illustration_chapter_interval", 1))),
        "min_chapter_chars": max(0, int(getattr(config, "ai_illustration_min_chapter_chars", 0))),
    }


def _resolve_ai_illustration_density(config: ParserConfig) -> Optional[str]:
    """Resolve canonical illustration density label when available."""
    resolver = getattr(config, "get_ai_illustration_density", None)
    if callable(resolver):
        return resolver()
    raw = str(getattr(config, "ai_illustration_density", "") or "").strip()
    return raw or None


_ENGLISH_CHARS_PER_WORD = 5
"""Average English characters per word (including trailing space).
Used to normalise min_chapter_chars so that the same density preset produces
a semantically equivalent illustration cadence for both Chinese and English."""


def _should_generate_chapter_illustration(
    chapter_index: int,
    chapter_text: str,
    generated_count: int,
    config: ParserConfig,
    language: str = "chinese",
) -> bool:
    """Check whether the current chapter should generate an illustration.

    ``language`` should be ``"chinese"`` or ``"english"`` (the value returned by
    :func:`~txt_to_epub.parser.detect_language`).  For English text the
    ``min_chapter_chars`` threshold is scaled up by :data:`_ENGLISH_CHARS_PER_WORD`
    so that the density presets represent a consistent *word-count* gate rather
    than a raw byte count, giving both languages a semantically equivalent
    illustration cadence.
    """
    if not getattr(config, "enable_ai_illustrations", False):
        return False

    policy = _resolve_ai_illustration_policy(config)
    max_images = max(0, int(policy.get("max_images_per_book", 0)))
    if max_images <= 0 or generated_count >= max_images:
        return False

    # Always reserve the opening visual beat for chapter one when illustrations are enabled.
    if chapter_index == 1:
        return True

    interval = max(1, int(policy.get("chapter_interval", 1)))
    if (chapter_index - 1) % interval != 0:
        return False

    min_chars = max(0, int(policy.get("min_chapter_chars", 0)))
    if language != "chinese":
        min_chars = min_chars * _ENGLISH_CHARS_PER_WORD
    if len((chapter_text or "").strip()) < min_chars:
        return False

    return True


def _detect_image_format(image_bytes: bytes) -> Tuple[str, str]:
    """Detect image extension/media type from magic header."""
    if image_bytes.startswith(b"\xff\xd8\xff"):
        return ".jpg", "image/jpeg"
    if image_bytes.startswith(b"RIFF") and b"WEBP" in image_bytes[:16]:
        return ".webp", "image/webp"
    if image_bytes.startswith(b"GIF87a") or image_bytes.startswith(b"GIF89a"):
        return ".gif", "image/gif"
    return ".png", "image/png"


def _create_epub_image_item(image_path: str, image_index: int, chapter_index: int) -> Tuple[epub.EpubItem, str]:
    """Create EPUB image item and return (item, href)."""
    with open(image_path, "rb") as image_file:
        image_bytes = image_file.read()

    ext, media_type = _detect_image_format(image_bytes)
    file_name = f"images/illustration_{chapter_index}_{image_index}{ext}"
    uid = f"illustration_{chapter_index}_{image_index}"
    item = epub.EpubItem(uid=uid, file_name=file_name, media_type=media_type, content=image_bytes)
    return item, file_name


def _normalize_illustration_continuity_guide(guide: Dict[str, Any], max_characters: int = 6) -> Dict[str, Any]:
    """Normalize continuity guide fields into a stable structure."""
    raw = guide if isinstance(guide, dict) else {}

    style_bible = str(raw.get("style_bible") or "").strip()[:400]
    setting_bible = str(raw.get("setting_bible") or "").strip()[:400]

    characters: List[Dict[str, str]] = []
    raw_characters = raw.get("characters")
    if isinstance(raw_characters, list):
        for item in raw_characters:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()[:60]
            if not name:
                continue
            appearance = str(item.get("appearance") or "").strip()[:260]
            identity = str(item.get("identity") or "").strip()[:120]
            characters.append({
                "name": name,
                "appearance": appearance,
                "identity": identity
            })
            if len(characters) >= max(1, max_characters):
                break

    negatives: List[str] = []
    raw_negatives = raw.get("negative_constraints")
    if isinstance(raw_negatives, list):
        for item in raw_negatives:
            text = str(item).strip()[:160]
            if text:
                negatives.append(text)
            if len(negatives) >= 8:
                break

    return {
        "style_bible": style_bible,
        "setting_bible": setting_bible,
        "characters": characters,
        "negative_constraints": negatives,
    }


def _build_default_illustration_continuity_guide(
    title: str,
    metadata_payload: Dict[str, Any],
    config: ParserConfig
) -> Dict[str, Any]:
    """Build a local fallback continuity guide without extra model calls."""
    styles = [
        getattr(config, "ai_illustration_style_hint", None),
        getattr(config, "ai_cover_style_hint", None),
        getattr(config, "ai_illustration_continuity_hint", None),
    ]
    style_bible = "; ".join([s.strip() for s in styles if isinstance(s, str) and s.strip()])
    if not style_bible:
        style_bible = "Maintain consistent color script, costume silhouette, and lens language across chapters."

    tags = metadata_payload.get("subjects") or []
    if isinstance(tags, list):
        tags_text = ", ".join([str(tag).strip() for tag in tags if str(tag).strip()][:6])
    else:
        tags_text = ""
    setting_bible = f"Book: {title}. Tags: {tags_text}".strip()
    setting_bible = setting_bible[:400]

    return {
        "style_bible": style_bible[:400],
        "setting_bible": setting_bible,
        "characters": [],
        "negative_constraints": [],
    }


def _generate_ai_illustration_continuity_guide(
    content: str,
    language: str,
    title: str,
    metadata_payload: Dict[str, Any],
    config: ParserConfig,
    source_hint: str = ""
) -> Tuple[Dict[str, Any], bool, Dict[str, Any], List[str]]:
    """Generate continuity guide for chapter illustrations."""
    warnings: List[str] = []
    if not getattr(config, "enable_ai_illustrations", False):
        return {}, False, {}, warnings
    if not getattr(config, "enable_ai_illustration_continuity", True):
        return {}, False, {}, warnings

    default_guide = _build_default_illustration_continuity_guide(
        title=title,
        metadata_payload=metadata_payload,
        config=config
    )
    max_characters = max(1, int(getattr(config, "ai_illustration_continuity_max_characters", 6)))
    sample_chars = max(4000, int(getattr(config, "ai_illustration_continuity_sample_chars", 16000)))
    sample = (content or "")[:sample_chars]
    if not sample.strip():
        return default_guide, False, {}, warnings

    api_key = getattr(config, "llm_api_key", None)
    if not api_key:
        return default_guide, False, {}, warnings

    try:
        from .llm.client import LLMClient

        model_name = (
            getattr(config, "ai_illustration_continuity_model", None)
            or getattr(config, "ai_metadata_model", None)
            or config.llm_model
        )
        client = LLMClient(
            api_key=config.llm_api_key,
            model=model_name,
            base_url=config.llm_base_url
        )
        lang = "Chinese" if language == "chinese" else "English"
        continuity_hint = str(getattr(config, "ai_illustration_continuity_hint", "") or "").strip()
        description = str(metadata_payload.get("description") or "").strip()[:400]
        tags = metadata_payload.get("subjects") or []
        if isinstance(tags, list):
            tags_text = ", ".join([str(tag).strip() for tag in tags if str(tag).strip()][:8])
        else:
            tags_text = ""

        prompt = f"""Build a stable visual continuity guide for chapter illustrations.

Language: {lang}
Book title: {title}
Source title hint: {source_hint or "N/A"}
Book description: {description or "N/A"}
Genre tags: {tags_text or "N/A"}
Manual continuity hint: {continuity_hint or "N/A"}
Character profile cap: {max_characters}

Content sample:
{sample}

Return strict JSON only:
{{
  "style_bible": "string, <= 80 words",
  "setting_bible": "string, <= 80 words",
  "characters": [
    {{
      "name": "string",
      "appearance": "stable visual appearance cues",
      "identity": "short role description"
    }}
  ],
  "negative_constraints": ["string"]
}}
"""
        response = client.call(prompt, max_tokens=900, temperature=0.2)
        raw = json.loads(response)
        normalized = _normalize_illustration_continuity_guide(raw, max_characters=max_characters)
        if not normalized.get("style_bible"):
            normalized["style_bible"] = default_guide.get("style_bible", "")
        if not normalized.get("setting_bible"):
            normalized["setting_bible"] = default_guide.get("setting_bible", "")
        stats = client.get_stats()
        return normalized, True, stats, warnings
    except Exception as e:
        warnings.append(f"AI illustration continuity guide failed: {e}")
        logger.warning(warnings[-1])
        return default_guide, False, {}, warnings


def _select_chapter_character_focus(
    chapter_text: str,
    continuity_guide: Dict[str, Any],
    max_focus: int = 2
) -> List[str]:
    """Select likely character focus for current chapter from continuity guide."""
    if not continuity_guide:
        return []

    characters = continuity_guide.get("characters")
    if not isinstance(characters, list):
        return []

    text = (chapter_text or "").strip()
    text_lower = text.lower()

    matched: List[str] = []
    for item in characters:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        if name in text or name.lower() in text_lower:
            matched.append(name)
        if len(matched) >= max_focus:
            break

    if matched:
        return matched

    fallback: List[str] = []
    for item in characters:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        fallback.append(name)
        if len(fallback) >= max_focus:
            break
    return fallback


def _generate_ai_chapter_illustration(
    chapter_title: str,
    chapter_content: str,
    language: str,
    book_title: str,
    metadata_payload: Dict[str, Any],
    config: ParserConfig,
    source_hint: str = "",
    continuity_guide: Optional[Dict[str, Any]] = None,
    character_focus: Optional[List[str]] = None,
) -> Tuple[Optional[str], bool, Dict[str, Any], List[str]]:
    """Generate chapter illustration using AI, returning image_path/generated/stats/warnings."""
    warnings: List[str] = []
    if not getattr(config, "enable_ai_illustrations", False):
        return None, False, {}, warnings

    try:
        from .ai import IllustrationGenerator

        context_chars = max(600, int(getattr(config, "ai_illustration_context_chars", 1200)))
        model_name = getattr(config, "ai_illustration_model", None) or config.ai_cover_model
        style_hint = (
            getattr(config, "ai_illustration_style_hint", None)
            or config.ai_cover_style_hint
            or ""
        )

        generator = IllustrationGenerator(
            api_key=config.llm_api_key,
            model=model_name,
            base_url=config.llm_base_url,
            size=config.ai_illustration_size,
            quality=config.ai_illustration_quality
        )

        result = generator.generate_illustration(
            book_title=book_title,
            chapter_title=chapter_title,
            chapter_content=(chapter_content or "")[:context_chars],
            description=metadata_payload.get("description", ""),
            tags=metadata_payload.get("subjects", []),
            language=language,
            style_hint=style_hint,
            source_hint=source_hint,
            continuity_guide=continuity_guide or {},
            character_focus=character_focus or []
        )
        stats = generator.get_stats()

        if result.get("success") and result.get("image_path"):
            return result.get("image_path"), True, stats, warnings

        warnings.append(f"AI illustration not applied ({chapter_title}): {result.get('reason', 'unknown_error')}")
        return None, False, stats, warnings
    except Exception as e:
        warnings.append(f"AI illustration generation failed ({chapter_title}): {e}")
        logger.warning(warnings[-1])
        return None, False, {}, warnings


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
    except Exception as e:
        raise Exception(f"Unable to write EPUB file {epub_file}: {e}")


def txt_to_epub(txt_file: str, epub_file: str, title: Optional[str] = None,
                author: Optional[str] = None, cover_image: Optional[str] = None,
                config: Optional[ParserConfig] = None, show_progress: bool = True,
                context=None, enable_resume: bool = False,
                metadata_overrides: Optional[Dict[str, Any]] = None,
                cover_prompt_hint: str = "") -> Dict[str, Any]:
    """
    Convert text file to EPUB format e-book, supports Chinese content.

    :param txt_file: Input text file path
    :param epub_file: Output EPUB file path
    :param title: Book title (optional, empty when not provided)
    :param author: Author name (optional, empty when not provided)
    :param cover_image: Cover image path (optional)
    :param config: Parser configuration (optional)
    :param show_progress: Show progress bar (optional, default True)
    :param context: OOMOL Context object for progress reporting (optional)
    :param enable_resume: Enable checkpoint resume feature (optional, default False)
    :param metadata_overrides: Metadata override dictionary (optional)
    :param cover_prompt_hint: Extra style/prompt hint for AI cover generation (optional)
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

    # Initialize checkpoint resume state
    resume_state = None
    if enable_resume:
        from .resume_state import ResumeState, get_state_file_path
        epub_dir = os.path.dirname(epub_file)
        state_file = get_state_file_path(txt_file, epub_dir)
        resume_state = ResumeState(state_file)

        # Verify if source file has changed
        if resume_state.verify_source_file(txt_file):
            print(f">>> Resume enabled: {resume_state.get_processed_count()} chapters already processed")
        else:
            print(">>> Resume: Source file changed or first run, starting fresh")
            resume_state.reset()
            resume_state.set_source_hash(txt_file)

    progress_context = _MonotonicProgressContext(context) if context else None

    # Report initial progress (already at 0% from __init__.py)
    if progress_context:
        progress_context.report_progress(1)  # Start conversion

    # Disable progress bar if tqdm not available
    if not TQDM_AVAILABLE and show_progress:
        logger.warning("tqdm not installed, progress bar disabled")
        show_progress = False

    ai_metadata_generated = False
    ai_cover_generated = False
    ai_illustrations_generated = 0
    ai_illustration_continuity_generated = False
    ai_usage: Dict[str, Any] = {}
    ai_warnings: List[str] = []
    ai_illustration_attempted = 0
    ai_illustration_skipped = 0
    ai_illustration_results: List[Dict[str, Any]] = []
    generated_cover_path: Optional[str] = None
    generated_illustration_paths: List[str] = []
    illustration_continuity_guide: Dict[str, Any] = {}

    try:
        with tqdm(total=5, desc="Conversion Progress", disable=not show_progress, ncols=80) as pbar:
            # Step 1: Read and analyze text content
            pbar.set_description("Reading text file")
            content = _read_txt_file(txt_file)
            source_title_hint = os.path.splitext(os.path.basename(txt_file))[0]

            # Verify content is not empty
            if not content or not content.strip():
                logger.warning("File content is empty, creating default content")
                content = "This document content is empty or cannot be parsed."

            pbar.update(1)

            if progress_context:
                progress_context.report_progress(5)

            # Step 2: Resolve book metadata and create EPUB object
            pbar.set_description("Preparing metadata")
            from .parser import detect_language
            language = detect_language(content)

            ai_metadata, ai_metadata_generated, ai_usage, warnings = _generate_ai_book_metadata(
                content=content,
                language=language,
                title_hint=title,
                author_hint=author,
                config=config,
                source_hint=source_title_hint
            )
            ai_warnings.extend(warnings)

            resolved_title, resolved_author, resolved_language, metadata_payload = _resolve_book_metadata(
                title=title,
                author=author,
                detected_language=language,
                metadata_overrides=metadata_overrides,
                ai_metadata=ai_metadata,
                source_hint=source_title_hint,
                max_tags=config.ai_metadata_max_tags
            )

            final_cover_image = cover_image
            if not cover_image:
                generated_cover_path, ai_cover_generated, cover_usage, cover_warnings = _generate_ai_cover_image(
                    content=content,
                    language=language,
                    title=resolved_title,
                    author=resolved_author,
                    metadata_payload=metadata_payload,
                    config=config,
                    cover_prompt_hint=cover_prompt_hint,
                    source_hint=source_title_hint
                )
                ai_usage = _merge_ai_usage(ai_usage, cover_usage)
                ai_warnings.extend(cover_warnings)
                if generated_cover_path:
                    final_cover_image = generated_cover_path

            book = _create_epub_book(
                title=resolved_title,
                author=resolved_author,
                cover_image=final_cover_image,
                language=resolved_language,
                metadata=metadata_payload
            )

            pbar.update(1)

            if progress_context:
                progress_context.report_progress(12)

            # Step 3: Parse hierarchical content
            pbar.set_description("Parsing document structure")

            # Preprocessing: Remove table of contents once before all parsing
            from .parser import remove_table_of_contents

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
                try:
                    parser = HybridParser(
                        llm_api_key=config.llm_api_key,
                        llm_base_url=config.llm_base_url,
                        llm_model=config.llm_model,
                        config=config
                    )
                    # Skip TOC removal since we already did it
                    volumes = parser.parse(
                        content,
                        skip_toc_removal=True,
                        context=progress_context,
                        resume_state=resume_state,
                    )
                except Exception as e:
                    logger.warning(f"Hybrid parser failed, falling back to rule-based parsing: {e}")
                    # Skip TOC removal since we already did it
                    # Even when falling back, pass llm_assistant for title generation
                    volumes = parse_hierarchical_content(
                        content,
                        config,
                        llm_assistant,
                        skip_toc_removal=True,
                        context=progress_context,
                        resume_state=resume_state,
                    )
            else:
                # Use traditional rule-based parsing
                if config.enable_llm_assistance and not LLM_AVAILABLE:
                    logger.warning("User enabled intelligent analysis, but LLM module is unavailable, falling back to rule-based parsing")
                # Skip TOC removal since we already did it
                # If llm_assistant is available, also pass it to rule-based parser for title generation
                volumes = parse_hierarchical_content(
                    content,
                    config,
                    llm_assistant,
                    skip_toc_removal=True,
                    context=progress_context,
                    resume_state=resume_state,
                )

            # Validate parsing results
            if not volumes:
                logger.error("Parsing failed, no volumes generated")
                raise Exception("Document parsing failed, unable to generate EPUB")

            illustration_continuity_guide, ai_illustration_continuity_generated, continuity_usage, continuity_warnings = (
                _generate_ai_illustration_continuity_guide(
                    content=content,
                    language=language,
                    title=resolved_title,
                    metadata_payload=metadata_payload,
                    config=config,
                    source_hint=source_title_hint
                )
            )
            ai_usage = _merge_ai_usage(ai_usage, continuity_usage)
            ai_warnings.extend(continuity_warnings)

            pbar.update(1)

            # Chapter parsing completed, report 95% progress
            if progress_context:
                progress_context.report_progress(95)

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

            # Track progress for context reporting during chapter assembly (95% to 99%)
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
                            chapter_illustration_href = None
                            chapter_sample_text = _extract_chapter_illustration_text(chapter)
                            should_generate_illustration = _should_generate_chapter_illustration(
                                chapter_index=chapter_counter,
                                chapter_text=chapter_sample_text,
                                generated_count=ai_illustrations_generated,
                                config=config,
                                language=language,
                            )
                            if should_generate_illustration:
                                ai_illustration_attempted += 1
                                chapter_character_focus = _select_chapter_character_focus(
                                    chapter_text=chapter_sample_text,
                                    continuity_guide=illustration_continuity_guide
                                )
                                image_path, image_generated, image_usage, image_warnings = _generate_ai_chapter_illustration(
                                    chapter_title=chapter.title,
                                    chapter_content=chapter_sample_text,
                                    language=language,
                                    book_title=resolved_title,
                                    metadata_payload=metadata_payload,
                                    config=config,
                                    source_hint=source_title_hint,
                                    continuity_guide=illustration_continuity_guide,
                                    character_focus=chapter_character_focus
                                )
                                ai_usage = _merge_ai_usage(ai_usage, image_usage)
                                ai_warnings.extend(image_warnings)
                                if image_generated and image_path:
                                    try:
                                        image_item, chapter_illustration_href = _create_epub_image_item(
                                            image_path=image_path,
                                            image_index=ai_illustrations_generated + 1,
                                            chapter_index=chapter_counter
                                        )
                                        book.add_item(image_item)
                                        ai_illustrations_generated += 1
                                        generated_illustration_paths.append(image_path)
                                        ai_illustration_results.append({
                                            "chapter_index": chapter_counter,
                                            "chapter_title": chapter.title,
                                            "status": "generated",
                                            "image_href": chapter_illustration_href
                                        })
                                    except Exception as image_error:
                                        warning = f"AI illustration embedding failed ({chapter.title}): {image_error}"
                                        ai_warnings.append(warning)
                                        logger.warning(warning)
                                        ai_illustration_results.append({
                                            "chapter_index": chapter_counter,
                                            "chapter_title": chapter.title,
                                            "status": "failed_embedding",
                                            "reason": str(image_error)
                                        })
                                        if os.path.exists(image_path):
                                            try:
                                                os.unlink(image_path)
                                            except OSError:
                                                pass
                                else:
                                    ai_illustration_results.append({
                                        "chapter_index": chapter_counter,
                                        "chapter_title": chapter.title,
                                        "status": "failed_generation",
                                        "reason": image_warnings[-1] if image_warnings else "unknown_error"
                                    })
                            else:
                                ai_illustration_skipped += 1

                            if chapter.sections:  # Chapter has sections
                                # Create chapter page
                                chapter_file_name = f"chap_{chapter_counter}.xhtml"
                                chapter_page = create_chapter_page(
                                    chapter.title,
                                    chapter.content,
                                    chapter_file_name,
                                    len(chapter.sections),
                                    watermark,
                                    illustration_href=chapter_illustration_href,
                                    illustration_caption=None,
                                    illustration_position=config.ai_illustration_position
                                )
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
                                chapter_page = create_chapter(
                                    chapter.title,
                                    chapter.content,
                                    f"chap_{chapter_counter}.xhtml",
                                    illustration_href=chapter_illustration_href,
                                    illustration_caption=None,
                                    illustration_position=config.ai_illustration_position
                                )
                                book.add_item(chapter_page)
                                chapter_items.append(chapter_page)
                                # Chapter directly as volume sub-item (indented one level relative to volume)
                                volume_chapters.append(epub.Link(f"chap_{chapter_counter}.xhtml", chapter.title, f"chap_{chapter_counter}"))

                            chapter_counter += 1
                            chapter_pbar.update(1)

                            # Report progress to context during chapter assembly (95% to 99%)
                            processed_chapters += 1
                            if progress_context and total_chapters > 0:
                                progress = 95 + int((processed_chapters / total_chapters) * 4)
                                progress = min(progress, 99)
                                progress_context.report_progress(progress)

                        # Add volume to table of contents structure: volume title + hierarchical structure of chapters and sections below it
                        toc_structure.append((volume_link, volume_chapters))
                        volume_counter += 1
                    else:  # No volumes, add chapters directly
                        for chapter in volume.chapters:
                            chapter_pbar.set_description(f"  Processing: {chapter.title[:20]}")
                            chapter_illustration_href = None
                            chapter_sample_text = _extract_chapter_illustration_text(chapter)
                            should_generate_illustration = _should_generate_chapter_illustration(
                                chapter_index=chapter_counter,
                                chapter_text=chapter_sample_text,
                                generated_count=ai_illustrations_generated,
                                config=config,
                                language=language,
                            )
                            if should_generate_illustration:
                                ai_illustration_attempted += 1
                                chapter_character_focus = _select_chapter_character_focus(
                                    chapter_text=chapter_sample_text,
                                    continuity_guide=illustration_continuity_guide
                                )
                                image_path, image_generated, image_usage, image_warnings = _generate_ai_chapter_illustration(
                                    chapter_title=chapter.title,
                                    chapter_content=chapter_sample_text,
                                    language=language,
                                    book_title=resolved_title,
                                    metadata_payload=metadata_payload,
                                    config=config,
                                    source_hint=source_title_hint,
                                    continuity_guide=illustration_continuity_guide,
                                    character_focus=chapter_character_focus
                                )
                                ai_usage = _merge_ai_usage(ai_usage, image_usage)
                                ai_warnings.extend(image_warnings)
                                if image_generated and image_path:
                                    try:
                                        image_item, chapter_illustration_href = _create_epub_image_item(
                                            image_path=image_path,
                                            image_index=ai_illustrations_generated + 1,
                                            chapter_index=chapter_counter
                                        )
                                        book.add_item(image_item)
                                        ai_illustrations_generated += 1
                                        generated_illustration_paths.append(image_path)
                                        ai_illustration_results.append({
                                            "chapter_index": chapter_counter,
                                            "chapter_title": chapter.title,
                                            "status": "generated",
                                            "image_href": chapter_illustration_href
                                        })
                                    except Exception as image_error:
                                        warning = f"AI illustration embedding failed ({chapter.title}): {image_error}"
                                        ai_warnings.append(warning)
                                        logger.warning(warning)
                                        ai_illustration_results.append({
                                            "chapter_index": chapter_counter,
                                            "chapter_title": chapter.title,
                                            "status": "failed_embedding",
                                            "reason": str(image_error)
                                        })
                                        if os.path.exists(image_path):
                                            try:
                                                os.unlink(image_path)
                                            except OSError:
                                                pass
                                else:
                                    ai_illustration_results.append({
                                        "chapter_index": chapter_counter,
                                        "chapter_title": chapter.title,
                                        "status": "failed_generation",
                                        "reason": image_warnings[-1] if image_warnings else "unknown_error"
                                    })
                            else:
                                ai_illustration_skipped += 1

                            if chapter.sections:  # Chapter has sections
                                # Create chapter page
                                chapter_file_name = f"chap_{chapter_counter}.xhtml"
                                chapter_page = create_chapter_page(
                                    chapter.title,
                                    chapter.content,
                                    chapter_file_name,
                                    len(chapter.sections),
                                    watermark,
                                    illustration_href=chapter_illustration_href,
                                    illustration_caption=None,
                                    illustration_position=config.ai_illustration_position
                                )
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
                                chapter_page = create_chapter(
                                    chapter.title,
                                    chapter.content,
                                    f"chap_{chapter_counter}.xhtml",
                                    illustration_href=chapter_illustration_href,
                                    illustration_caption=None,
                                    illustration_position=config.ai_illustration_position
                                )
                                book.add_item(chapter_page)
                                chapter_items.append(chapter_page)
                                # Chapter as top-level item
                                toc_structure.append(epub.Link(f"chap_{chapter_counter}.xhtml", chapter.title, f"chap_{chapter_counter}"))

                            chapter_counter += 1
                            chapter_pbar.update(1)

                            # Report progress to context during chapter assembly (95% to 99%)
                            processed_chapters += 1
                            if progress_context and total_chapters > 0:
                                progress = 95 + int((processed_chapters / total_chapters) * 4)
                                progress = min(progress, 99)
                                progress_context.report_progress(progress)

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
            if progress_context:
                progress_context.report_progress(100)

        # Verify conversion content integrity
        is_valid, validation_report = validate_conversion_integrity(content, volumes)

        # Output verification report
        print("\n" + validation_report)

        if not is_valid:
            logger.warning("Content integrity verification failed, possible content loss")

        # Mark checkpoint resume as completed and clean up state file
        if resume_state:
            resume_state.flush()  # Ensure all unsaved changes are persisted
            resume_state.mark_completed()
            resume_state.cleanup()

        ai_summary = {
            "metadata": {
                "generated": ai_metadata_generated
            },
            "cover": {
                "generated": ai_cover_generated
            },
            "illustration": {
                "density": _resolve_ai_illustration_density(config),
                "policy": _resolve_ai_illustration_policy(config),
                "continuity_generated": ai_illustration_continuity_generated,
                "attempted_count": ai_illustration_attempted,
                "generated_count": ai_illustrations_generated,
                "failed_count": max(0, ai_illustration_attempted - ai_illustrations_generated),
                "skipped_count": ai_illustration_skipped,
                "chapter_results": ai_illustration_results
            },
            "usage": ai_usage,
            "warnings": ai_warnings
        }

        return {
            "success": True,
            "output_file": epub_file,
            "validation_passed": is_valid,
            "validation_report": validation_report,
            "volumes_count": len(volumes),
            "chapters_count": sum(len(volume.chapters) for volume in volumes),
            "ai": ai_summary
        }

    except Exception as e:
        logger.error(f"Error occurred during conversion: {e}")
        raise Exception(f"EPUB conversion failed: {e}")
    finally:
        for image_path in generated_illustration_paths:
            if image_path and os.path.exists(image_path):
                try:
                    os.unlink(image_path)
                except OSError as cleanup_error:
                    logger.warning(f"Failed to clean temporary AI illustration file {image_path}: {cleanup_error}")
        if generated_cover_path and os.path.exists(generated_cover_path):
            try:
                os.unlink(generated_cover_path)
            except OSError as cleanup_error:
                logger.warning(f"Failed to clean temporary AI cover file {generated_cover_path}: {cleanup_error}")
