# TXT 转 EPUB 转换器

[![PyPI version](https://badge.fury.io/py/txt-to-epub-converter.svg)](https://badge.fury.io/py/txt-to-epub-converter)
[![Python Versions](https://img.shields.io/pypi/pyversions/txt-to-epub-converter.svg)](https://pypi.org/project/txt-to-epub-converter/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

一个功能强大的 Python 库,用于将纯文本文件 (.txt) 转换为专业的 EPUB 电子书,支持智能章节检测和 AI 增强的结构分析。

中文文档 | [English](README.md)

升级说明: [0.2.0 升级指南](UPGRADE_0.2.0.md)

## ✨ 特性

- **📚 智能章节检测**: 使用模式匹配自动识别层级结构(卷、章、节)
- **🤖 AI 增强解析** (可选): 集成 OpenAI 兼容的 LLM,改进章节标题生成和结构分析
- **🎯 断点续传支持**: 内置检查点机制,支持中断后继续转换
- **🌍 多语言支持**: 处理中文(GB18030、GBK、UTF-8)和英文文本,自动检测编码
- **💧 水印支持**: 可选水印文本,用于版权保护
- **✅ 内容验证**: 自动字数验证,确保转换完整性
- **⚡ 进度跟踪**: 实时进度条,显示详细状态更新
- **🎨 专业排版**: 清晰易读的 EPUB 输出,带有合适的 CSS 样式

## 🚀 安装

### 从 PyPI 安装(推荐)

```bash
pip install txt-to-epub-converter
```

### 从源码安装

```bash
git clone https://github.com/yourusername/txt-to-epub-converter.git
cd txt-to-epub-converter
pip install -e .
```

### 可选依赖

启用 AI 增强解析功能(需要 OpenAI 兼容 API):

```bash
pip install txt-to-epub-converter[ai]
```

开发依赖:

```bash
pip install txt-to-epub-converter[dev]
```

## 📖 快速开始

### 基础用法

```python
from txt_to_epub import txt_to_epub

# 简单转换
result = txt_to_epub(
    txt_file="我的小说.txt",
    epub_file="output/我的小说.epub",
    title="我的小说",
    author="作者名"
)

print(f"转换完成: {result['output_file']}")
print(f"章节数: {result['chapters_count']}")
print(f"验证: {'✓ 通过' if result['validation_passed'] else '✗ 失败'}")
```

### 高级配置

```python
from txt_to_epub import txt_to_epub, ParserConfig

# 自定义配置
config = ParserConfig(
    # 章节检测模式
    chapter_patterns=[
        r'^第[0-9零一二三四五六七八九十百千]+章\s+.+$',  # 中文: 第1章 标题
        r'^Chapter\s+\d+[:\s]+.+$'                      # 英文: Chapter 1: Title
    ],

    # 启用 AI 辅助
    enable_llm_assistance=True,
    llm_api_key="your-api-key",  # 建议去 https://console.oomol.com/ 获取
    llm_base_url="https://llm.oomol.com/v1",
    llm_model="gpt-4o-mini",

    # 水印
    enable_watermark=True,
    watermark_text="© 2026 作者名. 版权所有.",

    # 内容过滤
    min_chapter_length=100,  # 每章最少字符数
    max_chapter_length=50000 # 每章最多字符数
)

# 使用自定义配置转换
result = txt_to_epub(
    txt_file="我的书.txt",
    epub_file="output/我的书.epub",
    title="我的书",
    author="作者名",
    cover_image="封面.jpg",  # 可选封面图片
    config=config,
    enable_resume=True       # 启用断点续传
)
```

## 🎯 使用场景

### 转换网络小说

完美适用于转换下载的网络小说,支持标准章节格式:

```python
from txt_to_epub import txt_to_epub

result = txt_to_epub(
    txt_file="网络小说.txt",
    epub_file="网络小说.epub",
    title="史诗奇幻小说",
    author="网络作者"
)
```

### 转换技术文档

处理具有层级结构的技术书籍:

```python
from txt_to_epub import txt_to_epub, ParserConfig

config = ParserConfig(
    volume_patterns=[r'^Part\s+\d+[:\s]+.+$'],
    chapter_patterns=[r'^Chapter\s+\d+[:\s]+.+$'],
    section_patterns=[r'^\d+\.\d+\s+.+$']
)

result = txt_to_epub(
    txt_file="编程指南.txt",
    epub_file="编程指南.epub",
    title="编程指南",
    author="技术作者",
    config=config
)
```

### 批量转换

高效转换多个文件:

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
            author="合集"
        )
        print(f"✓ 已转换: {txt_file.name}")
    except Exception as e:
        print(f"✗ 失败: {txt_file.name} - {e}")
```

## 🛠️ 配置选项

### ParserConfig 参数

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `chapter_patterns` | List[str] | 内置模式 | 章节检测的正则表达式 |
| `volume_patterns` | List[str] | 内置模式 | 卷检测的正则表达式 |
| `section_patterns` | List[str] | 内置模式 | 节检测的正则表达式 |
| `min_chapter_length` | int | 50 | 每章最少字符数 |
| `max_chapter_length` | int | 100000 | 每章最多字符数 |
| `enable_llm_assistance` | bool | False | 启用 AI 增强解析 |
| `llm_api_key` | str | None | API 密钥（建议从 https://console.oomol.com/ 获取） |
| `llm_base_url` | str | `https://llm.oomol.com/v1` | API 基础 URL |
| `llm_model` | str | "gpt-4o-mini" | 模型名称 |
| `enable_watermark` | bool | False | 启用水印 |
| `watermark_text` | str | None | 水印文本 |

### txt_to_epub() 参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `txt_file` | str | 是 | 输入 TXT 文件路径 |
| `epub_file` | str | 是 | 输出 EPUB 文件路径 |
| `title` | str | 否 | 书名（默认空字符串；启用 AI metadata 时可自动推断） |
| `author` | str | 否 | 作者名（默认空字符串；启用 AI metadata 时可自动推断） |
| `cover_image` | str | 否 | 封面图片路径(PNG/JPG) |
| `config` | ParserConfig | 否 | 自定义配置 |
| `show_progress` | bool | 否 | 显示进度条(默认: True) |
| `enable_resume` | bool | 否 | 启用断点续传(默认: False) |

## 📊 输出结构

转换器生成的 EPUB 文件具有以下结构:

```
output.epub
├── 第一卷: 标题
│   ├── 第1章: 标题
│   ├── 第2章: 标题
│   └── ...
├── 第二卷: 标题
│   └── ...
└── 第N章: 标题 (没有卷的独立章节)
    ├── 1.1节
    └── 1.2节
```

## 🤖 AI 增强功能

当 `enable_llm_assistance=True` 时:

1. **智能标题生成**: 为没有明确标题的章节生成描述性标题
2. **目录检测**: 自动移除冗余的目录部分
3. **批量处理**: 并行处理多个章节以提高效率
4. **成本跟踪**: 报告 API 使用情况和成本

AI 使用示例:

```python
from txt_to_epub import txt_to_epub, ParserConfig

config = ParserConfig(
    enable_llm_assistance=True,
    llm_api_key="sk-...",
    llm_model="gpt-4o-mini",  # 快速且经济实惠
    fusion_image_api_url="https://your-proxy.example.com/v1/image/generate"  # 可选：覆盖 Fusion 出图接口地址
)

result = txt_to_epub(
    txt_file="小说.txt",
    epub_file="小说.epub",
    title="我的小说",
    author="作者",
    config=config
)

# AI 使用统计会自动记录
```

## 🔄 断点续传功能

断点续传功能允许您继续被中断的转换:

```python
result = txt_to_epub(
    txt_file="大型书籍.txt",
    epub_file="大型书籍.epub",
    title="大型书籍",
    author="作者",
    enable_resume=True  # 启用断点续传
)
```

如果转换被中断(Ctrl+C、崩溃等),只需再次运行相同的命令。转换器会:
- 检测到之前的状态文件
- 验证源文件是否更改
- 从最后处理的章节继续
- 完成后清理状态文件

## 📝 内容验证

每次转换都包含自动验证:

```
=== 转换内容完整性报告 ===
源文件: 我的小说.txt
原始字符数: 123,456
转换后字符数: 123,450
匹配率: 99.99%

✓ 内容完整性验证通过
```

## 🎨 支持的文本格式

### 章节标题格式

**中文:**
- `第一章 标题` (传统数字)
- `第1章 标题` (阿拉伯数字)
- `第001章 标题` (零填充)
- `Chapter 1: 标题` (混合)

**英文:**
- `Chapter 1: Title`
- `Chapter One: Title`
- `CHAPTER 1 - TITLE`
- `1. Title`

### 卷/部格式

- `第一卷 标题` / `第1卷 标题` (中文)
- `Volume 1: Title` / `Book 1: Title` (英文)
- `Part I: Title` (罗马数字)

## 🧪 测试

运行测试套件:

```bash
# 安装开发依赖
pip install -e .[dev]

# 运行测试
pytest

# 运行覆盖率测试
pytest --cov=txt_to_epub --cov-report=html
```

## 📚 示例

查看 [examples](examples/) 目录获取完整示例:

- [basic_example.py](examples/basic_example.py) - 简单转换
- [advanced_example.py](examples/advanced_example.py) - 自定义配置
- [batch_convert.py](examples/batch_convert.py) - 批量处理
- [README.md](examples/README.md) - 详细示例文档

## 🤝 贡献

欢迎贡献! 请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解指南。

### 开发设置

```bash
# 克隆仓库
git clone https://github.com/yourusername/txt-to-epub-converter.git
cd txt-to-epub-converter

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装开发依赖
pip install -e .[dev]

# 运行测试
pytest

# 格式化代码
black src/txt_to_epub
```

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- [EbookLib](https://github.com/aerkalov/ebooklib) - EPUB 文件生成
- [chardet](https://github.com/chardet/chardet) - 字符编码检测
- OpenAI - LLM 辅助(可选)

## 📮 支持

- **问题**: [GitHub Issues](https://github.com/yourusername/txt-to-epub-converter/issues)
- **文档**: [GitHub Wiki](https://github.com/yourusername/txt-to-epub-converter/wiki)
- **更新日志**: [CHANGELOG.md](CHANGELOG.md)

## 🗺️ 路线图

- [ ] 支持更多电子书格式(MOBI、PDF)
- [ ] GUI 应用程序
- [ ] 命令行界面(CLI)
- [ ] 云服务集成
- [ ] 增强的 AI 功能(风格分析、内容摘要)
- [ ] 多语言 UI

---

**由 TXT to EPUB Converter 团队用 ❤️ 制作**

*如果觉得有帮助,请给仓库一个 ⭐ Star!*
