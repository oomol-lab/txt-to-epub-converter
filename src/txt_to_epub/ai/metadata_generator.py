"""
Book metadata generation assistant powered by LLM.
"""
import json
import logging
import re
from typing import Any, Dict, List

from ..llm.client import LLMClient

logger = logging.getLogger(__name__)


class BookMetadataGenerator:
    """Generate title/description/tags metadata from book content."""

    def __init__(
        self,
        api_key: str = None,
        model: str = "gpt-4o-mini",
        base_url: str = None,
        organization: str = None,
        max_sample_chars: int = 12000,
        max_tags: int = 8,
    ):
        self.client = LLMClient(api_key=api_key, model=model, base_url=base_url, organization=organization)
        self.max_sample_chars = max(2000, int(max_sample_chars))
        self.max_tags = max(1, int(max_tags))

    def generate(
        self,
        content: str,
        language: str = "chinese",
        title_hint: str = "",
        author_hint: str = "",
    ) -> Dict[str, Any]:
        """Generate structured metadata."""
        content_sample = self._build_content_sample(content)
        if not content_sample:
            return {"success": False, "reason": "empty_content", "metadata": {}}

        prompt = self._build_prompt(content_sample, language, title_hint, author_hint)

        try:
            response = self.client.call(prompt, max_tokens=900, temperature=0.3)
            result = json.loads(response)
            metadata = self._normalize_metadata(result)

            if not metadata.get("title"):
                return {"success": False, "reason": "missing_title", "metadata": metadata}

            return {"success": True, "metadata": metadata}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse metadata JSON: {e}")
            return {"success": False, "reason": f"json_parse_error: {e}", "metadata": {}}
        except Exception as e:
            logger.error(f"Metadata generation failed: {e}")
            return {"success": False, "reason": str(e), "metadata": {}}

    def get_stats(self) -> Dict[str, Any]:
        """Return LLM usage stats."""
        return self.client.get_stats()

    def _build_content_sample(self, content: str) -> str:
        cleaned = (content or "").replace("\x00", "").strip()
        if not cleaned:
            return ""

        if len(cleaned) <= self.max_sample_chars:
            return cleaned

        head_chars = int(self.max_sample_chars * 0.7)
        tail_chars = self.max_sample_chars - head_chars
        return f"{cleaned[:head_chars]}\n\n...[content omitted]...\n\n{cleaned[-tail_chars:]}"

    def _build_prompt(self, content_sample: str, language: str, title_hint: str, author_hint: str) -> str:
        lang = "Chinese" if language == "chinese" else "English"
        return f"""You are a professional book editor. Read the content sample and produce concise book metadata.

Language: {lang}
Title hint: {title_hint or "None"}
Author hint: {author_hint or "None"}

Content sample:
{content_sample}

Requirements:
1. Return strict JSON only.
2. Keep title natural and marketable, avoid clickbait.
3. Description should be 60-220 words, no spoilers.
4. tags must be an array with 3-8 short tags.
5. language must be "zh" or "en".
6. Keep empty string when unknown.

JSON schema:
{{
  "title": "string",
  "subtitle": "string",
  "author": "string",
  "description": "string",
  "tags": ["string"],
  "publisher": "string",
  "date": "YYYY-MM-DD or empty",
  "identifier": "string",
  "language": "zh|en",
  "confidence": 0.0
}}
"""

    def _normalize_metadata(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        title = self._clean_text(raw.get("title"))
        subtitle = self._clean_text(raw.get("subtitle"))
        author = self._clean_text(raw.get("author"))
        description = self._clean_text(raw.get("description"), max_length=2000)
        publisher = self._clean_text(raw.get("publisher"))
        identifier = self._clean_text(raw.get("identifier"))
        date_value = self._normalize_date(raw.get("date"))
        language = self._normalize_language(raw.get("language"))
        tags = self._normalize_tags(raw.get("tags"))

        return {
            "title": title,
            "subtitle": subtitle,
            "author": author,
            "description": description,
            "tags": tags,
            "publisher": publisher,
            "date": date_value,
            "identifier": identifier,
            "language": language,
        }

    def _normalize_tags(self, tags_value: Any) -> List[str]:
        tags: List[str] = []
        if isinstance(tags_value, str):
            tags = [tag.strip() for tag in re.split(r"[;,，、/]", tags_value) if tag.strip()]
        elif isinstance(tags_value, list):
            tags = [self._clean_text(tag, max_length=40) for tag in tags_value if self._clean_text(tag)]

        deduped: List[str] = []
        seen = set()
        for tag in tags:
            key = tag.lower()
            if key not in seen:
                deduped.append(tag)
                seen.add(key)
            if len(deduped) >= self.max_tags:
                break
        return deduped

    @staticmethod
    def _clean_text(value: Any, max_length: int = 200) -> str:
        if not isinstance(value, str):
            return ""
        text = re.sub(r"\s+", " ", value).strip()
        return text[:max_length]

    @staticmethod
    def _normalize_language(language_value: Any) -> str:
        if not isinstance(language_value, str):
            return ""
        value = language_value.strip().lower()
        if value in {"zh", "zh-cn", "chinese"}:
            return "zh"
        if value in {"en", "en-us", "english"}:
            return "en"
        return ""

    @staticmethod
    def _normalize_date(date_value: Any) -> str:
        if not isinstance(date_value, str):
            return ""
        value = date_value.strip()
        if re.match(r"^\d{4}(-\d{2}(-\d{2})?)?$", value):
            return value
        return ""
