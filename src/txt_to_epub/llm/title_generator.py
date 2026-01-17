"""
Chapter title generation assistant
"""
import json
import logging
from typing import Dict, List

from .client import LLMClient

logger = logging.getLogger(__name__)


class TitleGenerator:
    """Chapter title generation using LLM"""

    def __init__(self, client: LLMClient):
        """
        Initialize title generator

        :param client: LLM client instance
        """
        self.client = client

    def generate_chapter_title(
        self,
        chapter_number: str,
        chapter_content: str,
        language: str = 'chinese',
        max_content_length: int = 400
    ) -> Dict:
        """
        Use LLM to generate appropriate chapter title based on chapter content

        :param chapter_number: Chapter number (e.g., "Chapter 007", "Chapter 7")
        :param chapter_content: Chapter content (beginning portion)
        :param language: Language type
        :param max_content_length: Maximum content length for analysis
        :return: Dictionary containing generated title
        """
        logger.info(f"LLM generating chapter title: {chapter_number}")

        # Limit content length
        content_sample = chapter_content[:max_content_length].strip()

        if language == 'english':
            prompt = self._build_english_title_prompt(chapter_number, content_sample)
        else:
            prompt = self._build_chinese_title_prompt(chapter_number, content_sample)

        try:
            response = self.client.call(prompt, temperature=0.3, max_tokens=100)
            result = json.loads(response)

            # Validate result
            if 'title' not in result:
                logger.warning("LLM response missing 'title' field")
                result['title'] = ""

            if 'confidence' not in result:
                result['confidence'] = 0.5

            logger.info(f"✓ Generated title: {result.get('title', 'N/A')} (confidence: {result.get('confidence', 0):.2f})")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed (title generation): {e}")
            return {
                'title': "",
                'confidence': 0.0,
                'reason': f'Parsing failed: {str(e)}',
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Title generation failed: {e}")
            return {
                'title': "",
                'confidence': 0.0,
                'reason': f'Generation failed: {str(e)}',
                'error': str(e)
            }

    def generate_chapter_titles_batch(
        self,
        chapters_info: List[Dict[str, str]],
        language: str = 'chinese',
        max_content_length: int = 400
    ) -> List[Dict]:
        """
        Batch generate chapter titles (process multiple chapters in one LLM call)

        :param chapters_info: List of chapter information
        :param language: Language type
        :param max_content_length: Maximum content length for analysis per chapter
        :return: List of title results
        """
        if not chapters_info:
            return []

        logger.info(f"LLM batch generating {len(chapters_info)} chapter titles...")

        # Limit batch size to avoid exceeding token limit
        batch_size = 50
        all_results = []

        for batch_start in range(0, len(chapters_info), batch_size):
            batch = chapters_info[batch_start:batch_start + batch_size]

            # Build batch chapter list
            chapters_text = []
            for i, ch_info in enumerate(batch, start=batch_start + 1):
                content_sample = ch_info['content'][:max_content_length].strip()
                chapters_text.append(f"{i}. {ch_info['number']}\nContent: {content_sample[:200]}...")

            chapters_list = "\n\n".join(chapters_text)

            if language == 'english':
                prompt = self._build_english_batch_prompt(chapters_list)
            else:
                prompt = self._build_chinese_batch_prompt(chapters_list)

            try:
                response = self.client.call(prompt, temperature=0.3, max_tokens=2000)
                result = json.loads(response)

                # Parse results
                titles = result.get('titles', [])

                # Create index-to-result mapping
                title_map = {item['index']: item for item in titles}

                # Return results in original order
                for i, ch_info in enumerate(batch, start=batch_start + 1):
                    if i in title_map:
                        all_results.append(title_map[i])
                    else:
                        all_results.append({
                            'index': i,
                            'title': "",
                            'confidence': 0.0
                        })

                logger.info(f"✓ Batch generation complete: {len(titles)}/{len(batch)} titles successful")

            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing failed (batch title generation): {e}")
                for i in range(len(batch)):
                    all_results.append({
                        'index': batch_start + i + 1,
                        'title': "",
                        'confidence': 0.0,
                        'error': str(e)
                    })
            except Exception as e:
                logger.error(f"Batch title generation failed: {e}")
                for i in range(len(batch)):
                    all_results.append({
                        'index': batch_start + i + 1,
                        'title': "",
                        'confidence': 0.0,
                        'error': str(e)
                    })

        logger.info(f"Batch title generation complete: total {len(all_results)} chapters")
        return all_results

    def _build_english_title_prompt(self, chapter_number: str, content_sample: str) -> str:
        """Build English title generation prompt"""
        return f"""Generate a 3-8 word chapter title for: {chapter_number}

Content: {content_sample}

Requirements: Concise, meaningful, avoid dialogue quotes.

JSON response:
{{"title": "title text", "confidence": 0.0-1.0}}"""

    def _build_chinese_title_prompt(self, chapter_number: str, content_sample: str) -> str:
        """Build Chinese title generation prompt"""
        return f"""Generate a 3-12 character title for the chapter: {chapter_number}

Content: {content_sample}

Requirements: Concise and meaningful, avoid dialogue quotes.

JSON format:
{{"title": "title", "confidence": 0.0-1.0}}"""

    def _build_english_batch_prompt(self, chapters_list: str) -> str:
        """Build English batch title generation prompt"""
        return f"""Generate concise titles (3-8 words) for the following chapters based on their content:

{chapters_list}

Requirements:
- Title should be meaningful and reflect the content
- Avoid dialogue quotes
- Keep titles concise

JSON response format:
{{
  "titles": [
    {{"index": 1, "title": "generated title", "confidence": 0.0-1.0}},
    {{"index": 2, "title": "generated title", "confidence": 0.0-1.0}}
  ]
}}"""

    def _build_chinese_batch_prompt(self, chapters_list: str) -> str:
        """Build Chinese batch title generation prompt"""
        return f"""Generate concise titles (3-12 characters) for the following chapters based on their content:

{chapters_list}

Requirements:
- Title should be meaningful and reflect the content
- Avoid dialogue quotes
- Keep titles concise

JSON format:
{{
  "titles": [
    {{"index": 1, "title": "generated title", "confidence": 0.0-1.0}},
    {{"index": 2, "title": "generated title", "confidence": 0.0-1.0}}
  ]
}}"""
