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

## [0.2.9] - 2026-03-17

### Added

- Added optional `fusion_image_api_url` override so external callers can supply a custom Fusion image endpoint for AI cover and illustration generation

### Tests

- Added regression coverage for custom Fusion image endpoint propagation in cover generation and config plumbing

## [0.2.8] - 2026-03-05

### Changed

- Patch release for package publishing and version alignment

## [0.2.4] - 2026-03-04

### Fixed

- Fixed AI metadata/cover handoff for source-slug titles (for example `qm` from `qm.txt`) so resolved cover title/author correctly prefer AI-detected metadata instead of filename-like placeholders
- Unified `source_hint` propagation in conversion pipeline to keep metadata, cover, and illustration prompt context consistent

### Tests

- Added regression tests for source-slug title hint normalization and metadata resolution fallback behavior
- Added integration-style regression test to assert AI cover receives AI-resolved title/author when input title equals a short source slug

## [0.2.3] - 2026-03-04

### Fixed

- Eliminated transient progress flicker in multi-volume parsing by enforcing monotonic progress reporting at the conversion entrypoint
- Added multi-volume regression test to guarantee progress never moves backward

## [0.2.2] - 2026-03-04

### Fixed

- Fixed context progress regression where conversion progress could jump backward (for example from 95% to 10%)
- Added regression test to ensure reported progress is monotonic from start to finish

## [0.2.1] - 2026-03-04

### Changed

- Patch release for package publishing and version alignment

## [0.2.0] - 2026-03-04

### Changed

- Simplified illustration density configuration to four presets: `低` / `中` / `高` / `超高`
- Added preset alias support (`low`/`medium`/`high`/`ultra`) and unified density-policy resolution
- Unified AI conversion return payload under `result["ai"]`
- Added chapter-level illustration result details under `result["ai"]["illustration"]["chapter_results"]`

### Breaking Changes

- Removed legacy top-level AI result fields from conversion return values:
  - `ai_metadata_generated`
  - `ai_cover_generated`
  - `ai_illustrations_generated`
  - `ai_illustration_continuity_generated`
  - `ai_usage`
  - `ai_warnings`

## [0.1.4] - 2026-03-03

### Changed

- Set default `llm_base_url` to `https://llm.oomol.com/v1`
- Clarified API key guidance to use OOMOL Console (`https://console.oomol.com/`)
- Improved Fusion API routing rules for OOMOL base URLs

### Documentation

- Updated README and README_zh examples and parameter table for OOMOL defaults

### Tests

- Added coverage for default base URL and Fusion selection behavior

## [0.1.3] - 2026-03-03

### Added

- Enhanced AI capabilities for cover and illustration generation

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

[Unreleased]: https://github.com/yourusername/txt-to-epub-converter/compare/v0.2.9...HEAD
[0.2.9]: https://github.com/yourusername/txt-to-epub-converter/compare/v0.2.8...v0.2.9
[0.2.8]: https://github.com/yourusername/txt-to-epub-converter/compare/v0.2.4...v0.2.8
[0.2.4]: https://github.com/yourusername/txt-to-epub-converter/compare/v0.2.3...v0.2.4
[0.2.3]: https://github.com/yourusername/txt-to-epub-converter/compare/v0.2.2...v0.2.3
[0.2.2]: https://github.com/yourusername/txt-to-epub-converter/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/yourusername/txt-to-epub-converter/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/yourusername/txt-to-epub-converter/compare/v0.1.4...v0.2.0
[0.1.4]: https://github.com/yourusername/txt-to-epub-converter/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/yourusername/txt-to-epub-converter/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/yourusername/txt-to-epub-converter/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/yourusername/txt-to-epub-converter/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/yourusername/txt-to-epub-converter/releases/tag/v0.1.0
