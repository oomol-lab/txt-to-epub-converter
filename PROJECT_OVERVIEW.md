# Project Overview

## TXT to EPUB Converter

A professional Python library for converting plain text files to beautifully formatted EPUB eBooks.

## 📁 Project Structure

```
txt-to-epub-converter/
│
├── src/txt_to_epub/          # Main library code
│   ├── __init__.py           # Package initialization & public API
│   ├── core.py               # Core conversion logic
│   ├── parser.py             # Chapter parsing & detection
│   ├── parser_config.py      # Configuration classes
│   ├── llm_parser_assistant.py  # AI-enhanced parsing
│   ├── html_generator.py     # EPUB content generation
│   ├── css.py                # Styling and typography
│   ├── data_structures.py    # Volume, Chapter, Section classes
│   ├── resume_state.py       # Checkpoint/resume functionality
│   └── word_count_validator.py  # Integrity validation
│
├── tests/                    # Test suite
│   ├── __init__.py
│   └── test_basic.py         # Basic functionality tests
│
├── examples/                 # Usage examples
│   ├── README.md             # Examples documentation
│   ├── basic_example.py      # Simple conversion
│   ├── advanced_example.py   # AI-enhanced conversion
│   └── batch_convert.py      # Batch processing
│
├── docs/                     # Documentation (future)
│
├── README.md                 # Main documentation
├── QUICKSTART.md             # Quick start guide
├── INSTALLATION.md           # Installation instructions
├── CHANGELOG.md              # Version history
├── CONTRIBUTING.md           # Contribution guidelines
├── LICENSE                   # MIT License
│
├── pyproject.toml            # Project metadata & dependencies
├── setup.py                  # Setup script
├── requirements.txt          # Runtime dependencies
├── requirements-dev.txt      # Development dependencies
├── MANIFEST.in               # Package data files
└── .gitignore                # Git ignore rules
```

## 🧩 Core Components

### 1. Core Module (`core.py`)
- Main conversion orchestration
- File I/O and encoding detection
- EPUB book creation and assembly
- Progress tracking

### 2. Parser (`parser.py`)
- Chapter detection using regex patterns
- Hierarchical structure parsing (Volumes → Chapters → Sections)
- Support for multiple chapter formats
- Confidence scoring for detections

### 3. LLM Assistant (`llm_parser_assistant.py`)
- OpenAI API integration
- AI-enhanced chapter detection
- Handles complex or ambiguous formats
- Confidence-based decision making

### 4. HTML Generator (`html_generator.py`)
- Converts parsed structure to HTML
- Creates chapter pages with proper styling
- Generates navigation structure

### 5. Configuration (`parser_config.py`)
- Centralized configuration management
- Tunable thresholds and parameters
- Easy customization

### 6. Resume Support (`resume_state.py`)
- Checkpoint creation during conversion
- Resume from interruption
- State persistence

### 7. Validator (`word_count_validator.py`)
- Word count verification
- Chapter integrity checks
- Detailed validation reports

## 🔄 Conversion Flow

```
1. Input TXT File
   ↓
2. Encoding Detection (chardet)
   ↓
3. Text Preprocessing
   ↓
4. TOC Detection & Analysis
   ↓
5. Chapter Parsing
   ├── Rule-based matching
   └── LLM assistance (optional)
   ↓
6. Structure Building (Volume/Chapter/Section)
   ↓
7. HTML Generation
   ↓
8. CSS Styling
   ↓
9. EPUB Assembly (EbookLib)
   ↓
10. Integrity Validation
    ↓
11. Output EPUB File
```

## 🎯 Key Features Implementation

### Smart Chapter Detection
- **Location**: `parser.py`
- **Method**: Regex pattern matching with confidence scoring
- **Supported formats**: Chinese (第X章), English (Chapter X), mixed

### AI Enhancement
- **Location**: `llm_parser_assistant.py`
- **Method**: OpenAI API calls with structured prompts
- **Trigger**: Based on confidence thresholds in `parser_config.py`

### Resume Support
- **Location**: `resume_state.py`
- **Method**: Pickle-based state persistence
- **Storage**: Temporary files with conversion state

### Validation
- **Location**: `word_count_validator.py`
- **Method**: Character count comparison between input and output
- **Report**: Detailed markdown report with statistics

## 🛠️ Development Workflow

### Adding a New Feature
1. Update relevant module in `src/txt_to_epub/`
2. Add tests in `tests/`
3. Add example in `examples/` if applicable
4. Update `CHANGELOG.md`
5. Update documentation

### Testing Strategy
- Unit tests for individual components
- Integration tests for full conversion
- Test various chapter formats
- Test edge cases (empty files, large files, special characters)

### Code Style
- Follow PEP 8
- Use Black for formatting
- Type hints where appropriate
- Comprehensive docstrings

## 📦 Distribution

### Building
```bash
python -m build
```

### Publishing to PyPI
```bash
twine upload dist/*
```

## 🚀 Future Roadmap

### Version 0.2.0
- [ ] CLI tool with rich UI
- [ ] More chapter format patterns
- [ ] Performance optimizations
- [ ] Expanded test coverage

### Version 0.3.0
- [ ] GUI application
- [ ] Plugin system for custom patterns
- [ ] Support for MOBI/AZW3 formats
- [ ] Web service API

### Version 1.0.0
- [ ] Stable API
- [ ] Complete documentation
- [ ] 90%+ test coverage
- [ ] Production-ready

## 📚 Resources

- **GitHub**: https://github.com/yourusername/txt-to-epub-converter
- **PyPI**: https://pypi.org/project/txt-to-epub-converter/
- **Issues**: https://github.com/yourusername/txt-to-epub-converter/issues
- **Documentation**: See README.md and QUICKSTART.md

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE) file.
