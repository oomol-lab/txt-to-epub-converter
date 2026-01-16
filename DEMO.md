# Demo & Tutorial

Quick hands-on tutorial for txt-to-epub-converter.

## Setup

```bash
# Install the package
pip install txt-to-epub-converter

# Or install from source
pip install -e .
```

## Demo 1: Simple Conversion

Create a sample text file:

```bash
cat > sample.txt << 'END'
第一章 初识世界

这是第一章的内容。小明出生在一个普通的家庭，他的童年充满了欢声笑语。

第二章 成长的烦恼

随着年龄的增长，小明开始面对各种挑战。学业、友情、梦想，这些都让他感到困惑。

第三章 追寻梦想

经过深思熟虑，小明决定勇敢地追寻自己的梦想。他知道前路艰难，但他已经做好了准备。

第四章 重要的决定

在人生的十字路口，小明做出了一个重要的决定。这个决定将改变他的一生。

第五章 新的开始

告别过去，小明迎来了新的开始。虽然未来充满未知，但他充满希望。
END
```

Convert to EPUB:

```python
# demo1.py
from txt_to_epub import txt_to_epub

result = txt_to_epub(
    txt_file="sample.txt",
    epub_file="sample.epub",
    title="小明的故事",
    author="示例作者"
)

print(f"✓ Created: {result['output_file']}")
print(f"✓ Chapters: {result['chapter_count']}")
print(f"✓ Characters: {result['total_chars']}")
```

Run it:
```bash
python demo1.py
```

Result: `sample.epub` with 5 chapters!

## Demo 2: English Book

```bash
cat > english_book.txt << 'END'
Chapter 1: The Beginning

It was a dark and stormy night. John sat by the window, watching the rain pour down.

Chapter 2: The Journey

The next morning, John decided to embark on a journey that would change his life forever.

Chapter 3: Challenges

Along the way, John faced numerous challenges. Each one tested his resolve and determination.

Chapter 4: The Discovery

In a small village, John made an incredible discovery that answered all his questions.

Chapter 5: Return Home

With newfound wisdom, John returned home, ready to share what he had learned.
END
```

```python
# demo2.py
from txt_to_epub import txt_to_epub

result = txt_to_epub(
    txt_file="english_book.txt",
    epub_file="english_book.epub",
    title="John's Adventure",
    author="Demo Author"
)

print(f"✓ English book created: {result['output_file']}")
```

## Demo 3: With AI Enhancement

For complex formats, use AI:

```python
# demo3.py
import os
from txt_to_epub import txt_to_epub, ParserConfig

# Set your API key
os.environ['OPENAI_API_KEY'] = 'your-key-here'

config = ParserConfig(
    enable_llm_assistance=True,
    llm_api_key=os.environ.get('OPENAI_API_KEY'),
    llm_model="gpt-4"
)

result = txt_to_epub(
    txt_file="complex_book.txt",
    epub_file="complex_book.epub",
    title="Complex Format Book",
    author="Author",
    config=config
)

print(f"✓ AI-enhanced conversion complete!")
```

## Demo 4: With Cover Image

Add a professional cover:

```python
# demo4.py
from txt_to_epub import txt_to_epub

result = txt_to_epub(
    txt_file="sample.txt",
    epub_file="sample_with_cover.epub",
    title="小明的故事",
    author="示例作者",
    cover_image="cover.png"  # Add your cover image
)

print(f"✓ EPUB with cover created!")
```

## Demo 5: Batch Conversion

Convert multiple books:

```python
# demo5.py
from pathlib import Path
from txt_to_epub import txt_to_epub

input_dir = Path("books")
output_dir = Path("output")
output_dir.mkdir(exist_ok=True)

for txt_file in input_dir.glob("*.txt"):
    try:
        result = txt_to_epub(
            txt_file=str(txt_file),
            epub_file=str(output_dir / f"{txt_file.stem}.epub"),
            title=txt_file.stem,
            author="Various"
        )
        print(f"✓ {txt_file.name} -> {result['output_file']}")
    except Exception as e:
        print(f"✗ {txt_file.name}: {e}")
```

## Reading Your EPUBs

Open with:
- **Mac**: Apple Books
- **Windows**: Calibre, Adobe Digital Editions
- **Linux**: Calibre, FBReader
- **Mobile**: Apple Books, Google Play Books, Moon+ Reader

## Next Steps

1. Try the examples in `examples/` directory
2. Read the full documentation in `README.md`
3. Customize with `ParserConfig` options
4. Report issues or contribute!

## Tips

### Better Chapter Detection
- Use consistent formatting
- Clear chapter markers
- Enable AI for tricky formats

### Performance
- Disable AI for faster conversion
- Use resume for large files
- Process multiple files in parallel

### Customization
- Modify CSS in `src/txt_to_epub/css.py`
- Add custom chapter patterns in `parser.py`
- Tune thresholds in `ParserConfig`

Happy converting! 📚
