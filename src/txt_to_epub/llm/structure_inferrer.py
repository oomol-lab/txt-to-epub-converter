"""
Structure inference assistant for documents without clear chapter markers
"""
import json
import logging
from typing import List, Dict

from .client import LLMClient

logger = logging.getLogger(__name__)


class StructureInferrer:
    """Infer document structure using LLM"""

    def __init__(self, client: LLMClient):
        """
        Initialize structure inferrer

        :param client: LLM client instance
        """
        self.client = client

    def infer_chapter_structure(
        self,
        content: str,
        max_length: int = 10000,
        language: str = 'chinese'
    ) -> List[Dict]:
        """
        Infer chapter structure for text without obvious chapter markers

        :param content: Text content
        :param max_length: Maximum analysis length
        :param language: Document language
        :return: Suggested chapter structure
        """
        logger.info(f"LLM inferring structure, text length: {len(content)} characters...")

        # Extract analysis sample
        sample = content[:max_length]

        prompt = f"""You are a document structure analysis expert. The following text lacks clear chapter markers; please analyze and suggest chapter divisions.

【Text Sample】({len(sample)} characters)
{sample}

【Language】{language}

【Task】
1. Identify topic transition points in the content
2. Suggest chapter division positions
3. Generate a title for each chapter

Output JSON format:
{{
  "suggested_chapters": [
    {{
      "start_char": 0,
      "end_char": 500,
      "title": "Suggested title",
      "reason": "Basis for division",
      "confidence": 0.85
    }}
  ],
  "format_analysis": "Analysis of format characteristics",
  "confidence": 0.8
}}
"""

        response = self.client.call(prompt, max_tokens=128000)
        result = self._parse_structure_response(response)

        logger.info(f"LLM suggested {len(result)} chapters")
        return result

    def _parse_structure_response(self, response: str) -> List[Dict]:
        """Parse structure inference response"""
        try:
            data = json.loads(response)
            return data.get('suggested_chapters', [])
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse structure response: {e}")
            return []
