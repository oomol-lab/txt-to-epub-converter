# Quick Start Guide

Get started with TXT to EPUB Converter in 5 minutes!

## Installation

```bash
pip install txt-to-epub-converter
```

## Basic Usage

Create a Python file `convert.py`:

```python
from txt_to_epub import txt_to_epub

# Convert your text file
result = txt_to_epub(
    txt_file="mybook.txt",
    epub_file="mybook.epub",
    title="My Book",
    author="Your Name"
)

print(f"Done! Created: {result['output_file']}")
```

Run it:

```bash
python convert.py
```

That's it! You now have an EPUB file.

## With AI Enhancement

For better chapter detection:

```python
from txt_to_epub import txt_to_epub, ParserConfig

config = ParserConfig(
    enable_llm_assistance=True,
    llm_api_key="your-openai-key"
)

result = txt_to_epub(
    txt_file="mybook.txt",
    epub_file="mybook.epub",
    title="My Book",
    author="Your Name",
    config=config
)
```

## Next Steps

- Check out [examples/](examples/) for more usage patterns
- Read the full [README.md](README.md) for detailed documentation
- See [CONTRIBUTING.md](CONTRIBUTING.md) to contribute

## Common Issues

### "No chapters detected"
- Make sure your chapters have clear markers like "Chapter 1" or "第一章"
- Try enabling AI assistance with `enable_llm_assistance=True`

### "Encoding error"
- The library auto-detects encoding, but if it fails, save your file as UTF-8

### Performance is slow
- For large files, the first scan takes time
- Enable resume support: `enable_resume=True`
- Consider disabling AI for faster processing

## Need Help?

- Open an issue: https://github.com/yourusername/txt-to-epub-converter/issues
- Check FAQ in README.md
- See examples/ directory

Happy converting! 📚
