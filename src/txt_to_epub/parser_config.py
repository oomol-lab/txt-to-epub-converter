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
    """Configuration class for text parser"""

    # Minimum content length thresholds
    min_chapter_length: int = 100  # Minimum chapter length in characters
    min_section_length: int = 50  # Minimum section length in characters

    # Validation settings
    enable_chapter_validation: bool = True  # Enable chapter title validation
    enable_length_validation: bool = False  # Enable length-based validation
    enable_fuzzy_matching: bool = False  # Enable fuzzy pattern matching (future)

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
    """LLM置信度阈值,低于此值时使用规则解析结果 (默认0.7)"""

    llm_toc_detection_threshold: float = 0.7
    """LLM判断存在目录的置信度阈值 (默认0.7)，LLM必须超过此值才确认存在目录"""

    llm_no_toc_threshold: float = 0.8
    """LLM判断无目录的置信度阈值 (默认0.8)，超过此值时直接跳过目录移除"""

    # ========== 目录检测配置 ==========

    toc_detection_score_threshold: float = 30.0
    """目录检测的综合评分阈值 (0-100, 默认30)，分数越高要求越严格"""

    toc_max_scan_lines: int = 300
    """目录检测的最大扫描行数 (默认300)，防止误判过长区域为目录"""

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
            toc_max_scan_lines=config_dict.get('toc_max_scan_lines', 300)
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
            'toc_max_scan_lines': self.toc_max_scan_lines
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
