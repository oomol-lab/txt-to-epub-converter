"""Content change analysis module for validation."""

from typing import Dict, Tuple, Any, Optional
from .messages import get_messages


def analyze_content_changes(
    original_stats: Dict[str, int],
    converted_stats: Dict[str, int],
    language: Optional[str] = None
) -> Dict[str, str]:
    """
    Analyze reasons for content changes and provide detailed explanations.

    :param original_stats: Original content statistics
    :param converted_stats: Converted content statistics
    :param language: Language for messages ('chinese' or 'english')
    :return: Dictionary containing change reason analysis
    """
    if not original_stats or not converted_stats:
        messages = get_messages(language)
        return {"error": messages['analysis_messages']['missing_data']}

    messages = get_messages(language)
    analysis_msgs = messages['analysis_messages']

    analysis = {}
    diffs = {
        'chinese_chars': converted_stats['chinese_chars'] - original_stats['chinese_chars'],
        'english_chars': converted_stats['english_chars'] - original_stats['english_chars'],
        'punctuation': converted_stats['punctuation'] - original_stats['punctuation'],
        'total_chars': converted_stats['total_chars'] - original_stats['total_chars']
    }

    # Analyze Chinese character changes
    if abs(diffs['chinese_chars']) <= original_stats['chinese_chars'] * 0.005:  # Within 0.5%
        analysis['chinese_reason'] = analysis_msgs['chinese_stable']
        analysis['chinese_concern'] = analysis_msgs['concern_levels']['none']
    elif diffs['chinese_chars'] > 0:
        analysis['chinese_reason'] = analysis_msgs['chinese_increase']
        analysis['chinese_concern'] = analysis_msgs['concern_levels']['minimal']
    elif diffs['chinese_chars'] < 0:
        loss_rate = abs(diffs['chinese_chars']) / original_stats['chinese_chars'] * 100
        if loss_rate <= 1.0:
            analysis['chinese_reason'] = analysis_msgs['chinese_minor_decrease']
            analysis['chinese_concern'] = analysis_msgs['concern_levels']['minor']
        else:
            analysis['chinese_reason'] = analysis_msgs['chinese_major_decrease']
            analysis['chinese_concern'] = analysis_msgs['concern_levels']['high']

    # Analyze English character changes
    if abs(diffs['english_chars']) <= max(original_stats['english_chars'] * 0.02, 10):  # Within 2% or 10 characters
        analysis['english_reason'] = analysis_msgs['english_stable']
        analysis['english_concern'] = analysis_msgs['concern_levels']['none']
    elif diffs['english_chars'] > 0:
        analysis['english_reason'] = analysis_msgs['english_increase']
        analysis['english_concern'] = analysis_msgs['concern_levels']['minimal']
    else:
        loss_rate = abs(diffs['english_chars']) / max(original_stats['english_chars'], 1) * 100
        if loss_rate <= 5.0:
            analysis['english_reason'] = analysis_msgs['english_minor_decrease']
            analysis['english_concern'] = analysis_msgs['concern_levels']['minor']
        else:
            analysis['english_reason'] = analysis_msgs['english_major_decrease']
            analysis['english_concern'] = analysis_msgs['concern_levels']['high']

    # Analyze punctuation changes
    if abs(diffs['punctuation']) <= max(original_stats['punctuation'] * 0.1, 5):  # Within 10% or 5 characters
        analysis['punctuation_reason'] = analysis_msgs['punctuation_stable']
        analysis['punctuation_concern'] = analysis_msgs['concern_levels']['none']
    elif diffs['punctuation'] > 0:
        analysis['punctuation_reason'] = analysis_msgs['punctuation_increase']
        analysis['punctuation_concern'] = analysis_msgs['concern_levels']['minimal']
    else:
        analysis['punctuation_reason'] = analysis_msgs['punctuation_decrease']
        analysis['punctuation_concern'] = analysis_msgs['concern_levels']['minor']

    # Analyze overall changes
    total_loss_rate = (original_stats['total_chars'] - converted_stats['total_chars']) / original_stats['total_chars'] * 100
    if total_loss_rate <= 0.5:
        analysis['overall_reason'] = analysis_msgs['overall_excellent']
        analysis['overall_concern'] = analysis_msgs['concern_levels']['none']
    elif total_loss_rate <= 1.0:
        analysis['overall_reason'] = analysis_msgs['overall_good']
        analysis['overall_concern'] = analysis_msgs['concern_levels']['minor']
    elif total_loss_rate <= 2.0:
        analysis['overall_reason'] = analysis_msgs['overall_moderate']
        analysis['overall_concern'] = analysis_msgs['concern_levels']['moderate']
    else:
        analysis['overall_reason'] = analysis_msgs['overall_poor']
        analysis['overall_concern'] = analysis_msgs['concern_levels']['critical']

    return analysis


def compare_content(
    original_stats: Dict[str, int],
    converted_stats: Dict[str, int],
    language: Optional[str] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Compare differences between original and converted content.

    :param original_stats: Original content statistics
    :param converted_stats: Converted content statistics
    :param language: Language for messages ('chinese' or 'english')
    :return: (validation_passed, comparison_result_details)
    """
    if not original_stats or not converted_stats:
        return False, {"error": "Missing statistical data, please analyze original and converted content first"}

    # Calculate differences
    chinese_diff = converted_stats['chinese_chars'] - original_stats['chinese_chars']
    english_diff = converted_stats['english_chars'] - original_stats['english_chars']
    punctuation_diff = converted_stats['punctuation'] - original_stats['punctuation']
    total_diff = converted_stats['total_chars'] - original_stats['total_chars']

    # Calculate loss rates
    def calc_loss_rate(original: int, converted: int) -> float:
        if original == 0:
            return 0.0
        return (original - converted) / original * 100

    chinese_loss_rate = calc_loss_rate(original_stats['chinese_chars'], converted_stats['chinese_chars'])
    english_loss_rate = calc_loss_rate(original_stats['english_chars'], converted_stats['english_chars'])
    total_loss_rate = calc_loss_rate(original_stats['total_chars'], converted_stats['total_chars'])

    # Validation criteria: allow minor character differences (considering parsing and formatting effects)
    # Chinese character loss rate <= 1%, English character loss rate <= 2%, total loss rate <= 1%
    is_valid = (
        chinese_loss_rate <= 1.0 and
        english_loss_rate <= 2.0 and
        total_loss_rate <= 1.0 and
        chinese_diff >= -original_stats['chinese_chars'] * 0.01  # Chinese character loss <= 1%
    )

    result = {
        "is_valid": is_valid,
        "original_stats": original_stats.copy(),
        "converted_stats": converted_stats.copy(),
        "differences": {
            "chinese_chars": chinese_diff,
            "english_chars": english_diff,
            "punctuation": punctuation_diff,
            "total_chars": total_diff
        },
        "loss_rates": {
            "chinese_chars": chinese_loss_rate,
            "english_chars": english_loss_rate,
            "total_chars": total_loss_rate
        }
    }

    return is_valid, result
