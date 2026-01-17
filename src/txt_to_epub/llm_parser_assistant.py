"""
LLM-assisted parser for ambiguous chapter detection
LLM-Assisted Parser - Implemented using OpenAI SDK

This module provides backward compatibility with the old API.
The implementation has been refactored into multiple modules under the llm package.

Supported models:
- GPT-4 series (recommended): gpt-4-turbo, gpt-4
- GPT-3.5 series (economical): gpt-3.5-turbo
- Other models compatible with OpenAI API
"""
import logging
from typing import List, Dict, Any, Optional

# Import from new modular structure
from .llm.data_structures import ChapterCandidate, LLMDecision
from .llm.client import LLMClient
from .llm.chapter_assistant import ChapterAssistant
from .llm.title_generator import TitleGenerator
from .llm.toc_assistant import TOCAssistant
from .llm.format_identifier import FormatIdentifier
from .llm.disambiguation import Disambiguator
from .llm.structure_inferrer import StructureInferrer

logger = logging.getLogger(__name__)

# Re-export data structures for backward compatibility
__all__ = ['ChapterCandidate', 'LLMDecision', 'LLMParserAssistant', 'RuleBasedParserWithConfidence', 'HybridParser']


class LLMParserAssistant:
    """LLM-Assisted Parser - OpenAI Implementation (Backward Compatibility Wrapper)"""

    def __init__(self, api_key: str = None, model: str = "gpt-4-turbo",
                 base_url: str = None, organization: str = None):
        """
        Initialize LLM assistant

        :param api_key: OpenAI API key (if None, will read from environment variables)
        :param model: Model to use
        :param base_url: API base URL (for compatibility with other services)
        :param organization: OpenAI organization ID (optional)
        """
        # Initialize client
        self.client = LLMClient(api_key, model, base_url, organization)

        # Initialize assistants
        self.chapter_assistant = ChapterAssistant(self.client)
        self.title_generator = TitleGenerator(self.client)
        self.toc_assistant = TOCAssistant(self.client)
        self.format_identifier = FormatIdentifier(self.client)
        self.disambiguator = Disambiguator(self.client)
        self.structure_inferrer = StructureInferrer(self.client)

        logger.info(f"LLM assistant initialized: model={model}")

    def analyze_chapter_candidates(
        self,
        candidates: List[ChapterCandidate],
        full_content: str,
        existing_chapters: List[Dict],
        doc_context: Dict = None
    ) -> List[LLMDecision]:
        """Analyze chapter candidates to determine if they are real chapters"""
        return self.chapter_assistant.analyze_chapter_candidates(
            candidates, full_content, existing_chapters, doc_context
        )

    def infer_chapter_structure(
        self,
        content: str,
        max_length: int = 10000,
        language: str = 'chinese'
    ) -> List[Dict]:
        """Infer chapter structure for text without obvious chapter markers"""
        return self.structure_inferrer.infer_chapter_structure(content, max_length, language)

    def disambiguate_reference(
        self,
        text_snippet: str,
        candidate: str,
        context: Dict
    ) -> Dict:
        """Disambiguate: determine if chapter title or text reference"""
        return self.disambiguator.disambiguate_reference(text_snippet, candidate, context)

    def identify_table_of_contents(
        self,
        content_sample: str,
        language: str = 'chinese'
    ) -> Dict:
        """Identify if text contains table of contents page"""
        return self.toc_assistant.identify_table_of_contents(content_sample, language)

    def identify_special_format(
        self,
        content_sample: str,
        observed_patterns: List[str]
    ) -> Dict:
        """Identify chapter patterns for books with special formats"""
        return self.format_identifier.identify_special_format(content_sample, observed_patterns)

    def generate_chapter_title(
        self,
        chapter_number: str,
        chapter_content: str,
        language: str = 'chinese',
        max_content_length: int = 400
    ) -> Dict:
        """Use LLM to generate appropriate chapter title based on chapter content"""
        return self.title_generator.generate_chapter_title(
            chapter_number, chapter_content, language, max_content_length
        )

    def generate_chapter_titles_batch(
        self,
        chapters_info: List[Dict[str, str]],
        language: str = 'chinese',
        max_content_length: int = 400
    ) -> List[Dict]:
        """Batch generate chapter titles"""
        return self.title_generator.generate_chapter_titles_batch(
            chapters_info, language, max_content_length
        )

    def get_stats(self) -> Dict:
        """Get usage statistics"""
        return self.client.get_stats()

    def reset_stats(self):
        """Reset statistics"""
        self.client.reset_stats()


# Import hybrid parser components
from .data_structures import Volume, Chapter


class RuleBasedParserWithConfidence:
    """Rule-based parser with confidence scoring"""

    def __init__(self, config=None):
        """
        Initialize rule parser

        :param config: ParserConfig instance
        """
        from .parser_config import ParserConfig, DEFAULT_CONFIG
        self.config = config or DEFAULT_CONFIG

    def parse_with_confidence(self, content: str, skip_toc_removal: bool = False, context=None, resume_state=None) -> Dict:
        """
        Parse content and return confidence

        :param content: Text content
        :param skip_toc_removal: If True, skip TOC removal
        :param context: Context for progress reporting
        :param resume_state: Resume state for checkpoint resume
        :return: Dictionary with volumes, chapters, uncertain_regions, overall_confidence
        """
        from .parser.core import parse_hierarchical_content, detect_language
        from .parser.validator import estimate_chapter_confidence

        # Use existing parser
        volumes = parse_hierarchical_content(
            content, self.config, llm_assistant=None,
            skip_toc_removal=skip_toc_removal, context=context, resume_state=resume_state
        )

        # Detect language
        language = detect_language(content)

        # Calculate confidence for each chapter
        chapters_with_confidence = []
        uncertain_regions = []

        for volume in volumes:
            for chapter in volume.chapters:
                # Calculate confidence
                confidence = estimate_chapter_confidence(chapter, content, language)

                chapter_info = {
                    'chapter': chapter,
                    'confidence': confidence,
                    'volume': volume,
                    'length': len(chapter.content) + sum(len(s.content) for s in chapter.sections),
                    'pattern_type': 'standard'
                }

                chapters_with_confidence.append(chapter_info)

                if confidence < 0.7:
                    uncertain_regions.append(chapter_info)

        if chapters_with_confidence:
            overall_confidence = sum(c['confidence'] for c in chapters_with_confidence) / len(chapters_with_confidence)
        else:
            overall_confidence = 0.0

        return {
            'volumes': volumes,
            'chapters': chapters_with_confidence,
            'uncertain_regions': uncertain_regions,
            'overall_confidence': overall_confidence
        }


class HybridParser:
    """Hybrid parser: Rule-based + LLM"""

    def __init__(
        self,
        llm_api_key: str = None,
        llm_base_url: str = None,
        llm_model: str = "deepseek-v3.2",
        config = None
    ):
        """
        Initialize hybrid parser

        :param llm_api_key: LLM API key
        :param llm_base_url: LLM API base URL
        :param llm_model: Model to use
        :param config: Parser configuration
        """
        from .parser_config import ParserConfig, DEFAULT_CONFIG

        self.config = config or DEFAULT_CONFIG
        self.rule_parser = RuleBasedParserWithConfidence(self.config)

        # If LLM assistance is enabled, initialize LLM assistant
        self.llm_assistant = None
        if self.config.enable_llm_assistance or llm_api_key:
            self.llm_assistant = LLMParserAssistant(
                api_key=llm_api_key or self.config.llm_api_key,
                base_url=llm_base_url or self.config.llm_base_url,
                model=llm_model or self.config.llm_model
            )

    def parse(self, content: str, skip_toc_removal: bool = False, context=None, resume_state=None):
        """
        Hybrid parsing workflow

        :param content: Text content
        :param skip_toc_removal: If True, skip TOC removal
        :param context: Context object for progress reporting
        :param resume_state: Resume state for checkpoint resume
        :return: List of volumes
        """
        from .parser.core import detect_language

        # Stage 1: Rule-based parsing + confidence scoring
        logger.info("Stage 1: Rule-based parsing...")

        rule_result = self.rule_parser.parse_with_confidence(
            content, skip_toc_removal=skip_toc_removal, context=context, resume_state=resume_state
        )
        volumes = rule_result['volumes']
        confidence = rule_result['overall_confidence']
        threshold = self.config.llm_confidence_threshold
        logger.debug(f"Rule parsing confidence: {confidence:.2f}, threshold: {threshold:.2f}")

        # If overall confidence is high, return directly
        if confidence >= threshold:
            logger.info(f"High confidence ({confidence:.2f} >= {threshold:.2f}), skipping chapter-level LLM assistance")
            logger.info(f"Parsing complete: {len(volumes)} volumes")
            return volumes

        logger.info(f"Confidence < threshold, LLM assistance needed for chapter identification")

        # Stage 2: Identify regions requiring LLM
        uncertain_regions = rule_result.get('uncertain_regions', [])
        chapters = rule_result.get('chapters', [])

        logger.debug(f"Rule parsing identified {len(chapters)} chapters")

        if uncertain_regions and self.llm_assistant:
            logger.info(f"Stage 2: LLM assisting with {len(uncertain_regions)} uncertain regions...")

            # Convert to candidate format
            candidates = self._convert_to_candidates(uncertain_regions, content)

            # LLM analysis
            llm_decisions = self.llm_assistant.analyze_chapter_candidates(
                candidates,
                content,
                rule_result['chapters'],
                {'language': detect_language(content), 'doc_type': 'Novel'}
            )

            logger.debug(f"LLM decision results: processed {len(llm_decisions)} candidates")

            # Stage 3: Merge results
            logger.info("Stage 3: Merging results...")
            final_volumes = self._merge_results(
                volumes,
                llm_decisions,
                candidates
            )

            # Output statistics
            stats = self.llm_assistant.get_stats()
            logger.info(f"LLM statistics: {stats['total_calls']} calls, ${stats['total_cost']:.4f} cost")

            return final_volumes

        # No LLM needed or client not provided
        return volumes

    def _convert_to_candidates(
        self,
        uncertain_regions: List[Dict],
        content: str
    ) -> List[ChapterCandidate]:
        """Convert to candidate format"""
        candidates = []

        for region in uncertain_regions:
            chapter = region['chapter']
            confidence = region['confidence']

            # Find position in content
            position = content.find(chapter.title)
            if position == -1:
                continue

            # Extract context
            context_size = 200
            context_before = content[max(0, position-context_size):position]
            context_after = content[position+len(chapter.title):position+len(chapter.title)+context_size]

            # Calculate line number
            line_number = content[:position].count('\n') + 1

            # Determine issues
            issues = []
            if confidence < 0.5:
                issues.append("Extremely low confidence")
            elif confidence < 0.7:
                issues.append("Low confidence")

            if "第" in chapter.title and ("在" in context_before[-10:] or "如" in context_before[-10:]):
                issues.append("Suspected reference")

            candidates.append(ChapterCandidate(
                text=chapter.title,
                position=position,
                line_number=line_number,
                confidence=confidence,
                context_before=context_before,
                context_after=context_after,
                pattern_type=region.get('pattern_type', 'standard'),
                issues=issues
            ))

        return candidates

    def _merge_results(
        self,
        rule_volumes,
        llm_decisions: List[LLMDecision],
        candidates: List[ChapterCandidate]
    ):
        """Merge rule-based and LLM results"""

        # Create decision mapping
        decision_map = {
            candidates[i].text: llm_decisions[i]
            for i in range(min(len(candidates), len(llm_decisions)))
        }

        # Process each volume
        new_volumes = []
        for volume in rule_volumes:
            new_chapters = []

            for chapter in volume.chapters:
                decision = decision_map.get(chapter.title)

                if decision:
                    if decision.is_chapter:
                        # LLM confirmed as chapter
                        if decision.suggested_title:
                            # Use suggested title
                            new_chapter = Chapter(
                                title=decision.suggested_title,
                                content=chapter.content,
                                sections=chapter.sections
                            )
                            new_chapters.append(new_chapter)
                        else:
                            new_chapters.append(chapter)
                    else:
                        # LLM rejected, do not add
                        logger.info(f"LLM rejected chapter: {chapter.title}")
                else:
                    # No LLM decision, keep original result
                    new_chapters.append(chapter)

            if new_chapters:
                new_volumes.append(Volume(
                    title=volume.title,
                    chapters=new_chapters
                ))

        return new_volumes

    def get_stats(self) -> Dict:
        """Get LLM usage statistics"""
        if self.llm_assistant:
            return self.llm_assistant.get_stats()
        return {
            'total_calls': 0,
            'total_input_tokens': 0,
            'total_output_tokens': 0,
            'total_cost': 0.0
        }


# Example usage function
def example_usage():
    """Usage examples"""

    # Example 1: Basic usage
    print("=== Example 1: Basic Usage ===")
    assistant = LLMParserAssistant(
        api_key="your-api-key",
        model="gpt-3.5-turbo"
    )

    # Create test candidates
    candidates = [
        ChapterCandidate(
            text="Chapter 1 Beginning",
            position=0,
            line_number=1,
            confidence=0.95,
            context_before="",
            context_after="This is the content of chapter 1...",
            pattern_type="standard"
        )
    ]

    # Analyze chapter candidates
    decisions = assistant.analyze_chapter_candidates(
        candidates=candidates,
        full_content="Complete text...",
        existing_chapters=[],
        doc_context={'language': 'chinese'}
    )

    for i, decision in enumerate(decisions):
        print(f"Candidate {i+1}: {decision.is_chapter}, confidence: {decision.confidence}")

    # View statistics
    stats = assistant.get_stats()
    print(f"\nStatistics: {stats['total_calls']} calls, ${stats['total_cost']:.4f} cost")


if __name__ == "__main__":
    pass
