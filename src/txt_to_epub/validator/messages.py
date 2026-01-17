"""Multi-language message definitions for validation reports."""

from typing import Dict, Optional


def get_messages(language: Optional[str] = None) -> Dict[str, Dict[str, str]]:
    """
    Get localized messages based on language.

    :param language: Language code - 'chinese' or 'english'
    :return: Dictionary of localized messages
    """
    lang = language or 'english'

    messages = {
        'chinese': {
            'original_stats_title': '原文件统计:',
            'converted_stats_title': '转换后内容统计:',
            'chinese_chars': '中文字符',
            'english_chars': '英文字符',
            'punctuation': '标点符号',
            'total_chars': '总字符数(不含空白)',
            'original_length': '原始长度(含空白)',
            'validation_passed': '✅ 内容验证通过！转换后内容完整性良好',
            'validation_failed': '⚠️ 内容验证失败！可能存在内容丢失',
            'chinese_loss_high': '中文字符丢失率过高',
            'english_loss_high': '英文字符丢失率过高',
            'total_loss_high': '总体字符丢失率过高',
            'char_diff_details': '字符差异详情:',
            'chinese_diff': '中文字符差异',
            'english_diff': '英文字符差异',
            'punctuation_diff': '标点符号差异',
            'total_diff': '总字符差异',
            'loss_rate': '丢失率',
            'report_title': 'TXT转EPUB文字内容完整性验证报告',
            'comparison_before_after': '📊 转换前后对比',
            'validation_result_pass': '✅ 验证结果：通过',
            'validation_result_fail': '❌ 验证结果：失败',
            'content_intact': '转换完成后正文内容完整，没有明显的内容丢失。',
            'check_suggestions': '转换过程中可能存在内容丢失，建议检查：',
            'analysis_title': '🔍 字数变化原因分析',
            'table_headers': ['项目', '转换前', '转换后', '差异', '丢失率'],
            'table_analysis_headers': ['类型', '变化原因', '关注程度'],
            'note_title': '💡 **说明**',
            'note_content': '少量字符数差异是正常的，通常由以下因素造成：',
            'note_reasons': [
                '- 格式化和标准化处理',
                '- 空白字符的统一处理',
                '- 章节结构的重新组织',
                '- EPUB格式的技术要求'
            ],
            'check_steps_title': '🔧 建议的检查步骤',
            'check_steps': [
                '1. 检查原文件是否使用了特殊编码',
                '2. 确认文件结构是否符合解析规则',
                '3. 验证重要章节内容是否完整',
                '4. 检查是否有特殊格式导致解析错误'
            ],
            'warnings': {
                'chinese_loss': '中文字符丢失率超过1%，可能存在编码或解析问题',
                'english_loss': '英文字符丢失率超过2%，可能存在格式处理问题',
                'total_loss': '总体字符丢失率超过1%，建议检查解析逻辑'
            },
            'total_chars_label': '**总字符数**',
            'overall_assessment': '**总体评估**',
            'analysis_messages': {
                'missing_data': '缺少统计数据',
                'no_concern': '无需担心',
                'minor_concern': '基本无需担心',
                'need_attention': '需要关注',
                'chinese_stable': '中文字符数量基本保持一致，这是正常的。',
                'chinese_increase': '中文字符数量轻微增加，可能原因：1) 解析器自动添加了章节标题；2) 补充了缺失的标点符号；3) 格式化过程中的正常处理。',
                'chinese_minor_decrease': '中文字符数量轻微减少，可能原因：1) 移除了重复的空白字符；2) 统一了标点符号格式；3) 清理了无效字符。',
                'chinese_major_decrease': '中文字符数量明显减少，可能原因：1) 文件编码问题导致部分字符丢失；2) 解析过程中跳过了某些内容；3) 格式识别错误。',
                'english_stable': '英文字符数量变化很小，这是正常的。可能是格式化时空格处理的差异。',
                'english_increase': '英文字符数量增加，可能原因：1) 解析器添加了HTML标签中的英文；2) 自动生成的章节导航；3) 格式化标识符。',
                'english_minor_decrease': '英文字符数量减少，可能原因：1) 移除了多余的空格和换行符；2) 统一了字符编码；3) 清理了格式控制符。',
                'english_major_decrease': '英文字符数量明显减少，可能原因：1) 编码转换问题；2) 解析时遗漏了英文内容；3) 文件结构识别错误。',
                'punctuation_stable': '标点符号数量变化很小，这是正常的。',
                'punctuation_increase': '标点符号数量增加，可能原因：1) 统一标点符号格式（如半角转全角）；2) 添加了EPUB格式需要的标点；3) 补充了语法标点。',
                'punctuation_decrease': '标点符号数量减少，可能原因：1) 移除了重复或无意义的标点；2) 统一了标点符号格式；3) 清理了格式控制符。',
                'overall_excellent': '总体字符数量保持稳定，转换质量良好。',
                'overall_good': '总体字符数量略有减少，主要是格式清理和标准化的结果。',
                'overall_moderate': '总体字符数量有所减少，可能是移除了冗余的格式字符和空白。',
                'overall_poor': '总体字符数量明显减少，可能存在内容解析或转换问题。',
                'concern_levels': {
                    'none': '无需担心',
                    'minimal': '无需担心，这通常是正常的处理结果',
                    'minor': '基本无需担心，丢失率在可接受范围内',
                    'moderate': '需要适度关注，建议抽查重要章节内容',
                    'high': '需要关注，建议检查原文件编码和内容结构',
                    'critical': '需要重点关注，强烈建议检查转换结果'
                }
            }
        },
        'english': {
            'original_stats_title': 'Original file statistics:',
            'converted_stats_title': 'Converted content statistics:',
            'chinese_chars': 'Chinese characters',
            'english_chars': 'English characters',
            'punctuation': 'Punctuation',
            'total_chars': 'Total characters (no whitespace)',
            'original_length': 'Original length (with whitespace)',
            'validation_passed': '✅ Content validation passed! Converted content integrity is good',
            'validation_failed': '⚠️ Content validation failed! Possible content loss detected',
            'chinese_loss_high': 'Chinese character loss rate too high',
            'english_loss_high': 'English character loss rate too high',
            'total_loss_high': 'Overall character loss rate too high',
            'char_diff_details': 'Character difference details:',
            'chinese_diff': 'Chinese character difference',
            'english_diff': 'English character difference',
            'punctuation_diff': 'Punctuation difference',
            'total_diff': 'Total character difference',
            'loss_rate': 'loss rate',
            'report_title': 'TXT to EPUB Content Integrity Validation Report',
            'comparison_before_after': '📊 Before/After Comparison',
            'validation_result_pass': '✅ Validation Result: PASSED',
            'validation_result_fail': '❌ Validation Result: FAILED',
            'content_intact': 'Content conversion completed successfully with no significant content loss.',
            'check_suggestions': 'Possible content loss during conversion, recommend checking:',
            'analysis_title': '🔍 Character Count Change Analysis',
            'table_headers': ['Item', 'Before', 'After', 'Difference', 'Loss Rate'],
            'table_analysis_headers': ['Type', 'Reason for Change', 'Concern Level'],
            'note_title': '💡 **Note**',
            'note_content': 'Minor character count differences are normal and typically result from:',
            'note_reasons': [
                '- Formatting and standardization processing',
                '- Uniform whitespace handling',
                '- Chapter structure reorganization',
                '- EPUB format technical requirements'
            ],
            'check_steps_title': '🔧 Recommended Check Steps',
            'check_steps': [
                '1. Check if original file uses special encoding',
                '2. Verify file structure matches parsing rules',
                '3. Validate important chapter content integrity',
                '4. Check for special formats causing parsing errors'
            ],
            'warnings': {
                'chinese_loss': 'Chinese character loss rate exceeds 1%, possible encoding or parsing issues',
                'english_loss': 'English character loss rate exceeds 2%, possible format processing issues',
                'total_loss': 'Overall character loss rate exceeds 1%, recommend checking parsing logic'
            },
            'total_chars_label': '**Total Characters**',
            'overall_assessment': '**Overall Assessment**',
            'analysis_messages': {
                'missing_data': 'Missing statistical data',
                'no_concern': 'No concern',
                'minor_concern': 'Minimal concern',
                'need_attention': 'Needs attention',
                'chinese_stable': 'Chinese character count remains stable, which is normal.',
                'chinese_increase': 'Chinese character count slightly increased. Possible reasons: 1) Parser automatically added chapter titles; 2) Supplemented missing punctuation; 3) Normal formatting processing.',
                'chinese_minor_decrease': 'Chinese character count slightly decreased. Possible reasons: 1) Removed duplicate whitespace; 2) Unified punctuation format; 3) Cleaned invalid characters.',
                'chinese_major_decrease': 'Chinese character count significantly decreased. Possible reasons: 1) File encoding issues causing character loss; 2) Content skipped during parsing; 3) Format recognition errors.',
                'english_stable': 'English character count changed minimally, which is normal. Possibly due to whitespace handling differences during formatting.',
                'english_increase': 'English character count increased. Possible reasons: 1) Parser added English in HTML tags; 2) Auto-generated chapter navigation; 3) Format identifiers.',
                'english_minor_decrease': 'English character count decreased. Possible reasons: 1) Removed excess spaces and line breaks; 2) Unified character encoding; 3) Cleaned format control characters.',
                'english_major_decrease': 'English character count significantly decreased. Possible reasons: 1) Encoding conversion issues; 2) English content missed during parsing; 3) File structure recognition errors.',
                'punctuation_stable': 'Punctuation count changed minimally, which is normal.',
                'punctuation_increase': 'Punctuation count increased. Possible reasons: 1) Unified punctuation format (half-width to full-width); 2) Added EPUB format required punctuation; 3) Supplemented grammatical punctuation.',
                'punctuation_decrease': 'Punctuation count decreased. Possible reasons: 1) Removed duplicate or meaningless punctuation; 2) Unified punctuation format; 3) Cleaned format control characters.',
                'overall_excellent': 'Overall character count remains stable, conversion quality is excellent.',
                'overall_good': 'Overall character count slightly decreased, mainly due to format cleaning and standardization.',
                'overall_moderate': 'Overall character count somewhat decreased, possibly due to removal of redundant format characters and whitespace.',
                'overall_poor': 'Overall character count significantly decreased, possible content parsing or conversion issues.',
                'concern_levels': {
                    'none': 'No concern',
                    'minimal': 'No concern, this is usually a normal processing result',
                    'minor': 'Minimal concern, loss rate is within acceptable range',
                    'moderate': 'Moderate attention needed, recommend spot-checking important chapters',
                    'high': 'Needs attention, recommend checking original file encoding and content structure',
                    'critical': 'Critical attention needed, strongly recommend checking conversion results'
                }
            }
        }
    }

    return messages.get(lang, messages['english'])
