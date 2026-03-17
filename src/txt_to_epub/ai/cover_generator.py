"""
Book cover generation assistant powered by text-to-image models.
"""
import logging
import os
import re
import tempfile
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import requests

from ..llm.client import LLMClient

logger = logging.getLogger(__name__)


class CoverGenerator:
    """Generate a temporary cover image file from book context."""
    FUSION_IMAGE_API_URL = "https://fusion-api.oomol.com/v1/doubao-text-to-image-seedream/action/generate"

    def __init__(
        self,
        api_key: str = None,
        model: str = "google/gemini-2.5-flash-image",
        base_url: str = None,
        organization: str = None,
        size: str = "1024x1536",
        quality: str = "standard",
        fusion_image_api_url: Optional[str] = None,
    ):
        self.client = LLMClient(api_key=api_key, model=model, base_url=base_url, organization=organization)
        self.model = model
        self.size = size
        self.quality = quality
        self.api_key = api_key or ""
        self.base_url = base_url or ""
        self.fusion_image_api_url = (fusion_image_api_url or self.FUSION_IMAGE_API_URL).strip()
        self.stats = {
            "total_calls": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost": 0.0,
        }

    def generate_cover(
        self,
        title: str,
        author: str,
        description: str = "",
        tags: Optional[list] = None,
        language: str = "chinese",
        style_hint: str = "",
        content_sample: str = "",
        source_hint: str = "",
    ) -> Dict[str, Any]:
        """
        Generate a cover image and write it to a temporary PNG file.
        """
        prompt = self._build_cover_prompt(
            title=title,
            author=author,
            description=description,
            tags=tags or [],
            language=language,
            style_hint=style_hint,
            content_sample=content_sample,
            source_hint=source_hint
        )

        try:
            # Prefer OOMOL Fusion image API flow for OOMOL/OneAPI-style keys.
            # This follows the referenced implementation and avoids provider-specific image SDK quirks.
            if self._should_use_fusion_api():
                try:
                    image_bytes = self._generate_image_with_fusion_api(prompt)
                except Exception as fusion_error:
                    logger.warning(f"Fusion API image generation failed, falling back to OpenAI-compatible API: {fusion_error}")
                    image_bytes = self.client.generate_image(
                        prompt=prompt,
                        model=self.model,
                        size=self.size,
                        quality=self.quality
                    )
            else:
                image_bytes = self.client.generate_image(
                    prompt=prompt,
                    model=self.model,
                    size=self.size,
                    quality=self.quality
                )

            fd, output_path = tempfile.mkstemp(prefix="txt_to_epub_cover_", suffix=".png")
            with os.fdopen(fd, "wb") as f:
                f.write(image_bytes)

            logger.info(f"AI cover generated at {output_path}")
            return {"success": True, "cover_path": output_path}
        except Exception as e:
            logger.error(f"Cover generation failed: {e}")
            return {"success": False, "reason": str(e), "cover_path": None}

    def get_stats(self) -> Dict[str, Any]:
        """Return LLM usage stats."""
        llm_stats = self.client.get_stats()
        merged = dict(self.stats)
        for key, value in llm_stats.items():
            if isinstance(value, (int, float)) and isinstance(merged.get(key), (int, float)):
                merged[key] = merged[key] + value
            elif key not in merged:
                merged[key] = value
        return merged

    def _should_use_fusion_api(self) -> bool:
        """Determine whether to call the Fusion image API first."""
        if not self.api_key:
            return False
        if self.api_key.startswith("api-"):
            return True
        if self.base_url:
            parsed = urlparse(self.base_url if "://" in self.base_url else f"https://{self.base_url}")
            host = (parsed.netloc or "").lower()
            if host == "llm.oomol.com" or host.endswith(".oomol.com"):
                return True
        if "oomol.com" in self.base_url.lower():
            return True
        if self.model.startswith("google/"):
            return True
        return False

    def _generate_image_with_fusion_api(self, prompt: str) -> bytes:
        """Generate image via Fusion API and download the resulting URL."""
        self.stats["total_calls"] += 1
        compact_prompt = self._compact_prompt_for_fusion(prompt)

        headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {"prompt": compact_prompt}
        size_obj = self._parse_size(self.size)
        if size_obj:
            payload["size"] = size_obj

        response = requests.post(
            self.fusion_image_api_url,
            headers=headers,
            json=payload,
            timeout=120,
        )
        if response.status_code >= 400:
            raise requests.HTTPError(
                f"{response.status_code} Client Error for Fusion API: {response.text}",
                response=response
            )
        result = response.json()

        image_url = ""
        data = result.get("data")
        if isinstance(data, list) and data:
            image_url = str(data[0].get("url") or "").strip()
        elif isinstance(data, dict):
            image_url = str(data.get("image_url") or data.get("url") or "").strip()
        if not image_url:
            image_url = str(result.get("image_url") or "").strip()

        if not image_url:
            raise ValueError(f"Unexpected Fusion API response format: {result}")

        image_response = requests.get(image_url, timeout=120)
        image_response.raise_for_status()
        return image_response.content

    @staticmethod
    def _compact_prompt_for_fusion(prompt: str, max_chars: int = 700) -> str:
        """
        Fusion endpoint is stricter on long prompts.
        Compact to a concise, stable form while preserving key constraints.
        """
        text = re.sub(r"\s+", " ", prompt or "").strip()
        if len(text) <= max_chars:
            return text
        return text[:max_chars]

    @staticmethod
    def _parse_size(size_value: str) -> Optional[Dict[str, int]]:
        """Parse size string like 1024x1536 into Fusion API object."""
        if not isinstance(size_value, str):
            return None
        matched = re.match(r"^\s*(\d+)\s*x\s*(\d+)\s*$", size_value)
        if not matched:
            return None
        width = int(matched.group(1))
        height = int(matched.group(2))
        if width <= 0 or height <= 0:
            return None
        return {"width": width, "height": height}

    @staticmethod
    def _build_cover_prompt(
        title: str,
        author: str,
        description: str,
        tags: list,
        language: str,
        style_hint: str,
        content_sample: str,
        source_hint: str
    ) -> str:
        lang = "Chinese" if language == "chinese" else "English"
        tags_text = ", ".join(tags[:6]) if tags else "none"
        opening_excerpt = (content_sample or "").strip()[:1000]
        source_text = (source_hint or "").strip()
        combined_text = " ".join([title or "", description or "", tags_text, source_text, opening_excerpt])
        known_book_brief = CoverGenerator._infer_known_book_brief(combined_text)
        opening_signals = CoverGenerator._extract_opening_signals(opening_excerpt)

        historical_cue = CoverGenerator._infer_historical_cue(combined_text)
        context_cue_block = f"- Historical context cue: {historical_cue}." if historical_cue else "- Historical context cue: not explicit."
        prior_block = (
            f"- Known-work prior: {known_book_brief}.\n"
            "- Use known-work prior as the primary narrative anchor, then align details with opening excerpt."
            if known_book_brief
            else "- Unknown-work mode: derive theme and atmosphere from opening excerpt instead of title-only assumptions."
        )
        opening_signals_block = (
            f"- Opening signals: {opening_signals}."
            if opening_signals
            else "- Opening signals: not enough explicit cues, infer conservatively."
        )
        clean_author = (author or "").strip()
        author_line = f"Author: {clean_author}" if clean_author else "Author: [omit]"
        author_requirement = (
            "- If author typography is used, use exactly the provided author name without rewriting."
            if clean_author
            else "- Do not render any author name text on the cover."
        )

        return f"""Design a professional fiction ebook cover.

Language: {lang}
Title: {title or "Untitled"}
{author_line}
Source title hint: {source_text or "N/A"}
Critical constraints:
- Vertical composition in strict book-cover ratio.
- No watermark, no logo, no extra random text.
- Keep style coherent with genre and tone.
{context_cue_block}
{prior_block}
{opening_signals_block}
Genre tags: {tags_text}
Description: {description[:400] if description else "N/A"}
Style hint: {style_hint or "cinematic, modern, high-contrast"}
Opening excerpt: {opening_excerpt or "N/A"}

Additional requirements:
- Strong focal element, readable typography area.
- Typography must be limited to the title (and optional real author name).
- Never invent placeholder names like "Unknown" or "Unknown Author".
- {author_requirement}
- Do NOT rely on title alone.
- Derive costumes/architecture/props from the provided context signals.
- If a historical era is implied, keep all visual details consistent with that era.
- Avoid mixing iconic symbols from unrelated eras, cultures, or genres unless explicitly requested.
- Prioritize narrative fit over generic "ancient style" tropes.
"""

    @staticmethod
    def _infer_historical_cue(text: str) -> str:
        """Infer broad historical cue from source signals for prompt conditioning."""
        if not text:
            return ""

        cues = [
            (r"(明朝|明代|大明|ming)", "Ming Dynasty China"),
            (r"(清朝|清代|大清|qing)", "Qing Dynasty China"),
            (r"(唐朝|唐代|大唐|tang)", "Tang Dynasty China"),
            (r"(宋朝|宋代|大宋|song dynasty)", "Song Dynasty China"),
            (r"(元朝|元代|yuan dynasty)", "Yuan Dynasty China"),
            (r"(汉朝|汉代|han dynasty)", "Han Dynasty China"),
            (r"(三国|three kingdoms)", "Three Kingdoms China"),
            (r"(民国|republic of china|roc era)", "Republic of China era"),
            (r"(古罗马|roman empire|ancient rome)", "Ancient Rome"),
            (r"(维多利亚|victorian)", "Victorian era"),
            (r"(中世纪|medieval)", "Medieval era"),
        ]

        lower = text.lower()
        for pattern, label in cues:
            if re.search(pattern, lower, re.IGNORECASE):
                return label

        return ""

    @staticmethod
    def _infer_known_book_brief(text: str) -> str:
        """Return high-confidence narrative prior for well-known books."""
        if not text:
            return ""

        lower = text.lower()
        known_books = [
            (r"(明朝那些事儿|明朝那些事|those things in ming|ming affairs)", "Witty and human-centered narrative history of Ming politics, court struggles, and major historical figures"),
            (r"(三国演义|romance of the three kingdoms)", "Epic war strategy narrative with heroes, alliances, and battlefield politics in late Han/Three Kingdoms"),
            (r"(红楼梦|dream of the red chamber)", "Aristocratic family decline, refined mansion life, poetic melancholy, and emotional complexity in Qing high society"),
            (r"(西游记|journey to the west)", "Mythic pilgrimage adventure with monk and disciples, fantasy demons, and spiritual quest motifs"),
            (r"(水浒传|water margin|outlaws of the marsh)", "Brotherhood of outlaws, rebel spirit, martial drama, and rustic Song-era atmosphere"),
            (r"(哈利[·\\. ]?波特|harry potter)", "Coming-of-age wizard school narrative with magic, mystery, and dark-vs-light tension"),
            (r"(1984|nineteen eighty[- ]?four)", "Dystopian surveillance state with oppressive architecture and bleak political atmosphere"),
        ]

        for pattern, brief in known_books:
            if re.search(pattern, lower, re.IGNORECASE):
                return brief
        return ""

    @staticmethod
    def _extract_opening_signals(opening_excerpt: str) -> str:
        """Extract compact narrative cues from the opening excerpt."""
        if not opening_excerpt:
            return ""

        text = re.sub(r"\s+", " ", opening_excerpt).strip()
        if not text:
            return ""

        pieces = re.split(r"[。！？!?；;]", text)
        selected = []
        for piece in pieces:
            part = piece.strip(" \t\r\n,，。;；")
            if len(part) < 8:
                continue
            selected.append(part[:48])
            if len(selected) >= 3:
                break

        return " | ".join(selected)
