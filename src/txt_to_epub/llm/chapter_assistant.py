"""
Chapter candidate analysis assistant
"""
import json
import logging
from typing import List, Dict

from .client import LLMClient
from .data_structures import ChapterCandidate, LLMDecision
from .prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


class ChapterAssistant:
    """Chapter candidate analysis using LLM"""

    def __init__(self, client: LLMClient):
        """
        Initialize chapter assistant

        :param client: LLM client instance
        """
        self.client = client

    def analyze_chapter_candidates(
        self,
        candidates: List[ChapterCandidate],
        full_content: str,
        existing_chapters: List[Dict],
        doc_context: Dict = None
    ) -> List[LLMDecision]:
        """
        Analyze chapter candidates to determine if they are real chapters

        :param candidates: List of chapter candidates
        :param full_content: Full text content
        :param existing_chapters: Confirmed chapter information
        :param doc_context: Document context information
        :return: List of decision results
        """
        if not candidates:
            return []

        logger.info(f"LLM analyzing {len(candidates)} chapter candidates...")

        # Calculate average chapter length
        if existing_chapters:
            avg_length = sum(ch.get('length', 0) for ch in existing_chapters) / len(existing_chapters)
        else:
            avg_length = 0

        # Build prompt
        prompt = PromptBuilder.build_chapter_analysis_prompt(
            candidates,
            existing_chapters,
            avg_length,
            doc_context or {}
        )

        # Call LLM
        response = self.client.call(prompt)

        # Parse response
        decisions = self._parse_llm_response(response)

        # Update statistics
        confirmed = sum(1 for d in decisions if d.is_chapter)
        logger.info(f"LLM confirmed {confirmed}/{len(candidates)} as real chapters")

        return decisions

    def _parse_llm_response(self, response: str) -> List[LLMDecision]:
        """Parse LLM JSON response"""
        try:
            data = json.loads(response)
            decisions = []

            for item in data.get('decisions', []):
                decisions.append(LLMDecision(
                    is_chapter=item.get('is_chapter', False),
                    confidence=item.get('confidence', 0.5),
                    reason=item.get('reason', ''),
                    suggested_title=item.get('suggested_title'),
                    suggested_position=item.get('suggested_position')
                ))

            return decisions

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            logger.debug(f"Response content: {response}")
            return []
