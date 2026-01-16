import re
import logging
from typing import Dict, List, Tuple, Any
from .data_structures import Volume, Chapter, Section

# Configure logging
logger = logging.getLogger(__name__)


class WordCountValidator:
    """Word count validator for comparing text quantity before and after conversion"""
    
    def __init__(self):
        self.original_stats = {}
        self.converted_stats = {}
        self.detected_language = None
    
    def clean_text_for_counting(self, text: str) -> str:
        """
        Clean text for counting, remove extra whitespace and punctuation
        
        :param text: Original text
        :return: Cleaned text
        """
        if not text:
            return ""
        
        # Remove extra whitespace (spaces, tabs, newlines, etc.)
        cleaned = re.sub(r'\s+', '', text)
        
        # Remove common punctuation and special characters (but keep Chinese characters)
        # Only remove obvious separators, keep potentially meaningful punctuation
        cleaned = re.sub(r'[　\u3000]+', '', cleaned)  # Remove Chinese spaces
        
        return cleaned
    
    def detect_primary_language(self, text: str) -> str:
        """
        Detect the primary language of the text based on character composition
        
        :param text: Text content to analyze
        :return: 'chinese' for primarily Chinese text, 'english' for primarily English text
        """
        if not text:
            return 'english'
        
        cleaned_text = self.clean_text_for_counting(text)
        
        # Count Chinese characters
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf]', cleaned_text))
        # Count English letters
        english_chars = len(re.findall(r'[a-zA-Z]', cleaned_text))
        
        total_meaningful_chars = chinese_chars + english_chars
        
        if total_meaningful_chars == 0:
            return 'english'
        
        # If Chinese characters make up more than 30% of meaningful characters, consider it Chinese
        chinese_ratio = chinese_chars / total_meaningful_chars
        
        return 'chinese' if chinese_ratio > 0.3 else 'english'
    
    def get_messages(self, language: str = None) -> Dict[str, Dict[str, str]]:
        """
        Get localized messages based on detected language
        
        :param language: Override language detection, 'chinese' or 'english'
        :return: Dictionary of localized messages
        """
        lang = language or self.detected_language or 'english'
        
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
    
    def count_characters(self, text: str) -> Dict[str, int]:
        """
        Count characters in text
        
        :param text: Text content
        :return: Character statistics dictionary
        """
        cleaned_text = self.clean_text_for_counting(text)
        
        # Count Chinese characters (including Chinese punctuation)
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf]', cleaned_text))
        
        # Count English letters and numbers
        english_chars = len(re.findall(r'[a-zA-Z0-9]', cleaned_text))
        
        # Count punctuation - use Unicode ranges to avoid encoding issues
        chinese_punctuation = len(re.findall(r'[\u3000-\u303f\uff00-\uffef]', cleaned_text))  # Chinese punctuation
        english_punctuation = len(re.findall(r'[.,!?;:()\[\]<>"\'\\-]', cleaned_text))  # English punctuation
        punctuation = chinese_punctuation + english_punctuation
        
        # Total characters (excluding whitespace)
        total_chars = len(cleaned_text)
        
        # Original text total length (including whitespace)
        original_length = len(text) if text else 0
        
        return {
            'chinese_chars': chinese_chars,
            'english_chars': english_chars,
            'punctuation': punctuation,
            'total_chars': total_chars,
            'original_length': original_length
        }
    
    def analyze_original_content(self, content: str) -> Dict[str, int]:
        """
        Analyze text statistics of original txt file
        
        :param content: Original text content
        :return: Statistics result dictionary
        """
        # Detect primary language
        self.detected_language = self.detect_primary_language(content)
        messages = self.get_messages()
        
        stats = self.count_characters(content)
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
        Extract all text content from converted volume structure
        
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
        Analyze text statistics of converted epub content
        
        :param volumes: Converted volume structure
        :return: Statistics result dictionary
        """
        extracted_content = self.extract_content_from_volumes(volumes)
        stats = self.count_characters(extracted_content)
        self.converted_stats = stats
        
        messages = self.get_messages()
        
        logger.info(f"{messages['converted_stats_title']}")
        logger.info(f"  - {messages['chinese_chars']}: {stats['chinese_chars']}")
        logger.info(f"  - {messages['english_chars']}: {stats['english_chars']}")
        logger.info(f"  - {messages['punctuation']}: {stats['punctuation']}")
        logger.info(f"  - {messages['total_chars']}: {stats['total_chars']}")
        logger.info(f"  - {messages['original_length']}: {stats['original_length']}")
        
        return stats
    
    def analyze_content_changes(self) -> Dict[str, str]:
        """
        Analyze reasons for content changes and provide detailed explanations
        
        :return: Dictionary containing change reason analysis
        """
        if not self.original_stats or not self.converted_stats:
            messages = self.get_messages()
            return {"error": messages['analysis_messages']['missing_data']}
        
        messages = self.get_messages()
        analysis_msgs = messages['analysis_messages']
        
        analysis = {}
        diffs = {
            'chinese_chars': self.converted_stats['chinese_chars'] - self.original_stats['chinese_chars'],
            'english_chars': self.converted_stats['english_chars'] - self.original_stats['english_chars'],
            'punctuation': self.converted_stats['punctuation'] - self.original_stats['punctuation'],
            'total_chars': self.converted_stats['total_chars'] - self.original_stats['total_chars']
        }
        
        # Analyze Chinese character changes
        if abs(diffs['chinese_chars']) <= self.original_stats['chinese_chars'] * 0.005:  # Within 0.5%
            analysis['chinese_reason'] = analysis_msgs['chinese_stable']
            analysis['chinese_concern'] = analysis_msgs['concern_levels']['none']
        elif diffs['chinese_chars'] > 0:
            analysis['chinese_reason'] = analysis_msgs['chinese_increase']
            analysis['chinese_concern'] = analysis_msgs['concern_levels']['minimal']
        elif diffs['chinese_chars'] < 0:
            loss_rate = abs(diffs['chinese_chars']) / self.original_stats['chinese_chars'] * 100
            if loss_rate <= 1.0:
                analysis['chinese_reason'] = analysis_msgs['chinese_minor_decrease']
                analysis['chinese_concern'] = analysis_msgs['concern_levels']['minor']
            else:
                analysis['chinese_reason'] = analysis_msgs['chinese_major_decrease']
                analysis['chinese_concern'] = analysis_msgs['concern_levels']['high']
        
        # Analyze English character changes
        if abs(diffs['english_chars']) <= max(self.original_stats['english_chars'] * 0.02, 10):  # Within 2% or 10 characters
            analysis['english_reason'] = analysis_msgs['english_stable']
            analysis['english_concern'] = analysis_msgs['concern_levels']['none']
        elif diffs['english_chars'] > 0:
            analysis['english_reason'] = analysis_msgs['english_increase']
            analysis['english_concern'] = analysis_msgs['concern_levels']['minimal']
        else:
            loss_rate = abs(diffs['english_chars']) / max(self.original_stats['english_chars'], 1) * 100
            if loss_rate <= 5.0:
                analysis['english_reason'] = analysis_msgs['english_minor_decrease']
                analysis['english_concern'] = analysis_msgs['concern_levels']['minor']
            else:
                analysis['english_reason'] = analysis_msgs['english_major_decrease']
                analysis['english_concern'] = analysis_msgs['concern_levels']['high']
        
        # Analyze punctuation changes
        if abs(diffs['punctuation']) <= max(self.original_stats['punctuation'] * 0.1, 5):  # Within 10% or 5 characters
            analysis['punctuation_reason'] = analysis_msgs['punctuation_stable']
            analysis['punctuation_concern'] = analysis_msgs['concern_levels']['none']
        elif diffs['punctuation'] > 0:
            analysis['punctuation_reason'] = analysis_msgs['punctuation_increase']
            analysis['punctuation_concern'] = analysis_msgs['concern_levels']['minimal']
        else:
            analysis['punctuation_reason'] = analysis_msgs['punctuation_decrease']
            analysis['punctuation_concern'] = analysis_msgs['concern_levels']['minor']
        
        # Analyze overall changes
        total_loss_rate = (self.original_stats['total_chars'] - self.converted_stats['total_chars']) / self.original_stats['total_chars'] * 100
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
    
    def compare_content(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Compare differences between original and converted content
        
        :return: (validation_passed, comparison_result_details)
        """
        if not self.original_stats or not self.converted_stats:
            return False, {"error": "Missing statistical data, please analyze original and converted content first"}
        
        # Calculate differences
        chinese_diff = self.converted_stats['chinese_chars'] - self.original_stats['chinese_chars']
        english_diff = self.converted_stats['english_chars'] - self.original_stats['english_chars']
        punctuation_diff = self.converted_stats['punctuation'] - self.original_stats['punctuation']
        total_diff = self.converted_stats['total_chars'] - self.original_stats['total_chars']
        
        # Calculate loss rates
        def calc_loss_rate(original, converted):
            if original == 0:
                return 0.0
            return (original - converted) / original * 100
        
        chinese_loss_rate = calc_loss_rate(self.original_stats['chinese_chars'], self.converted_stats['chinese_chars'])
        english_loss_rate = calc_loss_rate(self.original_stats['english_chars'], self.converted_stats['english_chars'])
        total_loss_rate = calc_loss_rate(self.original_stats['total_chars'], self.converted_stats['total_chars'])
        
        # Validation criteria: allow minor character differences (considering parsing and formatting effects)
        # Chinese character loss rate <= 1%, English character loss rate <= 2%, total loss rate <= 1%
        is_valid = (
            chinese_loss_rate <= 1.0 and 
            english_loss_rate <= 2.0 and 
            total_loss_rate <= 1.0 and
            chinese_diff >= -self.original_stats['chinese_chars'] * 0.01  # Chinese character loss <= 1%
        )
        
        result = {
            "is_valid": is_valid,
            "original_stats": self.original_stats.copy(),
            "converted_stats": self.converted_stats.copy(),
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
        
        # Log validation results
        messages = self.get_messages()
        
        if is_valid:
            logger.info(messages['validation_passed'])
        else:
            logger.warning(messages['validation_failed'])
            if chinese_loss_rate > 1.0:
                logger.warning(f"{messages['chinese_loss_high']}: {chinese_loss_rate:.2f}%")
            if english_loss_rate > 2.0:
                logger.warning(f"{messages['english_loss_high']}: {english_loss_rate:.2f}%")
            if total_loss_rate > 1.0:
                logger.warning(f"{messages['total_loss_high']}: {total_loss_rate:.2f}%")
        
        logger.info(f"{messages['char_diff_details']}")
        logger.info(f"  - {messages['chinese_diff']}: {chinese_diff} ({messages['loss_rate']}: {chinese_loss_rate:.2f}%)")
        logger.info(f"  - {messages['english_diff']}: {english_diff} ({messages['loss_rate']}: {english_loss_rate:.2f}%)")
        logger.info(f"  - {messages['punctuation_diff']}: {punctuation_diff}")
        logger.info(f"  - {messages['total_diff']}: {total_diff} ({messages['loss_rate']}: {total_loss_rate:.2f}%)")
        
        return is_valid, result
    
    def generate_validation_report(self) -> str:
        """
        Generate detailed validation report (Markdown format)
        
        :return: Markdown format validation report text
        """
        is_valid, result = self.compare_content()
        analysis = self.analyze_content_changes()
        messages = self.get_messages()
        
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
        
        def format_diff(diff):
            if diff > 0:
                return f"+{diff:,}"
            elif diff < 0:
                return f"{diff:,}"
            else:
                return "0"
        
        def format_loss_rate(rate):
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


def validate_conversion_integrity(original_content: str, volumes: List[Volume]) -> Tuple[bool, str]:
    """
    Validate content integrity for txt to epub conversion
    
    :param original_content: Original txt file content
    :param volumes: Converted volume structure
    :return: (validation_passed, validation_report)
    """
    validator = WordCountValidator()
    
    # Analyze original content
    validator.analyze_original_content(original_content)
    
    # Analyze converted content
    validator.analyze_converted_content(volumes)
    
    # Generate validation report
    report = validator.generate_validation_report()
    
    # Get validation result
    is_valid, _ = validator.compare_content()
    
    return is_valid, report
