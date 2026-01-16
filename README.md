# 📚 TXT to EPUB Converter

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/txt-to-epub-converter)](https://pypi.org/project/txt-to-epub-converter/)

一个强大的 Python 库,可以将纯文本文件(.txt)智能转换为专业格式的 EPUB 电子书。支持自动章节检测、智能目录生成,以及 AI 增强的结构分析。

[English](#english) | [中文文档](#中文文档)

---

## 中文文档

### ✨ 核心特性

- 🎯 **智能章节识别** - 自动检测和解析各种章节格式(第一章、Chapter 1、卷一等)
- 🤖 **AI 增强分析** - 可选的 LLM 辅助,准确识别复杂的章节结构
- 📖 **自动目录生成** - 智能创建层次化的目录结构
- 🎨 **专业排版** - 内置精美的 CSS 样式和响应式布局
- 💾 **断点续传** - 支持大文件转换时的中断恢复
- 🌍 **多编码支持** - 自动检测文件编码(UTF-8、GBK、GB18030 等)
- ✅ **完整性验证** - 转换后自动验证字数和章节完整性
- 📊 **实时进度** - 详细的转换进度显示和日志记录

### 🚀 快速开始

#### 安装

```bash
pip install txt-to-epub-converter
```

或从源码安装:

```bash
git clone https://github.com/yourusername/txt-to-epub-converter.git
cd txt-to-epub-converter
pip install -e .
```

#### 基础使用

```python
from txt_to_epub import txt_to_epub, ParserConfig

# 最简单的用法
result = txt_to_epub(
    txt_file="mybook.txt",
    epub_file="mybook.epub",
    title="我的书",
    author="作者名"
)

print(f"转换完成: {result['output_file']}")
print(result['validation_report'])
```

#### 启用 AI 智能分析

```python
from txt_to_epub import txt_to_epub, ParserConfig

# 配置 AI 增强解析
config = ParserConfig(
    enable_llm_assistance=True,
    llm_api_key="your-api-key",
    llm_base_url="https://api.openai.com/v1",
    llm_model="gpt-4",
    llm_confidence_threshold=0.5
)

# 转换时使用配置
result = txt_to_epub(
    txt_file="complex_book.txt",
    epub_file="complex_book.epub",
    title="复杂格式的书",
    author="作者",
    config=config
)
```

### 📋 详细示例

#### 完整功能示例

```python
from txt_to_epub import txt_to_epub, ParserConfig

# 创建自定义配置
config = ParserConfig(
    # AI 辅助设置
    enable_llm_assistance=True,
    llm_api_key="your-api-key",
    llm_base_url="https://api.openai.com/v1",
    llm_model="gpt-4",

    # 置信度阈值
    llm_confidence_threshold=0.5,          # LLM 触发阈值
    llm_toc_detection_threshold=0.5,      # 目录存在判定阈值
    llm_no_toc_threshold=0.6,             # 无目录判定阈值

    # 目录检测设置
    toc_detection_score_threshold=20,     # 目录检测评分阈值
    toc_max_scan_lines=300                # 最大扫描行数
)

# 执行转换
result = txt_to_epub(
    txt_file="book.txt",
    epub_file="output/book.epub",
    title="书名",
    author="作者",
    cover_image="cover.png",              # 可选:封面图片
    config=config,
    enable_resume=True                     # 启用断点续传
)

# 查看结果
print(f"输出文件: {result['output_file']}")
print(f"总字数: {result['total_chars']}")
print(f"检测到的章节数: {result['chapter_count']}")
print(f"\n验证报告:\n{result['validation_report']}")
```

#### 批量转换

```python
import os
from pathlib import Path
from txt_to_epub import txt_to_epub, ParserConfig

def batch_convert(input_dir, output_dir):
    """批量转换目录下的所有 txt 文件"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    config = ParserConfig(enable_llm_assistance=True)

    for txt_file in input_path.glob("*.txt"):
        epub_file = output_path / f"{txt_file.stem}.epub"

        try:
            print(f"转换: {txt_file.name}...")
            result = txt_to_epub(
                txt_file=str(txt_file),
                epub_file=str(epub_file),
                title=txt_file.stem,
                author="Unknown",
                config=config
            )
            print(f"✓ 完成: {epub_file.name}")
        except Exception as e:
            print(f"✗ 失败: {txt_file.name} - {e}")

# 使用示例
batch_convert("./books", "./output")
```

### 🔧 API 参考

#### `txt_to_epub()` 函数

主要的转换函数。

```python
def txt_to_epub(
    txt_file: str,
    epub_file: str,
    title: str,
    author: str,
    cover_image: Optional[str] = None,
    config: ParserConfig = DEFAULT_CONFIG,
    context: Optional[Any] = None,
    enable_resume: bool = True
) -> Dict[str, Any]:
    """
    将 TXT 文件转换为 EPUB 格式

    参数:
        txt_file: 输入的 TXT 文件路径
        epub_file: 输出的 EPUB 文件路径
        title: 书籍标题
        author: 作者名称
        cover_image: 封面图片路径(可选)
        config: 解析器配置对象
        context: 上下文对象(用于进度报告,可选)
        enable_resume: 是否启用断点续传

    返回:
        包含转换结果的字典:
        {
            'output_file': str,           # 输出文件路径
            'total_chars': int,           # 总字符数
            'chapter_count': int,         # 章节数量
            'validation_report': str,     # 验证报告
            'volumes': List[Volume]       # 解析的卷/章节结构
        }

    异常:
        FileNotFoundError: 输入文件不存在
        ValueError: 参数验证失败
        RuntimeError: 转换过程出错
    """
```

#### `ParserConfig` 类

解析器配置类。

```python
class ParserConfig:
    """
    解析器配置类

    属性:
        enable_llm_assistance: 是否启用 LLM 辅助(默认: False)
        llm_api_key: LLM API 密钥(仅当启用 LLM 时需要)
        llm_base_url: LLM API 基础 URL
        llm_model: 使用的 LLM 模型名称(默认: 'gpt-4')
        llm_confidence_threshold: LLM 触发的置信度阈值(0-1,默认: 0.5)
        llm_toc_detection_threshold: 确认存在目录的置信度阈值(默认: 0.5)
        llm_no_toc_threshold: 确认无目录的置信度阈值(默认: 0.6)
        toc_detection_score_threshold: 目录检测的最低分数(默认: 20)
        toc_max_scan_lines: 目录检测的最大扫描行数(默认: 300)
    """

    def __init__(
        self,
        enable_llm_assistance: bool = False,
        llm_api_key: Optional[str] = None,
        llm_base_url: Optional[str] = None,
        llm_model: str = "gpt-4",
        llm_confidence_threshold: float = 0.5,
        llm_toc_detection_threshold: float = 0.5,
        llm_no_toc_threshold: float = 0.6,
        toc_detection_score_threshold: int = 20,
        toc_max_scan_lines: int = 300
    ):
        ...
```

### 🎯 支持的章节格式

本库可以自动识别以下章节格式:

#### 中文格式
- `第一章 标题`
- `第1章 标题`
- `第001章 标题`
- `第一卷 标题`
- `卷一 标题`
- `正文 第一章`
- `楔子`、`序章`、`尾声`

#### 英文格式
- `Chapter 1 Title`
- `Chapter One`
- `CHAPTER 1`
- `Volume 1`
- `Part I`
- `Prologue`, `Epilogue`

#### 混合格式
- `第一卷 第一章 标题`
- `Volume 1 Chapter 1`
- 自定义分隔符和空格

### 📊 转换流程

```
输入 TXT 文件
     ↓
自动检测编码
     ↓
预处理文本内容
     ↓
检测目录结构 ←─────┐
     ↓              │
规则匹配章节        │ (可选)
     ↓              │
置信度评估 ────→ LLM 辅助分析
     ↓
生成层次结构
     ↓
创建 EPUB 内容
     ↓
应用 CSS 样式
     ↓
完整性验证
     ↓
输出 EPUB 文件
```

### 🛠️ 高级功能

#### 断点续传

对于大文件转换,支持断点续传功能:

```python
result = txt_to_epub(
    txt_file="large_book.txt",
    epub_file="large_book.epub",
    title="大型书籍",
    author="作者",
    enable_resume=True  # 启用断点续传
)
```

如果转换中断,再次运行相同代码会从上次中断的地方继续。

#### 自定义 CSS 样式

如果需要自定义样式,可以修改 `css.py` 文件中的样式定义,或在生成的 EPUB 中手动编辑。

#### 进度回调

```python
class ProgressContext:
    """简单的进度上下文"""
    def report_progress(self, progress: float):
        print(f"进度: {progress:.1%}")

context = ProgressContext()
result = txt_to_epub(
    txt_file="book.txt",
    epub_file="book.epub",
    title="书名",
    author="作者",
    context=context
)
```

### 📦 项目结构

```
txt-to-epub-converter/
├── src/
│   └── txt_to_epub/
│       ├── __init__.py              # 主入口
│       ├── core.py                  # 核心转换逻辑
│       ├── parser.py                # 章节解析器
│       ├── parser_config.py         # 配置类
│       ├── llm_parser_assistant.py  # LLM 辅助解析
│       ├── html_generator.py        # HTML 生成器
│       ├── css.py                   # CSS 样式
│       ├── data_structures.py       # 数据结构
│       ├── resume_state.py          # 断点续传
│       └── word_count_validator.py  # 完整性验证
├── tests/                           # 测试文件
├── examples/                        # 示例代码
├── README.md
├── LICENSE
├── pyproject.toml
└── setup.py
```

### 🔍 常见问题

#### Q: 为什么有些章节没有被识别?

A: 可以尝试以下方法:
1. 启用 AI 辅助分析 (`enable_llm_assistance=True`)
2. 降低 `llm_confidence_threshold` 值
3. 增加 `toc_max_scan_lines` 值
4. 检查文本格式是否一致

#### Q: 如何处理特殊格式的章节?

A: 本库支持大多数常见格式。如果有特殊需求,可以:
1. 使用 AI 辅助模式
2. 在 `parser.py` 中添加自定义正则表达式
3. 预处理文本文件,统一章节格式

#### Q: 转换后的 EPUB 在某些阅读器中显示异常?

A:
1. 确保使用支持 EPUB 3.0 的阅读器
2. 尝试使用 Calibre 等工具重新验证 EPUB 文件
3. 检查是否有特殊字符或格式问题

#### Q: 如何提高转换速度?

A:
1. 禁用 LLM 辅助(规则匹配速度更快)
2. 减少 `toc_max_scan_lines` 值
3. 如果不需要断点续传,设置 `enable_resume=False`

### 🤝 贡献指南

欢迎贡献!请遵循以下步骤:

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

#### 开发设置

```bash
# 克隆仓库
git clone https://github.com/yourusername/txt-to-epub-converter.git
cd txt-to-epub-converter

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化
black src/
flake8 src/
```

### 📝 更新日志

查看 [CHANGELOG.md](CHANGELOG.md) 了解详细的版本历史。

### 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

### 🙏 致谢

- [EbookLib](https://github.com/aerkalov/ebooklib) - EPUB 文件处理
- [chardet](https://github.com/chardet/chardet) - 字符编码检测
- [OpenAI](https://openai.com/) - AI 辅助分析

### 📧 联系方式

- 问题反馈: [GitHub Issues](https://github.com/yourusername/txt-to-epub-converter/issues)
- 邮件: your.email@example.com
- 项目主页: [https://github.com/yourusername/txt-to-epub-converter](https://github.com/yourusername/txt-to-epub-converter)

---

## English

### ✨ Core Features

- 🎯 **Smart Chapter Detection** - Automatically detect and parse various chapter formats
- 🤖 **AI-Enhanced Analysis** - Optional LLM assistance for complex chapter structures
- 📖 **Auto TOC Generation** - Intelligently create hierarchical table of contents
- 🎨 **Professional Typography** - Built-in beautiful CSS styles and responsive layout
- 💾 **Resume Support** - Support interruption recovery for large file conversion
- 🌍 **Multi-Encoding Support** - Auto-detect file encoding (UTF-8, GBK, GB18030, etc.)
- ✅ **Integrity Validation** - Automatic validation of word count and chapter integrity
- 📊 **Real-time Progress** - Detailed conversion progress display and logging

### 🚀 Quick Start

#### Installation

```bash
pip install txt-to-epub-converter
```

Or install from source:

```bash
git clone https://github.com/yourusername/txt-to-epub-converter.git
cd txt-to-epub-converter
pip install -e .
```

#### Basic Usage

```python
from txt_to_epub import txt_to_epub, ParserConfig

# Simplest usage
result = txt_to_epub(
    txt_file="mybook.txt",
    epub_file="mybook.epub",
    title="My Book",
    author="Author Name"
)

print(f"Conversion complete: {result['output_file']}")
print(result['validation_report'])
```

#### Enable AI Smart Analysis

```python
from txt_to_epub import txt_to_epub, ParserConfig

# Configure AI-enhanced parsing
config = ParserConfig(
    enable_llm_assistance=True,
    llm_api_key="your-api-key",
    llm_base_url="https://api.openai.com/v1",
    llm_model="gpt-4",
    llm_confidence_threshold=0.5
)

# Convert with config
result = txt_to_epub(
    txt_file="complex_book.txt",
    epub_file="complex_book.epub",
    title="Complex Format Book",
    author="Author",
    config=config
)
```

### 📋 Detailed Examples

#### Full Featured Example

```python
from txt_to_epub import txt_to_epub, ParserConfig

# Create custom config
config = ParserConfig(
    # AI assistance settings
    enable_llm_assistance=True,
    llm_api_key="your-api-key",
    llm_base_url="https://api.openai.com/v1",
    llm_model="gpt-4",

    # Confidence thresholds
    llm_confidence_threshold=0.5,          # LLM trigger threshold
    llm_toc_detection_threshold=0.5,      # TOC existence threshold
    llm_no_toc_threshold=0.6,             # No TOC threshold

    # TOC detection settings
    toc_detection_score_threshold=20,     # TOC detection score threshold
    toc_max_scan_lines=300                # Maximum lines to scan
)

# Execute conversion
result = txt_to_epub(
    txt_file="book.txt",
    epub_file="output/book.epub",
    title="Book Title",
    author="Author Name",
    cover_image="cover.png",              # Optional: cover image
    config=config,
    enable_resume=True                     # Enable resume support
)

# View results
print(f"Output file: {result['output_file']}")
print(f"Total chars: {result['total_chars']}")
print(f"Detected chapters: {result['chapter_count']}")
print(f"\nValidation report:\n{result['validation_report']}")
```

#### Batch Conversion

```python
import os
from pathlib import Path
from txt_to_epub import txt_to_epub, ParserConfig

def batch_convert(input_dir, output_dir):
    """Batch convert all txt files in directory"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    config = ParserConfig(enable_llm_assistance=True)

    for txt_file in input_path.glob("*.txt"):
        epub_file = output_path / f"{txt_file.stem}.epub"

        try:
            print(f"Converting: {txt_file.name}...")
            result = txt_to_epub(
                txt_file=str(txt_file),
                epub_file=str(epub_file),
                title=txt_file.stem,
                author="Unknown",
                config=config
            )
            print(f"✓ Done: {epub_file.name}")
        except Exception as e:
            print(f"✗ Failed: {txt_file.name} - {e}")

# Usage
batch_convert("./books", "./output")
```

### 🔧 API Reference

#### `txt_to_epub()` Function

The main conversion function.

```python
def txt_to_epub(
    txt_file: str,
    epub_file: str,
    title: str,
    author: str,
    cover_image: Optional[str] = None,
    config: ParserConfig = DEFAULT_CONFIG,
    context: Optional[Any] = None,
    enable_resume: bool = True
) -> Dict[str, Any]:
    """
    Convert TXT file to EPUB format

    Args:
        txt_file: Input TXT file path
        epub_file: Output EPUB file path
        title: Book title
        author: Author name
        cover_image: Cover image path (optional)
        config: Parser configuration object
        context: Context object (for progress reporting, optional)
        enable_resume: Enable resume support

    Returns:
        Dictionary containing conversion results:
        {
            'output_file': str,           # Output file path
            'total_chars': int,           # Total character count
            'chapter_count': int,         # Number of chapters
            'validation_report': str,     # Validation report
            'volumes': List[Volume]       # Parsed volume/chapter structure
        }

    Raises:
        FileNotFoundError: Input file does not exist
        ValueError: Parameter validation failed
        RuntimeError: Conversion error occurred
    """
```

#### `ParserConfig` Class

Parser configuration class.

```python
class ParserConfig:
    """
    Parser configuration class

    Attributes:
        enable_llm_assistance: Enable LLM assistance (default: False)
        llm_api_key: LLM API key (required only when LLM is enabled)
        llm_base_url: LLM API base URL
        llm_model: LLM model name to use (default: 'gpt-4')
        llm_confidence_threshold: Confidence threshold for LLM trigger (0-1, default: 0.5)
        llm_toc_detection_threshold: Confidence threshold for confirming TOC exists (default: 0.5)
        llm_no_toc_threshold: Confidence threshold for confirming no TOC (default: 0.6)
        toc_detection_score_threshold: Minimum score for TOC detection (default: 20)
        toc_max_scan_lines: Maximum lines to scan for TOC detection (default: 300)
    """

    def __init__(
        self,
        enable_llm_assistance: bool = False,
        llm_api_key: Optional[str] = None,
        llm_base_url: Optional[str] = None,
        llm_model: str = "gpt-4",
        llm_confidence_threshold: float = 0.5,
        llm_toc_detection_threshold: float = 0.5,
        llm_no_toc_threshold: float = 0.6,
        toc_detection_score_threshold: int = 20,
        toc_max_scan_lines: int = 300
    ):
        ...
```

### 🎯 Supported Chapter Formats

This library can automatically recognize the following chapter formats:

#### Chinese Formats
- `第一章 标题` (Chapter One Title)
- `第1章 标题` (Chapter 1 Title)
- `第001章 标题` (Chapter 001 Title)
- `第一卷 标题` (Volume One Title)
- `卷一 标题` (Volume One Title)
- `正文 第一章` (Main Text Chapter One)
- `楔子`, `序章`, `尾声` (Prologue, Preface, Epilogue)

#### English Formats
- `Chapter 1 Title`
- `Chapter One`
- `CHAPTER 1`
- `Volume 1`
- `Part I`
- `Prologue`, `Epilogue`

#### Mixed Formats
- `第一卷 第一章 标题`
- `Volume 1 Chapter 1`
- Custom separators and spacing

### 📊 Conversion Flow

```
Input TXT File
     ↓
Auto-detect Encoding
     ↓
Preprocess Text Content
     ↓
Detect TOC Structure ←─────┐
     ↓                     │
Rule-based Chapter Match   │ (Optional)
     ↓                     │
Confidence Evaluation ──→ LLM Analysis
     ↓
Generate Hierarchy
     ↓
Create EPUB Content
     ↓
Apply CSS Styles
     ↓
Integrity Validation
     ↓
Output EPUB File
```

### 🛠️ Advanced Features

#### Resume Support

For large file conversions, supports resume functionality:

```python
result = txt_to_epub(
    txt_file="large_book.txt",
    epub_file="large_book.epub",
    title="Large Book",
    author="Author",
    enable_resume=True  # Enable resume support
)
```

If conversion is interrupted, running the same code again will continue from where it left off.

#### Custom CSS Styles

If you need custom styles, you can modify the style definitions in `css.py` or manually edit them in the generated EPUB.

#### Progress Callback

```python
class ProgressContext:
    """Simple progress context"""
    def report_progress(self, progress: float):
        print(f"Progress: {progress:.1%}")

context = ProgressContext()
result = txt_to_epub(
    txt_file="book.txt",
    epub_file="book.epub",
    title="Book Title",
    author="Author",
    context=context
)
```

### 📦 Project Structure

```
txt-to-epub-converter/
├── src/
│   └── txt_to_epub/
│       ├── __init__.py              # Main entry point
│       ├── core.py                  # Core conversion logic
│       ├── parser.py                # Chapter parser
│       ├── parser_config.py         # Configuration class
│       ├── llm_parser_assistant.py  # LLM-assisted parsing
│       ├── html_generator.py        # HTML generator
│       ├── css.py                   # CSS styles
│       ├── data_structures.py       # Data structures
│       ├── resume_state.py          # Resume support
│       └── word_count_validator.py  # Integrity validation
├── tests/                           # Test files
├── examples/                        # Example code
├── README.md
├── LICENSE
├── pyproject.toml
└── setup.py
```

### 🔍 FAQ

#### Q: Why are some chapters not recognized?

A: Try the following:
1. Enable AI assistance (`enable_llm_assistance=True`)
2. Lower the `llm_confidence_threshold` value
3. Increase `toc_max_scan_lines` value
4. Check if text format is consistent

#### Q: How to handle special chapter formats?

A: This library supports most common formats. For special needs:
1. Use AI assistance mode
2. Add custom regex in `parser.py`
3. Preprocess text file to unify chapter format

#### Q: EPUB displays abnormally in some readers?

A:
1. Ensure using readers that support EPUB 3.0
2. Try revalidating EPUB with tools like Calibre
3. Check for special characters or formatting issues

#### Q: How to improve conversion speed?

A:
1. Disable LLM assistance (rule matching is faster)
2. Reduce `toc_max_scan_lines` value
3. Set `enable_resume=False` if resume not needed

### 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

#### Development Setup

```bash
# Clone repository
git clone https://github.com/yourusername/txt-to-epub-converter.git
cd txt-to-epub-converter

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Code formatting
black src/
flake8 src/
```

### 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

### 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

### 🙏 Acknowledgments

- [EbookLib](https://github.com/aerkalov/ebooklib) - EPUB file handling
- [chardet](https://github.com/chardet/chardet) - Character encoding detection
- [OpenAI](https://openai.com/) - AI-assisted analysis

### 📧 Contact

- Issue tracking: [GitHub Issues](https://github.com/yourusername/txt-to-epub-converter/issues)
- Email: your.email@example.com
- Project homepage: [https://github.com/yourusername/txt-to-epub-converter](https://github.com/yourusername/txt-to-epub-converter)

---

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=yourusername/txt-to-epub-converter&type=Date)](https://star-history.com/#yourusername/txt-to-epub-converter&Date)

---

**Made with ❤️ by the TXT to EPUB Converter team**
