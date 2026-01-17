"""
Table of Contents (TOC) identification assistant
"""
import json
import logging
from typing import Dict

from .client import LLMClient

logger = logging.getLogger(__name__)


class TOCAssistant:
    """Table of Contents identification using LLM"""

    def __init__(self, client: LLMClient):
        """
        Initialize TOC assistant

        :param client: LLM client instance
        """
        self.client = client

    def identify_table_of_contents(
        self,
        content_sample: str,
        language: str = 'chinese'
    ) -> Dict:
        """
        Identify if text contains table of contents page and return TOC location range

        :param content_sample: Text sample (first 1000 lines or more)
        :param language: Language type
        :return: TOC identification result
        """
        logger.info("LLM identifying table of contents page...")

        if language == 'english':
            prompt = self._build_english_toc_prompt(content_sample)
        else:
            prompt = self._build_chinese_toc_prompt(content_sample)

        response = self.client.call(prompt, max_tokens=128000, temperature=0.1)

        # Handle empty response
        if not response or not response.strip():
            logger.warning("LLM returned empty response (TOC identification)")
            return {
                'has_toc': False,
                'confidence': 0.0,
                'reason': 'LLM could not provide judgment'
            }

        try:
            result = json.loads(response)
            logger.info(f"TOC identification result: {'Found TOC' if result.get('has_toc') else 'No TOC'} "
                       f"(confidence: {result.get('confidence', 0):.2f})")
            return result
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed (TOC identification): {e}")
            return {
                'has_toc': False,
                'confidence': 0.0,
                'reason': 'Parsing failed',
                'error': str(e)
            }

    def _build_english_toc_prompt(self, content_sample: str) -> str:
        """Build English TOC identification prompt"""
        return f"""You are a document structure analysis expert. Please identify whether the following text contains a Table of Contents (TOC) page.

【Text Sample】(first 3000 characters)
{content_sample[:3000]}

【Task】
Carefully analyze if there is a TOC section, even WITHOUT explicit "Contents" or "TOC" labels.

【Key TOC Characteristics】
1. **High density of chapter-like patterns**: Multiple lines with "Chapter X", "Part X", etc.
2. **Consecutive short lines**: Lines with chapter names but minimal content (usually < 80 chars)
3. **Page numbers**: Lines ending with numbers (e.g., "Chapter 1 ... 15")
4. **Lack of narrative content**: No story text, just titles and numbers
5. **Early position**: Usually at document beginning (first 100-500 lines)
6. **Consistent format**: All entries follow similar pattern

【Important】
- A TOC can exist WITHOUT the word "Contents" or "Table of Contents"
- Focus on structural patterns, not keywords
- Look for 5+ consecutive chapter-like entries

【Response Format】JSON:
{{
  "has_toc": true/false,
  "confidence": 0.0-1.0,
  "start_indicator": "description of where TOC starts (e.g., 'line 5' or 'after preface')",
  "end_indicator": "description of where TOC ends (e.g., 'line 45' or 'before first paragraph')",
  "reason": "detailed explanation (mention specific patterns observed)",
  "toc_entries_count": estimated number of entries,
  "key_evidence": ["evidence 1", "evidence 2", "evidence 3"]
}}
"""

    def _build_chinese_toc_prompt(self, content_sample: str) -> str:
        """Build Chinese TOC identification prompt"""
        return f"""You are a document structure analysis expert. Please identify whether the following text contains a table of contents page.

【Text Sample】(first 3000 characters)
{content_sample[:3000]}

【Task】
Carefully analyze if there is a table of contents page, even **without explicit "Contents" or "CONTENTS" labels**.

【Key Characteristics of Table of Contents】
1. **High density of chapter patterns**: Multiple lines containing "Chapter X", "Part X" patterns
2. **Consecutive short lines**: Line content is brief (usually < 80 characters), only chapter names
3. **Page number markers**: Numbers at end of lines (e.g., "Chapter 1 Beginning ... 15")
4. **Lack of narrative content**: No story text, just titles and numbers
5. **Early position**: Usually at document beginning (first 100-500 lines)
6. **Consistent format**: All entries follow similar format

【Important Notes】
- Table of contents may not have the word "contents"
- Focus on structural patterns, not keywords
- Look for 5 or more consecutive chapter-style entries

【Output Format】JSON:
{{
  "has_toc": true/false,
  "confidence": 0.0-1.0,
  "start_indicator": "Description of where TOC starts (e.g., 'line 5' or 'after preface')",
  "end_indicator": "Description of where TOC ends (e.g., 'line 45' or 'before first long paragraph')",
  "reason": "Detailed explanation of reasoning (mention specific patterns observed)",
  "toc_entries_count": Estimated number of TOC entries,
  "key_evidence": ["evidence 1", "evidence 2", "evidence 3"]
}}
"""
