"""
Disambiguation assistant for chapter titles vs references
"""
import json
import logging
from typing import Dict

from .client import LLMClient

logger = logging.getLogger(__name__)


class Disambiguator:
    """Disambiguate chapter titles from text references"""

    def __init__(self, client: LLMClient):
        """
        Initialize disambiguator

        :param client: LLM client instance
        """
        self.client = client

    def disambiguate_reference(
        self,
        text_snippet: str,
        candidate: str,
        context: Dict
    ) -> Dict:
        """
        Disambiguate: determine if chapter title or text reference

        :param text_snippet: Text snippet containing candidate
        :param candidate: Candidate chapter text
        :param context: Context information
        :return: Decision dictionary
        """
        logger.debug(f"LLM disambiguation: {candidate}")

        language = context.get('language', 'chinese')

        if language == 'english':
            prompt = self._build_english_prompt(text_snippet, candidate, context)
        else:
            prompt = self._build_chinese_prompt(text_snippet, candidate, context)

        response = self.client.call(prompt, max_tokens=128000)

        # Handle empty response
        if not response or not response.strip():
            logger.warning("LLM returned empty response (disambiguation)")
            return {
                'type': 'reference',
                'confidence': 0.5,
                'reason': 'LLM could not provide clear judgment'
            }

        try:
            result = json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed (disambiguation): {e}")
            return {
                'type': 'reference',
                'confidence': 0.5,
                'reason': 'Parsing failed, conservatively judging as reference'
            }

        logger.debug(f"Decision: {result['type']} (confidence: {result['confidence']})")
        return result

    def _build_english_prompt(self, text_snippet: str, candidate: str, context: Dict) -> str:
        """Build English disambiguation prompt"""
        return f"""Determine whether "{candidate}" in the following text is a chapter title or a reference in the text?

【Text Snippet】
{text_snippet}

【Context】
- Previous Chapter: {context.get('prev_chapter', 'N/A')}
- Document Type: {context.get('doc_type', 'Unknown')}
- Language: English

Analysis Points:
1. Position: Standalone on a line or in the middle of a sentence?
2. Grammar: Is it part of sentence structure?
3. Format: Does it match chapter title format?

Response Format:
{{
  "type": "chapter" or "reference",
  "confidence": 0.0-1.0,
  "reason": "Reasoning for judgment"
}}
"""

    def _build_chinese_prompt(self, text_snippet: str, candidate: str, context: Dict) -> str:
        """Build Chinese disambiguation prompt"""
        return f"""Determine whether this is a chapter title or a reference in the following Chinese text?

【Text Snippet】
{text_snippet}

【Context】
- Previous Chapter: {context.get('prev_chapter', 'N/A')}
- Document Type: {context.get('doc_type', 'Unknown')}
- Language: Chinese

Analysis Points:
1. Position: Standalone on a line or in the middle of a sentence?
2. Grammar: Is it part of sentence structure?
3. Format: Does it match chapter title format?

Response Format:
{{
  "type": "chapter" or "reference",
  "confidence": 0.0-1.0,
  "reason": "Reasoning for judgment"
}}
"""
