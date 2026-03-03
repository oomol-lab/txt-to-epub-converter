"""
Chapter illustration generation assistant powered by text-to-image models.
"""
import logging
import os
import tempfile
from typing import Any, Dict, List, Optional

from .cover_generator import CoverGenerator

logger = logging.getLogger(__name__)


class IllustrationGenerator(CoverGenerator):
    """Generate temporary chapter illustration files."""

    def generate_illustration(
        self,
        book_title: str,
        chapter_title: str,
        chapter_content: str = "",
        description: str = "",
        tags: Optional[list] = None,
        language: str = "chinese",
        style_hint: str = "",
        source_hint: str = "",
        continuity_guide: Optional[Dict[str, Any]] = None,
        character_focus: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Generate one chapter illustration image and write it to a temporary PNG file."""
        prompt = self._build_illustration_prompt(
            book_title=book_title,
            chapter_title=chapter_title,
            chapter_content=chapter_content,
            description=description,
            tags=tags or [],
            language=language,
            style_hint=style_hint,
            source_hint=source_hint,
            continuity_guide=continuity_guide or {},
            character_focus=character_focus or [],
        )

        try:
            if self._should_use_fusion_api():
                try:
                    image_bytes = self._generate_image_with_fusion_api(prompt)
                except Exception as fusion_error:
                    logger.warning(f"Fusion API illustration generation failed, fallback to compatible API: {fusion_error}")
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

            fd, output_path = tempfile.mkstemp(prefix="txt_to_epub_illustration_", suffix=".png")
            with os.fdopen(fd, "wb") as f:
                f.write(image_bytes)

            logger.info(f"AI chapter illustration generated at {output_path}")
            return {"success": True, "image_path": output_path}
        except Exception as e:
            logger.error(f"Chapter illustration generation failed: {e}")
            return {"success": False, "reason": str(e), "image_path": None}

    @staticmethod
    def _build_illustration_prompt(
        book_title: str,
        chapter_title: str,
        chapter_content: str,
        description: str,
        tags: list,
        language: str,
        style_hint: str,
        source_hint: str,
        continuity_guide: Dict[str, Any],
        character_focus: List[str],
    ) -> str:
        lang = "Chinese" if language == "chinese" else "English"
        tags_text = ", ".join(tags[:6]) if tags else "none"
        chapter_excerpt = (chapter_content or "").strip()[:1000]
        source_text = (source_hint or "").strip()
        combined_text = " ".join([book_title or "", chapter_title or "", description or "", tags_text, chapter_excerpt])
        historical_cue = CoverGenerator._infer_historical_cue(combined_text)
        context_cue_block = f"- Historical context cue: {historical_cue}." if historical_cue else "- Historical context cue: not explicit."
        continuity_block = IllustrationGenerator._build_continuity_block(continuity_guide, character_focus)

        return f"""Create a single narrative ebook illustration for one chapter.

Language: {lang}
Book title: {book_title or "Untitled"}
Chapter title: {chapter_title or "Untitled chapter"}
Source title hint: {source_text or "N/A"}
{context_cue_block}
Genre tags: {tags_text}
Book description: {description[:300] if description else "N/A"}
Style hint: {style_hint or "cinematic, coherent with the book cover style"}
Chapter excerpt: {chapter_excerpt or "N/A"}
{continuity_block}

Requirements:
- One strong scene with clear focal subject and readable composition.
- Keep visual style consistent with the same book's cover.
- No text, no lettering, no watermark, no logo.
- Avoid mismatched eras/cultures unless explicitly requested in context.
- Focus on atmosphere and narrative fit, not generic fantasy symbols.
"""

    @staticmethod
    def _build_continuity_block(continuity_guide: Dict[str, Any], character_focus: List[str]) -> str:
        """Build continuity constraints block injected into chapter prompts."""
        if not continuity_guide:
            return "- Continuity guide: none."

        style_bible = str(continuity_guide.get("style_bible") or "").strip()
        setting_bible = str(continuity_guide.get("setting_bible") or "").strip()
        negative_constraints = continuity_guide.get("negative_constraints") or []
        if not isinstance(negative_constraints, list):
            negative_constraints = []
        negatives = [str(item).strip() for item in negative_constraints if str(item).strip()]

        char_lines: List[str] = []
        characters = continuity_guide.get("characters") or []
        if isinstance(characters, list):
            for character in characters[:8]:
                if not isinstance(character, dict):
                    continue
                name = str(character.get("name") or "").strip()
                appearance = str(character.get("appearance") or "").strip()
                identity = str(character.get("identity") or "").strip()
                if not name:
                    continue
                line = f"{name}: {appearance}" if appearance else name
                if identity:
                    line += f" ({identity})"
                char_lines.append(line)

        focus = [str(name).strip() for name in (character_focus or []) if str(name).strip()]
        focus_text = ", ".join(focus) if focus else "auto"

        parts: List[str] = ["- Continuity mode: keep consistent character identity, outfit silhouette, and art direction."]
        if style_bible:
            parts.append(f"- Style bible: {style_bible}")
        if setting_bible:
            parts.append(f"- Setting bible: {setting_bible}")
        if char_lines:
            parts.append(f"- Character bible: {'; '.join(char_lines[:6])}")
        parts.append(f"- Character focus for this chapter: {focus_text}.")
        if negatives:
            parts.append(f"- Continuity negatives: {'; '.join(negatives[:6])}")

        return "\n".join(parts)
