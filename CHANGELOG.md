# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned

- Add more unit tests
- Support for additional chapter formats
- Performance optimizations for large files
- CLI tool for command-line usage
- GUI application

## [0.1.2] - 2025-01-27

### Changed

- Cleaned up development files and debug scripts from repository
- Removed temporary debugging tools (debug_*.py scripts)
- Removed development utility scripts (convert_qm_fixed.py, translate_comments.py)
- Improved repository cleanliness for production release

## [0.1.1] - 2025-01-26

### Fixed

- Enhanced chapter processing logic to properly filter out already processed chapters in resume mode
- Improved inline chapter reference detection and filtering
- Fixed issue where already processed chapters were being re-enhanced

### Improved

- Removed unnecessary logging and improved code clarity in core parser modules
- Better handling of duplicate chapter titles with improved tracking
- Optimized chapter validation and filtering logic

### Enhancement

- Comprehensive content integrity validation for TXT to EPUB conversion
- Detailed validation report showing character count comparison before and after conversion
- Enhanced logging for filtered inline chapter references

## [0.1.0] - 2025-01-16

### Added
- Initial release of txt-to-epub-converter library
- Core conversion functionality from TXT to EPUB
- Intelligent chapter detection with regex patterns
- Support for multiple chapter formats (Chinese, English, mixed)
- AI-enhanced chapter detection using LLM
- Automatic encoding detection (UTF-8, GBK, GB18030, etc.)
- Resume support for interrupted conversions
- Word count and integrity validation
- Professional CSS styling for EPUB output
- Comprehensive configuration options via ParserConfig
- Support for custom cover images
- Hierarchical book structure (Volumes, Chapters, Sections)
- Detailed logging and progress reporting
- Python 3.10+ support

### Features
- **Smart Chapter Detection**: Automatically identifies chapters using pattern matching
- **LLM Integration**: Optional AI-powered analysis for complex chapter structures
- **Multi-format Support**: Handles various chapter numbering styles
- **Auto TOC Generation**: Creates hierarchical table of contents
- **Resume Capability**: Picks up from where conversion was interrupted
- **Encoding Detection**: Automatic detection and handling of various text encodings
- **Integrity Validation**: Validates word count and chapter completeness
- **Professional Output**: Beautiful typography and responsive layout

### Documentation
- Complete README with installation and usage instructions
- API reference documentation
- Multiple usage examples (basic, advanced, batch conversion)
- FAQ section
- Contributing guidelines

### Dependencies
- EbookLib >= 0.18
- chardet >= 5.2.0
- requests >= 2.32.0
- openai >= 1.0.0

## Notes

### Migration from Oomol Task
This library was extracted from the Oomol txt-to-epub task and refactored into a standalone Python package. Key changes include:

- Removed Oomol-specific dependencies (oocana)
- Simplified API for standalone usage
- Added comprehensive documentation
- Improved package structure following Python best practices
- Added development and testing infrastructure

### Future Plans
- Expand test coverage to 90%+
- Add CLI tool with rich terminal UI
- Support for more eBook formats (MOBI, AZW3)
- Performance optimization for very large files (>100MB)
- Plugin system for custom chapter patterns
- Web service API
- Docker container support

[Unreleased]: https://github.com/yourusername/txt-to-epub-converter/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/txt-to-epub-converter/releases/tag/v0.1.0
