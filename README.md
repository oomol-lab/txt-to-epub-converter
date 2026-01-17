# TXT to EPUB Converter

[![PyPI version](https://badge.fury.io/py/txt-to-epub-converter.svg)](https://badge.fury.io/py/txt-to-epub-converter)
[![Python Versions](https://img.shields.io/pypi/pyversions/txt-to-epub-converter.svg)](https://pypi.org/project/txt-to-epub-converter/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A powerful Python library for converting plain text files (.txt) to professional EPUB eBooks with intelligent chapter detection and AI-enhanced structure analysis.

[中文文档](README_zh.md) | English

## ✨ Features

- **📚 Intelligent Chapter Detection**: Automatically identifies hierarchical structure (volumes, chapters, sections) using pattern matching
- **🤖 AI-Enhanced Parsing** (Optional): Integrates with OpenAI-compatible LLMs for improved chapter title generation and structure analysis
- **🎯 Resume Support**: Built-in checkpoint mechanism allows resuming interrupted conversions
- **🌍 Multi-Language Support**: Handles both Chinese (GB18030, GBK, UTF-8) and English text with automatic encoding detection
- **💧 Watermark Support**: Optional watermark text for copyright protection
- **✅ Content Validation**: Automatic word count validation ensures conversion integrity
- **⚡ Progress Tracking**: Real-time progress bar with detailed status updates
- **🎨 Professional Formatting**: Clean, readable EPUB output with proper CSS styling

## 🚀 Installation

### Install from PyPI (Recommended)

```bash
pip install txt-to-epub-converter
```

### Install from Source

```bash
git clone https://github.com/yourusername/txt-to-epub-converter.git
cd txt-to-epub-converter
pip install -e .
```

### Optional Dependencies

For AI-enhanced parsing (requires OpenAI-compatible API):

```bash
pip install txt-to-epub-converter[ai]
```

For development:

```bash
pip install txt-to-epub-converter[dev]
```

## 📖 Quick Start

### Basic Usage

```python
from txt_to_epub import txt_to_epub

# Simple conversion
result = txt_to_epub(
    txt_file="my_novel.txt",
    epub_file="output/my_novel.epub",
    title="My Novel",
    author="Author Name"
)

print(f"Conversion completed: {result['output_file']}")
print(f"Chapters: {result['chapters_count']}")
print(f"Validation: {'✓ Passed' if result['validation_passed'] else '✗ Failed'}")
```

### Advanced Configuration

```python
from txt_to_epub import txt_to_epub, ParserConfig

# Custom configuration
config = ParserConfig(
    # Chapter detection patterns
    chapter_patterns=[
        r'^第[0-9零一二三四五六七八九十百千]+章\s+.+$',  # Chinese: 第1章 标题
        r'^Chapter\s+\d+[:\s]+.+$'                      # English: Chapter 1: Title
    ],

    # Enable AI assistance
    enable_llm_assistance=True,
    llm_api_key="your-api-key",
    llm_base_url="https://api.openai.com/v1",
    llm_model="gpt-4o-mini",

    # Watermark
    enable_watermark=True,
    watermark_text="© 2026 Author Name. All rights reserved.",

    # Content filtering
    min_chapter_length=100,  # Minimum characters per chapter
    max_chapter_length=50000 # Maximum characters per chapter
)

# Convert with custom config
result = txt_to_epub(
    txt_file="my_book.txt",
    epub_file="output/my_book.epub",
    title="My Book",
    author="Author Name",
    cover_image="cover.jpg",  # Optional cover image
    config=config,
    enable_resume=True         # Enable checkpoint resume
)
```

## 🎯 Use Cases

### Converting Web Novels

Perfect for converting downloaded web novels with standard chapter formatting:

```python
from txt_to_epub import txt_to_epub

result = txt_to_epub(
    txt_file="web_novel.txt",
    epub_file="web_novel.epub",
    title="Epic Fantasy Novel",
    author="Web Author"
)
```

### Converting Technical Documentation

Handles technical books with hierarchical structure:

```python
from txt_to_epub import txt_to_epub, ParserConfig

config = ParserConfig(
    volume_patterns=[r'^Part\s+\d+[:\s]+.+$'],
    chapter_patterns=[r'^Chapter\s+\d+[:\s]+.+$'],
    section_patterns=[r'^\d+\.\d+\s+.+$']
)

result = txt_to_epub(
    txt_file="programming_guide.txt",
    epub_file="programming_guide.epub",
    title="Programming Guide",
    author="Tech Writer",
    config=config
)
```

### Batch Conversion

Convert multiple files efficiently:

```python
from txt_to_epub import txt_to_epub
from pathlib import Path

txt_files = Path("books").glob("*.txt")

for txt_file in txt_files:
    epub_file = f"output/{txt_file.stem}.epub"

    try:
        result = txt_to_epub(
            txt_file=str(txt_file),
            epub_file=epub_file,
            title=txt_file.stem.replace("_", " ").title(),
            author="Collection"
        )
        print(f"✓ Converted: {txt_file.name}")
    except Exception as e:
        print(f"✗ Failed: {txt_file.name} - {e}")
```

## 🛠️ Configuration Options

### ParserConfig Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `chapter_patterns` | List[str] | Built-in patterns | Regex patterns for chapter detection |
| `volume_patterns` | List[str] | Built-in patterns | Regex patterns for volume detection |
| `section_patterns` | List[str] | Built-in patterns | Regex patterns for section detection |
| `min_chapter_length` | int | 50 | Minimum characters per chapter |
| `max_chapter_length` | int | 100000 | Maximum characters per chapter |
| `enable_llm_assistance` | bool | False | Enable AI-enhanced parsing |
| `llm_api_key` | str | None | OpenAI-compatible API key |
| `llm_base_url` | str | OpenAI URL | API base URL |
| `llm_model` | str | "gpt-4o-mini" | Model name |
| `enable_watermark` | bool | False | Enable watermark |
| `watermark_text` | str | None | Watermark text |

### txt_to_epub() Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `txt_file` | str | Yes | Input TXT file path |
| `epub_file` | str | Yes | Output EPUB file path |
| `title` | str | No | Book title (default: "My Book") |
| `author` | str | No | Author name (default: "Unknown") |
| `cover_image` | str | No | Cover image path (PNG/JPG) |
| `config` | ParserConfig | No | Custom configuration |
| `show_progress` | bool | No | Show progress bar (default: True) |
| `enable_resume` | bool | No | Enable checkpoint resume (default: False) |

## 📊 Output Structure

The converter generates EPUB files with the following structure:

```
output.epub
├── Volume 1: Title
│   ├── Chapter 1: Title
│   ├── Chapter 2: Title
│   └── ...
├── Volume 2: Title
│   └── ...
└── Chapter N: Title (standalone chapters without volumes)
    ├── Section 1.1
    └── Section 1.2
```

## 🤖 AI-Enhanced Features

When `enable_llm_assistance=True`:

1. **Smart Title Generation**: Generates descriptive titles for chapters without clear titles
2. **Table of Contents Detection**: Removes redundant TOC sections automatically
3. **Batch Processing**: Processes multiple chapters in parallel for efficiency
4. **Cost Tracking**: Reports API usage and costs

Example with AI:

```python
from txt_to_epub import txt_to_epub, ParserConfig

config = ParserConfig(
    enable_llm_assistance=True,
    llm_api_key="sk-...",
    llm_model="gpt-4o-mini"  # Fast and cost-effective
)

result = txt_to_epub(
    txt_file="novel.txt",
    epub_file="novel.epub",
    title="My Novel",
    author="Author",
    config=config
)

# AI usage stats are logged automatically
```

## 🔄 Resume Feature

The resume feature allows you to continue interrupted conversions:

```python
result = txt_to_epub(
    txt_file="large_book.txt",
    epub_file="large_book.epub",
    title="Large Book",
    author="Author",
    enable_resume=True  # Enable checkpoint resume
)
```

If the conversion is interrupted (Ctrl+C, crash, etc.), simply run the same command again. The converter will:
- Detect the previous state file
- Verify the source file hasn't changed
- Resume from the last processed chapter
- Clean up the state file when complete

## 📝 Content Validation

Every conversion includes automatic validation:

```
=== Conversion Content Integrity Report ===
Source file: my_novel.txt
Original characters: 123,456
Converted characters: 123,450
Match rate: 99.99%

✓ Content integrity verification passed
```

## 🎨 Supported Text Formats

### Chapter Title Formats

**Chinese:**
- `第一章 标题` (Traditional numbering)
- `第1章 标题` (Arabic numerals)
- `第001章 标题` (Zero-padded)
- `Chapter 1: 标题` (Mixed)

**English:**
- `Chapter 1: Title`
- `Chapter One: Title`
- `CHAPTER 1 - TITLE`
- `1. Title`

### Volume/Book Formats

- `第一卷 标题` / `第1卷 标题` (Chinese)
- `Volume 1: Title` / `Book 1: Title` (English)
- `Part I: Title` (Roman numerals)

## 🧪 Testing

Run the test suite:

```bash
# Install dev dependencies
pip install -e .[dev]

# Run tests
pytest

# Run with coverage
pytest --cov=txt_to_epub --cov-report=html
```

## 📚 Examples

Check the [examples](examples/) directory for complete examples:

- [basic_example.py](examples/basic_example.py) - Simple conversion
- [advanced_example.py](examples/advanced_example.py) - Custom configuration
- [batch_convert.py](examples/batch_convert.py) - Batch processing
- [README.md](examples/README.md) - Detailed example documentation

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone repository
git clone https://github.com/yourusername/txt-to-epub-converter.git
cd txt-to-epub-converter

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e .[dev]

# Run tests
pytest

# Format code
black src/txt_to_epub
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [EbookLib](https://github.com/aerkalov/ebooklib) - EPUB file generation
- [chardet](https://github.com/chardet/chardet) - Character encoding detection
- OpenAI - LLM assistance (optional)

## 📮 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/txt-to-epub-converter/issues)
- **Documentation**: [GitHub Wiki](https://github.com/yourusername/txt-to-epub-converter/wiki)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)

## 🗺️ Roadmap

- [ ] Support for more eBook formats (MOBI, PDF)
- [ ] GUI application
- [ ] Command-line interface (CLI)
- [ ] Cloud service integration
- [ ] Enhanced AI features (style analysis, content summarization)
- [ ] Multi-language UI

---

**Made with ❤️ by the TXT to EPUB Converter Team**

*Star ⭐ this repository if you find it helpful!*
