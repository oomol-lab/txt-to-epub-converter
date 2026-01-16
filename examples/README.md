# Examples

This directory contains example scripts demonstrating how to use the txt-to-epub-converter library.

## Examples

### 1. basic_example.py
The simplest way to convert a text file to EPUB.

```bash
python basic_example.py
```

### 2. advanced_example.py
Convert with AI-enhanced chapter detection and custom configuration.

```bash
# Set your OpenAI API key
export OPENAI_API_KEY="your-api-key"
python advanced_example.py
```

### 3. batch_convert.py
Batch convert multiple TXT files in a directory.

```bash
# Basic batch conversion
python batch_convert.py ./books ./output

# With AI enhancement
python batch_convert.py ./books ./output --ai
```

## Sample Files

To try these examples, you need some TXT files. You can:

1. Use your own TXT files
2. Create a sample file with Chinese chapters
3. Create a sample file with English chapters

## Notes

- Make sure to install the library first: `pip install -e ..`
- For AI-enhanced examples, you need a valid OpenAI API key
- Output files will be created in the specified output directory
