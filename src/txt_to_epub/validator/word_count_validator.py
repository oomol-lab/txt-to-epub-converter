"""Word count validator main class."""

import logging
from typing import Dict, List, Tuple, Any, Optional

from ..data_structures import Volume, Chapter, Section
from .counter import count_characters, detect_primary_language
from .messages import get_messages
from .analyzer import compare_content, analyze_content_changes
from .reporter import generate_validation_report

# Configure logging
logger = logging.getLogger(__name__)


class WordCountValidator:
    """Word count validator for comparing text quantity before and after conversion."""

    def __init__(self):
        self.original_stats: Dict[str, int] = {}
        self.converted_stats: Dict[str, int] = {}
        self.detected_language: Optional[str] = None

    def analyze_original_content(self, content: str) -> Dict[str, int]:
        """
        Analyze text statistics of original txt file.

        :param content: Original text content
        :return: Statistics result dictionary
        """
        # Detect primary language
        self.detected_language = detect_primary_language(content)
        messages = get_messages(self.detected_language)

        stats = count_characters(content)
        self.original_stats = stats

        logger.info(f"{messages['original_stats_title']}")
        logger.info(f"  - {messages['chinese_chars']}: {stats['chinese_chars']}")
        logger.info(f"  - {messages['english_chars']}: {stats['english_chars']}")
        logger.info(f"  - {messages['punctuation']}: {stats['punctuation']}")
        logger.info(f"  - {messages['total_chars']}: {stats['total_chars']}")
        logger.info(f"  - {messages['original_length']}: {stats['original_length']}")

        return stats

    def extract_content_from_volumes(self, volumes: List[Volume]) -> str:
        """
        Extract all text content from converted volume structure.

        :param volumes: Volume list
        :return: Extracted all text content
        """
        all_content = []

        for volume in volumes:
            # Add volume title (if exists)
            if volume.title:
                all_content.append(volume.title)

            for chapter in volume.chapters:
                # Add chapter title
                if chapter.title:
                    all_content.append(chapter.title)

                # Add chapter content
                if chapter.content:
                    all_content.append(chapter.content)

                # Add section content
                for section in chapter.sections:
                    if section.title:
                        all_content.append(section.title)
                    if section.content:
                        all_content.append(section.content)

        return '\n'.join(all_content)

    def analyze_converted_content(self, volumes: List[Volume]) -> Dict[str, int]:
        """
        Analyze text statistics of converted epub content.

        :param volumes: Converted volume structure
        :return: Statistics result dictionary
        """
        extracted_content = self.extract_content_from_volumes(volumes)
        stats = count_characters(extracted_content)
        self.converted_stats = stats

        messages = get_messages(self.detected_language)

        logger.info(f"{messages['converted_stats_title']}")
        logger.info(f"  - {messages['chinese_chars']}: {stats['chinese_chars']}")
        logger.info(f"  - {messages['english_chars']}: {stats['english_chars']}")
        logger.info(f"  - {messages['punctuation']}: {stats['punctuation']}")
        logger.info(f"  - {messages['total_chars']}: {stats['total_chars']}")
        logger.info(f"  - {messages['original_length']}: {stats['original_length']}")

        return stats

    def analyze_content_changes(self) -> Dict[str, str]:
        """
        Analyze reasons for content changes and provide detailed explanations.

        :return: Dictionary containing change reason analysis
        """
        return analyze_content_changes(
            self.original_stats,
            self.converted_stats,
            self.detected_language
        )

    def compare_content(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Compare differences between original and converted content.

        :return: (validation_passed, comparison_result_details)
        """
        is_valid, result = compare_content(
            self.original_stats,
            self.converted_stats,
            self.detected_language
        )

        # Log validation results
        messages = get_messages(self.detected_language)

        if is_valid:
            logger.info(messages['validation_passed'])
        else:
            logger.warning(messages['validation_failed'])
            rates = result['loss_rates']
            if rates['chinese_chars'] > 1.0:
                logger.warning(f"{messages['chinese_loss_high']}: {rates['chinese_chars']:.2f}%")
            if rates['english_chars'] > 2.0:
                logger.warning(f"{messages['english_loss_high']}: {rates['english_chars']:.2f}%")
            if rates['total_chars'] > 1.0:
                logger.warning(f"{messages['total_loss_high']}: {rates['total_chars']:.2f}%")

        diffs = result['differences']
        rates = result['loss_rates']
        logger.info(f"{messages['char_diff_details']}")
        logger.info(f"  - {messages['chinese_diff']}: {diffs['chinese_chars']} ({messages['loss_rate']}: {rates['chinese_chars']:.2f}%)")
        logger.info(f"  - {messages['english_diff']}: {diffs['english_chars']} ({messages['loss_rate']}: {rates['english_chars']:.2f}%)")
        logger.info(f"  - {messages['punctuation_diff']}: {diffs['punctuation']}")
        logger.info(f"  - {messages['total_diff']}: {diffs['total_chars']} ({messages['loss_rate']}: {rates['total_chars']:.2f}%)")

        return is_valid, result

    def generate_validation_report(self) -> str:
        """
        Generate detailed validation report (Markdown format).

        :return: Markdown format validation report text
        """
        return generate_validation_report(
            self.original_stats,
            self.converted_stats,
            self.detected_language
        )
