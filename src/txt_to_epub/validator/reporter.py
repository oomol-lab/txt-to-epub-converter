"""Validation report generation module."""

from typing import Dict, Any, Optional
from .messages import get_messages
from .analyzer import compare_content, analyze_content_changes


def generate_validation_report(
    original_stats: Dict[str, int],
    converted_stats: Dict[str, int],
    language: Optional[str] = None
) -> str:
    """
    Generate detailed validation report (Markdown format).

    :param original_stats: Original content statistics
    :param converted_stats: Converted content statistics
    :param language: Language for report ('chinese' or 'english')
    :return: Markdown format validation report text
    """
    is_valid, result = compare_content(original_stats, converted_stats, language)
    analysis = analyze_content_changes(original_stats, converted_stats, language)
    messages = get_messages(language)

    report = []
    report.append(f"# {messages['report_title']}")
    report.append("")

    # Use table to show before/after comparison
    report.append(f"## {messages['comparison_before_after']}")
    report.append("")
    headers = messages['table_headers']
    report.append(f"| {headers[0]} | {headers[1]} | {headers[2]} | {headers[3]} | {headers[4]} |")
    report.append("|------|--------|--------|------|--------|")

    diffs = result['differences']
    rates = result['loss_rates']

    def format_diff(diff: int) -> str:
        if diff > 0:
            return f"+{diff:,}"
        elif diff < 0:
            return f"{diff:,}"
        else:
            return "0"

    def format_loss_rate(rate: float) -> str:
        if rate > 0:
            return f"{rate:.2f}%"
        else:
            return "0%"

    # Add table rows
    report.append(f"| {messages['chinese_chars']} | {result['original_stats']['chinese_chars']:,} | {result['converted_stats']['chinese_chars']:,} | {format_diff(diffs['chinese_chars'])} | {format_loss_rate(rates['chinese_chars'])} |")
    report.append(f"| {messages['english_chars']} | {result['original_stats']['english_chars']:,} | {result['converted_stats']['english_chars']:,} | {format_diff(diffs['english_chars'])} | {format_loss_rate(rates['english_chars'])} |")
    report.append(f"| {messages['punctuation']} | {result['original_stats']['punctuation']:,} | {result['converted_stats']['punctuation']:,} | {format_diff(diffs['punctuation'])} | - |")
    report.append(f"| {messages['total_chars_label']} | **{result['original_stats']['total_chars']:,}** | **{result['converted_stats']['total_chars']:,}** | **{format_diff(diffs['total_chars'])}** | **{format_loss_rate(rates['total_chars'])}** |")
    report.append("")

    # Validation result
    if is_valid:
        report.append(f"## {messages['validation_result_pass']}")
        report.append("")
        report.append(messages['content_intact'])
        report.append("")
        report.append(f"> {messages['note_title']}: {messages['note_content']}")
        for reason in messages['note_reasons']:
            report.append(f"> {reason}")
    else:
        report.append(f"## {messages['validation_result_fail']}")
        report.append("")
        report.append(f"{messages['check_suggestions']}")
        report.append("")
        if rates['chinese_chars'] > 1.0:
            report.append(f"- ⚠️ {messages['warnings']['chinese_loss']}")
        if rates['english_chars'] > 2.0:
            report.append(f"- ⚠️ {messages['warnings']['english_loss']}")
        if rates['total_chars'] > 1.0:
            report.append(f"- ⚠️ {messages['warnings']['total_loss']}")
        report.append("")
        report.append(f"### {messages['check_steps_title']}")
        report.append("")
        for step in messages['check_steps']:
            report.append(step)

    report.append("")

    # Difference analysis details table
    report.append(f"## {messages['analysis_title']}")
    report.append("")

    if analysis:
        analysis_headers = messages['table_analysis_headers']
        report.append(f"| {analysis_headers[0]} | {analysis_headers[1]} | {analysis_headers[2]} |")
        report.append("|------|----------|----------|")

        if 'chinese_reason' in analysis:
            report.append(f"| {messages['chinese_chars']} | {analysis['chinese_reason']} | {analysis['chinese_concern']} |")

        if 'english_reason' in analysis:
            report.append(f"| {messages['english_chars']} | {analysis['english_reason']} | {analysis['english_concern']} |")

        if 'punctuation_reason' in analysis:
            report.append(f"| {messages['punctuation']} | {analysis['punctuation_reason']} | {analysis['punctuation_concern']} |")

        if 'overall_reason' in analysis:
            report.append(f"| {messages['overall_assessment']} | **{analysis['overall_reason']}** | **{analysis['overall_concern']}** |")

    report.append("")

    return "\n".join(report)
