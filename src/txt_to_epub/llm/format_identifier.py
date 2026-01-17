"""
Format identification assistant for special document formats
"""
import json
import logging
from typing import Dict, List

from .client import LLMClient

logger = logging.getLogger(__name__)


class FormatIdentifier:
    """Identify special document formats using LLM"""

    def __init__(self, client: LLMClient):
        """
        Initialize format identifier

        :param client: LLM client instance
        """
        self.client = client

    def identify_special_format(
        self,
        content_sample: str,
        observed_patterns: List[str]
    ) -> Dict:
        """
        Identify chapter patterns for books with special formats

        :param content_sample: Text sample
        :param observed_patterns: Observed patterns
        :return: Format identification result
        """
        logger.info("LLM identifying special format...")

        patterns_text = "\n".join(f"- {p}" for p in observed_patterns)

        prompt = f"""This is a book with a special format. Please help identify its chapter structure.

【Text Sample】
{content_sample[:2000]}

【Observed Patterns】
{patterns_text}

Please analyze:
1. What chapter marking method does this book use?
2. How to identify chapter boundaries?
3. Suggested regular expression

Output JSON:
{{
  "format_type": "Format type",
  "chapter_pattern": "Pattern description",
  "identification_rules": ["Rule 1", "Rule 2"],
  "sample_chapters": [{{"title": "...", "position": 0}}],
  "confidence": 0.8,
  "suggested_regex": "Regular expression"
}}
"""

        response = self.client.call(prompt, max_tokens=128000)

        # Debug: print raw response
        logger.debug(f"LLM raw response: {response}")

        # Handle empty response
        if not response or not response.strip():
            logger.warning("LLM returned empty response")
            return {
                'format_type': 'unknown',
                'chapter_pattern': 'unknown',
                'confidence': 0.0,
                'suggested_regex': None
            }

        try:
            result = json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}, raw response: {response[:200]}")
            return {
                'format_type': 'parse_error',
                'chapter_pattern': 'unknown',
                'confidence': 0.0,
                'suggested_regex': None,
                'error': str(e)
            }

        logger.info(f"Identified format: {result.get('format_type', 'unknown')}")
        return result
