# Installation Guide

## For Users

### From PyPI (Recommended)

```bash
pip install txt-to-epub-converter
```

### From Source

```bash
git clone https://github.com/yourusername/txt-to-epub-converter.git
cd txt-to-epub-converter
pip install -e .
```

## For Developers

### Clone and Setup

```bash
# Clone repository
git clone https://github.com/yourusername/txt-to-epub-converter.git
cd txt-to-epub-converter

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=txt_to_epub --cov-report=html

# View coverage report
open htmlcov/index.html  # On Mac
xdg-open htmlcov/index.html  # On Linux
start htmlcov/index.html  # On Windows
```

### Code Quality

```bash
# Format code
black src/

# Check style
flake8 src/

# Type checking
mypy src/
```

## Requirements

- Python 3.10 or higher
- pip (Python package installer)

### Dependencies

The library depends on:
- EbookLib (EPUB file handling)
- chardet (encoding detection)
- requests (HTTP requests for LLM APIs)
- openai (OpenAI API client, optional for AI features)

## Troubleshooting

### ImportError: No module named 'txt_to_epub'

Make sure you installed the package:
```bash
pip install txt-to-epub-converter
```

### Permission denied errors

Try installing with `--user` flag:
```bash
pip install --user txt-to-epub-converter
```

### Version conflicts

Create a fresh virtual environment:
```bash
python -m venv fresh_env
source fresh_env/bin/activate
pip install txt-to-epub-converter
```

## Upgrading

```bash
pip install --upgrade txt-to-epub-converter
```

## Uninstalling

```bash
pip uninstall txt-to-epub-converter
```
