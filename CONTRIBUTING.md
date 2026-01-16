# Contributing to TXT to EPUB Converter

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue on GitHub with:
- A clear, descriptive title
- Detailed steps to reproduce the problem
- Expected behavior vs actual behavior
- Your environment (OS, Python version, library version)
- Sample files if applicable (or minimal reproducible example)

### Suggesting Enhancements

Enhancement suggestions are welcome! Please create an issue with:
- A clear description of the enhancement
- Use cases and benefits
- Possible implementation approach (optional)

### Pull Requests

1. **Fork the repository** and create your branch from `main`
   ```bash
   git checkout -b feature/my-new-feature
   ```

2. **Install development dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

3. **Make your changes**
   - Write clear, readable code
   - Follow existing code style (PEP 8)
   - Add/update tests as needed
   - Update documentation if needed

4. **Run tests**
   ```bash
   pytest
   ```

5. **Format your code**
   ```bash
   black src/
   flake8 src/
   ```

6. **Commit your changes**
   ```bash
   git commit -m "Add some feature"
   ```
   
   Use clear commit messages:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation
   - `test:` for tests
   - `refactor:` for refactoring
   - `chore:` for maintenance

7. **Push and create Pull Request**
   ```bash
   git push origin feature/my-new-feature
   ```

### Code Style Guidelines

- Follow PEP 8 style guide
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and modular
- Add type hints where appropriate
- Write clear comments for complex logic

### Testing Guidelines

- Write tests for new features
- Ensure existing tests pass
- Aim for high test coverage
- Test edge cases and error conditions

### Documentation

- Update README.md if needed
- Add docstrings to new functions/classes
- Update CHANGELOG.md
- Add examples for new features

## Development Setup

```bash
# Clone repository
git clone https://github.com/yourusername/txt-to-epub-converter.git
cd txt-to-epub-converter

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Check code style
black src/ --check
flake8 src/
```

## Project Structure

```
txt-to-epub-converter/
├── src/txt_to_epub/     # Main library code
│   ├── core.py          # Core conversion logic
│   ├── parser.py        # Chapter parsing
│   ├── llm_parser_assistant.py  # LLM integration
│   └── ...
├── tests/               # Test files
├── examples/            # Usage examples
├── docs/                # Documentation
└── ...
```

## Questions?

Feel free to open an issue for questions or join discussions.

Thank you for contributing! 🎉
