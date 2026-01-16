# Release Guide

This document describes the process for releasing a new version of txt-to-epub-converter.

## Pre-release Checklist

- [ ] All tests pass (`pytest`)
- [ ] Code is formatted (`black src/`)
- [ ] No linting errors (`flake8 src/`)
- [ ] Documentation is up to date
- [ ] CHANGELOG.md is updated
- [ ] Version number is bumped

## Version Numbering

We follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backwards-compatible)
- **PATCH**: Bug fixes (backwards-compatible)

## Release Process

### 1. Update Version Number

Update version in these files:
- `src/txt_to_epub/__init__.py`
- `pyproject.toml`

```python
# src/txt_to_epub/__init__.py
__version__ = "0.2.0"  # Update this
```

```toml
# pyproject.toml
[project]
version = "0.2.0"  # Update this
```

### 2. Update CHANGELOG.md

Add release notes:

```markdown
## [0.2.0] - 2025-01-20

### Added
- New feature X
- New feature Y

### Changed
- Improved Z

### Fixed
- Bug in component A
```

### 3. Commit Changes

```bash
git add .
git commit -m "chore: bump version to 0.2.0"
```

### 4. Create Git Tag

```bash
git tag -a v0.2.0 -m "Release version 0.2.0"
```

### 5. Build Distribution

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build
python -m build
```

This creates:
- `dist/txt_to_epub_converter-0.2.0.tar.gz` (source distribution)
- `dist/txt_to_epub_converter-0.2.0-py3-none-any.whl` (wheel distribution)

### 6. Test Installation Locally

```bash
# Create test environment
python -m venv test_env
source test_env/bin/activate

# Install from local build
pip install dist/txt_to_epub_converter-0.2.0-py3-none-any.whl

# Test import
python -c "from txt_to_epub import txt_to_epub; print('Success!')"

# Deactivate
deactivate
```

### 7. Upload to PyPI Test

```bash
# Upload to test PyPI first
twine upload --repository testpypi dist/*
```

Test installation from test PyPI:
```bash
pip install --index-url https://test.pypi.org/simple/ txt-to-epub-converter
```

### 8. Upload to PyPI

```bash
# Upload to production PyPI
twine upload dist/*
```

### 9. Push to GitHub

```bash
# Push commits and tags
git push origin main
git push origin v0.2.0
```

### 10. Create GitHub Release

1. Go to: https://github.com/yourusername/txt-to-epub-converter/releases/new
2. Select tag: `v0.2.0`
3. Title: `Release 0.2.0`
4. Description: Copy from CHANGELOG.md
5. Attach distribution files (optional)
6. Publish release

## Post-release

- [ ] Verify installation: `pip install txt-to-epub-converter`
- [ ] Check PyPI page: https://pypi.org/project/txt-to-epub-converter/
- [ ] Update documentation site (if applicable)
- [ ] Announce on social media/forums

## Hotfix Release

For urgent bug fixes:

1. Create hotfix branch from main
2. Make fixes
3. Follow release process with PATCH version bump
4. Merge back to main

## Rollback

If a release has critical issues:

```bash
# Remove from PyPI (can't undo!)
# Contact PyPI support if needed

# Revert git tag
git tag -d v0.2.0
git push origin :refs/tags/v0.2.0
```

## Tools Setup

### First-time Setup

```bash
# Install build tools
pip install build twine

# Configure PyPI credentials
# Option 1: Use token (recommended)
# Create token at: https://pypi.org/manage/account/token/
# Add to ~/.pypirc:
[pypi]
username = __token__
password = pypi-...

# Option 2: Use username/password
twine upload --username YOUR_USERNAME dist/*
```

## Troubleshooting

### Build fails
- Check pyproject.toml syntax
- Ensure all files are included in MANIFEST.in
- Clean build artifacts and retry

### Upload fails
- Verify credentials in ~/.pypirc
- Check version number (can't reupload same version)
- Ensure package name is not taken

### Import fails after installation
- Check package structure
- Verify __init__.py exports
- Test in clean environment

## Release Schedule

- **Major releases**: As needed for breaking changes
- **Minor releases**: Every 2-3 months for new features
- **Patch releases**: As needed for bug fixes

## Security Releases

For security issues:
1. Fix in private
2. Release patch ASAP
3. Notify users
4. Update security advisory
