"""
Parser configuration module for customizing text parsing behavior.
"""
import os
import re
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Try to import yaml, make it optional
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    logger.warning("PyYAML not installed. YAML configuration support disabled.")


@dataclass
class ParserConfig:
    """
    配置类，用于自定义文本解析行为

    该类包含所有可配置的解析参数，用于控制章节识别、内容验证、
    LLM 辅助、目录检测等功能的行为。
    """

    # ========== 内容长度阈值配置 ==========

    min_chapter_length: int = 100
    """
    最小章节长度（字符数）

    默认值: 100

    说明: 用于验证章节是否过短。低于此长度的章节可能被视为误识别。
    仅在 enable_length_validation=True 时生效。

    调整建议:
    - 短章节书籍（如诗集）: 50-80
    - 正常小说: 100-200
    - 长章节书籍: 500+
    """

    min_section_length: int = 50
    """
    最小节长度（字符数）

    默认值: 50

    说明: 用于验证节（Section）是否过短。
    """

    # ========== 验证设置 ==========

    enable_chapter_validation: bool = True
    """
    是否启用章节标题验证

    默认值: True

    说明: 启用后，会过滤掉正文中对章节的引用（如"在第三章中"）。
    这可以显著提高章节识别准确性，但可能略微增加处理时间。

    推荐: 保持 True，除非遇到特殊格式导致误判。
    """

    enable_length_validation: bool = False
    """
    是否启用基于长度的章节验证

    默认值: False

    说明: 启用后，会合并过短的章节。适用于章节识别不准确的情况。

    注意: 可能会误合并真实的短章节。建议先尝试调整章节模式。
    """

    enable_fuzzy_matching: bool = False
    """
    是否启用模糊匹配（未来功能）

    默认值: False

    说明: 预留参数，当前未实现。
    """

    # Custom patterns (regex strings)
    custom_chapter_patterns: List[str] = field(default_factory=list)
    custom_volume_patterns: List[str] = field(default_factory=list)
    custom_section_patterns: List[str] = field(default_factory=list)

    # Keywords to ignore (patterns that should not be recognized as chapters)
    ignore_patterns: List[str] = field(default_factory=list)

    # Special keywords (additional chapter markers)
    special_chapter_keywords: List[str] = field(default_factory=list)

    # Language-specific settings
    language_hints: Dict[str, Any] = field(default_factory=dict)

    # Debug settings
    debug_mode: bool = False
    log_rejected_matches: bool = False

    # ========== LLM辅助配置 (简化版) ==========

    enable_llm_assistance: bool = False
    """是否启用LLM智能目录识别 (默认关闭)"""

    llm_api_key: Optional[str] = None
    """LLM API密钥"""

    llm_base_url: Optional[str] = None
    """LLM API地址 (可选，用于兼容百度千帆等服务)"""

    llm_model: str = "deepseek-v3.2"
    """使用的LLM模型"""

    llm_confidence_threshold: float = 0.7
    """
    LLM 置信度阈值

    范围: 0.0-1.0
    默认值: 0.7

    说明: 规则解析的整体置信度低于此值时，才会使用 LLM 辅助。
    - 较低的值（如 0.5）: 更频繁使用 LLM，成本更高但准确性更好
    - 较高的值（如 0.9）: 优先使用规则解析，降低成本

    推荐: 0.6-0.8 之间
    """

    llm_toc_detection_threshold: float = 0.7
    """
    LLM 判断存在目录的置信度阈值

    范围: 0.0-1.0
    默认值: 0.7

    说明: LLM 判断存在目录的置信度必须超过此值，才确认存在目录。

    调整建议:
    - 如果误判无目录为有目录：提高到 0.8-0.9
    - 如果漏检目录：降低到 0.5-0.6
    """

    llm_no_toc_threshold: float = 0.8
    """
    LLM 判断无目录的置信度阈值

    范围: 0.0-1.0
    默认值: 0.8

    说明: LLM 判断无目录的置信度超过此值时，直接跳过目录移除。
    这可以避免不必要的规则检测，提高效率。
    """

    # ========== 目录检测配置 ==========

    toc_detection_score_threshold: float = 30.0
    """
    目录检测的综合评分阈值

    范围: 0-100
    默认值: 30.0

    说明: 规则方法检测目录时，综合评分超过此阈值才判定为目录页。
    评分基于以下 6 个因子：
    1. 章节密度（章节数/1000字符）
    2. 绝对章节数（至少5个）
    3. 连续章节模式（3个以上连续）
    4. 短行占比（60%以上）
    5. 页码标记存在性
    6. 位置靠前加分

    调整建议:
    - 如果漏检目录：降低到 20-25
    - 如果误判正文为目录：提高到 40-50
    - 如果频繁误判：考虑启用 LLM 辅助（更准确）
    """

    toc_max_scan_lines: int = 300
    """
    目录检测的最大扫描行数

    默认值: 300

    说明: 防止误判过长区域为目录。目录通常在前 100-300 行内。

    调整建议:
    - 目录很长的书籍：提高到 500-800
    - 避免误判：降低到 150-200
    """

    # ========== HTML 输出配置 ==========

    enable_watermark: bool = True
    """
    是否在生成的 EPUB 页面中显示水印

    默认值: True

    说明: 水印会显示在卷页和章节页的底部。
    """

    watermark_text: str = "Powered by oomol.com, Please ensure that the copyright is in compliance"
    """
    水印文本内容

    默认值: "Powered by oomol.com, Please ensure that the copyright is in compliance"

    说明: 自定义水印文字。设置为空字符串可隐藏水印（需 enable_watermark=True）。
    """

    @classmethod
    def from_yaml(cls, yaml_path: str) -> 'ParserConfig':
        """
        Load configuration from YAML file.

        :param yaml_path: Path to YAML configuration file
        :return: ParserConfig instance
        """
        if not YAML_AVAILABLE:
            logger.error("Cannot load YAML config: PyYAML not installed")
            return cls()

        if not os.path.exists(yaml_path):
            logger.warning(f"Config file not found: {yaml_path}, using defaults")
            return cls()

        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)

            if not config_data:
                logger.warning(f"Empty config file: {yaml_path}, using defaults")
                return cls()

            # Extract configuration values
            config = cls(
                min_chapter_length=config_data.get('min_chapter_length', 100),
                min_section_length=config_data.get('min_section_length', 50),
                enable_chapter_validation=config_data.get('enable_chapter_validation', True),
                enable_length_validation=config_data.get('enable_length_validation', False),
                enable_fuzzy_matching=config_data.get('enable_fuzzy_matching', False),
                custom_chapter_patterns=config_data.get('custom_chapter_patterns', []),
                custom_volume_patterns=config_data.get('custom_volume_patterns', []),
                custom_section_patterns=config_data.get('custom_section_patterns', []),
                ignore_patterns=config_data.get('ignore_patterns', []),
                special_chapter_keywords=config_data.get('special_chapter_keywords', []),
                language_hints=config_data.get('language_hints', {}),
                debug_mode=config_data.get('debug_mode', False),
                log_rejected_matches=config_data.get('log_rejected_matches', False)
            )

            logger.info(f"Loaded configuration from {yaml_path}")
            return config

        except Exception as e:
            logger.error(f"Error loading config from {yaml_path}: {e}")
            return cls()

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'ParserConfig':
        """
        Create configuration from dictionary.

        :param config_dict: Configuration dictionary
        :return: ParserConfig instance
        """
        return cls(
            min_chapter_length=config_dict.get('min_chapter_length', 100),
            min_section_length=config_dict.get('min_section_length', 50),
            enable_chapter_validation=config_dict.get('enable_chapter_validation', True),
            enable_length_validation=config_dict.get('enable_length_validation', False),
            enable_fuzzy_matching=config_dict.get('enable_fuzzy_matching', False),
            custom_chapter_patterns=config_dict.get('custom_chapter_patterns', []),
            custom_volume_patterns=config_dict.get('custom_volume_patterns', []),
            custom_section_patterns=config_dict.get('custom_section_patterns', []),
            ignore_patterns=config_dict.get('ignore_patterns', []),
            special_chapter_keywords=config_dict.get('special_chapter_keywords', []),
            language_hints=config_dict.get('language_hints', {}),
            debug_mode=config_dict.get('debug_mode', False),
            log_rejected_matches=config_dict.get('log_rejected_matches', False),
            # LLM配置 (简化版)
            enable_llm_assistance=config_dict.get('enable_llm_assistance', False),
            llm_api_key=config_dict.get('llm_api_key'),
            llm_base_url=config_dict.get('llm_base_url'),
            llm_model=config_dict.get('llm_model', 'deepseek-v3.2'),
            llm_confidence_threshold=config_dict.get('llm_confidence_threshold', 0.7),
            llm_toc_detection_threshold=config_dict.get('llm_toc_detection_threshold', 0.7),
            llm_no_toc_threshold=config_dict.get('llm_no_toc_threshold', 0.8),
            # 目录检测配置
            toc_detection_score_threshold=config_dict.get('toc_detection_score_threshold', 30.0),
            toc_max_scan_lines=config_dict.get('toc_max_scan_lines', 300),
            # HTML 输出配置
            enable_watermark=config_dict.get('enable_watermark', True),
            watermark_text=config_dict.get('watermark_text', 'Powered by oomol.com, Please ensure that the copyright is in compliance')
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.

        :return: Configuration dictionary
        """
        return {
            'min_chapter_length': self.min_chapter_length,
            'min_section_length': self.min_section_length,
            'enable_chapter_validation': self.enable_chapter_validation,
            'enable_length_validation': self.enable_length_validation,
            'enable_fuzzy_matching': self.enable_fuzzy_matching,
            'custom_chapter_patterns': self.custom_chapter_patterns,
            'custom_volume_patterns': self.custom_volume_patterns,
            'custom_section_patterns': self.custom_section_patterns,
            'ignore_patterns': self.ignore_patterns,
            'special_chapter_keywords': self.special_chapter_keywords,
            'language_hints': self.language_hints,
            'debug_mode': self.debug_mode,
            'log_rejected_matches': self.log_rejected_matches,
            # LLM配置 (简化版)
            'enable_llm_assistance': self.enable_llm_assistance,
            'llm_api_key': self.llm_api_key,
            'llm_base_url': self.llm_base_url,
            'llm_model': self.llm_model,
            'llm_confidence_threshold': self.llm_confidence_threshold,
            'llm_toc_detection_threshold': self.llm_toc_detection_threshold,
            'llm_no_toc_threshold': self.llm_no_toc_threshold,
            # 目录检测配置
            'toc_detection_score_threshold': self.toc_detection_score_threshold,
            'toc_max_scan_lines': self.toc_max_scan_lines,
            # HTML 输出配置
            'enable_watermark': self.enable_watermark,
            'watermark_text': self.watermark_text
        }

    def save_to_yaml(self, yaml_path: str) -> None:
        """
        Save configuration to YAML file.

        :param yaml_path: Path to save YAML configuration
        """
        if not YAML_AVAILABLE:
            logger.error("Cannot save YAML config: PyYAML not installed")
            return

        try:
            with open(yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.to_dict(), f, default_flow_style=False, allow_unicode=True)
            logger.info(f"Saved configuration to {yaml_path}")
        except Exception as e:
            logger.error(f"Error saving config to {yaml_path}: {e}")

    def get_compiled_custom_patterns(self, pattern_type: str) -> List[re.Pattern]:
        """
        Get compiled regex patterns for the specified type.

        :param pattern_type: 'chapter', 'volume', or 'section'
        :return: List of compiled regex patterns
        """
        if pattern_type == 'chapter':
            patterns = self.custom_chapter_patterns
        elif pattern_type == 'volume':
            patterns = self.custom_volume_patterns
        elif pattern_type == 'section':
            patterns = self.custom_section_patterns
        else:
            return []

        compiled = []
        for pattern_str in patterns:
            try:
                compiled.append(re.compile(pattern_str, re.MULTILINE | re.IGNORECASE))
            except re.error as e:
                logger.error(f"Invalid regex pattern '{pattern_str}': {e}")

        return compiled

    def should_ignore_match(self, match_text: str) -> bool:
        """
        Check if a match should be ignored based on ignore patterns.

        :param match_text: Text to check
        :return: True if should ignore, False otherwise
        """
        for pattern_str in self.ignore_patterns:
            try:
                if re.search(pattern_str, match_text, re.IGNORECASE):
                    return True
            except re.error as e:
                logger.error(f"Invalid ignore pattern '{pattern_str}': {e}")

        return False


# Default configuration instance
DEFAULT_CONFIG = ParserConfig()


# Example configuration template
EXAMPLE_CONFIG = """
# Parser Configuration Example

# Minimum content length thresholds
min_chapter_length: 500
min_section_length: 100

# Validation settings
enable_chapter_validation: true
enable_length_validation: true
enable_fuzzy_matching: false

# Custom regex patterns for chapters (in addition to built-in patterns)
custom_chapter_patterns:
  - "第.*回"  # Support 章回体 novels
  - "Episode \\d+"  # English episodes

# Custom volume patterns
custom_volume_patterns:
  - "Act [IVX]+"  # Theater acts

# Custom section patterns
custom_section_patterns: []

# Patterns to ignore (inline references that should not be treated as chapters)
ignore_patterns:
  - "在第.*章"
  - "如第.*章所述"
  - "见第.*章"
  - "in Chapter \\d+"
  - "see Chapter \\d+"

# Special keywords (additional chapter markers)
special_chapter_keywords:
  - "开篇"
  - "引子"
  - "Epilogue"
  - "Aftermath"

# Language-specific hints
language_hints:
  chinese:
    prefer_numeric_chapters: false
  english:
    prefer_roman_numerals: false

# Debug settings
debug_mode: false
log_rejected_matches: true
"""


def create_example_config(output_path: str) -> None:
    """
    Create an example configuration file.

    :param output_path: Path to save example configuration
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(EXAMPLE_CONFIG)
        logger.info(f"Created example configuration at {output_path}")
    except Exception as e:
        logger.error(f"Error creating example config: {e}")
